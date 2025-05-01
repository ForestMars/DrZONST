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
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    prd = {
        'overview': {'description': '', 'business_area': '', 'importance': ''},
        'key_terms': [],
        'features': [],
        'things': [],
        'operations': [],
        'connections': [],
        'constraints': []
    }

    current_section = None
    current_thing = None
    current_op = None
    current_subsection = None

    for line in lines:
        line = line.strip()
        if not line or line.startswith('# Product Requirements Document'):
            continue

        # Section headers
        section_match = re.match(r'#\s*(?:Section:\s*)?(\w+(?:\s+\w+)?)', line, re.IGNORECASE)
        if section_match:
            current_section = section_match.group(1).lower().replace(' ', '_')
            current_thing = None
            current_op = None
            current_subsection = None
            logger.debug(f"Entering section: {current_section}")
            continue

        if not current_section:
            continue

        # Overview
        if current_section == 'overview':
            desc_match = re.match(r'- Product Description: (.*)', line)
            area_match = re.match(r'- Business Area: (.*)', line)
            imp_match = re.match(r'- Importance: (.*)', line)
            if desc_match:
                prd['overview']['description'] = desc_match.group(1)
            elif area_match:
                prd['overview']['business_area'] = area_match.group(1)
            elif imp_match:
                prd['overview']['importance'] = imp_match.group(1)

        # Key Terms, Features, Connections, Constraints
        elif current_section in ['key_terms', 'features', 'connections', 'constraints']:
            item_match = re.match(r'- (.*?)(?::\s*(.*))?$', line)
            if item_match:
                name, desc = item_match.groups()
                desc = desc or ''
                if current_section == 'key_terms':
                    prd['key_terms'].append({'name': name, 'description': desc})
                elif current_section == 'features':
                    prd['features'].append({'name': name, 'description': desc})
                elif current_section == 'connections':
                    prd['connections'].append({'name': name, 'description': desc})
                elif current_section == 'constraints':
                    prd['constraints'].append(name)

        # Things
        elif current_section == 'things':
            thing_match = re.match(r'- (\w+): (.*)', line)
            subheader_match = re.match(r'##\s*(Properties|Rules|Actions):?', line, re.IGNORECASE)
            if thing_match and not current_subsection:  # Only start a new thing if not in a subsection
                current_thing = {
                    'name': thing_match.group(1),
                    'description': thing_match.group(2),
                    'properties': [],
                    'rules': [],
                    'actions': []
                }
                prd['things'].append(current_thing)
                logger.debug(f"New thing: {current_thing['name']}")
            elif subheader_match and current_thing:
                current_subsection = subheader_match.group(1).lower()
                logger.debug(f"Subsection in {current_thing['name']}: {current_subsection}")
            elif current_thing and line.startswith('- ') and current_subsection:
                content = line[2:].strip()
                if current_subsection == 'properties':
                    prop_match = re.match(r'(\w+):\s*(.*)', content)
                    if prop_match:
                        current_thing['properties'].append({
                            'name': prop_match.group(1),
                            'description': prop_match.group(2)
                        })
                elif current_subsection == 'rules':
                    current_thing['rules'].append(content)
                elif current_subsection == 'actions':
                    action_match = re.match(r'(\w+\s+\w+):\s*(.*)', content)
                    if action_match:
                        current_thing['actions'].append({
                            'name': action_match.group(1),
                            'description': action_match.group(2)
                        })

        # Operations
        elif current_section == 'operations':
            op_match = re.match(r'##\s*(.*?)$', line)
            if op_match:
                current_op = {
                    'name': op_match.group(1),
                    'description': '',
                    'who': '',
                    'inputs': [],
                    'outputs': '',
                    'conditions': [],
                    'results': '',
                    'notifications': []
                }
                prd['operations'].append(current_op)
                current_subsection = None
                logger.debug(f"New operation: {current_op['name']}")
            elif current_op:
                desc_match = re.match(r'- Describe what the action does: (.*)', line)
                who_match = re.match(r'- Who Can Do It: (.*)', line)
                input_match = re.match(r'- (\w+): (\w+)', line)
                output_match = re.match(r'- Outputs: (.*)', line)
                cond_match = re.match(r'- Conditions:\s*(.*)', line) or re.match(r'\s*- (.*)', line) if 'conditions' in (current_subsection or '') else None
                result_match = re.match(r'- Results: (.*)', line)
                notif_match = re.match(r'- Notifications:\s*(.*)', line) or re.match(r'\s*- (.*)', line) if 'notifications' in (current_subsection or '') else None
                if desc_match:
                    current_op['description'] = desc_match.group(1)
                elif who_match:
                    current_op['who'] = who_match.group(1)
                elif input_match and 'inputs' in line.lower():
                    current_subsection = 'inputs'
                elif input_match and current_subsection == 'inputs':
                    current_op['inputs'].append({'name': input_match.group(1), 'type': input_match.group(2)})
                elif output_match:
                    current_op['outputs'] = output_match.group(1)
                    current_subsection = 'outputs'
                elif cond_match:
                    current_subsection = 'conditions'
                    if cond_match.group(1) and not cond_match.group(1).startswith('Conditions:'):
                        current_op['conditions'].append(cond_match.group(1))
                elif result_match:
                    current_op['results'] = result_match.group(1)
                    current_subsection = 'results'
                elif notif_match:
                    current_subsection = 'notifications'
                    if notif_match.group(1) and not notif_match.group(1).startswith('Notifications:'):
                        current_op['notifications'].append(notif_match.group(1))

    logger.info("PRD parsing completed")
    logger.debug(f"Parsed PRD: {prd}")
    return prd

def infer_ddd_elements(prd):
    """Infer DDD elements from the parsed PRD."""
    logger.info("Inferring DDD elements")
    ddd = {
        'bounded_context': re.sub(r'[^\w]', '', prd['overview']['business_area']) or 'UnnamedContext',
        'description': prd['overview']['description'],
        'entities': [],
        'value_objects': [],
        'aggregates': [],
        'domain_services': [],
        'domain_events': [],
        'repositories': [],
        'relationships': prd['connections']
    }

    # Entities and Aggregates
    for thing in prd['things']:
        has_id = any('unique' in p['description'].lower() for p in thing['properties'])
        if has_id:
            entity = {
                'name': thing['name'],
                'description': thing['description'],
                'attributes': [{'name': p['name'], 'type': p['description'].split(',')[0].strip().capitalize(),
                                'constraints': [c.strip() for c in p['description'].split(',')[1:]]} 
                               for p in thing['properties']],
                'invariants': thing['rules'],
                'behaviors': [{'name': a['name'], 'description': a['description']} for a in thing['actions']]
            }
            ddd['entities'].append(entity)
            ddd['aggregates'].append({'name': thing['name'], 'root': thing['name']})
            id_prop = next(p for p in thing['properties'] if 'unique' in p['description'].lower())
            ddd['repositories'].append({
                'name': f"{thing['name']}Repository",
                'behaviors': [
                    f"findById({id_prop['name']}: {id_prop['description'].split(',')[0].strip().capitalize()}): {thing['name']}",
                    f"findAll(): List<{thing['name']}>",
                    f"save({thing['name'].lower()}: {thing['name']})",
                    f"delete({thing['name'].lower()}: {thing['name']})"
                ]
            })

    # Value Objects (e.g., Role)
    for thing in prd['things']:
        for prop in thing['properties']:
            if 'list of roles' in prop['description'].lower():
                ddd['value_objects'].append({
                    'name': 'Role',
                    'description': 'Represents a user role.',
                    'attributes': [{'name': 'name', 'type': 'String'}],
                    'invariants': ['name must be Admin or Regular User'],
                    'instances': [
                        {'name': 'Admin', 'description': 'Grants add/remove permissions'},
                        {'name': 'Regular User', 'description': 'Grants view permissions'}
                    ]
                })

    # Domain Events
    for op in prd['operations']:
        for notif in op['notifications']:
            event_name = ''.join(word.capitalize() for word in notif.split(' ')[1:3])
            ddd['domain_events'].append({
                'name': event_name,
                'description': notif,
                'attributes': [{'name': i['name'], 'type': i['type'].capitalize()} for i in op['inputs']]
            })

    # Domain Services
    permission_behaviors = []
    for op in prd['operations']:
        behavior_name = f"can{''.join(word.capitalize() for word in op['name'].split())}"
        rule = "True for Admin or Regular User roles" if 'all users' in op['who'].lower() else f"True for {op['who'].upper().replace(' ONLY', '')} role"
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
    logger.debug(f"Inferred DDD: {ddd}")
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
                f.write(f"      {attr['name']}: {attr['type']}")
                if attr['constraints']:
                    f.write(f" {{ {', '.join(attr['constraints'])} }}")
                f.write("\n")
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
        logger.error("Invalid arguments. Usage: python prd_to_csl.py <prd_file>")
        print("Usage: python prd_to_csl.py <prd_file>")
        sys.exit(1)

    prd_file = sys.argv[1]
    if not os.path.exists(prd_file):
        logger.error(f"PRD file not found: {prd_file}")
        print(f"Error: PRD file '{prd_file}' not found.")
        sys.exit(1)

    output_csl = f"{os.path.splitext(prd_file)[0]}_domain_model.csl"
    prd = parse_prd(prd_file)
    ddd = infer_ddd_elements(prd)
    generate_csl(ddd, output_csl)
    print(f"CSL file generated at: {output_csl}")

if __name__ == "__main__":
    main()