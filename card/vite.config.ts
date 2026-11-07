import { defineConfig } from "vitest/config";

// A release sets PIERPRESSURE_VERSION, as it does for the image; any other build is `dev`.
const version = process.env.PIERPRESSURE_VERSION?.trim() || "dev";

export default defineConfig({
  define: {
    __CARD_VERSION__: JSON.stringify(version),
  },
  build: {
    // One ES module with Lit inside it: Home Assistant loads a card from a single URL.
    lib: {
      entry: "src/pierpressure-card.ts",
      formats: ["es"],
      fileName: () => "pierpressure-card.js",
    },
  },
  test: {
    environment: "happy-dom",
  },
});
