import anthropic
import os
from openai import OpenAI


class AnthropicAgent:
    """A class for the agent to use Anthropic"""

    def __init__(self, api_key=None):
        self.client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.provider = "anthropic"
        self.default_model = "claude-3-7-sonnet-20250219"


class OpenAIAgent:
    """A class for the agent to use OpenAI"""

    def __init__(self, api_key=None):
        self.client = OpenAI(
            api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        self.provider = "openai"
        self.default_model = "gpt-4o"
