import openai
import json
import re
import os
from typing import List, Dict, Any, Optional
import xml_utils
import uuid

class Agent:
    """
    A synchronous agent class that can run conversations with tool calling capabilities.
    Designed to be run in parallel with other agent instances using thread pools.
    """
    
    def __init__(
        self,
        messages,
        tools,
        tool_funcs,
        model,
        temperature,
        client = None,
        system_message = "You are a helpful assistant. Use available tools when appropriate."
    ):
        """
        Initialize the agent with conversation context and configuration.
        
        Args:
            messages: List of conversation messages
            tools: List of tool definitions
            tool_funcs: Dictionary of tool functions
            model: Model name to use for completions
            temperature: Temperature for model responses
            client: OpenAI client instance (optional, will create default if not provided)
            system_message: System message to prepend to conversation
        """
        self.messages = messages.copy() if messages else []
        self.tools = tools
        self.tool_funcs = tool_funcs
        self.model = model
        self.temperature = temperature
        self.client = client or openai.OpenAI(
            base_url="http://localhost:1234/v1",
            api_key="lm-studio"
        )
        
        # Add system message if not already present
        if not self.messages or self.messages[0].get("role") != "system":
            self.messages.insert(0, {"role": "system", "content": system_message})
    
    def execute_function(self, function_name, arguments):
        if function_name in self.tool_funcs:
            result = self.tool_funcs[function_name](arguments)
        else:
            print(f"Unknown function: {function_name}")
            return "Unknown function"
        return result
    
    def run(self, user_message: str) -> str:
        """
        Run the agent with a user message and return the response.
        This method will continue calling the LLM after tool calls until regular content is received.
        
        Args:
            user_message: The user's input message
            
        Returns:
            The agent's final response after processing all tool calls
        """
        import time
        agent_id = uuid.uuid4()  # Simple agent ID for logging
        print(f"🤖 Agent {agent_id} started: {user_message}")
        
        # Add user message to conversation
        self.messages.append({"role": "user", "content": user_message})
        
        # Loop until we get a response without tool calls
        while True:
            print(f"📡 Agent {agent_id} making LLM call")
            llm_start = time.time()
            
            # Get response from model
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=self.tools,
                tool_choice="auto",
                temperature=self.temperature
            )
            
            llm_time = time.time() - llm_start
            print(f"✅ Agent {agent_id} LLM response received in {llm_time:.2f}s")

            # Handle both dict and object response formats
            message = response.choices[0].message
            if hasattr(message, 'content'):
                ai_content = message.content or ''
            else:
                ai_content = message.get('content', '') if isinstance(message, dict) else ''
            
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
                        args = xml_utils.parse_xml_parameters(tool_call.function.arguments) if tool_call.function.arguments else {}
                    
                    all_tool_calls.append({
                        'name': tool_call.function.name,
                        'arguments': args,
                        'raw_args': tool_call.function.arguments
                    })
            
            # Check for XML tool calls in the content (fallback)
            elif ai_content and xml_utils.contains_xml_tool_call(ai_content):
                xml_tool_calls = xml_utils.parse_xml_tool_calls_from_content(ai_content)
                for xml_call in xml_tool_calls:
                    all_tool_calls.append({
                        'name': xml_call['name'],
                        'arguments': xml_call['arguments'],
                        'raw_args': str(xml_call['arguments'])
                    })
            
            # If no tool calls, we're done - return the final response
            if not all_tool_calls:
                # Add the final assistant response to conversation
                final_response = ai_content or "I've completed the requested task."
                self.messages.append({"role": "assistant", "content": final_response})
                return final_response
            
            # Process tool calls
            print(f"🔧 Tool calls detected: {len(all_tool_calls)}")
            
            # Print tool call info first
            for tool_call in all_tool_calls:
                func_name = tool_call['name']
                args = tool_call['arguments']
                raw_args = tool_call.get('raw_args', args)
                
                print(f"📞 Function: {func_name}")
                print(f"   Raw arguments: {raw_args}")
                print(f"   Parsed arguments: {args}")
            
            # Execute all tool calls sequentially
            print(f"⏱️ Executing {len(all_tool_calls)} tool calls...")
            
            tool_results = []
            for tool_call in all_tool_calls:
                func_name = tool_call['name']
                args = tool_call['arguments']
                result = self.execute_function(func_name, args)
                tool_results.append(result)
                print(f"   ✅ {func_name} Result: {result}")
            
            # Create tool results message
            tool_results_content = ""
            if tool_results:
                if len(tool_results) == 1 and "Weather in" in tool_results[0]:
                    tool_results_content = f"I called the weather function and got: {tool_results[0]}"
                elif len(tool_results) == 1 and ("Contents of" in tool_results[0] or "Error" in tool_results[0]):
                    tool_results_content = f"I listed the files and found: {tool_results[0]}"
                elif len(tool_results) == 1 and ("Successfully saved" in tool_results[0] or "Error" in tool_results[0]):
                    tool_results_content = f"I saved the file: {tool_results[0]}"
                elif len(tool_results) == 1 and ("Successfully read" in tool_results[0] or "Error" in tool_results[0]):
                    tool_results_content = f"I read the file: {tool_results[0]}"
                else:
                    tool_results_content = f"I called the functions and got: {', '.join(tool_results)}"
            
            # Add the assistant's tool call message to conversation
            self.messages.append({"role": "assistant", "content": ai_content or "[Tool call made]"})
            
            # Add tool results as a user message to continue the conversation
            self.messages.append({"role": "user", "content": tool_results_content})
            
            print(f"🔄 Continuing conversation with tool results: {tool_results_content}")
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the current conversation history"""
        return self.messages.copy()
    
    def reset_conversation(self, system_message: str = "You are a helpful assistant. Use available tools when appropriate."):
        """Reset the conversation history"""
        self.messages = [{"role": "system", "content": system_message}] 