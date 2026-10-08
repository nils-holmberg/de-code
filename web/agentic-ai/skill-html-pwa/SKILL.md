---
name: skill-html-pwa
description: Convert an existing single-page HTML web app into a branded, installable, mobile-compatible PWA and prepare or verify it on a static live host such as Netlify. Use when adapting a supplied HTML app rather than building an unrelated site from scratch.
---

# HTML app to hosted PWA

Turn the supplied single-page app into a real progressive web app while preserving its purpose and behavior. Treat branding, mobile usability, installability, offline behavior, host path, and live verification as one delivery problem.

## Establish the deployment shape

Before editing, inspect:

- the source HTML and its scripts, styles, assets, and existing behavior;
- supplied brand names, copy, colors, logos, favicons, and icons;
- the requested output directory;
- the host's publish root and the app's public URL path; and
- existing manifests, service workers, redirects, headers, and host configuration.

Infer straightforward details from the repository and requested URL. Ask only when a missing choice would materially change the product or deployment. Preserve the original source unless the user explicitly wants it edited in place.

Map the filesystem to the public URL explicitly. For example, if the publish root is `web/` and the target URL is `/app-building/pwas/de-code-regex/`, the app belongs in `web/app-building/pwas/de-code-regex/`.

## Preserve and brand the app

Keep the original app's useful interactions, content, saved state, and accessibility semantics unless the user requests a change. Apply requested branding consistently to:

- the document title, description, theme color, and mobile metadata;
- the visible primary title and subtitle;
- the header or app chrome;
- the favicon, application icons, and installed-app name; and
- focus, selection, match, and other primary highlight states.

Prefer supplied brand assets. Inspect them before use. Generate raster sizes from the supplied vector or highest-quality source when needed; do not merely rename a small bitmap as a larger icon.

## Build a real PWA

Create physical, host-served files rather than Blob URLs:

- `index.html`
- `manifest.webmanifest` (or a correctly linked JSON manifest)
- `sw.js`
- at least actual 192×192 and 512×512 PNG icons
- the supplied SVG or other logo assets used by the page

For an app hosted below the domain root, default to relative paths:

    {
      "id": "./",
      "start_url": "./",
      "scope": "./"
    }

Link resources with `./...` and register `./sw.js` with scope `./`. Avoid root-relative paths such as `/icons/icon.png` unless the asset intentionally lives at the origin root. A service worker cannot be registered from a `blob:` URL.

The manifest should include the requested name, a short name that fits launcher UI, description, `standalone` display mode, theme and background colors, and valid icon entries. Use `purpose: "any maskable"` only when the artwork stays legible inside the maskable safe area.

## Design offline behavior safely

Cache the local application shell during service-worker installation and provide a cached navigation fallback. Use a site-specific cache namespace and increment its version when shell files change.

When removing old caches, delete only caches owned by this app. Cache storage is origin-wide even though service-worker control is scoped; never delete every cache on a host that may contain sibling apps.

Browser storage is origin-wide as well: `localStorage`, `sessionStorage` and IndexedDB are shared by every app on the host. Give new keys and database names an app-specific prefix, such as `regexcraft_pattern`, and never clear all storage. Keep the source app's existing keys unless you also migrate their values, so users do not lose saved state.

Prefer local CSS, JavaScript, fonts, and icons for dependable offline startup. If the source relies on CDNs and retaining them is proportionate, explain that the first visit must be online and use runtime caching deliberately. Do not claim complete offline behavior until it has been tested with network access disabled.

## Make the existing UI mobile-compatible

Use a responsive viewport without disabling zoom. Keep primary body text readable, controls touch-friendly, focus visible, and text selectable where useful. Verify that:

- the title and essential brand copy remain visible;
- navigation condenses without becoming ambiguous;
- controls do not clip or overlap;
- intentional horizontal toolbars scroll without causing page-wide overflow;
- editors and results remain usable on a narrow portrait screen; and
- the layout also remains coherent at desktop width and 200% text enlargement.

Do not replace a functioning app with a landing page or put promotional content ahead of its primary activity.

## Prepare the host

The app requires HTTPS in production. Preserve the user's hosting provider and deployment workflow. Do not publish, push, or mutate a live host unless requested.

For Netlify-specific placement, MIME headers, and verification, read [references/netlify.md](references/netlify.md).

## Validate before handoff

Run the bundled validator:

    python scripts/validate_pwa.py /path/to/pwa

Then serve the app over HTTP; `file://` cannot validate service workers. Check at least one desktop and one narrow mobile viewport, exercise the app's primary interaction, and inspect the actual screenshots. Verify the manifest and every icon URL, service-worker registration and cache creation, reload behavior, and offline startup after an online load.

For a live URL, check response status and MIME types rather than assuming the upload path is correct. Confirm that HTML is served as HTML, the service worker as JavaScript, the manifest as `application/manifest+json` or another browser-accepted JSON type, and icons with their declared image types.

Report what was created, the public-path assumption, what was directly verified, and any remaining host-side action. Distinguish "prepared for deployment" from "deployed and live."
