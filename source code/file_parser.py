import tree_sitter_java as tsjava
from tree_sitter import Language, Parser

def initialize_parser():
    global parser
    parser = Parser()
    JAVA_LANGUAGE = Language(tsjava.language(), 'java')
    parser.set_language(JAVA_LANGUAGE)

def extract_node_text(node, field_name, default):
    field_node = node.child_by_field_name(field_name)
    return field_node.text.decode('utf-8') if field_node else default

def get_method_signature(method_declaration_node):
    method_name = extract_node_text(method_declaration_node, 'name', '<unknown>')
    parameters = extract_node_text(method_declaration_node, 'parameters', '()')

    return f'{method_name}{parameters}'

def get_method_body(method_declaration_node):
    return method_declaration_node.text.decode('utf-8')

def extract_package_and_methods(content):
    try:
        root_node = parse_file(content)
        methods = {}
        package = None
        if(root_node is not None):
            for node in root_node.children:
                if node.type == 'package_declaration':
                    for child in node.children:
                        if child.type == 'scoped_identifier':
                            package = child.text.decode('utf-8')
            
            def traverse(node):
                if node.type == 'method_declaration' or node.type == 'constructor_declaration':
                        method_signature = get_method_signature(node)
                        method_body = get_method_body(node)
                        methods[method_signature] = method_body
                for child in node.children:
                    traverse(child)

            traverse(root_node)
        return package, methods
    
    except Exception as e:
        print(f"Error processing: {e}")
        return package, methods

def extract_node_text(node, field_name, default):
    field_node = node.child_by_field_name(field_name)
    return field_node.text.decode('utf-8') if field_node else default

def get_method_signature(method_declaration_node):
    method_name = extract_node_text(method_declaration_node, 'name', '<unknown>')
    parameters = extract_node_text(method_declaration_node, 'parameters', '()')

    return f'{method_name}{parameters}'

def get_method_body(method_declaration_node):
    return method_declaration_node.text.decode('utf-8')


def parse_file(content): 
    root_node = None
    if (content is not None) and (len(content) != 0):
        tree = parser.parse(bytes(content, "utf8"))
        root_node = tree.root_node

    return root_node
    
    