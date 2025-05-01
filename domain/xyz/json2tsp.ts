import * as fs from "fs";

interface Property {
  name: string;
  type: string;
  required: boolean;
  isKey: boolean;
  enumValues?: string[];
}

interface Entity {
  name: string;
  description: string;
  properties: Property[];
  rules: string[];
  relationships: { name: string; type: string; targetEntity: string }[];
}

interface Operation {
  name: string;
  description: string;
  entity: string;
  type: string;
  inputs: string[];
  output: string;
  rule: string;
}

interface DomainModel {
  entities: Entity[];
  operations: Operation[];
}

function generateTypeSpec(domainModel: DomainModel): string {
  let typespec = `@service(#{title: "InventoryManagement Service"})\n@route("/api")\nnamespace InventoryManagement;\n\n`;

  // Generate models
  for (const entity of domainModel.entities) {
    typespec += `@doc("${entity.description}")\nmodel ${entity.name} {\n`;
    typespec += `  @key id: string;\n`; // Always add ID
    for (const prop of entity.properties) {
      const optional = prop.required ? "" : "?";
      typespec += `  ${prop.name}${optional}: ${prop.type}`;
      if (prop.enumValues) {
        typespec += `; // Values: ${prop.enumValues.join(", ")}`;
      }
      typespec += `;\n`;
    }
    for (const rel of entity.relationships) {
      typespec += `  ${rel.name}: ${rel.targetEntity}[];\n`;
    }
    if (entity.rules.length) {
      typespec += `  // Rules: ${entity.rules.join(", ")}\n`;
    }
    typespec += `}\n\n`;
  }

  // Generate interfaces
  for (const entity of domainModel.entities) {
    typespec += `@route("/${entity.name.toLowerCase()}s")\ninterface ${entity.name}s {\n`;
    for (const op of domainModel.operations.filter(op => op.entity === entity.name)) {
      let methodName = op.name.toLowerCase().replace(/\s+/g, "");
      if (op.type === "create") methodName = `create${entity.name}`;
      else if (op.type === "list") methodName = `list${entity.name}s`;
      else if (op.type === "delete") methodName = `delete${entity.name}`;
      typespec += `  @${op.type === "create" ? "post" : op.type === "list" ? "get" : "delete"} `;
      if (op.type === "delete") typespec += `@route("/{id}") `;
      typespec += `@doc("${op.description}")\n`;
      typespec += `  ${methodName}(`;
      if (op.type === "delete") {
        typespec += `@path id: string`;
      } else if (op.type === "create") {
        typespec += `@body ${entity.name.toLowerCase()}: ${entity.name}`;
      }
      typespec += `): ${op.output}`;
      if (op.type !== "list" && op.output !== "void") {
        typespec += ` | { @statusCode statusCode: 404; @body error: ErrorResponse; }`;
      }
      if (op.rule) {
        typespec += `; // ${op.rule}`;
      }
      typespec += `;\n`;
    }
    typespec += `}\n\n`;
  }

  typespec += `model ErrorResponse {\n  @doc("Error message")\n  message: string;\n  @doc("Error code")\n  code?: string;\n}\n`;

  return typespec;
}

// Example usage
const domainModel: DomainModel = JSON.parse(fs.readFileSync("domain_model.json", "utf8"));
const typespec = generateTypeSpec(domainModel);
fs.writeFileSync("bookshop.tsp", typespec);