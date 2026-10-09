"""de-code-mcp: an MCP server for finding pages on the de-code website in plain language."""
import json
import os
import re
from urllib.request import urlopen

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

SITE = "https://de-code-ai.netlify.app"
INDEX_SOURCE = os.environ.get("SITE_INDEX", f"{SITE}/site/index.json")
LLMS_SOURCE = os.environ.get("SITE_LLMS", f"{SITE}/llms.txt")
WEIGHTS = {"title": 5, "headings": 3, "description": 2, "text": 1, "type": 2}
SKIP = {"the", "and", "for", "can", "how", "what", "where", "which", "find", "site", "page", "about"}

mcp = MCPServer("de-code-mcp")


def read(source: str) -> str:
    """Read a URL or a local file as text."""
    if source.startswith("http"):
        with urlopen(source, timeout=20) as response:
            return response.read().decode("utf-8")
    with open(source, encoding="utf-8") as f:
        return f.read()


INDEX = json.loads(read(INDEX_SOURCE))       # loaded once, kept in memory
PAGES = {page["url"]: page for page in INDEX["pages"]}


def score(page: dict, words: list[str]) -> float:
    fields = {"title": page["title"], "headings": " ".join(page["headings"]),
              "description": page["description"], "text": page["text"]}
    fields = {name: value.lower() for name, value in fields.items()}
    total, matched = 0, 0
    for word in words:
        # a word anywhere in a long text counts once, so long pages do not win by length
        hits = {name: min(value.count(word), 1 if name == "text" else 3) for name, value in fields.items()}
        hits["type"] = 3 if word == page["type"] else 0     # "app", "slides", "download"
        if any(hits.values()):
            matched += 1
        total += sum(WEIGHTS[name] * n for name, n in hits.items())
    if page["type"] == "slides":
        total /= 2                                # prefer the web page over its slides
    return total * matched / len(words)           # pages that match every word rank first


@mcp.tool()
def list_sections() -> list[dict]:
    """List the sections of the de-code website, with their landing pages."""
    return [{"id": s["id"], "title": s["title"], "url": s["url"], "description": s["description"]}
            for s in INDEX["sections"]]


@mcp.tool()
def search_site(query: str, section: str = "", limit: int = 5) -> list[dict]:
    """Search all pages, slides, apps and downloads on the de-code website.

    Args:
        query: What to look for, in plain words, e.g. "welch t-test" or "install app".
        section: Optional section id to search in, e.g. "coding" (see list_sections).
        limit: How many results to return.
    """
    words = [w for w in re.findall(r"[a-z0-9]+", query.lower()) if len(w) > 2 and w not in SKIP]
    words = [w[:-1] if len(w) > 3 and w.endswith("s") else w for w in words]   # apps -> app
    if not words:
        return []
    ranked = sorted(((score(p, words), p) for p in INDEX["pages"]
                     if not section or p["section"] == section), key=lambda x: -x[0])
    results = []
    seen = set()
    for points, page in ranked:
        if points == 0 or len(results) == limit:
            break
        base = page["url"].replace("-slides.html", ".html")
        if base in seen:
            continue                                # slides of a page already listed
        seen.add(base)
        text = page["text"]
        at = min([i for i in (text.lower().find(w) for w in words) if i >= 0], default=0)
        results.append({"title": page["title"], "url": page["url"], "type": page["type"],
                        "section": page["section"], "snippet": text[max(0, at - 80):at + 160]})
    return results


@mcp.tool()
def get_page(url: str) -> dict:
    """Get one page's description, headings and text, to answer from its content.

    Args:
        url: The page's full URL, as returned by search_site.
    """
    page = PAGES.get(url)
    if page is None:
        # a ToolError is a deliberate error, and the agent sees its message
        raise ToolError(f"No page with that URL in the site index: {url}. Use search_site first.")
    return {key: page[key] for key in ("title", "url", "description", "headings", "text")}


@mcp.resource("site://llms.txt")
def overview() -> str:
    """The site's llms.txt: every section and page, with one-line descriptions."""
    return read(LLMS_SOURCE)


def main():
    mcp.run()  # local server: talks to the host over stdin/stdout


if __name__ == "__main__":
    main()
