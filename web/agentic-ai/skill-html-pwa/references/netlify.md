# Netlify deployment notes

Read this reference when the target host is Netlify or when reviewing a Netlify deployment.

## Publish-root mapping

Determine the publish directory from `netlify.toml`, the Netlify UI configuration, build output, or the correspondence between repository files and live URLs. A URL such as:

    https://example.netlify.app/app-building/pwas/de-code-regex/

maps to this location when `web/` is the publish root:

    web/app-building/pwas/de-code-regex/index.html

Netlify normally serves a directory's `index.html`; a redirect is not needed for an ordinary static app directory.

## Custom response headers

Netlify processes `_headers` only when it reaches the publish directory. Put it at the publish root, not inside the nested PWA directory, unless that nested directory itself is the configured publish root.

If a `.webmanifest` file is served as `application/octet-stream`, add a narrow rule such as:

    /app-building/pwas/de-code-regex/manifest.webmanifest
      Content-Type: application/manifest+json; charset=UTF-8

Merge with an existing `_headers` file rather than replacing unrelated rules. Do not add `Service-Worker-Allowed` when `sw.js` sits inside the app directory and uses the same relative scope; its default scope is already sufficient.

The HTML can also identify the manifest type:

    <link rel="manifest" type="application/manifest+json" href="./manifest.webmanifest">

The response header remains the authoritative hosting fix.

## Live verification

After the deployment finishes, verify the exact public URLs:

    curl -I https://example.netlify.app/app-building/pwas/de-code-regex/
    curl -I https://example.netlify.app/app-building/pwas/de-code-regex/manifest.webmanifest
    curl -I https://example.netlify.app/app-building/pwas/de-code-regex/sw.js
    curl -I https://example.netlify.app/app-building/pwas/de-code-regex/icons/icon-192.png
    curl -I https://example.netlify.app/app-building/pwas/de-code-regex/icons/icon-512.png

Expected essentials:

- all responses return `200`;
- the manifest uses `application/manifest+json` (or at least an appropriate JSON type);
- `sw.js` uses a JavaScript MIME type;
- the PNG icons use `image/png`; and
- HTTPS is active.

Render the live URL at desktop and mobile sizes. A successful `curl` request does not prove that CDN dependencies loaded, the layout works, or the service worker registered.

When testing a fresh installation, uninstall the app and clear that origin's site data. Removing only the home-screen icon may leave the old service worker, cache, and local storage in place.
