/**  
 * @fileoverview Given an OAS file in JSON format, generates a coresponding Zod schema
 * @description Takes input from a file (openapi.json) as a parameter; returns schemas as an object and writes output to a file (zodSchemas.ts)
 * @version 0.0.1
 * @license All rights reserved. 
 * 
 * @TODO Possible support for OAS files in XML format (?)
 */ 

// Importing necessary modules
import { readFileSync, writeFileSync } from 'node:fs'; // Use node: prefix for clarity
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';

// Get __dirname equivalent in ESM
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Path to the OpenAPI JSON file
const openApiFilePath = path.join(__dirname, 'openapi.json');
const outputFilePath = path.join(__dirname, 'zodSchemas.ts');

// Rest of your code remains the same
const openApiData = JSON.parse(readFileSync(openApiFilePath, 'utf-8'));

if (!openApiData.components?.schemas) {
    throw new Error('No schemas found in OpenAPI JSON.');
}

const mapOpenApiToZod = (type?: string, format?: string): string => {
    if (!type) return 'z.any()';
    if (type === 'string') {
        if (format === 'uuid') return 'z.string().uuid()';
        if (format === 'email') return 'z.string().email()';
        return 'z.string()';
    }
    if (type === 'integer' || type === 'number') return 'z.number()';
    if (type === 'boolean') return 'z.boolean()';
    if (type === 'array') return 'z.array(z.any())';
    return 'z.any()';
};

let zodSchemaFileContent = `import { z } from 'zod';\n\n`;

for (const [schemaName, schemaDef] of Object.entries(openApiData.components.schemas)) {
    const typedSchemaDef = schemaDef as any;
    if (typedSchemaDef.type !== 'object' || !typedSchemaDef.properties) continue;

    let zodProperties: string[] = [];
    for (const [propName, propDef] of Object.entries(typedSchemaDef.properties)) {
        const typedPropDef = propDef as any;
        const zodType = mapOpenApiToZod(typedPropDef.type, typedPropDef.format);
        zodProperties.push(`  ${propName}: ${zodType},`);
    }
    zodSchemaFileContent += `export const ${schemaName}Schema = z.object({\n${zodProperties.join('\n')}\n});\n\n`;
}

writeFileSync(outputFilePath, zodSchemaFileContent);
console.log(`✅ Zod schemas generated and saved to ${outputFilePath}`);