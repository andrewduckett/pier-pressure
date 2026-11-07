import { mkdtemp, readdir, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { build } from "vite";

const root = join(import.meta.dirname, "..");

async function buildCard(version: string | undefined, outDir: string): Promise<string[]> {
  const saved = process.env.PIERPRESSURE_VERSION;
  if (version === undefined) delete process.env.PIERPRESSURE_VERSION;
  else process.env.PIERPRESSURE_VERSION = version;
  try {
    // The config reads the version when it loads, so each build loads it afresh.
    await build({ root, logLevel: "silent", build: { outDir, emptyOutDir: true } });
  } finally {
    if (saved === undefined) delete process.env.PIERPRESSURE_VERSION;
    else process.env.PIERPRESSURE_VERSION = saved;
  }
  return readdir(outDir);
}

describe("the card build", () => {
  let outDir: string;

  beforeEach(async () => {
    outDir = await mkdtemp(join(tmpdir(), "pierpressure-card-"));
  });

  afterEach(async () => {
    await rm(outDir, { recursive: true, force: true });
  });

  it("writes one JavaScript file", async () => {
    const files = await buildCard(undefined, outDir);

    expect(files.filter((name) => name.endsWith(".js"))).toEqual(["pierpressure-card.js"]);
  });

  it("bundles every library into the file", async () => {
    await buildCard(undefined, outDir);
    const code = await readFile(join(outDir, "pierpressure-card.js"), "utf8");

    expect(code).not.toMatch(/^\s*import\b/m);
    expect(code).not.toMatch(/\bimport\s*\(/);
    expect(code).toContain("litHtmlVersions");
  });

  it("stamps the release version", async () => {
    await buildCard("2026.11.0", outDir);
    const code = await readFile(join(outDir, "pierpressure-card.js"), "utf8");

    expect(code).toContain("2026.11.0");
  });

  it.each([undefined, "", "  "])("stamps dev when the version is %j", async (version) => {
    await buildCard(version, outDir);
    const code = await readFile(join(outDir, "pierpressure-card.js"), "utf8");

    expect(code).toContain('"dev"');
  });
});
