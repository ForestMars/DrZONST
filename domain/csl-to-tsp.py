import re
from typing import Dict, List

class CSLToTypeSpecConverter:
    def __init__(self):
        self.output = []
        self.indent_level = 0

    def indent(self) -> str:
        return "  " * self.indent_level

    def add_line(self, line: str):
        self.output.append(f"{self.indent()}{line}")

    def parse_attributes(self, attrs: str) -> List[Dict]:
        attributes = []
        attr_lines = attrs.strip().split('\n')
        for line in attr_lines:
            if ':' in line:
                name, rest = line.split(':', 1)
                name = name.strip()
                type_match = re.match(r'(\w+)(?:\s*\{([^}]*)\})?', rest.strip())
                if type_match:
                    type_name, constraints = type_match.groups()
                    attr = {'name': name, 'type': type_name.strip()}
                    if constraints:
                        attr['constraints'] = [c.strip() for c in constraints.split(',')]
                    attributes.append(attr)
        return attributes

    def convert(self, csl_content: str) -> str:
        self.output = []
        lines = csl_content.split('\n')
        context_name = ""
        
        # Extract bounded context name
        context_match = re.match(r'BoundedContext\s+(\w+)', csl_content)
        if context_match:
            context_name = context_match.group(1)

        # Generate service header
        self.add_line(f"namespace {context_name};")
        self.add_line("")
        self.add_line('@doc("Generated API from CSL model")')
        self.add_line(f"service {context_name}Service {{")
        self.indent_level += 1
        self.add_line('host: "api.example.com";')
        self.add_line('version: "1.0.0";')
        self.indent_level -= 1
        self.add_line("}")
        self.add_line("")

        # Parse entities and generate models
        entity_pattern = r'Entity\s+(\w+)\s*{(.*?)}'
        for entity_match in re.finditer(entity_pattern, csl_content, re.DOTALL):
            entity_name, entity_content = entity_match.groups()
            
            # Extract attributes
            attrs_match = re.search(r'attributes:\s*{(.*?)}', entity_content, re.DOTALL)
            if attrs_match:
                attributes = self.parse_attributes(attrs_match.group(1))
                
                # Generate model
                self.add_line(f"model {entity_name} {{")
                self.indent_level += 1
                for attr in attributes:
                    line = f"{attr['name']}"
                    if attr['type'] == 'List':
                        line += ": string[]"
                    else:
                        line += f": {attr['type'].lower()}"
                    if attr.get('constraints'):
                        if 'optional' not in attr['constraints']:
                            line += ";"
                        else:
                            line += "?;"
                    else:
                        line += ";"
                    self.add_line(line)
                self.indent_level -= 1
                self.add_line("}")
                self.add_line("")

            # Extract behaviors and generate endpoints
            behaviors_match = re.search(r'behaviors:\s*{(.*?)}', entity_content, re.DOTALL)
            if behaviors_match:
                behaviors = behaviors_match.group(1).strip().split('\n')
                self.add_line(f"@route(\"/{entity_name.lower()}s\")")
                self.add_line(f"interface {entity_name}Operations {{")
                self.indent_level += 1
                
                for behavior in behaviors:
                    if ':' in behavior:
                        name, desc = behavior.split(':', 1)
                        name = name.strip()
                        if "add" in name.lower():
                            self.add_line("@post")
                            self.add_line(f"@doc(\"{desc.strip()}\")")
                            self.add_line(f"create(@body {entity_name.lower()}: {{")
                            self.indent_level += 1
                            for attr in attributes:
                                if 'required' in attr.get('constraints', []):
                                    self.add_line(f"{attr['name']}: {attr['type'].lower()};")
                            self.indent_level -= 1
                            self.add_line("}): {")
                            self.indent_level += 1
                            self.add_line(f"@statusCode statusCode: 201;")
                            self.add_line(f"@body created{entity_name}: {entity_name};")
                            self.indent_level -= 1
                            self.add_line("} | {")
                            self.indent_level += 1
                            self.add_line("@statusCode statusCode: 400;")
                            self.add_line('@body error: string;')
                            self.indent_level -= 1
                            self.add_line("};")
                            self.add_line("")
                        elif "remove" in name.lower():
                            self.add_line("@delete")
                            self.add_line(f"@route(\"/{{inventoryId}}\")")
                            self.add_line(f"@doc(\"{desc.strip()}\")")
                            self.add_line(f"delete(@path inventoryId: string): {{")
                            self.indent_level += 1
                            self.add_line("@statusCode statusCode: 204;")
                            self.indent_level -= 1
                            self.add_line("} | {")
                            self.indent_level += 1
                            self.add_line("@statusCode statusCode: 404;")
                            self.add_line('@body error: string;')
                            self.indent_level -= 1
                            self.add_line("};")
                            self.add_line("")
                
                self.indent_level -= 1
                self.add_line("}")

        # Handle ValueObjects as enums
        vo_pattern = r'ValueObject\s+(\w+)\s*{(.*?)}'
        for vo_match in re.finditer(vo_pattern, csl_content, re.DOTALL):
            vo_name, vo_content = vo_match.groups()
            instances_match = re.search(r'instances:\s*{(.*?)}', vo_content, re.DOTALL)
            if instances_match:
                self.add_line(f"enum {vo_name} {{")
                self.indent_level += 1
                instances = instances_match.group(1).strip().split('\n')
                for instance in instances:
                    if ':' in instance:
                        name, desc = instance.split(':', 1)
                        self.add_line(f"@doc(\"{desc.strip()}\")")
                        self.add_line(f"{name.strip()},")
                self.indent_level -= 1
                self.add_line("}")
                self.add_line("")

        return "\n".join(self.output)

# Example usage
def convert_csl_to_typespec(csl_file_path: str, output_file_path: str):
    with open(csl_file_path, 'r') as f:
        csl_content = f.read()
    
    converter = CSLToTypeSpecConverter()
    typespec_content = converter.convert(csl_content)
    
    with open(output_file_path, 'w') as f:
        f.write(typespec_content)

# Test with your CSL content
if __name__ == "__main__":
    # You would typically read from a file, but here's an example with the content
    csl_content = """[your CSL content here]"""
    converter = CSLToTypeSpecConverter()
    print(converter.convert(csl_content))