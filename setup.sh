#!/bin/bash

# Function to handle Ctrl+C (SIGINT) and clean exit
trap 'echo "Exiting setup script..."; exit 0' SIGINT

# Check for -y flag in arguments
AUTO_YES=false
if [[ "$1" == "-y" ]]; then
  AUTO_YES=true
fi

# Function to prompt user for confirmation
confirm() {
  # If AUTO_YES is true, print the step description and automatically answer "yes"
  if [ "$AUTO_YES" = true ]; then
    echo "$1"
    echo "Automatically answering 'yes' to this prompt."
    return 0  # Automatically answer 'yes'
  fi
  # Otherwise, prompt the user for input
  while true; do
    read -p "$1 (y/n/exit): " yn
    case $yn in
      [Yy]* ) return 0;;  # Proceed
      [Nn]* ) return 1;;  # Skip
      [Ee]* ) echo "Exiting setup script..."; exit 0;;  # Exit
      * ) echo "Please answer y, n, or 'exit' to quit.";;
    esac
  done
}

# Step 1: Install Bun
echo "Step 1: Installing Bun..."
curl -fsSL https://bun.sh/install | bash

# Step 2: Confirm starting the setup process
confirm "Step 2: Do you want to initialize the Node.js project?" || exit 1

# Initialize Node.js project with proper defaults
bun init -y \
  --init-author-name="" \
  --init-license="MIT" \
  --init-version="0.1.0"

# Step 3: Confirm installing core dependencies
confirm "Step 3: Do you want to install core dependencies?" || exit 1

# Install core dependencies for Supabase and other libraries using Bun
bun add @supabase/supabase-js

# Step 4: Confirm installing dev dependencies
confirm "Step 4: Do you want to install dev dependencies?" || exit 1

# Install dev dependencies using Bun
bun add -d \
  @types/node \
  ts-node \
  nodemon \
  drizzle-kit \
  drizzle-orm \
  postgres \
  @types/bunyan \
  openapi-types \
  dotenv-cli

# Step 5: Confirm installation of Supabase CLI
confirm "Step 5: Do you want to install the Supabase CLI via GitHub?" || exit 1

# Install Supabase CLI manually (for now, to avoid npm errors)
echo "Please manually install the Supabase CLI following the instructions."
echo "Visit https://github.com/supabase/cli/releases to download the correct version."
echo "You can follow the steps below to install it:"
echo "  curl -L https://github.com/supabase/cli/releases/download/v1.0.0/supabase_darwin_arm64.tar.gz -o supabase_cli.tar.gz"
echo "  tar -xvzf supabase_cli.tar.gz"
echo "  mv supabase /usr/local/bin/"

# Step 6: Confirm creating TypeScript config
confirm "Step 6: Do you want to create a TypeScript config file (tsconfig.json)?" || exit 1

# Create optimized TypeScript config
cat > tsconfig.json << EOL
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM"],
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "resolveJsonModule": true,
    "types": ["node"],
    "experimentalDecorators": true,
    "emitDecoratorMetadata": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules"]
}
EOL

# Step 7: Confirm creating .env file
confirm "Step 7: Do you want to create an .env file with database credentials?" || exit 1

# Create environment template
cat > .env << EOL
DATABASE_URL="postgres://user:pass@host:5432/db"
SUPABASE_URL=""
SUPABASE_ANON_KEY=""
EOL

# Step 8: Confirm creating project structure
confirm "Step 8: Do you want to create the basic project structure?" || exit 1

# Create proper project structure
mkdir -p src/{api,db/schemas,lib,modules}

# Step 9: Confirm initializing Drizzle configuration
confirm "Step 9: Do you want to initialize Drizzle configuration?" || exit 1

# Initialize Drizzle configuration
cat > drizzle.config.ts << EOL
import type { Config } from "drizzle-kit";

export default {
  schema: "./src/db/schemas/*",
  out: "./drizzle/migrations",
  driver: "pg",
  dbCredentials: {
    connectionString: process.env.DATABASE_URL!,
  },
  verbose: true,
  strict: true,
} satisfies Config;
EOL

# Step 10: Confirm creating a basic Drizzle schema
confirm "Step 10: Do you want to create a basic Drizzle schema?" || exit 1

# Create basic Drizzle schema example
cat > src/db/schemas/users.ts << EOL
import { pgTable, serial, text, timestamp } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  email: text("email").notNull().unique(),
  createdAt: timestamp("created_at").defaultNow(),
});

export const insertUserSchema = createInsertSchema(users, {
  email: z.string().email(),
});
EOL

# Step 11: Confirm creating database client setup
confirm "Step 11: Do you want to create database client setup?" || exit 1

# Create database client setup
cat > src/db/client.ts << EOL
import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import * as schema from "./schemas";

const client = postgres(process.env.DATABASE_URL!);
export const db = drizzle(client, { schema });
EOL

# Step 12: Confirm updating package.json with scripts
confirm "Step 12: Do you want to update package.json with necessary scripts?" || exit 1

# Manually update package.json with necessary scripts using npm
echo "Updating package.json with necessary scripts..."
npm pkg set scripts.build="tsc"
npm pkg set scripts.start="node -r dotenv/config dist/index.js"
npm pkg set scripts.dev="nodemon --exec 'dotenv -e .env ts-node src/index.ts'"
npm pkg set scripts.migrate:generate="drizzle-kit generate:pg"
npm pkg set scripts.migrate:up="drizzle-kit migrate:up"
npm pkg set scripts.migrate:down="drizzle-kit migrate:down"
npm pkg set scripts.lint="tsc --noEmit"

# Step 13: Confirm creating the entry point
confirm "Step 13: Do you want to create the basic entry point (src/index.ts)?" || exit 1

# Create proper entry point
cat > src/index.ts << EOL
import { db } from "./db/client";
import { users } from "./db/schemas/users";

const main = async () => {
  console.log("Starting application...");
  
  // Example DB query
  const allUsers = await db.select().from(users);
  console.log("Users:", allUsers);
};

main().catch(console.error);
EOL

# Final message
echo "Project setup complete!"
echo "Environment variables need to be configured in .env"
echo "Run commands:"
echo "  bun run dev      - Start development server"
echo "  bun run build    - Build production bundle"
echo "  bun run start    - Run production build"
echo "  bun run migrate:generate - Create new migrations"
