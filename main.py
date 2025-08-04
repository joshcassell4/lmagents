import json
import time
import concurrent.futures
from pathlib import Path
from tools import get_tools, get_tool_funcs
import xml_utils
from agent import Agent
import openai

tool_funcs = get_tool_funcs()
TOOLS = get_tools()

def run_agent_task(agent_config):
    """
    Task function to run a single agent.
    This will be executed in a separate thread.
    """
    agent_id, message, system_message = agent_config
    
    # Create client for this thread
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
        client=client,
        system_message=system_message
    )
    
    print(f"🚀 Starting Agent {agent_id} with message: {message}")
    
    # Run the agent
    result = agent.run(message)
    
    print(f"✅ Agent {agent_id} completed")
    return agent_id, result

def main():
    print("🤖 Multi-Agent Parallel Execution Demo")
    print("=" * 50)
    
    # Define agent configurations
    agent_configs = [
        (1, "What is the weather in Tokyo?", "You are a weather assistant. Get weather information quickly."),
        (2, "What is the weather in London?", "You are a weather assistant. Get weather information quickly."),
        (3, "What is the weather in New York?", "You are a weather assistant. Get weather information quickly."),
        (4, "What is the weather in Sydney?", "You are a weather assistant. Get weather information quickly."),
        (5, "List the files in the current directory.", "You are a file assistant. Help with file operations."),
        (6, "Save a file named 'test' with content 'Hello World2'.", "You are a file assistant. Help with file operations."),
        (7, "Read the file named 'test.txt'.", "You are a file assistant. Help with file operations."),
        (8, "List the directory contents, pick a .txt file, and then read it. Don't ask for anything else.","You are a file assistant. Help with file operations.")
    ]
    
    print(f"📋 Running {len(agent_configs)} agents in parallel")
    start_time = time.time()
    
    # Use ThreadPoolExecutor to run agents in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all tasks
        future_to_agent = {
            executor.submit(run_agent_task, config): config[0] 
            for config in agent_configs
        }
        
        # Collect results as they complete
        results = {}
        for future in concurrent.futures.as_completed(future_to_agent):
            agent_id = future_to_agent[future]
            try:
                agent_id, result = future.result()
                results[agent_id] = result
                print(f"📊 Agent {agent_id} result: {result}")
            except Exception as exc:
                print(f"❌ Agent {agent_id} generated an exception: {exc}")
    
    total_time = time.time() - start_time
    
    print("\n" + "=" * 50)
    print(f"✅ All agents completed in {total_time:.2f} seconds")
    print("\n📋 Final Results:")
    for agent_id in sorted(results.keys()):
        result = results[agent_id]
        print(f"  Agent {agent_id}: {result}")
    
    print(f"\n🚀 Performance: {len(agent_configs)} agents completed in {total_time:.2f}s")

if __name__ == "__main__":
    main()
