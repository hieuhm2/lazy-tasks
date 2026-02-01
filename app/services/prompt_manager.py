"""Prompt management service for loading YAML prompts and rendering Jinja2 templates."""

import logging
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
SYSTEM_DIR = PROMPTS_DIR / "system"
TEMPLATES_DIR = PROMPTS_DIR / "templates"


class PromptManager:
    """Loads YAML system prompts and renders Jinja2 templates.

    Uses simple dict cache for YAML files. Singleton usage recommended.
    """

    def __init__(self) -> None:
        """Initialize prompt manager with file paths and caches."""
        self._cache: dict[str, dict[str, Any]] = {}
        self._jinja_env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _load_yaml(self, agent_name: str) -> dict[str, Any]:
        """Load and cache a YAML prompt file.

        Args:
            agent_name: Name of the agent (matches filename without .yaml).

        Returns:
            Parsed YAML content.

        Raises:
            FileNotFoundError: If the YAML file doesn't exist.
        """
        if agent_name in self._cache:
            return self._cache[agent_name]

        file_path = SYSTEM_DIR / f"{agent_name}.yaml"
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {file_path}")

        with open(file_path) as f:
            data = yaml.safe_load(f)

        self._cache[agent_name] = data
        logger.debug(f"Loaded prompt: {agent_name}")
        return data

    def get_system_prompt(self, agent_name: str) -> str:
        """Get the system prompt string for an agent.

        Args:
            agent_name: Name of the agent (e.g. 'personality', 'analyzer').

        Returns:
            The system prompt text.
        """
        data = self._load_yaml(agent_name)
        return data.get("system_prompt", "")

    def render_template(self, template_name: str, **kwargs: Any) -> str:
        """Render a Jinja2 template with given variables.

        Args:
            template_name: Template filename (e.g. 'task_clarification.jinja2').
            **kwargs: Template variables.

        Returns:
            Rendered template string.
        """
        template = self._jinja_env.get_template(template_name)
        return template.render(**kwargs)
