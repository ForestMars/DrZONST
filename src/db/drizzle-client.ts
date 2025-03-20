// drizzle-client.ts
// Not actively used in Dr ZONST (which uses Supabase instead)

import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import * as schema from "./schemas";

const client = postgres(process.env.DATABASE_URL!);
export const db = drizzle(client, { schema });
