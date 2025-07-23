#!/usr/bin/env python3
"""
Simple Python script to interact with Inception Labs Mercury LLM
with bash session tool support in Docker.
"""

import json
import uuid
import time
import subprocess
import requests
import re
from typing import Dict, List, Optional, Any


class BashSessionManager:
    """Manages bash sessions running in Docker container."""
    
    def __init__(self, container_name: str = "zerozerocode"):
        self.container_name = container_name
        self.sessions: Dict[int, Dict[str, Any]] = {}
        
    def start_session(self, session_id: int) -> str:
        """Start a new bash session with given index."""
        try:
            # Generate unique prompt UUID for this session
            prompt_uuid = str(uuid.uuid4())
            
            # Start bash session in Docker with custom prompt
            cmd = [
                "docker", "exec", "-it", self.container_name,
                "bash", "-c", f'export PROMPT="{prompt_uuid}"; bash'
            ]
            
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            self.sessions[session_id] = {
                "process": process,
                "prompt_uuid": prompt_uuid
            }
            
            return f"Started bash session {session_id} with prompt UUID: {prompt_uuid}"
            
        except Exception as e:
            return f"Error starting bash session {session_id}: {str(e)}"
    
    def send_command(self, session_id: int, command: str) -> str:
        """Send command to bash session and return output."""
        if session_id not in self.sessions:
            return f"Error: Bash session {session_id} not found. Start it first."
        
        try:
            session = self.sessions[session_id]
            process = session["process"]
            prompt_uuid = session["prompt_uuid"]
            
            # Send command followed by echo of prompt UUID to detect completion
            full_command = f"{command}\necho 'COMMAND_DONE_{prompt_uuid}'\n"
            process.stdin.write(full_command)
            process.stdin.flush()
            
            # Read output until we see our completion marker
            output_lines = []
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                    
                output_lines.append(line)
                
                # Check if we've reached our completion marker
                if f"COMMAND_DONE_{prompt_uuid}" in line:
                    break
                    
                # Timeout safety
                if len(output_lines) > 1000:
                    output_lines.append("... (output truncated - too long)")
                    break
            
            # Remove the completion marker line
            output = "".join(output_lines[:-1]) if output_lines else ""
            return output.strip()
            
        except Exception as e:
            return f"Error executing command in session {session_id}: {str(e)}"
    
    def cleanup(self):
        """Clean up all bash sessions."""
        for session_id, session in self.sessions.items():
            try:
                session["process"].terminate()
                session["process"].wait(timeout=5)
            except:
                session["process"].kill()


class MercuryLLMClient:
    """Client for Inception Labs Mercury LLM."""
    
    def __init__(self, api_url: str, api_key: Optional[str] = None):
        self.api_url = api_url
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
    
    def send_prompt(self, messages: List[Dict[str, str]], tools: Optional[List[Dict]] = None) -> Dict:
        """Send prompt to Mercury LLM and return response."""
        payload = {
            "messages": messages,
            "model": "mercury",  # Adjust model name as needed
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        try:
            response = self.session.post(
                f"{self.api_url}/chat/completions",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"API call failed: {str(e)}"}


def define_tools() -> List[Dict]:
    """Define available tools for the LLM."""
    return [
        {
            "type": "function",
            "function": {
                "name": "start_bash_session",
                "description": "Start a new bash session with the given index in the Docker container",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "integer",
                            "description": "Index/ID for the bash session"
                        }
                    },
                    "required": ["session_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "send_bash_command",
                "description": "Send a command to an existing bash session and return the output",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "integer",
                            "description": "Index/ID of the bash session to use"
                        },
                        "command": {
                            "type": "string",
                            "description": "Command to execute in the bash session"
                        }
                    },
                    "required": ["session_id", "command"]
                }
            }
        }
    ]


def execute_tool_call(tool_call: Dict, bash_manager: BashSessionManager) -> str:
    """Execute a tool call and return the result."""
    function_name = tool_call["function"]["name"]
    arguments = json.loads(tool_call["function"]["arguments"])
    
    if function_name == "start_bash_session":
        session_id = arguments["session_id"]
        return bash_manager.start_session(session_id)
    
    elif function_name == "send_bash_command":
        session_id = arguments["session_id"]
        command = arguments["command"]
        return bash_manager.send_command(session_id, command)
    
    else:
        return f"Unknown tool: {function_name}"


def main():
    """Main interaction loop."""
    # Configuration - adjust these as needed
    MERCURY_API_URL = "https://api.inceptionlabs.ai/v1"  # Adjust URL
    MERCURY_API_KEY = None  # Add your API key if needed
    
    # Initialize components
    llm_client = MercuryLLMClient(MERCURY_API_URL, MERCURY_API_KEY)
    bash_manager = BashSessionManager()
    tools = define_tools()
    
    # Initialize conversation
    messages = []
    
    print("Mercury LLM Tool Loop - Type 'quit' to exit")
    print("=" * 50)
    
    try:
        while True:
            # Get user input
            user_input = input("\nUser: ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            if not user_input:
                continue
            
            # Add user message
            messages.append({"role": "user", "content": user_input})
            
            # Main interaction loop
            while True:
                print("\nSending to Mercury LLM...")
                
                # Send to LLM
                response = llm_client.send_prompt(messages, tools)
                
                if "error" in response:
                    print(f"Error: {response['error']}")
                    break
                
                # Get assistant message
                assistant_message = response["choices"][0]["message"]
                print(f"\nAssistant: {assistant_message.get('content', '')}")
                
                # Add assistant message to conversation
                messages.append(assistant_message)
                
                # Check for tool calls
                tool_calls = assistant_message.get("tool_calls", [])
                if not tool_calls:
                    break  # No tools to execute, wait for next user input
                
                # Execute tool calls
                print("\nExecuting tools...")
                for tool_call in tool_calls:
                    tool_name = tool_call["function"]["name"]
                    print(f"  Running {tool_name}...")
                    
                    # Execute tool
                    result = execute_tool_call(tool_call, bash_manager)
                    print(f"  Result: {result[:200]}{'...' if len(result) > 200 else ''}")
                    
                    # Add tool result to conversation
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": result
                    })
                
                # Continue loop to send tool results back to LLM
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    
    except Exception as e:
        print(f"\nUnexpected error: {e}")
    
    finally:
        # Cleanup
        print("\nCleaning up bash sessions...")
        bash_manager.cleanup()
        print("Done!")


if __name__ == "__main__":
    main()