import re
import os

def parse_prd(file_path):
    """Parse a PRD file into a structured dictionary."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    prd = {
        'overview': {'description': '', 'business_area': '', 'importance': ''},
        'key_terms': [],
        'features': [],
        'things': [],
        'operations': [],
        'connections': [],
        'constraints': []
    }

    # Split content into sections
    sections = re.split(r'# Section: (\w+)', content)[1:]
    section_pairs = [(sections[i], sections[i+1]) for i in range(0, len(sections), 2)]

    for section_name, section_content in section_pairs:
        section_name = section_name.strip().lower().replace(' ', '_')

        if section_name == 'overview':
            description = re.search(r'- Product Description: (.*?)(?=- Business Area:|\Z)', section_content, re.DOTALL)
            business_area = re.search(r'- Business Area: (.*?)(?=- Importance:|\Z)', section_content, re.DOTALL)
            importance = re.search(r'- Importance: (.*?)(?=\Z)', section_content, re.DOTALL)
            if description:
                prd['overview']['description'] = description.group(1).strip()
            if business_area:
                prd['overview']['business_area'] = business_area.group(1).strip()
            if importance:
                prd['overview']['importance'] = importance.group(1).strip()

        elif section_name == 'key_terms':
            terms = re.findall(r'- (\w+): (.*?)(?=(?:- \w+: |\Z))', section_content, re.DOTALL)
            prd['key_terms'] = [{'name': term[0], 'description': term[1].strip()} for term in terms]

        elif section_name == 'features':
            features = re.findall(r'- (.*?): (.*?)(?=(?:- |(?:#|\Z)))', section_content, re.DOTALL)
            prd['features'] = [{'name': f[0].strip(), 'description': f[1].strip()} for f in features]

        elif section_name == 'things':
            things = section_content.split('- ')[1:]  # Split by each thing
            for thing in things:
                if not thing.strip():
                    continue
                name_match = re.match(r'(\w+): (.*?)(?=(?:##|\Z))', thing, re.DOTALL)
                if not name_match:
                    continue
                thing_name = name_match.group(1).strip()
                thing_desc = name_match.group(2).strip()

                properties = re.findall(r'- (\w+): (.*?)(?=(?:- |\Z))', thing, re.DOTALL)
                rules = re.findall(r'## Rules:\s*- (.*?)(?=(?:- |\Z))', thing, re.DOTALL)
                actions = re.findall(r'## Actions:\s*- (.*?)(?=(?:- |\Z))', thing, re.DOTALL)

                prd['things'].append({
                    'name': thing_name,
                    'description': thing_desc,
                    'properties': [{'name': p[0], 'description': p[1].strip()} for p in properties],
                    'rules': [r.strip() for r in rules],
                    'actions': [a.strip() for a in actions]
                })

        elif section_name == 'operations':
            ops = re.findall(r'## (.*?)\n(.*?)(?=(?:## |\Z))', section_content, re.DOTALL)
            for op_name, op_content in ops:
                desc = re.search(r'- Describe what the action does: (.*?)(?=- Who Can Do It:|\Z)', op_content, re.DOTALL)
                who = re.search(r'- Who Can Do It: (.*?)(?=- Inputs:|\Z)', op_content, re.DOTALL)
                inputs = re.findall(r'- (\w+): (\w+)', op_content)
                outputs = re.search(r'- Outputs: (.*?)(?=- Conditions:|\Z)', op_content, re.DOTALL)
                conditions = re.findall(r'- Conditions:\s*(.*?)(?=(?:- |\Z))', op_content, re.DOTALL)
                results = re.search(r'- Results: (.*?)(?=- Notifications:|\Z)', op_content, re.DOTALL)
                notifications = re.findall(r'- Notifications:\s*(.*?)(?=(?:- |\Z))', op_content, re.DOTALL)

                prd['operations'].append({
                    'name': op_name.strip(),
                    'description': desc.group(1).strip() if desc else '',
                    'who': who.group(1).strip() if who else '',
                    'inputs': [{'name': i[0], 'type': i[1]} for i in inputs],
                    'outputs': outputs.group(1).strip() if outputs else '',
                    'conditions': [c.strip() for c in conditions],
                    'results': results.group(1).strip() if results else '',
                    'notifications': [n.strip() for n in notifications]
                })

        elif section_name == 'connections':
            connections = re.findall(r'- (.*?): (.*?)(?=(?:- |\Z))', section_content, re.DOTALL)
            prd['connections'] = [{'name': c[0].strip(), 'description': c[1].strip()} for c in connections]

        elif section_name == 'constraints':
            constraints = re.findall(r'- (.*?)(?=(?:- |\Z))', section_content, re.DOTALL)
            prd['constraints'] = [c.strip() for c in constraints]

    return prd

def infer_ddd_elements(prd):
    """Infer DDD elements from the parsed PRD."""
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

    # Infer entities and value objects from Things
    for thing in prd['things']:
        # Assume Things with a unique ID property are entities
        has_id = any('unique' in p['description'].lower() for p in thing['properties'])
        if has_id:
            entity = {
                'name': thing['name'],
                'description': thing['description'],
                'attributes': [],
                'invariants': thing['rules'],
                'behaviors': [a.split(':')[0].strip() for a in thing['actions']]
            }
            for prop in thing['properties']:
                # Parse property description (e.g., "text, required, unique")
                desc = prop['description'].split(',')
                type_ = desc[0].strip()
                constraints = [c.strip() for c in desc[1:]] if len(desc) > 1 else []
                entity['attributes'].append({
                    'name': prop['name'],
                    'type': type_.capitalize(),
                    'constraints': constraints
                })
            ddd['entities'].append(entity)
            # Each entity is an aggregate root
            ddd['aggregates'].append({
                'name': thing['name'],
                'root': thing['name']
            })
            # Assume a repository for each entity
            ddd['repositories'].append({
                'name': f"{thing['name']}Repository",
                'behaviors': [
                    f"findById({prop['name']}: {prop['type'].capitalize()}): {thing['name']}",
                    f"findAll(): List<{thing['name']}>",
                    f"save({thing['name'].lower()}: {thing['name']})",
                    f"delete({thing['name'].lower()}: {thing['name']})"
                ] for prop in thing['properties'] if 'unique' in prop['description'].lower()
            })
        else:
            # Assume non-ID properties (e.g., roles) are value objects
            ddd['value_objects'].append({
                'name': thing['name'],
                'description': thing['description'],
                'attributes': [{'name': p['name'], 'type': p['description'].split(',')[0].strip().capitalize()} for p in thing['properties']],
                'invariants': thing['rules'],
                'instances': []  # Infer instances for roles
            })

    # Infer value objects from properties (e.g., inventoryId, email)
    for thing in prd['things']:
        for prop in thing['properties']:
            if 'unique' in prop['description'].lower() or 'valid email' in prop['description'].lower():
                vo_name = prop['name'].capitalize()
                ddd['value_objects'].append({
                    'name': vo_name,
                    'description': f"{vo_name} for {thing['name']}.",
                    'attributes': [{'name': 'value', 'type': prop['description'].split(',')[0].strip().capitalize()}],
                    'invariants': [c.strip() for c in prop['description'].split(',')[1:] if c],
                    'instances': []
                })
            elif 'list of roles' in prop['description'].lower():
                # Handle roles as a value object with instances
                role_vo = next((vo for vo in ddd['value_objects'] if vo['name'] == 'Role'), None)
                if role_vo:
                    role_vo['instances'] = [
                        {'name': 'ADMIN', 'description': 'Grants add/remove permissions'},
                        {'name': 'REGULAR_USER', 'description': 'Grants view permissions'}
                    ]

    # Infer domain events from notifications
    for op in prd['operations']:
        for notif in op['notifications']:
            event_name = notif.split(' ')[1].capitalize() + notif.split(' ')[2].capitalize()
            event_attrs = [{'name': i['name'], 'type': i['type'].capitalize()} for i in op['inputs']]
            ddd['domain_events'].append({
                'name': event_name,
                'description': notif,
                'attributes': event_attrs
            })

    # Infer domain service for permissions
    permission_behaviors = []
    for op in prd['operations']:
        if op['who'].lower() != 'all users':
            behavior_name = f"can{op['name'].replace(' ', '')}"
            permission_behaviors.append({
                'name': behavior_name,
                'description': f"Checks if a user can {op['name'].lower()}.",
                'rule': f"True for {op['who'].upper().replace(' ONLY', '')} role"
            })
        # Add view permission for all users
        if 'view' in op['name'].lower():
            permission_behaviors.append({
                'name': f"can{op['name'].replace(' ', '')}",
                'description': f"Checks if a user can {op['name'].lower()}.",
                'rule': "True for ADMIN or REGULAR_USER roles"
            })
    if permission_behaviors:
        ddd['domain_services'].append({
            'name': 'InventoryPermissionPolicy',
            'description': 'Manages permissions for inventory operations.',
            'behaviors': permission_behaviors
        })

    return ddd

def generate_csl(ddd, output_file):
    """Generate a CSL file from DDD elements."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"BoundedContext {ddd['bounded_context']} {{\n")
        f.write(f"  description: \"{ddd['description']}\"\n\n")

        # Aggregates
        for agg in ddd['aggregates']:
            f.write(f"  Aggregate {agg['name']} {{\n")
            f.write(f"    description: \"Represents a {agg['name'].lower()}.\"\n")
            f.write(f"    root: {agg['root']}\n")
            f.write("  }\n\n")

        # Entities
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
                f.write(f"      {beh}: \"Performs {beh.lower()}.\"\n")
            f.write("    }\n")
            f.write("  }\n\n")

        # Value Objects
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

        # Domain Services
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

        # Domain Events
        for event in ddd['domain_events']:
            f.write(f"  DomainEvent {event['name']} {{\n")
            f.write(f"    description: \"{event['description']}\"\n")
            f.write("    attributes: {\n")
            for attr in event['attributes']:
                f.write(f"      {attr['name']}: {attr['type']}\n")
            f.write("    }\n")
            f.write("  }\n\n")

        # Repositories
        for repo in ddd['repositories']:
            f.write(f"  Repository {repo['name']} {{\n")
            f.write(f"    description: \"Manages {repo['name'].replace('Repository', '')} persistence.\"\n")
            f.write("    behaviors: {\n")
            for beh in repo['behaviors']:
                f.write(f"      {beh}\n")
            f.write("    }\n")
            f.write("  }\n\n")

        f.write("}\n")

def main(prd_file, output_csl):
    prd = parse_prd(prd_file)
    ddd = infer_ddd_elements(prd)
    generate_csl(ddd, output_csl)
    print(f"CSL file generated at: {output_csl}")

if __name__ == "__main__":
    prd_file = "simple_bookshop_inventory.prd"  # Replace with your PRD file path
    output_csl = "simple_bookshop_inventory.csl"
    main(prd_file, output_csl)