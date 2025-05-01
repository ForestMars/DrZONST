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

    prd = {
        'overview': {'description': '', 'business_area': '', 'importance': ''},
        'key_terms': [],
        'features': [],
        'things': [],
        'operations': [],
        'connections': [],
        'constraints': []
    }

    # Normalize content (handle extra newlines, spaces)
    content = re.sub(r'\n\s*\n', '\n', content.strip())
    logger.debug(f"Normalized PRD content length: {len(content)} characters")

    # Split into sections
    sections = re.split(r'# Section: (\w+)', content)
    if len(sections) < 2:
        logger.error("No sections found in PRD file")
        return prd
    section_pairs = [(sections[i], sections[i+1]) for i in range(1, len(sections), 2)]
    logger.info(f"Found {len(section_pairs)} sections")

    for section_name, section_content in section_pairs:
        section_name = section_name.strip().lower().replace(' ', '_')
        logger.debug(f"Processing section: {section_name}")

        if section_name == 'overview':
            description = re.search(r'- Product Description: (.*?)(?=(?:- Business Area:|\Z))', section_content, re.DOTALL)
            business_area = re.search(r'- Business Area: (.*?)(?=(?:- Importance:|\Z))', section_content, re.DOTALL)
            importance = re.search(r'- Importance: (.*?)(?=\Z)', section_content, re.DOTALL)
            prd['overview']['description'] = description.group(1).strip() if description else ''
            prd['overview']['business_area'] = business_area.group(1).strip() if business_area else ''
            prd['overview']['importance'] = importance.group(1).strip() if importance else ''
            logger.debug(f"Overview parsed: description={prd['overview']['description'][:50]}..., business_area={prd['overview']['business_area']}")

        elif section_name == 'key_terms':
            terms = re.findall(r'- (\w+): (.*?)(?=(?:- \w+: |\Z))', section_content, re.DOTALL)
            prd['key_terms'] = [{'name': term[0].strip(), 'description': term[1].strip()} for term in terms]
            logger.debug(f"Parsed {len(prd['key_terms'])} key terms")

        elif section_name == 'features':
            features = re.findall(r'- (.*?): (.*?)(?=(?:- |(?:#|\Z)))', section_content, re.DOTALL)
            prd['features'] = [{'name': f[0].strip(), 'description': f[1].strip()} for f in features]
            logger.debug(f"Parsed {len(prd['features'])} features")

        elif section_name == 'things':
            things = re.split(r'- (\w+):', section_content)[1:]
            things = [(things[i], things[i+1]) for i in range(0, len(things), 2)]
            for thing_name, thing_content in things:
                thing_name = thing_name.strip()
                thing_desc = re.match(r'(.*?)(?=(?:##|\Z))', thing_content, re.DOTALL)
                thing_desc = thing_desc.group(1).strip() if thing_desc else ''

                properties = re.findall(r'- (\w+): (.*?)(?=(?:- |\Z))', thing_content, re.DOTALL)
                rules = re.findall(r'## Rules:\s*- (.*?)(?=(?:- |\Z))', thing_content, re.DOTALL)
                actions = re.findall(r'## Actions:\s*- (.*?)(?=(?:- |\Z))', thing_content, re.DOTALL)

                prd['things'].append({
                    'name': thing_name,
                    'description': thing_desc,
                    'properties': [{'name': p[0].strip(), 'description': p[1].strip()} for p in properties],
                    'rules': [r.strip() for r in rules],
                    'actions': [a.strip() for a in actions]
                })
            logger.debug(f"Parsed {len(prd['things'])} things")

        elif section_name == 'operations':
            ops = re.findall(r'## (.*?)\n(.*?)(?=(?:## |\Z))', section_content, re.DOTALL)
            for op_name, op_content in ops:
                desc = re.search(r'- Describe what the action does: (.*?)(?=(?:- Who Can Do It:|\Z))', op_content, re.DOTALL)
                who = re.search(r'- Who Can Do It: (.*?)(?=(?:- Inputs:|\Z))', op_content, re.DOTALL)
                inputs = re.findall(r'- (\w+): (\w+)', op_content)
                outputs = re.search(r'- Outputs: (.*?)(?=(?:- Conditions:|\Z))', op_content, re.DOTALL)
                conditions = re.findall(r'- Conditions:\s*- (.*?)(?=(?:- |\Z))', op_content, re.DOTALL)
                results = re.search(r'- Results: (.*?)(?=(?:- Notifications:|\Z))', op_content, re.DOTALL)
                notifications = re.findall(r'- Notifications:\s*- (.*?)(?=(?:- |\Z))', op_content, re.DOTALL)

                prd['operations'].append({
                    'name': op_name.strip(),
                    'description': desc.group(1).strip() if desc else '',
                    'who': who.group(1).strip() if who else '',
                    'inputs': [{'name': i[0].strip(), 'type': i[1].strip()} for i in inputs],
                    'outputs': outputs.group(1).strip() if outputs else '',
                    'conditions': [c.strip() for c in conditions],
                    'results': outputs.group(1).strip() if outputs else '',
                    'notifications': [n.strip() for n in notifications]
                })
            logger.debug(f"Parsed {len(prd['operations'])} operations")

        elif section_name == 'connections':
            connections = re.findall(r'- (.*?): (.*?)(?=(?:- |\Z))', section_content, re.DOTALL)
            prd['connections'] = [{'name': c[0].strip(), 'description': c[1].strip()} for c in connections]
            logger.debug(f"Parsed {len(prd['connections'])} connections")

        elif section_name == 'constraints':
            constraints = re.findall(r'- (.*?)(?=(?:- |\Z))', section_content, re.DOTALL)
            prd['constraints'] = [c.strip() for c in constraints]
            logger.debug(f"Parsed {len(prd['constraints'])} constraints")

    logger.info("PRD parsing completed")
    logger.debug(f"PRD structure: {prd}")
    return prd

def infer_ddd_elements(prd):
    """Infer DDD elements from the parsed PRD."""
    logger.info("Inferring DDD elements")
    ddd = {
        'bounded_context': prd['overview']['business_area'].replace(' ', ''),
        'description': prd['overview']['description'],
        'entities': [],
        'value_objects': [],
        'aggregates': [],
        'domain_services': [],
        'domain_events': [],
        'repositories': [],
        'relationships': prd['connections']
    }
    logger.debug(f"Bounded context: {ddd['bounded_context']}")

    # Infer entities and value objects from Things
    for thing in prd['things']:
        logger.debug(f"Processing thing: {thing['name']}")
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
            logger.debug(f"Added entity: {thing['name']}")
        else:
            vo = {
                'name': thing['name'],
                'description': thing['description'],
                'attributes': [{'name': p['name'], 'type': p['description'].split(',')[0].strip().capitalize()} for p in thing['properties']],
                'invariants': thing['rules'],
                'instances': []
            }
            ddd['value_objects'].append(vo)
            logger.debug(f"Added value object: {thing['name']}")

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
                logger.debug(f"Added value object from property: {vo_name}")
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
                logger.debug("Added Role instances: ADMIN, REGULAR_USER")

    # Infer domain events from notifications
    for op in prd['operations']:
        for notif in op['notifications']:
            event_name = ''.join(word.capitalize() for word in notif.split(' ')[1:3])
            event_attrs = [{'name': i['name'], 'type': i['type'].capitalize()} for i in op['inputs']]
            ddd['domain_events'].append({
                'name': event_name,
                'description': notif,
                'attributes': event_attrs
            })
            logger.debug(f"Added domain event: {event_name}")

    # Infer domain service for permissions
    permission_behaviors = []
    for op in prd['operations']:
        behavior_name = f"can{''.join(word.capitalize() for word in op['name'].split())}"
        rule = "True for ADMIN or REGULAR_USER roles" if 'all users' in op['who'].lower() else f"True for {op['who'].upper().replace(' ONLY', '')} role"
        permission_behaviors.append({
            'name': behavior_name,
            'description': f"Checks if a user can {op['name'].lower()}.",
            'rule': rule
        })
        logger.debug(f"Added permission behavior: {behavior_name}")
    if permission_behaviors:
        ddd['domain_services'].append({
            'name': 'InventoryPermissionPolicy',
            'description': 'Manages permissions for inventory operations.',
            'behaviors': permission_behaviors
        })
        logger.debug("Added domain service: InventoryPermissionPolicy")

    logger.info("DDD inference completed")
    logger.debug(f"DDD structure: {ddd}")
    return ddd

def generate_csl(ddd, output_file):
    """Generate a CSL file from DDD elements."""
    logger.info(f"Generating CSL file: {output_file}")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"BoundedContext {ddd['bounded_context']} {{\n")
            f.write(f"  description: \"{ddd['description']}\"\n\n")

            for agg in ddd['aggregates']:
                f.write(f"  Aggregate {agg['name']} {{\n")
                f.write(f"    description: \"Represents a {agg['name'].lower()}.\"\n")
                f.write(f"    root: {agg['root']}\n")
                f.write("  }\n\n")
                logger.debug(f"Wrote aggregate: {agg['name']}")

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
                logger.debug(f"Wrote entity: {entity['name']}")

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
                logger.debug(f"Wrote value object: {vo['name']}")

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
                logger.debug(f"Wrote domain service: {svc['name']}")

            for event in ddd['domain_events']:
                f.write(f"  DomainEvent {event['name']} {{\n")
                f.write(f"    description: \"{event['description']}\"\n")
                f.write("    attributes: {\n")
                for attr in event['attributes']:
                    f.write(f"      {attr['name']}: {attr['type']}\n")
                f.write("    }\n")
                f.write("  }\n\n")
                logger.debug(f"Wrote domain event: {event['name']}")

            for repo in ddd['repositories']:
                f.write(f"  Repository {repo['name']} {{\n")
                f.write(f"    description: \"Manages {repo['name'].replace('Repository', '')} persistence.\"\n")
                f.write("    behaviors: {\n")
                for beh in repo['behaviors']:
                    f.write(f"      {beh}\n")
                f.write("    }\n")
                f.write("  }\n\n")
                logger.debug(f"Wrote repository: {repo['name']}")

            f.write("}\n")
        logger.info(f"CSL file generated successfully: {output_file}")
    except Exception as e:
        logger.error(f"Failed to generate CSL file: {e}")
        raise

def main():
    logger.info("Starting PRD to CSL conversion")
    if len(sys.argv) != 2:
        logger.error("Invalid arguments. Usage: python prd_to_csl.py <prd_file>")
        print("Usage: python prd_to_csl.py <prd_file>")
        sys.exit(1)

    prd_file = sys.argv[1]
    logger.info(f"Input PRD file: {prd_file}")
    if not os.path.exists(prd_file):
        logger.error(f"PRD file not found: {prd_file}")
        print(f"Error: PRD file '{prd_file}' not found.")
        sys.exit(1)

    output_csl = f"{os.path.splitext(prd_file)[0]}_domain_model.csl"
    logger.info(f"Output CSL file: {output_csl}")
    try:
        prd = parse_prd(prd_file)
        ddd = infer_ddd_elements(prd)
        generate_csl(ddd, output_csl)
        logger.info("Conversion completed successfully")
        print(f"CSL file generated at: {output_csl}")
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        print(f"Error: Conversion failed. Check prd_to_csl.log for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()