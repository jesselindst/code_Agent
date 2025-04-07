import os
import subprocess
import threading
import time
import uuid
import signal


class Terminal_for_agent:
    """A class for the agent to use the terminal"""

    def __init__(self):
        self.cwd = os.getcwd()
        self.background_processes = {}

    def run_command(self, command, timeout=10):
        """Run a command in the terminal with timeout"""
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            try:
                stdout, stderr = process.communicate(timeout=timeout)
                return {
                    "stdout": stdout,
                    "stderr": stderr,
                    "returncode": process.returncode
                }
            except subprocess.TimeoutExpired:
                return {
                    "stdout": self._read_nonblocking(process.stdout),
                    "stderr": self._read_nonblocking(process.stderr),
                    "returncode": None,
                    "status": "running",
                    "message": f"Command still running after {timeout} seconds. Continuing in background."
                }

        except Exception as e:
            return {"error": str(e)}

    def _read_nonblocking(self, pipe):
        """Read from pipe without blocking"""
        output = ""
        while True:
            import select
            r, _, _ = select.select([pipe], [], [], 0)
            if pipe not in r:
                break

            data = pipe.read(1024)
            if not data:
                break
            output += data

        return output

    def start_background_process(self, command):
        """Start a process in the background and return its ID"""
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid
            )

            process_id = str(uuid.uuid4())

            self.background_processes[process_id] = {
                "process": process,
                "command": command,
                "start_time": time.time(),
                "stdout": "",
                "stderr": ""
            }

            self._start_output_threads(process_id)

            time.sleep(0.5)

            return {
                "process_id": process_id,
                "status": "started",
                "stdout": self.background_processes[process_id]["stdout"],
                "stderr": self.background_processes[process_id]["stderr"]
            }

        except Exception as e:
            return {"error": str(e)}

    def _start_output_threads(self, process_id):
        """Start threads to collect process output"""
        process_info = self.background_processes[process_id]
        process = process_info["process"]

        def collect_output(pipe, output_type):
            while process.poll() is None:
                try:
                    line = pipe.readline()
                    if line:
                        process_info[output_type] += line
                except:
                    break

        stdout_thread = threading.Thread(
            target=collect_output,
            args=(process.stdout, "stdout"),
            daemon=True
        )
        stderr_thread = threading.Thread(
            target=collect_output,
            args=(process.stderr, "stderr"),
            daemon=True
        )

        stdout_thread.start()
        stderr_thread.start()

    def list_background_processes(self):
        """List all background processes"""
        result = {}
        for process_id, info in list(self.background_processes.items()):
            process = info["process"]

            status = "running" if process.poll() is None else "terminated"

            if status == "terminated" and process_id in self.background_processes:
                del self.background_processes[process_id]

            result[process_id] = {
                "command": info["command"],
                "status": status,
                "runtime": time.time() - info["start_time"]
            }

        return result

    def get_process_output(self, process_id):
        """Get output from a background process"""
        if process_id not in self.background_processes:
            return {"error": f"Process with ID {process_id} not found"}

        process_info = self.background_processes[process_id]
        process = process_info["process"]

        status = "running" if process.poll() is None else "terminated"

        result = {
            "status": status,
            "stdout": process_info["stdout"],
            "stderr": process_info["stderr"]
        }

        if status == "terminated":
            result["returncode"] = process.returncode
            del self.background_processes[process_id]

        return result

    def stop_background_process(self, process_id):
        """Stop a background process"""
        if process_id not in self.background_processes:
            return {"error": f"Process with ID {process_id} not found"}

        process_info = self.background_processes[process_id]
        process = process_info["process"]

        if process.poll() is None:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)

                time.sleep(0.5)

                if process.poll() is None:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)

                result = {
                    "success": True,
                    "message": f"Process {process_id} stopped",
                    "stdout": process_info["stdout"],
                    "stderr": process_info["stderr"]
                }
            except Exception as e:
                result = {"error": str(e)}
        else:
            result = {"message": f"Process {process_id} was already terminated"}

        if process_id in self.background_processes:
            del self.background_processes[process_id]

        return result

    def send_input_to_process(self, process_id, input_text):
        """Send input to a running background process"""
        if process_id not in self.background_processes:
            return {"error": f"Process with ID {process_id} not found"}

        process_info = self.background_processes[process_id]
        process = process_info["process"]

        if process.poll() is None:
            try:
                process.stdin.write(input_text + "\n")
                process.stdin.flush()

                time.sleep(0.2)

                return {
                    "success": True,
                    "message": f"Input sent to process {process_id}",
                    "stdout": process_info["stdout"],
                    "stderr": process_info["stderr"]
                }
            except Exception as e:
                return {"error": str(e)}
        else:
            return {"error": f"Process {process_id} is not running"}

    def get_files_and_dirs_at_path(self, path):
        """Get all files and directories at a given path"""
        try:
            return os.listdir(path)
        except Exception as e:
            return {"error": str(e)}

    def get_functions_and_classes(self, path, file_extension=".py"):
        """Extract all function and class names from files with the given extension in a directory.
        This is more token-efficient than getting full file contents when you only need structure information."""
        try:
            results = {}
            files = self.get_files_and_dirs_at_path(path)

            if isinstance(files, dict) and "error" in files:
                return files

            for file in files:
                if file.endswith(file_extension):
                    file_path = os.path.join(path, file)
                    functions = []
                    classes = []

                    with open(file_path, 'r') as f:
                        lines = f.readlines()

                    for line in lines:
                        line = line.strip()
                        if line.startswith('def ') and '(' in line:
                            func_name = line[4:line.find('(')].strip()
                            functions.append(func_name)
                        elif line.startswith('class ') and (':' in line or '(' in line):
                            end_marker = min(line.find('(') if '(' in line else len(line),
                                             line.find(':') if ':' in line else len(line))
                            class_name = line[6:end_marker].strip()
                            classes.append(class_name)

                    results[file] = {
                        "functions": functions,
                        "classes": classes
                    }

            return results
        except Exception as e:
            return {"error": str(e)}

    def get_function_content(self, path, function_name):
        """
        Extract the content of a specific function from a file.
        Much more token-efficient than loading the entire file when you only need one function.

        Parameters:
        - path: The path to the file
        - function_name: The name of the function to extract

        Returns:
        - The function's code as a string, including the definition line and docstring
        """
        try:
            if not os.path.exists(path):
                return {"error": f"File not found: {path}"}

            with open(path, 'r') as file:
                content = file.read()

            import re

            pattern = r'(^|\n)(\s*)def\s+' + \
                re.escape(function_name) + r'\s*\(.*?\):'
            match = re.search(pattern, content, re.DOTALL)

            if not match:
                return {"error": f"Function '{function_name}' not found in {path}"}

            start_pos = match.start()
            indentation = match.group(2)
            function_start = content[start_pos:].strip()

            lines = function_start.split('\n')
            function_lines = [lines[0]]
            for line in lines[1:]:

                if not line.strip() or line.startswith(indentation + ' ') or line.startswith(indentation + '\t'):
                    function_lines.append(line)
                elif line.strip() and not line.startswith(indentation):
                    break

            return '\n'.join(function_lines)

        except Exception as e:
            return {"error": f"Error extracting function: {str(e)}"}

    def get_file_contents(self, path):
        """Get the contents of a file. 
        Note: For large files, consider using get_all_functions_and_class_names first to analyze structure
        without consuming tokens on full file contents."""
        try:
            with open(path, 'r') as file:
                return file.read()
        except Exception as e:
            return {"error": str(e)}

    def get_file_contents_of_type(self, path, file_type):
        """Get the contents of a file of a given type"""
        try:
            files = self.get_files_and_dirs_at_path(path)
            if isinstance(files, dict) and "error" in files:
                return files

            for file in files:
                if file.endswith(file_type):
                    return self.get_file_contents(os.path.join(path, file))
            return {"error": f"No files with type {file_type} found at {path}"}
        except Exception as e:
            return {"error": str(e)}

    def write_file(self, path, content):
        """Write content to a file"""
        try:
            with open(path, 'w') as file:
                file.write(content)
            return {"success": True, "message": f"File {path} written successfully"}
        except Exception as e:
            return {"error": str(e)}

    def append_to_file(self, path, content):
        """Append content to a file"""
        try:
            with open(path, 'a') as file:
                file.write(content)
            return {"success": True, "message": f"Content appended to {path} successfully"}
        except Exception as e:
            return {"error": str(e)}
