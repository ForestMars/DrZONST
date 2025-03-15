# Dr. ZONST

Dr. ZONST is a utility tool designed to streamline the setup of Node.js projects, with seamless integration of **Drizzle ORM**, **Zod**, **OpenAPI**, **Node.js**, **Supabase** and **Typescript**. It automates the creation of the essential project structure, configuration files, and ensures automatic generation of API endpoints with validation.

Dr. ZONST is perfect for quickly bootstrapping a modern full-stack project with a PostgreSQL database, API validation, and Swagger documentation. It uses bun for speed instead of npm. 

---

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Setup Instructions](#setup-instructions)
- [How OpenAPI, Supabase, and Zod Work Together](#how-openapi-supabase-and-zod-work-together)
- [Project Structure](#project-structure)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **Supabase Integration**: Automatically sets up and connects to a Supabase project for easy authentication, real-time database management, and more.
- **Seamless API Generation**: Uses OpenAPI (Swagger) for automatic API documentation generation.
- **Zod Validation**: Strongly typed request validation integrated with the API endpoints to ensure data integrity.
- **TypeScript Support**: Built with TypeScript for type safety throughout the stack.
- **Automated Setup**: Use the setup script to configure the project with a single command.
- **Migrations**: Drizzle ORM and Supabase for database migrations and schema management.

---

## Prerequisites

Before running the `setup.sh` script, you must have the following installed:

- **Bun**: Bun is a modern JavaScript runtime. [Install Bun here](https://bun.sh/).
- **PostgreSQL**: Required for database management, Supabase manages this for you.
- **Node.js**: Ensure that Node.js is installed on your machine.
- **Supabase Account**: Sign up at [Supabase](https://supabase.com/). You don't need to have a Supabase project created before running the script, but you will need to authenticate with Supabase during the setup.

---

## Installation

Clone the repository to get started:

```bash
git clone https://github.com/your-username/dr-zonst.git
cd dr-zonst
```

### 1. Run the Setup Script

To initialize the project with all dependencies, run the `setup.sh` script. You can either interactively answer the prompts or use the `-y` flag to automatically answer **yes** to all prompts.

```bash
# Normal setup (you'll answer prompts)
./setup.sh

# Auto setup (answers 'yes' to all prompts)
./setup.sh -y

# Dr. ZONST Setup Guide

## The Script Will:

- Install Bun (the modern JavaScript runtime).
- Set up Supabase authentication and connection (you’ll need your Supabase credentials).
- Install core dependencies like Supabase SDK, Drizzle ORM, Zod, and others.
- Generate configuration files such as `.env`, `tsconfig.json`, and create database schema files.

## 2. Configure Supabase

After running the setup script, you'll need to configure your `.env` file with your Supabase credentials. Open the `.env` file and set the following:

```env
DATABASE_URL="postgres://user:password@host:5432/db"
SUPABASE_URL="your-supabase-url"
SUPABASE_ANON_KEY="your-supabase-anon-key"
```

You can retrieve the `SUPABASE_URL` and `SUPABASE_ANON_KEY` from your Supabase project settings.

## 3. Install Dependencies

Now that the setup is complete, run the following command to install all the necessary dependencies via Bun:

```bash
bun install
```

## 4. Start the Development Server

You can now start the development server with:

```bash
bun run dev
```

## How OpenAPI, Supabase, and Zod Work Together

### OpenAPI (Swagger) Integration

OpenAPI is used to automatically generate an API specification for your endpoints. Dr. ZONST integrates OpenAPI with Zod validation schemas to create a robust, self-documenting API. You get live API documentation and client SDK generation right out of the box.

- OpenAPI provides the API structure and documentation.
- Zod ensures that your requests and responses are type-safe and validated.
- As you modify your database schema using Supabase and Drizzle ORM, the API definitions and validation schemas update automatically.

### Supabase Database Management

Supabase provides an easy-to-use, open-source database-as-a-service solution. It integrates with Drizzle ORM to manage database migrations and schema updates.

1. Create a Supabase project (from the Supabase dashboard).
2. Set up your database connection by providing the credentials in the `.env` file.
3. Use Drizzle ORM to manage database queries and migrations.
4. Automatically sync database schema updates with Zod validation schemas, ensuring your API always handles the correct data.

### Zod Validation

Zod is a TypeScript-first schema validation library. It ensures that every incoming request (e.g., POST data) matches the expected types and structures defined in your API endpoints. Dr. ZONST uses Zod to automatically generate validation schemas for your endpoints.

- Zod validates request data before it hits the database, ensuring type safety and preventing invalid data.
- It generates validation rules based on your database schema, keeping everything in sync.
- Automatically generates response validation to ensure that the output also adheres to the expected structure.

## Workflow Example

1. **Define Database Schema**: Use Drizzle ORM to define tables and relationships in the database.
2. **Zod Validation**: Create Zod schemas to define the request and response structures for API endpoints.
3. **OpenAPI Generation**: OpenAPI automatically generates API documentation and the client SDK based on the Zod schemas.
4. **Database Sync**: Run drizzle-kit migrations, which keep both the database and Zod schemas in sync.
5. **API Validation**: Zod validates the incoming requests and ensures the data is valid before interacting with the database.

## Project Structure

```
.
├── src
│   ├── api
│   ├── db
│   │   ├── client.ts
│   │   └── schemas
│   └── lib
├── .env
├── tsconfig.json
└── drizzle.config.ts
```

- `src/api`: Contains your API routes and business logic.
- `src/db`: Houses your database schema definitions and Drizzle ORM configuration.
- `src/lib`: Utility functions and shared logic.
- `.env`: Configuration file for your Supabase credentials.
- `tsconfig.json`: TypeScript configuration.
- `drizzle.config.ts`: Drizzle ORM configuration file for schema migrations.

## Development

To start building your API, follow these steps:

1. **Add New Routes**: Define your routes in the `src/api` directory.
2. **Define Database Schema**: Use Drizzle ORM to create or modify your database tables in `src/db/schemas`.
3. **Generate Migrations**: Run the Drizzle migration tool to apply changes to your database schema.
4. **Test the API**: Validate endpoints and test them using your API testing tool (e.g., Postman).
5. **API Documentation**: The OpenAPI (Swagger) documentation will automatically update based on your API and Zod schemas.

## Contributing

We welcome contributions! To contribute to Dr. ZONST, please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-name`).
3. Make your changes.
4. Commit your changes (`git commit -am 'Add new feature'`).
5. Push to the branch (`git push origin feature-name`).
6. Open a pull request.

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Final Words

Dr. ZONST is designed to be a flexible, extensible framework that automates much of the repetitive setup required for modern Node.js development. With integrated tools like Supabase, Zod, and OpenAPI, it simplifies API development, schema management, and validation for any Node.js project.
