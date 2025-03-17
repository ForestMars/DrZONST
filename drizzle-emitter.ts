// drizzle-emitter.ts
import {
  AssetEmitter,
  TypeEmitter,
  EmitterOutput,
  Declaration,
  CodeTypeEmitter
} from "@typespec/compiler";

export class DrizzleTypeEmitter extends CodeTypeEmitter {
  // Map TypeSpec types to SQL column types
  scalarDeclaration(scalar: Scalar, name: string): EmitterOutput<string> {
    switch (scalar.name) {
      case "float64":
        return this.emitter.result.rawCode("numeric(10, 2)");
      case "string":
        return this.emitter.result.rawCode("varchar");
      default:
        return super.scalarDeclaration(scalar, name);
    }
  }

  modelDeclaration(model: Model, name: string): EmitterOutput<string> {
    const tableName = `${model.name.toLowerCase()}s`;
    
    // Generate Drizzle table definition
    const columns = Array.from(model.properties.values())
      .map(prop => {
        const type = this.emitTypeReference(prop.type);
        return `  ${prop.name}: ${type}('${prop.name}')`;
      })
      .join(",\n");

    return this.emitter.result.declaration(
      name,
      `export const ${tableName} = pgTable('${tableName}', {\n${columns}\n});\n`
    );
  }

  // Handle relationships
  modelReference(model: Model): EmitterOutput<string> {
    if (model.name === "Order") {
      return this.emitter.result.rawCode(`
        export const orderItems = pgTable('order_items', {
          orderId: varchar('order_id').references(() => orders.id),
          albumId: varchar('album_id').references(() => albums.id),
        });`);
    }
    return super.modelReference(model);
  }
}

export function $onEmit(context: EmitContext) {
  const emitter = getAssetEmitter<string>(context.program, DrizzleTypeEmitter);
  emitter.emitProgram();
  emitter.writeOutput();
}

