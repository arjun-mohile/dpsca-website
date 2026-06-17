import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";

// https://astro.build/config
export default defineConfig({
  site: "https://dpsca.in",
  integrations: [sitemap()],
  server: { port: 4321, open: true },
});
