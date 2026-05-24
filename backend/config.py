"""Default configuration loader for API keys and settings."""
from __future__ import annotations
import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

CONFIG_FILENAME = "aippt_config.json"
CONFIG_EXAMPLE_FILENAME = "aippt_config.example.json"


def get_project_root() -> Path:
    """Get project root directory (looking for package.json or backend folder)."""
    current = Path(__file__).parent
    # Check up to 3 levels
    for _ in range(3):
        if (current / "package.json").exists() or (current / "backend").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return Path.cwd()


def get_config_path() -> Path:
    """Get path to config file in project root."""
    return get_project_root() / CONFIG_FILENAME


def get_config_example_path() -> Path:
    """Get path to example config file."""
    return get_project_root() / CONFIG_EXAMPLE_FILENAME


def load_default_config() -> Dict[str, Any]:
    """Load default config from aippt_config.json if exists."""
    config_path = get_config_path()
    
    if not config_path.exists():
        logger.debug(f"Config file not found at {config_path}")
        return {}
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        logger.info(f"Loaded config from {config_path}")
        return config
    except Exception as e:
        logger.warning(f"Failed to load config from {config_path}: {e}")
        return {}


def create_example_config():
    """Create an example config file if it doesn't exist."""
    example_path = get_config_example_path()
    
    if example_path.exists():
        return
    
    example_config = {
        "_comment": "Copy this file to aippt_config.json and fill in your API keys",
        "api_keys": {
            "deepseek-v4-flash": {
                "api_key": "sk-your-deepseek-key-here",
                "base_url": "https://api.deepseek.com"
            },
            "gpt-4o": {
                "api_key": "sk-your-openai-key-here",
                "base_url": "https://api.openai.com/v1"
            },
            "qwen-max": {
                "api_key": "sk-your-qwen-key-here",
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
            }
        },
        "default_model": "deepseek-v4-flash",
        "settings": {
            "temperature": 0.4,
            "max_tokens": 4096
        }
    }
    
    try:
        with open(example_path, "w", encoding="utf-8") as f:
            json.dump(example_config, f, indent=2, ensure_ascii=False)
        logger.info(f"Created example config at {example_path}")
    except Exception as e:
        logger.warning(f"Failed to create example config: {e}")


def get_api_keys_from_config() -> Dict[str, Dict[str, str]]:
    """Get API keys from config file."""
    config = load_default_config()
    return config.get("api_keys", {})


def get_default_model() -> Optional[str]:
    """Get default model from config file."""
    config = load_default_config()
    return config.get("default_model")


def get_settings() -> Dict[str, Any]:
    """Get settings from config file."""
    config = load_default_config()
    return config.get("settings", {})


# Initialize - create example config on first run
create_example_config()
