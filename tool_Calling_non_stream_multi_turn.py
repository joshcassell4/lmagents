import openai
import asyncio
import json
import re
import os

# Configure OpenAI client for LMStudio
client = openai.OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio"
)

# Tool definitions
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City and country, e.g. 'Paris, France'"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit"
                    }
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories in a specified path",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path to list files from (defaults to current directory if not specified)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_file",
            "description": "Save content to a file with specified filename and extension",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Name of the file (without extension)"
                    },
                    "extension": {
                        "type": "string",
                        "description": "File extension (e.g., 'txt', 'py', 'json', 'md')"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file"
                    }
                },
                "required": ["filename", "extension", "content"]
            }
        }
    }
]

def parse_xml_parameters(xml_string: str) -> dict:
    """Parse XML-style function parameters"""
    params = {}
    pattern = r'<parameter=([^>]+)>(.*?)</parameter>'
    matches = re.findall(pattern, xml_string, re.DOTALL)
    for param_name, param_value in matches:
        params[param_name] = param_value.strip()
    return params

def execute_function(function_name: str, arguments: dict) -> str:
    """
    Execute a function call and return the result"""
    print("Executing function: ", function_name)
    print("Arguments: ", arguments)
    if function_name == "get_weather":
        location = arguments.get("location", "Unknown Location")
        unit = arguments.get("unit", "fahrenheit")
        temp = "22°C" if unit == "celsius" else "72°F"
        return f"Weather in {location}: Clear skies, {temp}, light breeze"
    elif function_name == "list_files":
        path = arguments.get("path", ".")
        try:
            if not os.path.exists(path):
                return f"Error: Path '{path}' does not exist"
            if not os.path.isdir(path):
                return f"Error: '{path}' is not a directory"
            files = os.listdir(path)
            result = f"Contents of '{path}':\n" + "\n".join(files)
            return result
        except Exception as e:
            return f"Error: {str(e)}"
    elif function_name == "save_file":
        filename = arguments.get("filename", "")
        extension = arguments.get("extension", "")
        content = arguments.get("content", "")
        full_filename = f"{filename}.{extension}"
        try:
            with open(full_filename, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully saved '{full_filename}'"
        except Exception as e:
            return f"Error saving file: {str(e)}"
    return f"Unknown function: {function_name}"

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

async def handle_turn(messages, model, turn_number, user_message):
    """Handle a single turn in the conversation"""
    print(f"\n{'='*60}")
    print(f"Turn {turn_number}")
    print(f"{'='*60}")
    print(f"👤 User: {user_message}")
    
    # Add user message to conversation
    messages.append({"role": "user", "content": user_message})
    
    # Get response from model
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        temperature=0.3
    )

    # Handle both dict and object response formats
    message = response.choices[0].message
    if hasattr(message, 'content'):
        ai_content = message.content or ''
    else:
        ai_content = message.get('content', '') if isinstance(message, dict) else ''
    
    print(f"🤖 Assistant: {ai_content}")
    
    # Debug: Print response structure if content is empty
    if not ai_content:
        print(f"[DEBUG] Empty content. Message structure: {message}")
        print(f"[DEBUG] Full response: {response}")
    
    # Check for both standard OpenAI tool calls and XML tool calls
    all_tool_calls = []
    
    # Handle standard OpenAI tool calls (from message.tool_calls)
    if hasattr(message, 'tool_calls') and message.tool_calls:
        for tool_call in message.tool_calls:
            try:
                # Parse JSON arguments if they exist
                args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
            except json.JSONDecodeError:
                # Fallback to XML parsing if JSON fails
                args = parse_xml_parameters(tool_call.function.arguments) if tool_call.function.arguments else {}
            
            all_tool_calls.append({
                'name': tool_call.function.name,
                'arguments': args,
                'raw_args': tool_call.function.arguments
            })
    
    # Check for XML tool calls in the content (fallback)
    elif ai_content and contains_xml_tool_call(ai_content):
        xml_tool_calls = parse_xml_tool_calls_from_content(ai_content)
        for xml_call in xml_tool_calls:
            all_tool_calls.append({
                'name': xml_call['name'],
                'arguments': xml_call['arguments'],
                'raw_args': str(xml_call['arguments'])
            })
    
    assistant_response = ai_content or "[Tool call completed]"
    
    if all_tool_calls:
        print(f"\n🔧 Tool calls detected: {len(all_tool_calls)}")
        print()
        
        tool_results = []
        for tool_call in all_tool_calls:
            func_name = tool_call['name']
            args = tool_call['arguments']
            raw_args = tool_call.get('raw_args', args)
            
            print(f"📞 Function: {func_name}")
            print(f"   Raw arguments: {raw_args}")
            print(f"   Parsed arguments: {args}")
            
            result = execute_function(func_name, args)
            tool_results.append(result)
            print(f"   ✅ Result: {result}")
            print()
        
        # Create assistant response with tool results
        if tool_results:
            if len(tool_results) == 1 and "Weather in" in tool_results[0]:
                assistant_response = f"I called the weather function and got: {tool_results[0]}"
            elif len(tool_results) == 1 and ("Contents of" in tool_results[0] or "Error" in tool_results[0]):
                assistant_response = f"I listed the files and found: {tool_results[0]}"
            elif len(tool_results) == 1 and ("Successfully saved" in tool_results[0] or "Error" in tool_results[0]):
                assistant_response = f"I saved the file: {tool_results[0]}"
            else:
                assistant_response = f"I called the functions and got: {', '.join(tool_results)}"
    
    # Add assistant response to conversation
    messages.append({"role": "assistant", "content": assistant_response})
    print(assistant_response)
    return messages

async def demo_non_stream_multi_turn_conversation():
    """Demonstrate multi-turn conversation without streaming"""
    print("=" * 60)
    print("🔧 NON-STREAMING MULTI-TURN TOOL CALLING DEMO")
    print("=" * 60)
    
    try:
        model = client.models.list().data[0].id
        print(f"🤖 Model: {model}")
        
        # Start with system message
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Use available tools when appropriate."}
        ]

        # Prompts for the conversation
        prompts = [
            "save a python file named fibo containing a function to calculate Fibonacci numbers.",
            "List the files in the current directory.",
            "What is the weather in Paris?",
            "Tell me something interesting about Python programming."
        ]

        prompt = input("What is your prompt?")

        # Turn 1: Save a file
        messages = await handle_turn(messages, model, 1, prompt)
        
        prompt = input("What is your prompt?")

        # Turn 2: List files
        messages = await handle_turn(messages, model, 2, prompt)
        
        prompt = input("What is your prompt?")

        # Turn 3: Get weather
        messages = await handle_turn(messages, model, 3, prompt)

        prompt = input("What is your prompt?")
        # Turn 4: Regular conversation
        messages = await handle_turn(messages, model, 4, prompt)
        
        print("\n" + "="*60)
        print("✅ Multi-turn conversation completed!")
        print("="*60)
        print("\nFinal conversation history:")
        for i, msg in enumerate(messages):
            role = msg['role'].capitalize()
            content = msg['content']#[:100] + "..." if len(msg['content']) > 100 else msg['content']
            print(f"{i+1}. {role}: {content}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(demo_non_stream_multi_turn_conversation())

