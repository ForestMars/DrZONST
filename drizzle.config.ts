import type { defineConfig } from "drizzle-kit";

export default defineConfig {
  schema: "./src/db/schemas/*",
  out: "./drizzle/migrations",
  driver: "pg",
  dbCredentials: {
    connectionString: process.env.DATABASE_URL!,
  },
  verbose: true,
  strict: true,
}
