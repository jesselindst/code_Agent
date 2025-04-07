import os
from tools.terminal import Terminal_for_agent

class Tools:
    """
    Tools manager that provides access to all available tools.
    Additional tools can be easily added to this class.
    """
    
    def __init__(self):
        """Initialize the tools manager with available tools."""
        self.terminal = Terminal_for_agent()
        # Future tools can be added here
        # self.other_tool = OtherTool()
        
        # Dictionary of all available tools with their descriptions and functions
        self.available_tools = self._register_tools()
    
    def _register_tools(self):
        """Register all available tools with their descriptions and function handlers."""
        return {
            "terminal.run_command": {
                "description": "Run a command in the terminal with a 10-second timeout. If the command doesn't complete within the timeout, it continues running in the background, and the function returns the partial output.",
                "parameters": {"command": "string"},
                "handler": self.terminal.run_command
            },
            "terminal.start_background_process": {
                "description": "Start a long-running process in the background and return its ID for future reference. Use this for servers, continuous processes, or interactive programs.",
                "parameters": {"command": "string"},
                "handler": self.terminal.start_background_process
            },
            "terminal.list_background_processes": {
                "description": "List all background processes and their status",
                "parameters": {},
                "handler": self.terminal.list_background_processes
            },
            "terminal.get_process_output": {
                "description": "Get the current output from a background process",
                "parameters": {"process_id": "string"},
                "handler": self.terminal.get_process_output
            },
            "terminal.stop_background_process": {
                "description": "Stop a background process",
                "parameters": {"process_id": "string"},
                "handler": self.terminal.stop_background_process
            },
            "terminal.send_input_to_process": {
                "description": "Send input to a running background process (for interactive programs)",
                "parameters": {
                    "process_id": "string",
                    "input_text": "string"
                },
                "handler": self.terminal.send_input_to_process
            },
            "terminal.get_files_and_dirs_at_path": {
                "description": "Get all files and directories at a given path",
                "parameters": {"path": "string"},
                "handler": self.terminal.get_files_and_dirs_at_path
            },
            "terminal.get_functions_and_classes": {
                "description": "Extract function and class names from files with the given extension in a directory. This is more token-efficient than getting full file contents when you only need structure information.",
                "parameters": {"path": "string", "file_extension": "string"},
                "handler": self.terminal.get_functions_and_classes
            },
            "terminal.get_function_content": {
                "description": "Extract the content of a specific function from a file. This is more token-efficient than loading the entire file when you only need one function.",
                "parameters": {"path": "string", "function_name": "string"},
                "handler": self.terminal.get_function_content
            },
            "terminal.get_file_contents": {
                "description": "Get the contents of a file. WARNING: For large files, this consumes many tokens. Consider using get_functions_and_classes or get_function_content for more targeted extraction.",
                "parameters": {"path": "string"},
                "handler": self.terminal.get_file_contents
            },
            "terminal.get_file_contents_of_type": {
                "description": "Get the contents of a file of a given type. WARNING: For large files, this consumes many tokens. Consider using get_function_content for more targeted extraction.",
                "parameters": {"path": "string", "file_type": "string"},
                "handler": self.terminal.get_file_contents_of_type
            },
            "terminal.write_file": {
                "description": "Write content to a file (overwriting any existing content)",
                "parameters": {"path": "string", "content": "string"},
                "handler": self.terminal.write_file
            },
            "terminal.append_to_file": {
                "description": "Append content to an existing file",
                "parameters": {"path": "string", "content": "string"},
                "handler": self.terminal.append_to_file
            }
        }
    
    def get_available_tools(self):
        """Return the list of available tools with their descriptions."""
        tools_description = {}
        for tool_name, tool_info in self.available_tools.items():
            tools_description[tool_name] = {
                "description": tool_info["description"],
                "parameters": tool_info["parameters"]
            }
        return tools_description
    
    def run_tool(self, function_name, parameters):
        """Run a tool based on its name and parameters."""
        if "." not in function_name:
            for full_name in self.available_tools.keys():
                if full_name.endswith("." + function_name):
                    function_name = full_name
                    break
        
        if function_name in self.available_tools:
            handler = self.available_tools[function_name]["handler"]
            return handler(**parameters)
        else:
            return {"error": f"Unknown function: {function_name}"} 