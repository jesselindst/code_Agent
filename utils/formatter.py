import textwrap
import shutil
from colorama import Fore, Back, Style, init


class Formatter:
    """
    A utility class handling all the formatting and display logic for the Agent.
    This separates presentation concerns from the core agent logic.
    """

    def __init__(self):
        """Initialize the formatter with color codes and get terminal width."""
        init(autoreset=True)

        self.term_width = shutil.get_terminal_size().columns

        self.colors = {
            'task': Fore.CYAN + Style.BRIGHT,
            'step': Fore.YELLOW + Style.BRIGHT,
            'thought': Fore.MAGENTA,
            'action': Fore.GREEN,
            'result': Fore.WHITE,
            'success': Fore.GREEN + Style.BRIGHT,
            'error': Fore.RED + Style.BRIGHT,
            'error_box': Fore.WHITE + Back.RED,
            'warning': Fore.YELLOW,
            'highlight': Fore.CYAN,
            'time': Fore.WHITE + Back.BLUE,
            'info': Fore.BLUE + Style.BRIGHT,
            'json_key': Fore.YELLOW,
            'json_value': Fore.WHITE,
            'json_null': Fore.RED,
            'json_bool': Fore.MAGENTA,
            'json_number': Fore.CYAN,
            'command': Fore.YELLOW + Style.BRIGHT,
            'context': Fore.CYAN,
            'progress': Fore.GREEN + Style.BRIGHT,
            'separator': Fore.BLUE,
            'stdout': Fore.WHITE,
            'stderr': Fore.RED,
            'debug': Fore.CYAN + Back.BLACK,
            'retry': Fore.YELLOW + Back.BLACK + Style.BRIGHT,
        }

    def print_debug(self, message, timestamp=""):
        """Print a debug message with optional timestamp"""
        if timestamp:
            print(
                f"{self.colors['debug']}[DEBUG {timestamp}] {message}{Style.RESET_ALL}")
        else:
            print(
                f"{self.colors['debug']}[DEBUG] {message}{Style.RESET_ALL}")

    def print_separator(self, style='thin'):
        """Print a visual separator line with different styles."""
        width = self.term_width

        if style == 'thin':
            print(self.colors['separator'] + "─" * width)
        elif style == 'thick':
            print(self.colors['separator'] + "━" * width)
        elif style == 'double':
            print(self.colors['separator'] + "═" * width)
        elif style == 'dot':
            print(self.colors['separator'] + "┄" * width)
        elif style == 'dash':
            print(self.colors['separator'] + "┅" * width)

    def print_header(self, text, level=1):
        """Print a formatted header with different emphasis levels."""
        width = self.term_width
        padding = 2
        text_length = len(text)

        if level == 1:
            self.print_separator('double')
            print(f"{self.colors['task']}{text.center(width)}")
            self.print_separator('double')
        elif level == 2:
            print(
                f"\n{self.colors['step']}{'━' * padding} {text} {'━' * (width - text_length - padding - 3)}")
        elif level == 3:
            print(
                f"\n{self.colors['highlight']}{'┄' * padding} {text} {'┄' * (width - text_length - padding - 3)}")

    def print_error_box(self, title, error_details, raw_data=None):
        """Print a visually distinct error box with detailed information."""
        width = self.term_width - 4

        print(f"\n{self.colors['error']}╔{'═' * width}╗")
        print(
            f"{self.colors['error']}║ {self.colors['error_box']} {title.center(width - 2)} {self.colors['error']}║")
        print(f"{self.colors['error']}╠{'═' * width}╣")

        wrapped_details = textwrap.wrap(error_details, width=width - 2)
        for line in wrapped_details:
            print(f"{self.colors['error']}║ {line.ljust(width - 2)} ║")

        if raw_data:
            print(f"{self.colors['error']}╠{'─' * width}╣")
            print(
                f"{self.colors['error']}║ {self.colors['warning']} Raw Data Preview:{' ' * (width - 18)} {self.colors['error']}║")

            data_preview = str(raw_data)
            if len(data_preview) > 500:
                data_preview = data_preview[:497] + "..."

            wrapped_data = textwrap.wrap(data_preview, width=width - 4)
            for line in wrapped_data:
                print(
                    f"{self.colors['error']}║  {self.colors['debug']}{line.ljust(width - 4)}{self.colors['error']}  ║")

        print(f"{self.colors['error']}╚{'═' * width}╝")

    def print_action(self, function_call):
        """Print an action (function call) in a formatted box"""
        print(
            f"\n{self.colors['action']}🛠️  ACTION:{Style.RESET_ALL}")
        command_width = min(
            len(function_call) + 4, self.term_width - 4)
        print(f"{self.colors['command']}┌{'─' * command_width}┐")
        print(
            f"{self.colors['command']}│ {function_call}{' ' * (command_width - len(function_call) - 2)}│")
        print(f"{self.colors['command']}└{'─' * command_width}┘")

    def print_result(self, result):
        """Print a result from a function call with appropriate formatting"""
        print(
            f"\n{self.colors['result']}📋 RESULT:{Style.RESET_ALL}")

        if isinstance(result, dict) and "error" in result:
            error_msg = result["error"]
            print(f"{self.colors['error']}❌ {error_msg}")
        else:
            if isinstance(result, dict):
                if "stdout" in result and result["stdout"]:
                    stdout = result["stdout"]
                    if len(stdout) > 1000:
                        print(
                            f"{self.colors['stdout']}│ Standard Output ({len(stdout)} chars):")
                        for line in stdout[:500].split('\n')[:10]:
                            print(
                                f"{self.colors['stdout']}│ {line}")
                        print(
                            f"{self.colors['stdout']}│ ... [truncated]")
                    else:
                        print(
                            f"{self.colors['stdout']}│ Standard Output:")
                        for line in stdout.split('\n'):
                            print(
                                f"{self.colors['stdout']}│ {line}")

                    result_copy = result.copy()
                    del result_copy["stdout"]
                else:
                    result_copy = result

                if "stderr" in result and result["stderr"]:
                    stderr = result["stderr"]
                    print(
                        f"{self.colors['stderr']}│ Error Output:")
                    for line in stderr.split('\n'):
                        print(f"{self.colors['stderr']}│ {line}")

                    if "stderr" in result_copy:
                        del result_copy["stderr"]

                for key, value in result_copy.items():
                    if key not in ["stdout", "stderr"]:
                        value_str = str(value)
                        print(
                            f"{self.colors['json_key']}{key}: {self.colors['json_value']}{value_str}")
            else:
                print(str(result))
