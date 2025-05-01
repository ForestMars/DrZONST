# prd2csl.py - Converts a well-formatted PRD into a CSL domain model.
# __version__ = '0.0.python3'

import re
import argparse
import os
import logging
import traceback
import sys

# Set up logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s", force=True)
logger = logging.getLogger(__name__)
logger.debug("Logger initialized")

# Type mapping from PRD-inferred types to CSL types
TYPE_MAPPING = {
    "string": "String",
    "integer": "Integer",
    "decimal": "Decimal",
    "boolean": "Boolean",
    "utcDateTime": "UTCDateTime",
    "plainDate": "PlainDate",
    "enum": "String"
}

def infer_type(prop: str) -> str:
    """Infer property type from its name."""
    print(f"DEBUG: Inferring type for property: {prop}")
    logger.debug(f"Inferring type for property: {prop}")
    if "title" in prop.lower() or "author" in prop.lower():
        return "string"
    if "quantity" in prop.lower():
        return "integer"
    return "string"

def parse_prd_to_domain_model(prd_file: str) -> dict:
    """Parse a PRD file into a domain model dictionary."""
    print(f"DEBUG: Starting parse_prd_to_domain_model: {prd_file}")
    logger.debug(f"Starting parse_prd_to_domain_model: {prd_file}")

    if not os.path.exists(prd_file):
        msg = f"PRD file not found: {prd_file}"
        print(f"ERROR: {msg}")
        logger.error(msg)
        raise FileNotFoundError(msg)
    
    try:
        print(f"DEBUG: Attempting to read {prd_file}")
        logger.debug(f"Attempting to read {prd_file}")
        with open(prd_file, "r", encoding="utf-8") as f:
            prd_text = f.read()
        print(f"DEBUG: Successfully read {prd_file}")
        logger.debug(f"PRD content:\n{prd_text}")
    except Exception as e:
        msg = f"Failed to read PRD file: {str(e)}"
        print(f"ERROR: {msg}")
        logger.error(msg)
        raise

    domain_model = {"entities": [], "operations": []}

    # Extract entities
    print("DEBUG: Searching for Entities section")
    logger.debug("Searching for Entities section")
    entities_section = re.search(r"Entities\s*([\s\S]*?)\s*Operations", prd_text, re.DOTALL)
    if entities_section:
        entities_text = entities_section.group(1).strip()
        print(f"DEBUG: Entities section found:\n{entities_text}")
        logger.debug(f"Entities section found:\n{entities_text}")
        entity_blocks = re.findall(r"- (\w+): (.*?)(?=\n- |\nOperations|\Z)", entities_text, re.DOTALL)
        print(f"DEBUG: Entity blocks: {entity_blocks}")
        logger.debug(f"Entity blocks: {entity_blocks}")
        for name, details in entity_blocks:
            print(f"DEBUG: Processing entity: {name}, details: {details}")
            logger.debug(f"Processing entity: {name}, details: {details}")
            properties_match = re.search(r"(?:It has|Includes)\s+([^.]+)\.", details, re.IGNORECASE)
            rules_match = re.search(r"(?:The|Its)\s+([^.]+)\.", details, re.IGNORECASE)
            properties = properties_match.group(1).split(", ") if properties_match else []
            rules = [rules_match.group(1)] if rules_match else []
            print(f"DEBUG: Properties: {properties}, Rules: {rules}")
            logger.debug(f"Properties: {properties}, Rules: {rules}")
            entity_properties = [
                {"name": "id", "type": "string", "required": True, "isKey": True}
            ] + [
                {
                    "name": p.strip(),
                    "type": infer_type(p),
                    "required": True,
                    "isKey": False
                } for p in properties
            ]
            domain_model["entities"].append({
                "name": name,
                "description": details.split(".")[0].strip(),
                "properties": entity_properties,
                "rules": rules,
                "relationships": []
            })
        print(f"DEBUG: Parsed entities: {domain_model['entities']}")
        logger.debug(f"Parsed entities: {domain_model['entities']}")
    else:
        print("WARNING: Entities section not found")
        logger.warning("Entities section not found")

    # Extract operations
    print("DEBUG: Searching for Operations section")
    logger.debug("Searching for Operations section")
    operations_section = re.search(r"Operations\s*([\s\S]*?)\s*Constraints", prd_text, re.DOTALL)
    if operations_section:
        operations_text = operations_section.group(1).strip()
        print(f"DEBUG: Operations section found:\n{operations_text}")
        logger.debug(f"Operations section found:\n{operations_text}")
        operation_blocks = re.findall(r"- (.*?): (.*?)(?=\n- |\nConstraints|\Z)", operations_text, re.DOTALL)
        print(f"DEBUG: Operation blocks: {operation_blocks}")
        logger.debug(f"Operation blocks: {operation_blocks}")
        operation_types = {
            "Add a book": {"type": "create", "inputs": ["title", "author", "quantity"], "output": "Book"},
            "View inventory": {"type": "list", "inputs": [], "output": "Book[]"},
            "Remove a book": {"type": "delete", "inputs": ["id"], "output": "void"}
        }
        for name, description in operation_blocks:
            name = name.strip()
            description = description.strip()
            print(f"DEBUG: Processing operation: {name}, description: {description}")
            logger.debug(f"Processing operation: {name}, description: {description}")
            op_info = operation_types.get(name, {"type": "unknown", "inputs": [], "output": "void"})
            domain_model["operations"].append({
                "name": name,
                "description": description,
                "entity": "Book",
                "type": op_info["type"],
                "inputs": op_info["inputs"],
                "output": op_info["output"],
                "rule": ""
            })
        print(f"DEBUG: Parsed operations: {domain_model['operations']}")
        logger.debug(f"Parsed operations: {domain_model['operations']}")
    else:
        print("WARNING: Operations section not found")
        logger.warning("Operations section not found")

    print(f"DEBUG: Final domain model: {domain_model}")
    logger.debug(f"Final domain model: {domain_model}")
    return domain_model

def generate_method_signature(op: dict, entities: list) -> str:
    """Generate a CSL method signature for an operation."""
    print(f"DEBUG: Generating method signature for operation: {op['name']}")
    logger.debug(f"Generating method signature for operation: {op['name']}")
    entity = next((e for e in entities if e["name"] == op["entity"]), None)
    if not entity:
        print(f"WARNING: No entity found for operation: {op['name']}")
        logger.warning(f"No entity found for operation: {op['name']}")
        return ""
    if op["type"] == "create":
        params = ", ".join(
            f"{TYPE_MAPPING[prop['type']]} {prop['name']}"
            for prop in entity["properties"]
            if not prop.get("isKey", False)
        )
        return f"{op['entity']} create{op['entity']}({params})"
    elif op["type"] == "delete":
        return f"void delete{op['entity']}(String id)"
    elif op["type"] == "list":
        return f"{op['entity']}[] list{op['entity']}s()"
    print(f"WARNING: Unknown operation type: {op['type']}")
    logger.warning(f"Unknown operation type: {op['type']}")
    return ""

def generate_csl(domain_model: dict) -> str:
    """Generate CSL syntax from the domain model dictionary."""
    print("DEBUG: Generating CSL content")
    logger.debug("Generating CSL content")
    csl = "BoundedContext BookshopInventory {\n"

    # Generate entities
    for entity in domain_model["entities"]:
        print(f"DEBUG: Adding entity to CSL: {entity['name']}")
        logger.debug(f"Adding entity to CSL: {entity['name']}")
        csl += f"  Entity {entity['name']} {{\n"
        for prop in entity["properties"]:
            csl += f"    - {TYPE_MAPPING[prop['type']]} {prop['name']}\n"
        for rule in entity["rules"]:
            csl += f"    constraint \"{rule}\"\n"
        csl += "  }\n"

    # Generate service with operations
    csl += "  Service InventoryService {\n"
    for op in domain_model["operations"]:
        method_signature = generate_method_signature(op, domain_model["entities"])
        if method_signature:
            csl += f"    {method_signature}\n"
    csl += "  }\n"

    csl += "}\n"
    print(f"DEBUG: Generated CSL:\n{csl}")
    logger.debug(f"Generated CSL:\n{csl}")
    return csl

def main():
    print("DEBUG: Starting prd2csl.py")
    logger.debug("Starting prd2csl.py")
    parser = argparse.ArgumentParser(
        description="Parse a Product Requirements Document (PRD) text file into a CSL domain model.",
        epilog=(
            "Example usage:\n"
            "  python prd2csl.py prd.txt\n"
            "  python prd2csl.py prd.txt --output my_domain_model.csl"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "prd_file",
        type=str,
        help="Path to the input PRD text file (e.g., 'prd.txt')."
    )
    # Get default output filename based on input filename
    default_output = lambda x: os.path.splitext(x)[0] + "_domain_model.csl"
    parser.add_argument(
        "--output",
        type=str,
        help="Path to the output CSL file (default: input_filename_domain_model.csl)",
        default=None
    )
    try:
        args = parser.parse_args()
        # Set output filename if not explicitly provided
        if args.output is None:
            args.output = default_output(args.prd_file)
        print(f"DEBUG: Parsed arguments: prd_file={args.prd_file}, output={args.output}")
        logger.debug(f"Parsed arguments: prd_file={args.prd_file}, output={args.output}")
    except Exception as e:
        print(f"ERROR: Failed to parse arguments: {str(e)}")
        logger.error(f"Failed to parse arguments: {str(e)}")
        raise

    try:
        print(f"DEBUG: Processing PRD file: {args.prd_file}")
        logger.debug(f"Processing PRD file: {args.prd_file}")
        domain_model = parse_prd_to_domain_model(args.prd_file)
        csl_content = generate_csl(domain_model)
        print(f"DEBUG: Writing CSL to {args.output}")
        logger.debug(f"Writing CSL to {args.output}")
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(csl_content)
        print(f"CSL domain model generated successfully: {args.output}")
        logger.info(f"CSL domain model generated successfully: {args.output}")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        print(f"Stack trace:\n{traceback.format_exc()}")
        logger.error(f"Error: {str(e)}")
        logger.error(f"Stack trace:\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()