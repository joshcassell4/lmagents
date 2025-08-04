from pathlib import Path
import json
import os

def get_weather(arguments):
    if not "location" in arguments and not "unit" in arguments:
        print("Missing required arguments")
        return
    location = arguments.get("location")
    unit = arguments.get("unit")

    print(f"Fetching weather for {location}...")

    temp = "22°C" if unit == "celsius" else "72°F"
    return f"Weather in {location}: Clear skies, {temp}, light breeze"

def list_files(arguments):  
    path = arguments.get("path", ".")
    if path == " " or path == "":
        path = "."
    if not os.path.exists(path):
        return f"Error: Path '{path}' does not exist"
    if not os.path.isdir(path):
        return f"Error: '{path}' is not a directory"
    files = os.listdir(path)
    result = f"Contents of '{path}':\n" + "\n".join(files)
    return result

def save_file(arguments):
    if not "filename" in arguments and not "extension" in arguments and not "content" in arguments:
        print("Missing required arguments")
        return
    filename = arguments.get("filename")
    extension = arguments.get("extension")
    content = arguments.get("content")

    full_filename = f"{filename}.{extension}"
    try:
        with open(full_filename, 'w', encoding='utf-8') as f:
            f.write(content)
        result = f"Successfully saved '{full_filename}'"
    except Exception as e:
        result = f"Error saving file: {str(e)}"
    return result

def read_file(arguments):
    if not "filename" in arguments and not "extension" in arguments:
        print("Missing required arguments")
        return
    filename = arguments.get("filename")
    extension = arguments.get("extension")

    full_filename = f"{filename}.{extension}"
    try:
        with open(full_filename, 'r', encoding='utf-8') as f:
            content = f.read()
        result = f"Successfully read '{full_filename}':\n{content}"
    except FileNotFoundError:
        result = f"Error: File '{full_filename}' not found"
    except Exception as e:
        result = f"Error reading file: {str(e)}"
    return result

def get_tool_funcs():
    TOOLS_funcs = {
        "get_weather": get_weather,
        "list_files": list_files,
        "save_file": save_file,
        "read_file": read_file
    }
    return TOOLS_funcs

def get_tools(path="tools.json"):
    file_path = Path(path)
    TOOLS = json.loads(file_path.read_text(encoding='utf-8'))        
    return TOOLS