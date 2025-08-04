import re

def parse_xml_parameters(xml_string: str) -> dict:
    """Parse XML-style function parameters"""
    params = {}
    pattern = r'<parameter=([^>]+)>(.*?)</parameter>'
    matches = re.findall(pattern, xml_string, re.DOTALL)
    for param_name, param_value in matches:
        params[param_name] = param_value.strip()
    return params

def parse_xml_tool_calls_from_content(content: str) -> list:
    """Parse XML tool calls from content"""
    tool_calls = []
    # Pattern to match <function=name>...</function>
    function_pattern = r'<function=([^>]+)>(.*?)</function>'
    function_matches = re.findall(function_pattern, content, re.DOTALL)
    for func_name, func_content in function_matches:
        # Parse parameters within this function call
        params = parse_xml_parameters(func_content)
        tool_calls.append({
            'name': func_name,
            'arguments': params
        })
    return tool_calls

def contains_xml_tool_call(content: str) -> bool:
    """Check if content contains XML tool call format"""
    return '<function=' in content and '</function>' in content