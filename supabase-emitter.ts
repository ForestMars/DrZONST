// drizzle-emitter.ts

import {
  AssetEmitter,
  TypeEmitter,
  EmitterOutput,
  Declaration,
  CodeTypeEmitter,
  EmitContext,
  getAssetEmitter,
  Model,
  Scalar
} from "@typespec/compiler";
import { createClient } from '@supabase/supabase-js';

export class SupabaseTypeEmitter extends CodeTypeEmitter {
  scalarDeclaration(scalar: Scalar, name: string): EmitterOutput<string> {
    switch (scalar.name) {
      case "float64":
        return this.emitter.result.rawCode("number");
      case "string":
        return this.emitter.result.rawCode("string");
      default:
        return super.scalarDeclaration(scalar, name);
    }
  }

  modelDeclaration(model: Model, name: string): EmitterOutput<string> {
    const tableName = `${model.name.toLowerCase()}s`;
    
    const columns = Array.from(model.properties.values())
      .map(prop => {
        const type = this.emitTypeReference(prop.type);
        return `  ${prop.name}: ${type}`;
      })
      .join(",\n");

    return this.emitter.result.declaration(
      name,
      `export interface ${name} {\n${columns}\n}\n`
    );
  }

  modelReference(model: Model): EmitterOutput<string> {
    if (model.name === "Order") {
      return this.emitter.result.rawCode(`
        export interface OrderItem {
          orderId: string;
          albumId: string;
        }`);
    }
    return super.modelReference(model);
  }
}

export function $onEmit(context: EmitContext) {
  const emitter = getAssetEmitter<string>(context.program, SupabaseTypeEmitter);
  emitter.emitProgram();
  emitter.writeOutput();

  // Generate Supabase client initialization
  const supabaseClientCode = `
import { createClient } from '@supabase/supabase-js'
import { Database } from './types/supabase'

export const supabase = createClient<Database>(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)`;

  context.program.host.writeFile("supabaseClient.ts", supabaseClientCode);
}
