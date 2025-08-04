# LM Agents - Experimental Agent Framework

An experimental agent framework built with LM Studio for parallel multi-agent conversations with tool calling capabilities.

## Overview

This project implements a synchronous agent framework that can run multiple AI agents in parallel using thread pools. Each agent can perform tool calls and engage in multi-turn conversations until completion.

## Features

- **Multi-Agent Parallel Execution**: Run multiple agents simultaneously using ThreadPoolExecutor
- **Tool Calling Support**: Agents can call various tools including file operations, weather data, and more
- **Multi-turn Conversations**: Agents continue calling the LLM after tool calls until regular content is received
- **XML Tool Call Support**: Fallback support for XML-style tool calls
- **Thread-Safe Design**: Each agent runs in its own thread with isolated conversation history

## Architecture

### Core Components

- **Agent Class**: Main agent implementation with conversation management and tool calling
- **Tools System**: Modular tool definitions in JSON and Python function implementations
- **Thread Pool Executor**: Parallel execution of multiple agents
- **XML Utils**: Support for XML-style tool call parsing

### File Structure

```
lmagents/
├── agent.py          # Main Agent class implementation
├── tools.py          # Tool function implementations
├── tools.json        # Tool definitions in JSON format
├── xml_utils.py      # XML tool call parsing utilities
├── main.py           # Multi-agent parallel execution demo
└── README.md         # This file
```

## Tools Available

### File Operations
- **list_files**: List files and directories in a specified path
- **save_file**: Save content to a file with specified filename and extension
- **read_file**: Read content from a file with specified filename and extension

### External Data
- **get_weather**: Get current weather for a location (simulated)

## Usage

### Basic Agent Usage

```python
from agent import Agent
from tools import get_tools, get_tool_funcs
import openai

# Initialize tools
tool_funcs = get_tool_funcs()
TOOLS = get_tools()

# Create client
client = openai.OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio"
)

# Get model
model = client.models.list().data[0].id

# Create agent
agent = Agent(
    messages=[],
    tools=TOOLS,
    tool_funcs=tool_funcs,
    model=model,
    temperature=0.3,
    client=client
)

# Run agent
response = agent.run("What is the weather in Paris?")
print(response)
```

### Parallel Multi-Agent Execution

```python
import concurrent.futures
from main import run_agent_task

# Define agent configurations
agent_configs = [
    (1, "What is the weather in Tokyo?", "Weather assistant"),
    (2, "List files in current directory", "File assistant"),
    (3, "Save a file named 'test' with content 'Hello World'", "File assistant")
]

# Run agents in parallel
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    future_to_agent = {
        executor.submit(run_agent_task, config): config[0] 
        for config in agent_configs
    }
    
    for future in concurrent.futures.as_completed(future_to_agent):
        agent_id, result = future.result()
        print(f"Agent {agent_id}: {result}")
```

## Setup

### Prerequisites

1. **LM Studio**: Download and install [LM Studio](https://lmstudio.ai/)
2. **Python Dependencies**:
   ```bash
   pip install openai
   ```

### Configuration

1. **Start LM Studio**: Launch LM Studio and load your preferred model
2. **Configure API**: Ensure LM Studio is running on `http://localhost:1234/v1`
3. **Run the Demo**:
   ```bash
   python main.py
   ```

## Agent Behavior

### Multi-turn Tool Calling

Agents follow this pattern:
1. Receive user message
2. Call LLM with conversation context
3. If tool calls are detected:
   - Execute tools
   - Add tool results to conversation
   - Continue loop
4. If no tool calls: return final response

### Tool Execution Flow

```
User Message → LLM Response → Tool Calls? → Execute Tools → Add Results → Continue Loop
                                                      ↓
                                              No Tools → Return Response
```

## Experimental Features

### XML Tool Call Support

The framework includes fallback support for XML-style tool calls:
```xml
<function=get_weather>
<parameter=location>Paris, France</parameter>
<parameter=unit>celsius</parameter>
</function>
```

### Thread-Safe Agent IDs

Each agent gets a unique UUID for logging and debugging:
```python
agent_id = uuid.uuid4()  # Unique identifier for each agent
```

## Performance

- **Parallel Execution**: Up to 10 agents can run simultaneously
- **Thread Pool**: Configurable worker threads (default: 10)
- **Isolated Conversations**: Each agent maintains its own conversation history

## Limitations

- **Experimental**: This is a research/experimental project
- **LM Studio Dependency**: Requires LM Studio running locally
- **Synchronous Tools**: All tool functions are synchronous
- **Local Only**: Designed for local development and testing

## Contributing

This is an experimental project. Feel free to:
- Add new tools to `tools.py` and `tools.json`
- Modify agent behavior in `agent.py`
- Extend the parallel execution capabilities
- Add new tool call formats

## License

This is an experimental project. Use at your own risk.

## Acknowledgments

- Built with [LM Studio](https://lmstudio.ai/) for local LLM inference
- Uses OpenAI-compatible API for tool calling
- Inspired by multi-agent conversation frameworks
