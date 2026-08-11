# de-code design system

Rules extracted from the pages as built (`web/index.html`, `web/data-analysis.html`,
`web/app-building.html`, `web/education.html`, `web/resn-dev/index.html`,
`web/data-analysis/ailund.html`). This file is the reference; `web/assets/design.css`
is the same rules as code.

The system is deliberately small: four colors, one font stack, one grid unit, one
breakpoint. A page should be buildable from this document without looking at
another page.

## 1. Tokens

Declared on `:root` in every page.

| Token     | Value       | Role                                          |
| --------- | ----------- | --------------------------------------------- |
| `--lime`  | `limegreen` | Brand accent: CTAs, headline spans, card `h3` |
| `--dark`  | `#222`      | Body text, header, footer, cards, dark blocks |
| `--light` | `#fff`      | Page background, text on dark                 |
| `--soft`  | `#f4f4f4`   | Hero band background only                     |

There is no fifth color. Greys other than `--soft` do not appear; borders are
`--dark`, never a light grey.

`* { box-sizing: border-box; }` is set globally.

## 2. Typography

- Family: `Arial, sans-serif` — system stack, no web fonts, no external font loads.
- `line-height: 1.6` on `body`; `1.1` on `h1`.
- `h1` 3.5rem (2.5rem under 800px), `.section-title` 2.2rem, hero `p` 1.2rem,
  `.section-lead` 1.1rem, body 1rem.
- Hero `h1` contains exactly one `<span>` in `--lime` — the accent word, never the
  whole heading.
- Bold body emphasis uses `<strong>`; do not add colour to emphasis.

## 3. Layout

- **Page gutter: `8%`** on every full-width element (`header`, `section`, `footer`).
  Nothing is centred in a fixed-width container.
- `section` padding: `5rem 8%`. Hero padding: `6rem 8%`.
- Prose measure: hero `p` `max-width: 650px`, `.section-lead` and `.band p`
  `max-width: 760px`. Never let text run the full 84% content width.
- Grid gaps: `1rem` between blocks, `1.5rem` between cards, `3rem` between hero
  columns.

### Block geometry

The abstract blocks are the visual signature. One unit is **130px**, gap **1rem**,
radius **12px**. Derived sizes must be computed from those, not guessed:

- 1×1 block: `130px`
- 2×2 patch: `2 × 130 + 16 = 276px`

`border-radius` is `12px` on blocks and cards, `6px` on buttons and the header logo.

## 4. Components

### Header

Dark bar, `1.5rem 8%`, flex with `justify-content: space-between`. Left: `.logo`
(2.2rem square mark, `6px` radius, `0.7rem` gap, 1.6rem bold lime wordmark) linking
to `/`. Right: `nav` links in `--light`, `margin-left: 1.5rem`, no underline.
`nav` is hidden below 800px — the logo remains the only navigation.

### Buttons

`.button`: lime fill, `--dark` text, bold, `0.9rem 1.4rem`, `6px` radius,
`margin-top: 1.5rem`, `display: inline-block`.

`.button.alt`: transparent fill, `3px solid var(--dark)` border, dark text. Use for
the secondary action only; never two lime buttons side by side.

### Blocks and the abstract grid

`.abstract` is `repeat(3, 1fr)` with `1rem` gap, filled with six `.block`s
(`min-height: 130px`). Modifiers: `.lime`, `.dark`, `.white` (white fill plus
`3px solid var(--dark)` — a white block is always outlined, since the page is white).

Exactly **one** block per page carries the brand mark, via a `.brand` modifier that
composites an avatar SVG over the block's own background colour.

### Cards

`.services` grid, `repeat(3, 1fr)`, `1.5rem` gap. `.card` is `--dark` background,
`--light` text, `2rem` padding, `12px` radius, with a lime `h3` (`margin-top: 0`).
Card links inherit colour and underline on hover only.

### Band

`.band` is a full-bleed lime section with centred bold 1.25rem text, `max-width: 760px`,
used once per page for a single statement of principle.

### Footer

Dark, centred, `2rem 8%`, one line of copy.

## 5. Hero variants

Every landing page runs the same hero recipe with **one deliberate variation** — the
variation is the page's identity, so pick one and change nothing else.

| Page               | Variation                                                       |
| ------------------ | --------------------------------------------------------------- |
| `index.html`       | `1.2fr 1fr`, 3×2 abstract right; brand on the **lime** block     |
| `data-analysis`    | same grid; brand moved to the **dark** block                     |
| `app-building`     | same grid; brand on a different block again                      |
| `education.html`   | **three columns** — 276px brand panel left, copy centre, two 130px blocks far right |

Rules for a new variant:

- Keep `gap: 3rem`, `align-items: center`, and the `--soft` background.
- Blocks may move, recolour, or regroup; the 130px unit and 12px radius may not change.
- Side clusters that should read as "pinned to the top" use `align-self: start` on
  the cluster, not a margin.

## 6. Brand assets

Graphics are served from the **resn-dev** repo, not from `web/assets/`:

```
https://nils-holmberg.github.io/resn-dev/res/avatar/<file>
```

`resn.dev` cannot be used as the asset base: its document root is that repo's `web/`
directory, so `resn.dev/res/...` returns 404. Revisit if `res/` is added to the
publish directory.

### SVG naming: `avatar-256-<field>-<chars>.svg`

Field first, characters second:

- `transparent-green` — green characters, transparent field (composite over any colour)
- `transparent-white` — white characters, transparent field
- `green-transparent` — solid green square with the characters knocked out
- `black-white` — black field, white characters

The two halves are not interchangeable: `green-transparent` and `transparent-green`
are inverses of each other. Check which one a block needs before wiring it up.

Compositing over a coloured block:

```css
.dark.brand {
  background: var(--dark) url("<base>/avatar-256-transparent-green.svg")
              center / contain no-repeat;
}
```

Use `contain` for a block that is mostly mark; a fixed percentage (e.g. `72%`) when
the mark should sit inside a larger panel with breathing room.

### Remote first, local as incomplete backup

**The resn-dev repo is the single source of truth for brand graphics.** It is the
superset: every SVG, PNG, and PDF variant, all favicon sizes, plus material that was
never copied locally at all.

`web/assets/` holds an older, partial copy — an **incomplete backup**, not a mirror.
It is missing variants (`avatar-256-transparent-green.svg` had to be generated by
hand before we switched), and nothing keeps it in step with the repo. Maintaining
both was the reason for the move.

Rules:

- New pages reference remote URLs only, and add nothing to `web/assets/`.
- Existing pages keep their local references until migrated deliberately; a
  half-migrated page is worse than either state.
- Never fix a missing graphic by copying a file into `web/assets/`. Push it to the
  resn-dev repo and point at it.
- Retire local files only once no page references them, checked with
  `grep -rn "assets/" web/`.

The trade this accepts: brand graphics now depend on an origin the site does not
control, with no automatic fallback — if that host is unreachable, logos and favicons
fail across every migrated page while the pages themselves still render. That is the
known cost of removing the duplicate maintenance.

`web/assets/` is **not** deprecated as a directory: `design.css` lives there and is
de-code's own, duplicated nowhere. The deprecation is about graphics only.

## 7. Links

### Inline text links

Prose links use `.link`: the word keeps the surrounding text colour and carries a
`3px` lime underline at `4px` offset. On hover and keyboard focus the whole word
fills lime with `--dark` text and the rule turns dark — the same lime-block language
as the abstract grid, at word scale.

```html
provided by <a class="link" href="...">resn.dev</a>
```

Because `.link` inherits `color` and only recolours on hover, it works unchanged in
prose, in a `.card`, and on the dark footer. Do not colour link text lime at rest:
lime is reserved for CTAs and headline accents, and lime-on-white body text fails
contrast.

Navigation links, card-title links, and `.button` are separate patterns — `.link` is
for links inside sentences only.

### Target rules

- External destinations: `target="_blank" rel="noopener noreferrer"`. The `rel` is
  not optional; it prevents the opened page reaching back via `window.opener`.
- Internal destinations: same tab, no `target`.
- Header logo always points at `/`.
- Contact CTAs are `mailto:nils.holmberg@yahoo.com`.
- The live site `https://de-code-ai.netlify.app/` is **not** an external destination:
  it is this site. Link it same-tab, even when written as an absolute URL.

## 8. Responsive

One breakpoint: `@media (max-width: 800px)`.

- `.hero` and `.services` collapse to `1fr`.
- `nav { display: none; }`
- `.hero h1` drops to 2.5rem.
- Fixed-size block clusters re-flow to a row (`grid-template-columns: repeat(2, auto)`
  plus `justify-content: start`) rather than stacking into a tall column.

Nothing else changes. There is no tablet tier and no desktop max-width.

## 9. Page structure

Landing page: `header` → `.hero` → topic `section`(s) → optional `.band` →
`#contact` section → `footer`.

Subpages live in a directory named for the parent page (`education/quarto.html`,
`data-analysis/ailund.html`), link back to the parent with a `.button.alt`, and use
`../` for internal links while brand assets stay absolute.

## 10. Applying the system

**New pages link the stylesheet. They do not carry an inline `<style>` block.**

```html
<link rel="stylesheet" href="assets/design.css" />        <!-- web/*.html -->
<link rel="stylesheet" href="../assets/design.css" />     <!-- web/<topic>/*.html -->
```

`web/education.html` is the reference implementation: 71 lines of markup, no CSS.

- A page-specific hero variant belongs in `design.css` as a modifier class
  (`.hero.hero-panel`), not as an inline override. The variation is part of the
  system, so it is documented in §5 and shipped in the stylesheet.
- Genuinely one-off styling — a page with an embedded notebook, say — goes in a small
  inline block *after* the link tag, holding only what is unique to that page.
- Never redefine a token locally. If a page needs a colour the tokens do not provide,
  that is a system decision, not a page decision.

### Migrating a legacy page

The other pages still carry inline styles. Convert them **one at a time**, never in
bulk: each has small deliberate differences, and a half-converted page is worse than
either state (§6).

Procedure, per page:

1. Screenshot the page before the change (headless, desktop and 390px mobile).
2. Replace the `<style>` block with the link tag; add whatever modifier class the
   page's hero variant needs.
3. Screenshot again and diff. **Expect zero differing pixels** — anything else means
   the page had a difference the system does not yet capture. Document it in §5 and
   add the modifier, or revert.

```bash
chromium --headless --disable-gpu --hide-scrollbars --window-size=1440,1600 \
  --screenshot=after.png --virtual-time-budget=6000 "file://$PWD/web/<page>.html"
compare -metric AE before.png after.png null:
```

A page that cannot reach a zero-pixel diff is telling you the system is incomplete.
Fix the system, then migrate the page.
