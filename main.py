from agent.agent import Agent
from tools.Tools import Tools
from llm.models import AnthropicAgent, OpenAIAgent
import shutil
from colorama import Fore, Back, Style, init
from dotenv import load_dotenv
import argparse
import os


def main():
    init(autoreset=True)

    load_dotenv()

    parser = argparse.ArgumentParser(description='AI Agent Terminal')
    parser.add_argument('--provider', type=str, default='anthropic', choices=['anthropic', 'openai'],
                        help='The LLM provider to use (default: anthropic)')
    parser.add_argument('--model', type=str,
                        help='The specific model to use (defaults to provider default)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode')
    parser.add_argument('task', nargs='?', default=None,
                        help='The task to solve (if not provided, will prompt for input)')
    args = parser.parse_args()

    term_width = shutil.get_terminal_size().columns

    banner = f"""
{Fore.CYAN + Style.BRIGHT}╔{'═' * (term_width - 2)}╗
║{' ' * (term_width - 2)}║
║{' AI Agent Terminal '.center(term_width - 2)}║
║{' Claude/OpenAI-Powered Task Execution System '.center(term_width - 2)}║
║{' ' * (term_width - 2)}║
╚{'═' * (term_width - 2)}╝{Style.RESET_ALL}
"""
    print(banner)

    tools = Tools()

    if args.provider.lower() == 'anthropic':
        llm = AnthropicAgent()
    else:
        llm = OpenAIAgent()

    agent = Agent(
        tools=tools,
        llm=llm,
        provider=args.provider,
        model=args.model
    )

    agent.debug = args.debug

    task = args.task
    if not task:
        task = input(f"{Fore.GREEN}Enter your task: {Style.RESET_ALL}")

    agent.solve_task(task)


if __name__ == "__main__":
    main()
