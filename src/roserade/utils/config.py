import os
import yaml
from pathlib import Path
from typing import Optional
from ..models.config import AppConfig


def get_config_dir() -> Path:
    """Get the configuration directory following XDG standards."""
    xdg_config = os.getenv("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "roserade"
    return Path.home() / ".config" / "roserade"


def get_default_config_path() -> Path:
    """Get the default configuration file path."""
    return get_config_dir() / "config.yaml"


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    """Load configuration from YAML file."""
    if config_path is None:
        config_path = get_default_config_path()
    
    if not config_path.exists():
        # Create default config if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config = AppConfig()
        save_config(config, config_path)
        return config
    
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f) or {}
        return AppConfig(**config_data)
    except Exception as e:
        raise RuntimeError(f"Failed to load config from {config_path}: {e}")


def save_config(config: AppConfig, config_path: Optional[Path] = None) -> None:
    """Save configuration to YAML file."""
    if config_path is None:
        config_path = get_default_config_path()
    
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to dict and handle Path objects
    config_dict = config.model_dump()
    
    def convert_paths(obj):
        if isinstance(obj, dict):
            return {k: convert_paths(v) for k, v in obj.items()}
        elif isinstance(obj, Path):
            return str(obj)
        elif isinstance(obj, list):
            return [convert_paths(item) for item in obj]
        return obj
    
    config_dict = convert_paths(config_dict)
    
    with open(config_path, 'w') as f:
        yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)


def create_default_config() -> None:
    """Create a default configuration file."""
    config_path = get_default_config_path()
    if not config_path.exists():
        config = AppConfig()
        save_config(config, config_path)
        print(f"Created default configuration at {config_path}")