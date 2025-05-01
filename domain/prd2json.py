#!/usr/bin/env python3
# prd2csl.py - Converts a well-formatted PRD into a CSL domain model.
# __version__ = '0.0.3'

import re
import argparse
import os
import logging
import traceback

# Set up logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

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
    logger.debug(f"Inferring type for property: {prop}")
    if "title" in prop.lower() or "author" in prop.lower():
        return "string"
    if "quantity" in prop.lower():
        return "integer"
    return "string"

def parse_prd_to_domain_model(prd_file: str) -> dict:
    """Parse a PRD file into a domain model dictionary."""
    logger.debug(f"Attempting to read PRD file: {prd_file}")
    print(f"DEBUG: Checking file {prd_file}")  # Fallback print
    if not os.path.exists(prd_file):
        logger.error(f"PRD file not found: {prd_file}")
        raise FileNotFoundError(f"PRD file not found: {prd_file}")
    
    try:
        with open(prd_file, "r", encoding="utf-8") as f:
            prd_text = f.read()
        logger.debug(f"PRD content:\n{prd_text}")
        print(f"DEBUG: Successfully read PRD content")
    except Exception as e:
        logger.error(f"Failed to read PRD file: {str(e)}")
        raise

    domain_model = {"entities": [], "operations": []}

    # Extract entities
    logger.debug("Searching for Entities section")
    entities_section = re.search(r"Entities\s*([\s\S]*?)\s*Operations", prd_text, re.DOTALL)
    if entities_section:
        entities_text = entities_section.group(1).strip()
        logger.debug(f"Entities section found:\n{entities_text}")
        entity_blocks = re.findall(r"- (\w+): (.*?)(?=\n- |\nOperations|\Z)", entities_text, re.DOTALL)
        logger.debug(f"Entity blocks: {entity_blocks}")
        for name, details in entity_blocks:
            logger.debug(f"Processing entity: {name}, details: {details}")
            properties_match = re.search(r"(?:It has|Includes)\s+([^.]+)\.", details, re.IGNORECASE)
            rules_match = re.search(r"(?:The|Its)\s+([^.]+)\.", details, re.IGNORECASE)
            properties = properties_match.group(1).split(", ") if properties_match else []
            rules = [rules_match.group(1)] if rules_match else []
            logger.debug(f"Properties: {properties}, Rules: {rules}")
            # Add an 'id' property implicitly
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
        logger.debug(f"Parsed entities: {domain_model['entities']}")
    else:
        logger.warning("Entities section not found")

    # Extract operations
    logger.debug("Searching for Operations section")
    operations_section = re.search(r"Operations\s*([\s\S]*?)\s*Constraints", prd_text, re.DOTALL)
    if operations_section:
        operations_text = operations_section.group(1).strip()
        logger.debug(f"Operations section found:\n{operations_text}")
        operation_blocks = re.findall(r"- (.*?): (.*?)(?=\n- |\nConstraints|\Z)", operations_text, re.DOTALL)
        logger.debug(f"Operation blocks: {operation_blocks}")
        operation_types = {
            "Add a book": {"type": "create", "inputs": ["title", "author", "quantity"], "output": "Book"},
            "View inventory": {"type": "list", "inputs": [], "output": "Book[]"},
            "Remove a book": {"type": "delete", "inputs": ["id"], "output": "void"}
        }
        for name, description in operation_blocks:
            name = name.strip()
            description = description.strip()
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
        logger.debug(f"Parsed operations: {domain_model['operations']}")
    else:
        logger.warning("Operations section not found")

    logger.debug(f"Final domain model: {domain_model}")
    return domain_model

def generate_method_signature(op: dict, entities: list) -> str:
    """Generate a CSL method signature for an operation."""
    logger.debug(f"Generating method signature for operation: {op['name']}")
    entity = next((e for e in entities if e["name"] == op["entity"]), None)
    if not entity:
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
    logger.warning(f"Unknown operation type: {op['type']}")
    return ""

def generate_csl(domain_model: dict) -> str:
    """Generate CSL syntax from the domain model dictionary."""
    logger.debug("Generating CSL content")
    csl = "BoundedContext BookshopInventory {\n"

    # Generate entities
    for entity in domain_model["entities"]:
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
    logger.debug(f"Generated CSL:\n{csl}")
    return csl

def main():
    logger.debug("Starting main function")
    print("DEBUG: Starting prd2csl.py")
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
    parser.add_argument(
        "--output",
        type=str,
        default="domain_model.csl",
        help="Path to the output CSL file (default: 'domain_model.csl')."
    )
    args = parser.parse_args()

    try:
        logger.debug(f"Processing PRD file: {args.prd_file}")
        domain_model = parse_prd_to_domain_model(args.prd_file)
        csl_content = generate_csl(domain_model)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(csl_content)
        logger.info(f"CSL domain model generated successfully: {args.output}")
        print(f"CSL domain model generated successfully: {args.output}")
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        logger.error(f"Stack trace:\n{traceback.format_exc()}")
        print(f"Error: {str(e)}")
        print(f"Stack trace:\n{traceback.format_exc()}")
        exit(1)

if __name__ == "__main__":
    main()