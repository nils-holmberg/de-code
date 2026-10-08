#!/usr/bin/env python3
"""Validate the structural essentials of a static single-page PWA."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import struct
import sys
from urllib.parse import unquote, urlsplit


class AppHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.manifests: list[str] = []
        self.scripts: list[str] = []
        self.external_assets: list[str] = []
        self.has_viewport = False
        self.has_theme_color = False
        self.has_title = False
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag == "link":
            rels = values.get("rel", "").lower().split()
            href = values.get("href", "")
            if "manifest" in rels and href:
                self.manifests.append(href)
            if "stylesheet" in rels and is_external(href):
                self.external_assets.append(href)
        elif tag == "script":
            src = values.get("src", "")
            if src:
                self.scripts.append(src)
                if is_external(src):
                    self.external_assets.append(src)
        elif tag == "meta":
            name = values.get("name", "").lower()
            self.has_viewport |= name == "viewport"
            self.has_theme_color |= name == "theme-color"
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title and data.strip():
            self.has_title = True


def is_external(value: str) -> bool:
    return urlsplit(value).scheme in {"http", "https"}


def local_path(root: Path, source_file: Path, url: str) -> Path | None:
    split = urlsplit(url)
    if split.scheme or split.netloc or url.startswith("data:"):
        return None
    clean = unquote(split.path)
    if clean.startswith("/"):
        return root / clean.lstrip("/")
    return source_file.parent / clean


def png_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as handle:
            header = handle.read(24)
    except OSError:
        return None
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", header[16:24])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="Directory containing index.html")
    args = parser.parse_args()

    root = args.directory.expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []
    notes: list[str] = []

    index = root / "index.html"
    if not index.is_file():
        errors.append(f"missing {index}")
        return report(errors, warnings, notes)

    html = index.read_text(encoding="utf-8")
    parsed = AppHTMLParser()
    parsed.feed(html)

    if not parsed.has_title:
        errors.append("index.html has no non-empty <title>")
    if not parsed.has_viewport:
        errors.append("index.html has no viewport meta tag")
    if not parsed.has_theme_color:
        warnings.append("index.html has no theme-color meta tag")
    if re.search(r"user-scalable\s*=\s*no|maximum-scale\s*=\s*1", html, re.I):
        warnings.append("viewport appears to disable user zoom")

    if len(parsed.manifests) != 1:
        errors.append(f"expected one manifest link, found {len(parsed.manifests)}")
        manifest_path = None
    else:
        manifest_path = local_path(root, index, parsed.manifests[0])
        if manifest_path is None:
            errors.append("manifest must be a local host-served file")
        elif not manifest_path.is_file():
            errors.append(f"manifest link does not resolve: {manifest_path}")

    script_text = html
    for src in parsed.scripts:
        path = local_path(root, index, src)
        if path and path.is_file():
            script_text += "\n" + path.read_text(encoding="utf-8")

    registration = re.search(
        r"serviceWorker\s*\.\s*register\s*\(\s*(['\"])(.+?)\1",
        script_text,
        re.S,
    )
    sw_path: Path | None = None
    if not registration:
        errors.append("no static service-worker registration found in HTML or local scripts")
    else:
        sw_path = local_path(root, index, registration.group(2))
        if sw_path is None or not sw_path.is_file():
            errors.append(f"service-worker registration does not resolve: {registration.group(2)}")
        else:
            sw = sw_path.read_text(encoding="utf-8")
            for event in ("install", "activate", "fetch"):
                if not re.search(rf"addEventListener\s*\(\s*['\"]{event}['\"]", sw):
                    errors.append(f"service worker has no {event!r} event handler")
            if "caches.keys" in sw:
                deletes_every_other_cache = re.search(
                    r"filter\s*\(\s*\(?\w+\)?\s*=>\s*\w+\s*!==\s*CACHE_NAME",
                    sw,
                )
                has_owned_namespace = any(
                    marker in sw for marker in ("startsWith", "CACHE_PREFIX", "OWNED_CACHES")
                )
                if deletes_every_other_cache or not has_owned_namespace:
                    warnings.append("cache cleanup may delete caches belonging to sibling apps")

    if manifest_path and manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"manifest is not valid JSON: {exc}")
            manifest = {}

        for key in ("name", "short_name", "start_url", "scope", "display", "theme_color", "background_color", "icons"):
            if not manifest.get(key):
                errors.append(f"manifest is missing {key!r}")

        for key in ("start_url", "scope"):
            value = manifest.get(key)
            if isinstance(value, str) and value.startswith("/"):
                warnings.append(f"manifest {key} is root-relative; confirm it matches the hosted subpath")

        declared_sizes: set[tuple[int, int]] = set()
        for icon in manifest.get("icons", []) if isinstance(manifest.get("icons"), list) else []:
            if not isinstance(icon, dict) or not icon.get("src"):
                errors.append("manifest contains an icon without src")
                continue
            path = local_path(root, manifest_path, str(icon["src"]))
            if path is None:
                warnings.append(f"external or embedded manifest icon not inspected: {icon['src']}")
                continue
            if not path.is_file():
                errors.append(f"manifest icon does not resolve: {path}")
                continue
            sizes = str(icon.get("sizes", ""))
            if path.suffix.lower() == ".png":
                actual = png_dimensions(path)
                if actual is None:
                    errors.append(f"declared PNG is invalid: {path}")
                    continue
                declared_sizes.add(actual)
                if sizes != f"{actual[0]}x{actual[1]}":
                    errors.append(f"icon size mismatch for {path.name}: declared {sizes!r}, actual {actual[0]}x{actual[1]}")
        for required in ((192, 192), (512, 512)):
            if required not in declared_sizes:
                errors.append(f"manifest lacks an actual {required[0]}x{required[1]} PNG icon")

    if parsed.external_assets:
        unique = sorted(set(parsed.external_assets))
        warnings.append("external assets require deliberate offline handling: " + ", ".join(unique))

    if not errors:
        notes.append(f"PWA structure is valid: {root}")
    if sw_path:
        notes.append(f"service worker: {sw_path.relative_to(root) if sw_path.is_relative_to(root) else sw_path}")
    return report(errors, warnings, notes)


def report(errors: list[str], warnings: list[str], notes: list[str]) -> int:
    for message in errors:
        print(f"ERROR: {message}")
    for message in warnings:
        print(f"WARN: {message}")
    for message in notes:
        print(f"OK: {message}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
