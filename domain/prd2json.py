#!/usr/bin/env python3
# prd2json.py - converts a well-formatted prd into a json domain model. 
# __author__ = 'Forest Mars'
# __version__ = '0.0.1'

import re
import json
import jsonschema
import argparse
import os

# JSON Schema for Domain Model
DOMAIN_MODEL_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Domain Model Schema",
    "type": "object",
    "required": ["entities", "operations"],
    "properties": {
        "entities": {
            "type": "array",
            "description": "List of domain entities extracted from the PRD",
            "items": {
                "type": "object",
                "required": ["name", "description", "properties", "rules", "relationships"],
                "properties": {
                    "name": {"type": "string", "description": "Entity name (e.g., 'Book')", "minLength": 1},
                    "description": {"type": "string", "description": "Brief description of the entity", "minLength": 1},
                    "properties": {
                        "type": "array",
                        "description": "List of entity properties",
                        "items": {
                            "type": "object",
                            "required": ["name", "type"],
                            "properties": {
                                "name": {"type": "string", "description": "Property name (e.g., 'title')", "minLength": 1},
                                "type": {"type": "string", "description": "Property type", "enum": ["string", "integer", "decimal", "boolean", "utcDateTime", "plainDate", "enum"]},
                                "required": {"type": "boolean", "description": "Whether the property is mandatory", "default": False},
                                "isKey": {"type": "boolean", "description": "Whether the property is a primary key", "default": False},
                                "enumValues": {"type": "array", "description": "Allowed values for enum type", "items": {"type": "string"}, "minItems": 1}
                            }
                        }
                    },
                    "rules": {"type": "array", "description": "Business rules or constraints for the entity", "items": {"type": "string", "minLength": 1}},
                    "relationships": {
                        "type": "array",
                        "description": "Relationships to other entities",
                        "items": {
                            "type": "object",
                            "required": ["name", "type", "targetEntity"],
                            "properties": {
                                "name": {"type": "string", "description": "Relationship name (e.g., 'items')", "minLength": 1},
                                "type": {"type": "string", "description": "Relationship type", "enum": ["one-to-many", "many-to-one", "one-to-one"]},
                                "targetEntity": {"type": "string", "description": "Target entity name (e.g., 'OrderItem')", "minLength": 1}
                            }
                        }
                    }
                }
            }
        },
        "operations": {
            "type": "array",
            "description": "List of business operations extracted from the PRD",
            "items": {
                "type": "object",
                "required": ["name", "description", "entity", "type"],
                "properties": {
                    "name": {"type": "string", "description": "Operation name (e.g., 'Add a book')", "minLength": 1},
                    "description": {"type": "string", "description": "Description of the operation", "minLength": 1},
                    "entity": {"type": "string", "description": "Entity the operation applies to (e.g., 'Book')", "minLength": 1},
                    "type": {"type": "string", "description": "Operation type", "enum": ["create", "read", "update", "delete", "list"]},
                    "inputs": {"type": "array", "description": "Input properties or entities", "items": {"type": "string"}},
                    "output": {"type": "string", "description": "Output type (e.g., 'Book', 'Book[]', 'void')", "minLength": 1},
                    "rule": {"type": "string", "description": "Optional business rule for the operation", "minLength": 0}
                }
            }
        }
    }
}

def infer_type(prop: str) -> str:
    """Infer property type from name."""
    if "title" in prop.lower() or "author" in prop.lower():
        return "string"
    if "quantity" in prop.lower():
        return "integer"
    return "string"  # Default

def parse_prd_to_domain_model(prd_file: str) -> dict:
    """Parse a PRD file into a JSON domain model, validated against the schema."""
    # Read the PRD file
    if not os.path.exists(prd_file):
        raise FileNotFoundError(f"PRD file not found: {prd_file}")
    with open(prd_file, "r", encoding="utf-8") as f:
        prd_text = f.read()

    domain_model = {"entities": [], "operations": []}

    # Extract entities
    entities_section = re.search(r"Entities\s*(.*?)\s*Operations", prd_text, re.DOTALL)
    if entities_section:
        entities_text = entities_section.group(1)
        entity_blocks = re.findall(r"- (\w+): (.*?)\s*(?=- |\nOperations)", entities_text, re.DOTALL)
        for name, details in entity_blocks:
            properties_match = re.search(r"(It has|Includes) (.*?)\.", details)
            rules_match = re.search(r"(The|Its) (.*?)\.", details)
            properties = properties_match.group(2).split(", ") if properties_match else []
            rules = [rules_match.group(2)] if rules_match else []
            domain_model["entities"].append({
                "name": name,
                "description": details.split(".")[0].strip(),
                "properties": [
                    {
                        "name": p.strip(),
                        "type": infer_type(p),
                        "required": True,  # Assume required for simplicity
                        "isKey": p.strip().lower() == "id"
                    } for p in properties
                ],
                "rules": rules,
                "relationships": []  # None in this PRD
            })

    # Extract operations
    operations_section = re.search(r"Operations\s*(.*?)\s*Constraints", prd_text, re.DOTALL)
    if operations_section:
        operations_text = operations_section.group(1)
        operation_blocks = re.findall(r"- (\w+ \w+): (.*?)(?=\n- |\nConstraints)", operations_text)
        operation_types = {
            "Add a book": {"type": "create", "inputs": ["book"], "output": "Book"},
            "View inventory": {"type": "list", "inputs": [], "output": "Book[]"},
            "Remove a book": {"type": "delete", "inputs": ["id"], "output": "void"}
        }
        for name, description in operation_blocks:
            op_info = operation_types.get(name, {"type": "unknown", "inputs": [], "output": "void"})
            domain_model["operations"].append({
                "name": name,
                "description": description.strip(),
                "entity": "Book",  # Inferred from PRD context
                "type": op_info["type"],
                "inputs": op_info["inputs"],
                "output": op_info["output"],
                "rule": ""
            })

    # Validate against schema
    try:
        jsonschema.validate(instance=domain_model, schema=DOMAIN_MODEL_SCHEMA)
    except jsonschema.exceptions.ValidationError as e:
        raise ValueError(f"Invalid domain model: {e.message}")

    return domain_model

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description=(
            "Parse a Product Requirements Document (PRD) text file into a JSON domain model, "
            "validated against a predefined schema. The output is used to generate TypeSpec definitions."
        ),
        epilog=(
            "Example usage:\n"
            "  python prd_to_domain_model.py prd.txt\n"
            "  python prd_to_domain_model.py prd.txt --output my_domain_model.json"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "prd_file",
        type=str,
        help="Path to the input PRD text file (e.g., 'prd.txt'). Must contain sections like 'Entities' and 'Operations'."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="domain_model.json",
        help="Path to the output JSON domain model file (default: 'domain_model.json')."
    )
    args = parser.parse_args()

    # Generate domain model
    try:
        domain_model = parse_prd_to_domain_model(args.prd_file)
        with open(args.output, "w") as f:
            json.dump(domain_model, f, indent=2)
        print(f"Domain model generated successfully: {args.output}")
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()