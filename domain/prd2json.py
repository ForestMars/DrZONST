import re
import json
import jsonschema

# JSON Schema for Domain Model
DOMAIN_MODEL_SCHEMA = {
  # [Insert the JSON Schema from above]
}

def infer_type(prop: str) -> str:
    """Infer property type from name."""
    if "title" in prop.lower() or "author" in prop.lower():
        return "string"
    if "quantity" in prop.lower():
        return "integer"
    return "string"  # Default

def parse_prd_to_domain_model(prd_text: str) -> dict:
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

# Example usage
with open("prd.txt", "r") as f:
    prd_text = f.read()
domain_model = parse_prd_to_domain_model(prd_text)
with open("domain_model.json", "w") as f:
    json.dump(domain_model, f, indent=2)