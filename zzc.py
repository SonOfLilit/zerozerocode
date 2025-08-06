#!/usr/bin/env python3
"""
Simple Python script to interact with Inception Labs Mercury LLM
with bash session tool support in Docker.
"""

import json
import os
from pathlib import Path
import time
import uuid
import subprocess
import requests
from typing import Dict, List, Optional, Any
import dotenv
import logging

dotenv.load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

ISSUE = """\
Hey there, hope you're doing well. I've noticed a strange issue which seems to occur in certain circumstances. The library switches my Calibri font in the following spreadsheet to Arial upon loading and saving the file. I created the file in ONLYOFFICE.

Here's the workbook: fonts.xlsx

And the code used to round-trip:

fn main() {
    let book = umya_spreadsheet::reader::xlsx::read("fonts.xlsx").unwrap();
    umya_spreadsheet::writer::xlsx::write(&book, "output.xlsx").unwrap();
}
And the output file: output.xlsx

As you'll see when opening it, the font has been changed to Arial instead of being retained as Calibri.

Cheers
Fotis
"""
PROMPT = Path("prompt.txt").read_text().format(issue=ISSUE)


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

            # Start bash session in Docker
            cmd = ["docker", "exec", "-i", self.container_name, "bash"]

            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            self.sessions[session_id] = {"process": process, "prompt_uuid": prompt_uuid}
            test_response = self.send_command(session_id, "echo hello")
            if test_response != "hello":
                raise RuntimeError(f"Error starting session: {test_response}")

            return f"Started bash session {session_id}"

        except Exception as e:
            return f"Error starting bash session {session_id}: {str(e)}"

    def send_command(self, session_id: int, command: str) -> str:
        """Send command to bash session and return output."""
        if session_id not in self.sessions:
            self.start_session(session_id)

        try:
            session = self.sessions[session_id]
            process = session["process"]
            prompt_uuid = session["prompt_uuid"]

            # Send command followed by echo of prompt UUID to detect completion
            full_command = f"{command};echo EXIT_CODE_{prompt_uuid}:$?\n"
            process.stdin.write(full_command)
            process.stdin.flush()

            # Read output until we see our completion marker
            output_lines = []
            while True:
                line = process.stdout.readline()
                print(repr(line))
                if not line:
                    time.sleep(0.1)
                    continue

                output_lines.append(line)

                # Check if we've reached our completion marker
                if line.startswith(f"EXIT_CODE_{prompt_uuid}"):
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

    def send_prompt(
        self, messages: List[Dict[str, str]], tools: Optional[List[Dict]] = None
    ) -> Dict:
        """Send prompt to Mercury LLM and return response."""
        payload = {
            "messages": messages,
            "model": "mercury-coder",  # Adjust model name as needed
            "temperature": 0.0,
            "max_tokens": 2000,
        }

        if tools:
            payload["tools"] = tools

        response = self.session.post(
            f"{self.api_url}/chat/completions", json=payload, timeout=60
        )
        response.raise_for_status()
        return response.json()


def define_tools() -> List[Dict]:
    """Define available tools for the LLM."""
    return [
        {
            "type": "function",
            "function": {
                "name": "run",
                "description": "Send a command to an existing bash session and return the output",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer",
                            "description": "bash session to use (if it doesn't exist, it will be created)",
                        },
                        "command": {
                            "type": "string",
                            "description": "command to execute",
                        },
                    },
                    "required": ["id", "command"],
                },
            },
        },
    ]


def execute_tool_call(tool_call: Dict, bash_manager: BashSessionManager) -> str:
    """Execute a tool call and return the result."""
    function_name = tool_call["function"]["name"]
    arguments = json.loads(tool_call["function"]["arguments"])

    if function_name == "run":
        id = arguments["id"]
        command = arguments["command"]
        return bash_manager.send_command(id, command)

    else:
        return f"Unknown tool: {function_name}"


def main():
    """Main interaction loop."""
    # Configuration - adjust these as needed
    MERCURY_API_URL = "https://api.inceptionlabs.ai/v1"  # Adjust URL
    MERCURY_API_KEY = os.environ["MERCURY_API_KEY"]  # Add your API key if needed

    # Initialize components
    llm_client = MercuryLLMClient(MERCURY_API_URL, MERCURY_API_KEY)
    bash_manager = BashSessionManager()
    tools = define_tools()

    # Initialize conversation
    messages = [{"role": "system", "content": PROMPT}]
    first_new_message = 0

    try:
        while True:
            print(
                f"\nSending to Mercury LLM...\n{json.dumps(messages[first_new_message:], indent=2)}"
            )
            first_new_message = len(messages)
            # Send to LLM
            response = llm_client.send_prompt(messages, tools)

            # Get assistant message
            assistant_message = response["choices"][0]["message"]
            print(
                f"\nAssistant: {assistant_message.get('content', '')}{assistant_message.get('tool_calls', '')}"
            )
            input()

            # Add assistant message to conversation
            messages.append(assistant_message)

            # Check for tool calls
            tool_calls = assistant_message.get("tool_calls", [])
            for tool_call in tool_calls:
                tool_name = tool_call["function"]["name"]
                print(f"  Running {tool_name}...\n{tool_call}")

                # Execute tool
                result = execute_tool_call(tool_call, bash_manager)
                print(f"  Result: {result[:200]}{'...' if len(result) > 200 else ''}")

                # Add tool result to conversation
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": result,
                    }
                )
    finally:
        bash_manager.cleanup()


if __name__ == "__main__":
    main()
