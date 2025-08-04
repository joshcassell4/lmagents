def load_tools_from_json(path="tools.json"):
    file_path = Path(path)
    TOOLS = json.loads(file_path.read_text(encoding='utf-8'))
    return TOOLS