// de-code-mcp, hosted: an MCP server for finding pages on the de-code website in plain language.
//
// The same server as web/agentic-ai/mcps/de-code-mcp/de_code_mcp.py (the local Python version),
// ported to TypeScript because Netlify Functions do not run Python. Tool names, parameters,
// descriptions and search scoring are kept identical; src/mcp-contract-test.py checks that both
// versions give the same results. Stateless and read-only: each POST to /mcp gets a fresh server
// with JSON responses, following Netlify's guide for MCP servers on Functions.
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/webStandardStreamableHttp.js";
import { z } from "zod";
import index from "../../web/site/index.json" with { type: "json" };

const VERSION = "0.1.0";
const WEIGHTS = { title: 5, headings: 3, description: 2, text: 1, type: 2 } as const;
const SKIP = new Set(["the", "and", "for", "can", "how", "what", "where", "which", "find", "site", "page", "about"]);

type Page = {
  url: string; title: string; description: string; section: string; type: string;
  headings: string[]; text: string;
};
const PAGES: Page[] = index.pages as Page[];
const BY_URL = new Map(PAGES.map((page) => [page.url, page]));

const count = (haystack: string, needle: string) => haystack.split(needle).length - 1;

function score(page: Page, words: string[]): number {
  const fields = {
    title: page.title.toLowerCase(),
    headings: page.headings.join(" ").toLowerCase(),
    description: page.description.toLowerCase(),
    text: page.text.toLowerCase(),
  };
  let total = 0;
  let matched = 0;
  for (const word of words) {
    // a word anywhere in a long text counts once, so long pages do not win by length
    const hits = {
      title: Math.min(count(fields.title, word), 3),
      headings: Math.min(count(fields.headings, word), 3),
      description: Math.min(count(fields.description, word), 3),
      text: Math.min(count(fields.text, word), 1),
      type: word === page.type ? 3 : 0, // "app", "slides", "download"
    };
    if (Object.values(hits).some((n) => n > 0)) matched += 1;
    for (const [name, n] of Object.entries(hits)) total += WEIGHTS[name as keyof typeof WEIGHTS] * n;
  }
  if (page.type === "slides") total /= 2; // prefer the web page over its slides
  return (total * matched) / words.length; // pages that match every word rank first
}

function searchSite(query: string, section = "", limit = 5) {
  let words = (query.toLowerCase().match(/[a-z0-9]+/g) ?? []).filter((w) => w.length > 2 && !SKIP.has(w));
  words = words.map((w) => (w.length > 3 && w.endsWith("s") ? w.slice(0, -1) : w)); // apps -> app
  if (words.length === 0) return [];
  const ranked = PAGES.filter((p) => !section || p.section === section)
    .map((page) => ({ points: score(page, words), page }))
    .sort((a, b) => b.points - a.points);
  const results: object[] = [];
  const seen = new Set<string>();
  for (const { points, page } of ranked) {
    if (points === 0 || results.length === limit) break;
    const base = page.url.replace("-slides.html", ".html");
    if (seen.has(base)) continue; // slides of a page already listed
    seen.add(base);
    const lower = page.text.toLowerCase();
    const positions = words.map((w) => lower.indexOf(w)).filter((i) => i >= 0);
    const at = positions.length ? Math.min(...positions) : 0;
    results.push({ title: page.title, url: page.url, type: page.type, section: page.section,
                   snippet: page.text.slice(Math.max(0, at - 80), at + 160) });
  }
  return results;
}

const json = (value: unknown) => ({ content: [{ type: "text" as const, text: JSON.stringify(value, null, 2) }] });

function buildServer(siteUrl: string) {
  const server = new McpServer({ name: "de-code-mcp", version: VERSION });

  server.registerTool("list_sections", {
    description: "List the sections of the de-code website, with their landing pages.",
  }, async () => json(index.sections.map(({ id, title, url, description }) => ({ id, title, url, description }))));

  server.registerTool("search_site", {
    description: "Search all pages, slides, apps and downloads on the de-code website.",
    inputSchema: {
      query: z.string().describe('What to look for, in plain words, e.g. "welch t-test" or "install app".'),
      section: z.string().default("").describe('Optional section id to search in, e.g. "coding" (see list_sections).'),
      limit: z.number().int().default(5).describe("How many results to return."),
    },
    outputSchema: { result: z.array(z.object({ title: z.string(), url: z.string(), type: z.string(),
                                               section: z.string(), snippet: z.string() })) },
  }, async ({ query, section, limit }) => {
    const result = searchSite(query, section, limit);
    return { ...json(result), structuredContent: { result } };
  });

  server.registerTool("get_page", {
    description: "Get one page's description, headings and text, to answer from its content.",
    inputSchema: { url: z.string().describe("The page's full URL, as returned by search_site.") },
  }, async ({ url }) => {
    const page = BY_URL.get(url);
    if (!page) {
      // a thrown error becomes a tool error whose message the agent sees
      throw new Error(`No page with that URL in the site index: ${url}. Use search_site first.`);
    }
    const { title, description, headings, text } = page;
    return json({ title, url: page.url, description, headings, text });
  });

  server.registerResource("overview", "site://llms.txt", {
    description: "The site's llms.txt: every section and page, with one-line descriptions.",
    mimeType: "text/plain",
  }, async (uri) => {
    const response = await fetch(new URL("/llms.txt", siteUrl));
    return { contents: [{ uri: uri.href, mimeType: "text/plain", text: await response.text() }] };
  });

  return server;
}

export default async (req: Request) => {
  if (req.method !== "POST") {
    // a GET would make the transport open a stream that a serverless function cannot keep open
    return new Response(
      "This is de-code-mcp, an MCP server for the de-code website (POST only).\n" +
      "Add it to an agent, e.g.: agy mcp add de-code-mcp https://de-code-ai.netlify.app/mcp\n",
      { status: 405, headers: { Allow: "POST", "Content-Type": "text/plain; charset=utf-8" } },
    );
  }
  const server = buildServer(req.url);
  const transport = new WebStandardStreamableHTTPServerTransport({
    sessionIdGenerator: undefined, // stateless: every request stands alone
    enableJsonResponse: true,      // one JSON reply instead of an event stream
  });
  await server.connect(transport);
  return transport.handleRequest(req);
};

export const config = {
  path: "/mcp",
  // 600 requests a minute per visitor (IP), then 429: a classroom often shares one IP, and
  // each agent question takes several requests; still a cap against runaway use
  rateLimit: { windowLimit: 600, windowSize: 60, aggregateBy: ["ip", "domain"] },
};
