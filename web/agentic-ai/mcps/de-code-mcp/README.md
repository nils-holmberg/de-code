# de-code-mcp

An MCP server for finding pages on the [de-code website](https://de-code-ai.netlify.app/)
in plain language. Add it to an AI agent such as Antigravity, then ask questions like
*"Where on de-code can I learn about Welch's t-test?"* — the agent searches the site with
these tools and answers with real links.

| What | Kind | What the agent gets |
|---|---|---|
| `list_sections()` | tool | the site's sections and their landing pages |
| `search_site(query, section, limit)` | tool | the best-matching pages: title, link, type and a short snippet |
| `get_page(url)` | tool | one page's headings and text, to answer from its content |
| `site://llms.txt` | resource | the overview of the whole site |

The server reads the site's published content index,
<https://de-code-ai.netlify.app/site/index.json>, once at start-up. Set `SITE_INDEX` (and
`SITE_LLMS`) to a file path or URL to use another copy.

It is explained step by step in session 5 of the skill school,
[section 2.5](https://de-code-ai.netlify.app/coding/skill-school/sessions/05-skills-mcp.html#an-mcp-server-for-this-website).

## Run it

**With uv** (no Python setup and no download; [uv](https://docs.astral.sh/uv/) fetches what it needs):

    uvx --from "git+https://github.com/nils-holmberg/de-code#subdirectory=web/agentic-ai/mcps/de-code-mcp" de-code-mcp

**With Python 3.10 or newer**, from this folder:

    pip install -r requirements.txt
    python de_code_mcp.py

**In Colab**, without installing anything locally: see the test cell in session 5, section 2.5.

The server talks to its host over stdin/stdout, so starting it by hand just waits for input.
Let the agent start it instead.

## Add it to Antigravity

    agy mcp add de-code-mcp uvx --from "git+https://github.com/nils-holmberg/de-code#subdirectory=web/agentic-ai/mcps/de-code-mcp" de-code-mcp

or, with Python and this folder on your computer:

    agy mcp add de-code-mcp python /full/path/to/de_code_mcp.py

Check with `agy mcp list`, or try the tools by hand in the MCP Inspector: `mcp dev de_code_mcp.py`.

## Other agents

The same command works in any MCP client; only the way to add it differs:

    claude mcp add de-code-mcp -- uvx --from "git+https://github.com/nils-holmberg/de-code#subdirectory=web/agentic-ai/mcps/de-code-mcp" de-code-mcp
    codex mcp add de-code-mcp -- uvx --from "git+https://github.com/nils-holmberg/de-code#subdirectory=web/agentic-ai/mcps/de-code-mcp" de-code-mcp

The first start downloads the package and its dependencies. If an agent gives up waiting,
run the `uvx` command once in a terminal (Ctrl+C to stop), then start the agent again.

Adding again is safe in Antigravity and Codex (the entry is updated); Claude Code answers
"already exists" and changes nothing, so remove the server first to replace it.

## Remove it

    agy mcp remove de-code-mcp
    claude mcp remove de-code-mcp
    codex mcp remove de-code-mcp

ChatGPT on the web only connects to remote MCP servers at a public HTTPS address, so it
cannot start this local server. A hosted version would work there as a custom connector
without authentication, since the server only reads public pages.
