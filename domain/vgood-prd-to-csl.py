import re
import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('prd_to_csl.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def parse_prd(file_path):
    """Parse a PRD file into a structured dictionary."""
    logger.info(f"Parsing PRD file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read PRD file: {e}")
        raise

    # Log raw content for debugging
    logger.debug(f"Raw PRD content (first 500 chars):\n{content[:500]}...")

    # Initialize the PRD dictionary
    prd = {
        'overview': {'description': '', 'business_area': '', 'importance': ''},
        'key_terms': [],
        'features': [],
        'things': [],
        'operations': [],
        'connections': [],
        'constraints': []
    }

    # Normalize content by removing excessive newlines
    content = re.sub(r'\n\s*\n+', '\n', content.strip())
    logger.debug(f"Normalized PRD content length: {len(content)} characters")

    # Split into sections
    sections = re.split(r'#\s*(?:Section:\s*)?(\w+(?:\s+\w+)?)', content, flags=re.IGNORECASE)
    if len(sections) < 2:
        logger.error("No sections found. Expected headers like '# Section: Overview'")
        return prd
    section_pairs = [(sections[i], sections[i+1]) for i in range(1, len(sections), 2)]
    logger.info(f"Found {len(section_pairs)} sections: {[s[0] for s in section_pairs]}")

    for section_name, section_content in section_pairs:
        section_name = section_name.strip().lower().replace(' ', '_')
        section_content = section_content.strip()
        logger.debug(f"Processing section: {section_name}")

        if section_name == 'overview':
            desc = re.search(r'- Product Description: (.*?)(?=(?:- Business Area:|\Z))', section_content, re.DOTALL)
            area = re.search(r'- Business Area: (.*?)(?=(?:- Importance:|\Z))', section_content, re.DOTALL)
            imp = re.search(r'- Importance: (.*?)(?=\Z)', section_content, re.DOTALL)
            prd['overview']['description'] = desc.group(1).strip() if desc else ''
            prd['overview']['business_area'] = area.group(1).strip() if area else ''
            prd['overview']['importance'] = imp.group(1).strip() if imp else ''

        elif section_name == 'key_terms':
            terms = re.findall(r'- (\w+): (.*?)(?=(?:- \w+: |\Z))', section_content, re.DOTALL)
            prd['key_terms'] = [{'name': t[0].strip(), 'description': t[1].strip()} for t in terms]

        elif section_name == 'features':
            features = re.findall(r'- (.*?): (.*?)(?=(?:- |#|\Z))', section_content, re.DOTALL)
            prd['features'] = [{'name': f[0].strip(), 'description': f[1].strip()} for f in features]

        elif section_name == 'things':
            things = re.split(r'^- (\w+):', section_content, flags=re.MULTILINE)
            things = [(things[i], things[i+1]) for i in range(1, len(things), 2) if things[i+1].strip()]
            for thing_name, thing_content in things:
                thing_name = thing_name.strip()
                thing_content = thing_content.strip()
                logger.debug(f"Parsing thing: {thing_name}")

                # Extract description
                desc_match = re.match(r'^(.*?)(?=(?:## Properties:|## Rules:|## Actions:|- \w+:|\Z))', thing_content, re.DOTALL)
                thing_desc = desc_match.group(1).strip() if desc_match else ''

                # Extract properties with indentation support
                properties = []
                prop_section = re.search(r'## Properties:\s*((?:\s*- \w+:.*?\n)+)', thing_content, re.DOTALL)
                if prop_section:
                    prop_lines = re.findall(r'\s*- (\w+): (.*?)\n', prop_section.group(1), re.DOTALL)
                    properties = [{'name': name.strip(), 'description': desc.strip()} for name, desc in prop_lines]

                # Extract rules with indentation support
                rules = []
                rules_section = re.search(r'## Rules:\s*((?:\s*-.*?\n)+)', thing_content, re.DOTALL)
                if rules_section:
                    rules = re.findall(r'\s*- (.*?)\n', rules_section.group(1), re.DOTALL)
                    rules = [r.strip() for r in rules if r.strip()]

                # Extract actions with indentation support
                actions = []
                actions_section = re.search(r'## Actions:\s*((?:\s*-.*?\n)+)', thing_content, re.DOTALL)
                if actions_section:
                    actions = re.findall(r'\s*- (.*?)\n', actions_section.group(1), re.DOTALL)
                    actions = [a.strip() for a in actions if a.strip()]

                prd['things'].append({
                    'name': thing_name,
                    'description': thing_desc,
                    'properties': properties,
                    'rules': rules,
                    'actions': actions
                })

        elif section_name == 'operations':
            ops = re.split(r'##\s*([^#]+?)\n(?=(?:-|\Z))', section_content, flags=re.DOTALL)
            ops = [(ops[i].strip(), ops[i+1].strip()) for i in range(1, len(ops), 2) if ops[i+1].strip()]
            for op_name, op_content in ops:
                desc = re.search(r'- Describe what the action does: (.*?)(?=(?:- Who Can Do It:|\Z))', op_content, re.DOTALL)
                who = re.search(r'- Who Can Do It: (.*?)(?=(?:- Inputs:|\Z))', op_content, re.DOTALL)
                
                # Extract inputs with indentation support
                inputs = []
                inputs_section = re.search(r'- Inputs:\s*((?:\s*- \w+: \w+\n)+)', op_content, re.DOTALL)
                if inputs_section:
                    inputs = re.findall(r'\s*- (\w+): (\w+)', inputs_section.group(1))
                
                outputs = re.search(r'- Outputs: (.*?)(?=(?:- Conditions:|\Z))', op_content, re.DOTALL)
                
                # Extract conditions with indentation support
                conditions = []
                cond_section = re.search(r'- Conditions:\s*((?:\s*-.*?\n)+)', op_content, re.DOTALL)
                if cond_section:
                    conditions = re.findall(r'\s*- (.*?)\n', cond_section.group(1), re.DOTALL)
                    conditions = [c.strip() for c in conditions if c.strip()]
                elif 'None' in op_content:
                    conditions = []
                
                results = re.search(r'- Results: (.*?)(?=(?:- Notifications:|\Z))', op_content, re.DOTALL)
                notif = re.search(r'- Notifications: (.*?)(?=\Z)', op_content, re.DOTALL)

                prd['operations'].append({
                    'name': op_name,
                    'description': desc.group(1).strip() if desc else '',
                    'who': who.group(1).strip() if who else '',
                    'inputs': [{'name': i[0].strip(), 'type': i[1].strip()} for i in inputs],
                    'outputs': outputs.group(1).strip() if outputs else '',
                    'conditions': conditions,
                    'results': results.group(1).strip() if results else '',
                    'notifications': [notif.group(1).strip()] if notif and 'None' not in notif.group(1) else []
                })

        elif section_name == 'connections':
            connections = re.findall(r'- (.*?): (.*?)(?=(?:- |\Z))', section_content, re.DOTALL)
            prd['connections'] = [{'name': c[0].strip(), 'description': c[1].strip()} for c in connections]

        elif section_name == 'constraints':
            constraints = re.findall(r'- (.*?)(?=(?:- |\Z))', section_content, re.DOTALL)
            prd['constraints'] = [c.strip() for c in constraints]

    logger.info("PRD parsing completed")
    return prd

def infer_ddd_elements(prd):
    """Infer DDD elements from the parsed PRD."""
    logger.info("Inferring DDD elements")
    ddd = {
        'bounded_context': re.sub(r'[^\w]', '', prd['overview']['business_area']) if prd['overview']['business_area'] else 'UnnamedContext',
        'description': prd['overview']['description'],
        'entities': [],
        'value_objects': [],
        'aggregates': [],
        'domain_services': [],
        'domain_events': [],
        'repositories': [],
        'relationships': prd['connections']
    }

    # Infer entities and value objects
    for thing in prd['things']:
        has_id = any('unique' in p['description'].lower() for p in thing['properties'])
        if has_id:
            entity = {
                'name': thing['name'],
                'description': thing['description'],
                'attributes': [],
                'invariants': thing['rules'],
                'behaviors': []
            }
            for prop in thing['properties']:
                desc = prop['description'].split(',')
                type_ = desc[0].strip().capitalize()
                constraints = [c.strip() for c in desc[1:]] if len(desc) > 1 else []
                attr_type = 'List' if 'list of' in prop['description'].lower() else type_
                entity['attributes'].append({
                    'name': prop['name'],
                    'type': attr_type,
                    'constraints': constraints
                })
            for action in thing['actions']:
                action_parts = action.split(':')
                action_name = action_parts[0].strip()
                action_desc = action_parts[1].strip() if len(action_parts) > 1 else f"Performs {action_name.lower()}."
                entity['behaviors'].append({'name': action_name, 'description': action_desc})
            ddd['entities'].append(entity)
            ddd['aggregates'].append({
                'name': thing['name'],
                'root': thing['name']
            })
            id_prop = next((p for p in thing['properties'] if 'unique' in p['description'].lower()), None)
            if id_prop:
                ddd['repositories'].append({
                    'name': f"{thing['name']}Repository",
                    'behaviors': [
                        f"findById({id_prop['name']}: {id_prop['description'].split(',')[0].strip().capitalize()}): {thing['name']}",
                        f"findAll(): List<{thing['name']}>",
                        f"save({thing['name'].lower()}: {thing['name']})",
                        f"delete({thing['name'].lower()}: {thing['name']})"
                    ]
                })

    # Infer value objects from properties
    for thing in prd['things']:
        for prop in thing['properties']:
            if 'unique' in prop['description'].lower() or 'valid email' in prop['description'].lower():
                vo_name = prop['name'].capitalize()
                vo = {
                    'name': vo_name,
                    'description': f"{vo_name} for {thing['name']}.",
                    'attributes': [{'name': 'value', 'type': prop['description'].split(',')[0].strip().capitalize()}],
                    'invariants': [c.strip() for c in prop['description'].split(',')[1:] if c],
                    'instances': []
                }
                ddd['value_objects'].append(vo)
            elif 'list of roles' in prop['description'].lower():
                role_vo = next((vo for vo in ddd['value_objects'] if vo['name'] == 'Role'), None)
                if not role_vo:
                    role_vo = {
                        'name': 'Role',
                        'description': 'Represents a user role.',
                        'attributes': [{'name': 'name', 'type': 'String'}],
                        'invariants': ['name must be ADMIN or REGULAR_USER'],
                        'instances': []
                    }
                    ddd['value_objects'].append(role_vo)
                role_vo['instances'] = [
                    {'name': 'ADMIN', 'description': 'Grants add/remove permissions'},
                    {'name': 'REGULAR_USER', 'description': 'Grants view permissions'}
                ]

    # Infer domain events
    for op in prd['operations']:
        for notif in op['notifications']:
            event_name = ''.join(word.capitalize() for word in notif.split(' ')[1:3])
            event_attrs = [{'name': i['name'], 'type': i['type'].capitalize()} for i in op['inputs']]
            ddd['domain_events'].append({
                'name': event_name,
                'description': notif,
                'attributes': event_attrs
            })

    # Infer domain service
    permission_behaviors = []
    for op in prd['operations']:
        behavior_name = f"can{''.join(word.capitalize() for word in op['name'].split())}"
        rule = "True for ADMIN or REGULAR_USER roles" if 'all users' in op['who'].lower() else f"True for {re.sub(r'[^\w\s]', '', op['who']).upper().replace(' ONLY', '')} role"
        permission_behaviors.append({
            'name': behavior_name,
            'description': f"Checks if a user can {op['name'].lower()}.",
            'rule': rule
        })
    if permission_behaviors:
        ddd['domain_services'].append({
            'name': 'InventoryPermissionPolicy',
            'description': 'Manages permissions for inventory operations.',
            'behaviors': permission_behaviors
        })

    logger.info("DDD inference completed")
    return ddd

def generate_csl(ddd, output_file):
    """Generate a CSL file from DDD elements."""
    logger.info(f"Generating CSL file: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"BoundedContext {ddd['bounded_context']} {{\n")
        f.write(f"  description: \"{ddd['description']}\"\n\n")

        for agg in ddd['aggregates']:
            f.write(f"  Aggregate {agg['name']} {{\n")
            f.write(f"    description: \"Represents a {agg['name'].lower()}.\"\n")
            f.write(f"    root: {agg['root']}\n")
            f.write("  }\n\n")

        for entity in ddd['entities']:
            f.write(f"  Entity {entity['name']} {{\n")
            f.write(f"    description: \"{entity['description']}\"\n")
            f.write("    attributes: {\n")
            for attr in entity['attributes']:
                f.write(f"      {attr['name']}: {attr['type']}\n")
            f.write("    }\n")
            f.write("    invariants: {\n")
            for i, inv in enumerate(entity['invariants'], 1):
                f.write(f"      I{i}: \"{inv}\"\n")
            f.write("    }\n")
            f.write("    behaviors: {\n")
            for beh in entity['behaviors']:
                f.write(f"      {beh['name']}: \"{beh['description']}\"\n")
            f.write("    }\n")
            f.write("  }\n\n")

        for vo in ddd['value_objects']:
            f.write(f"  ValueObject {vo['name']} {{\n")
            f.write(f"    description: \"{vo['description']}\"\n")
            f.write("    attributes: {\n")
            for attr in vo['attributes']:
                f.write(f"      {attr['name']}: {attr['type']}\n")
            f.write("    }\n")
            f.write("    invariants: {\n")
            for i, inv in enumerate(vo['invariants'], 1):
                f.write(f"      I{i}: \"{inv}\"\n")
            f.write("    }\n")
            if vo['instances']:
                f.write("    instances: {\n")
                for inst in vo['instances']:
                    f.write(f"      {inst['name']}: \"{inst['description']}\"\n")
                f.write("    }\n")
            f.write("  }\n\n")

        for svc in ddd['domain_services']:
            f.write(f"  DomainService {svc['name']} {{\n")
            f.write(f"    description: \"{svc['description']}\"\n")
            f.write("    behaviors: {\n")
            for beh in svc['behaviors']:
                f.write(f"      {beh['name']}: Boolean\n")
                f.write(f"        description: \"{beh['description']}\"\n")
                f.write(f"        rule: \"{beh['rule']}\"\n")
            f.write("    }\n")
            f.write("  }\n\n")

        for event in ddd['domain_events']:
            f.write(f"  DomainEvent {event['name']} {{\n")
            f.write(f"    description: \"{event['description']}\"\n")
            f.write("    attributes: {\n")
            for attr in event['attributes']:
                f.write(f"      {attr['name']}: {attr['type']}\n")
            f.write("    }\n")
            f.write("  }\n\n")

        for repo in ddd['repositories']:
            f.write(f"  Repository {repo['name']} {{\n")
            f.write(f"    description: \"Manages {repo['name'].replace('Repository', '')} persistence.\"\n")
            f.write("    behaviors: {\n")
            for beh in repo['behaviors']:
                f.write(f"      {beh}\n")
            f.write("    }\n")
            f.write("  }\n\n")

        f.write("}\n")
    logger.info(f"CSL file generated successfully: {output_file}")

def main():
    logger.info("Starting PRD to CSL conversion")
    if len(sys.argv) != 2:
        logger.error("Invalid arguments. Usage: python newnew-prd-to-csl.py <prd_file>")
        print("Usage: python newnew-prd-to-csl.py <prd_file>")
        sys.exit(1)

    prd_file = sys.argv[1]
    if not os.path.exists(prd_file):
        logger.error(f"PRD file not found: {prd_file}")
        print(f"Error: PRD file '{prd_file}' not found.")
        sys.exit(1)

    output_csl = f"{os.path.splitext(prd_file)[0]}_domain_model.csl"
    try:
        prd = parse_prd(prd_file)
        ddd = infer_ddd_elements(prd)
        generate_csl(ddd, output_csl)
        print(f"CSL file generated at: {output_csl}")
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        print(f"Error: Conversion failed. Check prd_to_csl.log for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()