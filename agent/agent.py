import re
import json
import datetime
import shutil
import time
from colorama import Fore, Back, Style

from utils.formatter import Formatter
from tools.terminal import Terminal_for_agent
from tools.Tools import Tools

from llm.models import AnthropicAgent, OpenAIAgent


class Agent:
    def __init__(self, tools=None, llm=None, provider="anthropic", model=None):
        """
        Initialize the Agent with tools and LLM provider.

        Parameters:
        - tools: The tools manager instance
        - llm: The language model instance (Anthropic or OpenAI)
        - provider: The provider name ("anthropic" or "openai")
        - model: The specific model to use (defaults to provider's default model)
        """
        self.tools = tools

        self.provider = provider
        self.client = llm.client if llm else None
        self.model = model or (llm.default_model if llm else None)

        self.formatter = Formatter()

        self.terminal = tools.terminal if tools else None

        self.history = []
        self.response_errors = []

        self.debug = False

        print(
            f"{self.formatter.colors['info']}Using {self.provider.upper()} with model: {self.model}")

    def timestamp(self):
        """Get current timestamp in a readable format."""
        return datetime.datetime.now().strftime("%H:%M:%S")

    def print_debug(self, message):
        """Print a debug message if debug mode is on."""
        if self.debug:
            self.formatter.print_debug(message, self.timestamp())

    def get_available_tools(self):
        """Return the list of available tools with their descriptions."""
        return self.tools.get_available_tools() if self.tools else {}

    def format_function_call(self, function_name, parameters):
        """Format a function call for display and history."""
        if not parameters:
            return function_name + "()"

        params_str = []
        for key, value in parameters.items():
            if isinstance(value, str):
                if len(value) > 50:
                    value_str = f'"{value[:47]}..."'
                else:
                    value_str = f'"{value}"'
            else:
                value_str = str(value)
            params_str.append(f"{key}={value_str}")

        return f"{function_name}({', '.join(params_str)})"

    def run_function(self, function_name, parameters):
        """Run a function based on its name and parameters."""
        if function_name in ["write_file", "append_to_file", "run_command", "start_background_process",
                             "list_background_processes", "get_process_output", "stop_background_process",
                             "send_input_to_process", "get_files_and_dirs_at_path", "get_file_contents",
                             "get_file_contents_of_type", "get_all_functions_and_class_names"]:
            function_name = f"terminal.{function_name}"
            print(
                f"{self.formatter.colors['warning']}⚠️  Auto-corrected function name to {function_name}")

        if function_name.startswith("terminal."):
            method_name = function_name.split(".", 1)[1]

            if method_name in ["write_file", "append_to_file"] and "content" in parameters:
                content = parameters.get("content", "")
                content_size = len(content)
                path = parameters.get("path", "")

                print(
                    f"{self.formatter.colors['progress']}📂 Writing file: {path} ({content_size} bytes)")

                if content_size > 50000:
                    print(
                        f"{self.formatter.colors['progress']}⚠️  Large file operation - this may take a moment...")

                    if content_size > 100000:
                        return self.chunk_large_file_operations(function_name, parameters)

            return self.tools.run_tool(function_name, parameters)
        else:
            return {"error": f"Unknown function: {function_name}"}

    def extract_response_from_tags(self, text):
        """
        Extract the agent's response from XML-style tags instead of JSON.
        This is more resilient to special characters and escape sequences.
        """
        result = {}

        thought_match = re.search(r'<thought>(.*?)</thought>', text, re.DOTALL)
        if thought_match:
            result['thought'] = thought_match.group(1).strip()

        function_match = re.search(
            r'<function>(.*?)</function>', text, re.DOTALL)
        if function_match:
            function_value = function_match.group(1).strip()
            result['function'] = function_value if function_value.lower(
            ) != "null" else None

        task_complete_match = re.search(
            r'<task_complete>(.*?)</task_complete>', text, re.DOTALL)
        if task_complete_match:
            task_complete_str = task_complete_match.group(1).strip().lower()
            result['task_complete'] = task_complete_str == "true"

        parameters_match = re.search(
            r'<parameters>(.*?)</parameters>', text, re.DOTALL)
        if parameters_match and result.get('function'):
            parameters_text = parameters_match.group(1).strip()

            if "write_file" in result.get('function', '') or "append_to_file" in result.get('function', ''):
                path_match = re.search(
                    r'path:\s*(.*?)(?:\n|$)', parameters_text)
                path = path_match.group(1).strip(
                ) if path_match else "unknown_path.txt"

                content_match = re.search(
                    r'content:\s*(.*?)(?=\n\w+:|$)', parameters_text, re.DOTALL)
                content = content_match.group(
                    1).strip() if content_match else ""

                if content.startswith('\n'):
                    content = content[1:]

                result['parameters'] = {"path": path, "content": content}
            else:
                parameters = {}
                param_lines = parameters_text.split('\n')
                for line in param_lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        parameters[key.strip()] = value.strip()
                result['parameters'] = parameters
        else:
            result['parameters'] = {}

        if 'thought' not in result:
            result['thought'] = "No thought provided"

        if 'task_complete' not in result:
            result['task_complete'] = False

        return result, "Successfully extracted response from tags"

    def execute_step(self, task, step_num=1, max_steps=20, max_retries=2):
        """Execute a single step of the task with retry mechanism for API errors."""
        tools_description = json.dumps(self.get_available_tools(), indent=2)

        history_text = ""
        for i, (function_name, result) in enumerate(self.history, 1):
            if isinstance(result, dict) and isinstance(result.get("stdout"), str) and len(result["stdout"]) > 500:
                result = result.copy()
                result["stdout"] = result["stdout"][:500] + \
                    "... [output truncated]"
            if isinstance(result, dict) and isinstance(result.get("stderr"), str) and len(result["stderr"]) > 500:
                result = result.copy()
                result["stderr"] = result["stderr"][:500] + \
                    "... [output truncated]"

            history_text += f"\nStep {i}: {function_name}, Result: {json.dumps(result, indent=2) if isinstance(result, dict) else str(result)}"

        system_message = f"""
            You are an AI agent that solves tasks step by step. You have access to the following tools:

            {tools_description}

            For each step, you should analyze the task and decide on the next action.
            Your response must use the following XML-style tag format:

            <thought>
            Your reasoning for this step. This can include multiple lines and special characters.
            </thought>

            <function>
            function_name or null if the task is complete
            </function>

            <parameters>
            path: example/path.txt
            content: the content to write
            # For other functions, include appropriate parameters as key-value pairs
            </parameters>

            <task_complete>
            true or false
            </task_complete>

            IMPORTANT: 
            1. The content for file operations should be placed inside the <parameters> tags after "content:"
            2. You can include any special characters, quotes, or code in the content without escaping
            3. When writing code, include the full code exactly as it should be written to the file
            4. No need to escape special characters in any field

            IMPORTANT FILE HANDLING GUIDELINES:
            1. When analyzing code, use terminal.get_all_functions_and_class_names first to understand structure
            2. Only use terminal.get_file_contents for small files or when you need to see implementation details
            3. Reading large files consumes many tokens and may impact performance
            4. For large codebases, analyze files incrementally rather than all at once

            When you need to run programs that don't exit immediately (like web servers or interactive programs):
            1. Use terminal.start_background_process instead of terminal.run_command
            2. Use the returned process_id to check on its progress with terminal.get_process_output
            3. For interactive programs, use terminal.send_input_to_process to provide input
            4. When done, use terminal.stop_background_process to clean up

            IMPORTANT: If working with large files, try to make smaller, incremental changes rather than rewriting entire files at once.
            
            If task_complete is true, no function will be called and the task will be considered done.
            """

        user_message = f"""
Task: {task}

Current step: {step_num}
Current working directory: {self.terminal.cwd}
{history_text}

Decide on the next step, or mark the task as complete.
"""

        timestamp = self.timestamp()
        context_info = f"{self.formatter.colors['time']} {timestamp} {Style.RESET_ALL} {self.formatter.colors['context']}Step {step_num}/{max_steps} - Working dir: {self.terminal.cwd}{Style.RESET_ALL}"
        print(f"\n{context_info}")

        retry_count = 0
        while retry_count <= max_retries:
            try:
                if retry_count > 0:
                    print(
                        f"{self.formatter.colors['retry']}♻️  RETRY ATTEMPT {retry_count}/{max_retries} - Adjusting request...")

                # Handle different API calls based on provider
                if self.provider == "anthropic":
                    response = self.client.messages.create(
                        model=self.model,
                        max_tokens=4000,
                        system=system_message,
                        messages=[{"role": "user", "content": user_message}]
                    )
                    content = response.content[0].text if hasattr(
                        response, 'content') else ""

                elif self.provider == "openai":
                    response = self.client.chat.completions.create(
                        model=self.model,
                        max_completion_tokens=4000,
                        messages=[
                            {"role": "system", "content": system_message},
                            {"role": "user", "content": user_message}
                        ]
                    )
                    content = response.choices[0].message.content

                decision, diagnostic = self.extract_response_from_tags(content)

                if not decision or (not decision.get("function") and not decision.get("task_complete", False)):
                    error_message = f"Failed to extract valid response structure: {diagnostic}"

                    if retry_count < max_retries:
                        retry_count += 1
                        print(
                            f"{self.formatter.colors['error']}⚠️  {error_message}")
                        print(
                            f"{self.formatter.colors['retry']}♻️  Retry attempt {retry_count}/{max_retries}...")
                        continue
                    else:
                        self.formatter.print_error_box(
                            "RESPONSE PARSING ERROR",
                            f"Failed to extract valid response structure after {max_retries} retries: {diagnostic}",
                            content
                        )
                        return False, "", None, {"error": error_message}

                if decision.get("function") and not decision.get("task_complete", False):
                    function_name = decision["function"]
                    parameters = decision.get("parameters", {})

                    if function_name in ["terminal.write_file", "terminal.append_to_file"] and "content" in parameters:
                        content_size = len(parameters["content"])
                        if content_size > 100000:
                            self.print_debug(
                                f"Large file operation detected: {content_size} bytes")

                    formatted_call = self.format_function_call(
                        function_name, parameters)

                    result = self.run_function(function_name, parameters)

                    self.history.append((formatted_call, result))

                    return False, decision.get("thought", ""), formatted_call, result

                if decision.get("task_complete", False):
                    processes = self.terminal.list_background_processes()
                    for process_id in processes:
                        self.terminal.stop_background_process(process_id)

                    return True, decision.get("thought", ""), None, None

                return False, decision.get("thought", ""), None, {"error": "No function specified but task not marked as complete"}

            except Exception as e:
                error_message = f"Error processing step: {str(e)}"

                if retry_count < max_retries:
                    retry_count += 1
                    print(
                        f"{self.formatter.colors['error']}⚠️  {error_message}")
                    print(
                        f"{self.formatter.colors['retry']}♻️  Retry attempt {retry_count}/{max_retries}...")
                    continue
                else:
                    self.formatter.print_error_box(
                        "EXECUTION ERROR",
                        f"Failed after {max_retries} retries: {str(e)}",
                        content if 'content' in locals() else None
                    )
                    self.response_errors.append({
                        "step": step_num,
                        "error": str(e),
                        "response": content if 'content' in locals() else None
                    })
                    return False, "", None, {"error": error_message}

    def chunk_large_file_operations(self, function_name, parameters, chunk_size=50000):
        """Split large file writing operations into smaller chunks"""
        if function_name in ["terminal.write_file", "terminal.append_to_file"] and "content" in parameters:
            content = parameters.get("content", "")
            path = parameters.get("path", "")

            if len(content) > chunk_size:
                self.print_debug(
                    f"Chunking large file operation ({len(content)} bytes) into smaller pieces")

                if function_name == "terminal.write_file":
                    self.terminal.write_file(path, "")

                content_chunks = [content[i:i + chunk_size]
                                  for i in range(0, len(content), chunk_size)]

                for i, chunk in enumerate(content_chunks):
                    print(
                        f"{self.formatter.colors['progress']}📝 Writing chunk {i + 1}/{len(content_chunks)} ({len(chunk)} bytes)")
                    result = self.terminal.append_to_file(path, chunk)
                    if "error" in result:
                        return result

                return {"success": True, "message": f"File {path} written successfully in {len(content_chunks)} chunks"}

        return self.run_function(function_name, parameters)

    def solve_task(self, task, max_steps=20):
        """Solve a task step by step, up to a maximum number of steps."""
        print(
            f"\n{self.formatter.colors['task']}🤖 AGENT SESSION STARTED {self.timestamp()}")
        self.formatter.print_header(f"TASK: {task}", level=1)

        step = 1

        try:
            while step <= max_steps:
                progress = f"[{step}/{max_steps}]"
                self.formatter.print_header(f"STEP {step} {progress}", level=2)

                done, thought, function_call, result = self.execute_step(
                    task, step, max_steps)

                if thought:
                    print(f"\n{self.formatter.colors['thought']}🧠 THOUGHT:{Style.RESET_ALL}")
                    for paragraph in thought.split('\n'):
                        print(f"{self.formatter.colors['thought']}   {paragraph}")

                if function_call:
                    self.formatter.print_action(function_call)
                    self.formatter.print_result(result)

                if done:
                    self.formatter.print_separator('double')
                    elapsed = datetime.datetime.now() - self.start_time
                    print(
                        f"{self.formatter.colors['success']}✅ TASK COMPLETED IN {step} STEPS")
                    print(
                        f"{self.formatter.colors['success']}⏱️  Total time: {elapsed.seconds}.{elapsed.microseconds // 1000:03d} seconds")

                    print(
                        f"\n{self.formatter.colors['task']}🎯 FINAL THOUGHT:{Style.RESET_ALL}")
                    print(f"{self.formatter.colors['thought']}   {thought}")

                    if self.response_errors:
                        print(
                            f"\n{self.formatter.colors['warning']}⚠️  There were {len(self.response_errors)} errors during execution")
                        print(
                            f"{self.formatter.colors['warning']}    Consider reviewing the error logs for more information")

                    self.formatter.print_separator('double')
                    return True

                step += 1

            self.formatter.print_separator('double')
            print(
                f"{self.formatter.colors['error']}⚠️  REACHED MAXIMUM STEPS ({max_steps}) WITHOUT COMPLETING THE TASK")
            print(
                f"{self.formatter.colors['warning']}   Consider increasing max_steps or breaking down the task")
            self.formatter.print_separator('double')
            return False

        finally:
            processes = self.terminal.list_background_processes()
            for process_id in processes:
                self.terminal.stop_background_process(process_id)
