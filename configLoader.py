# configLoader.py
import os
import yaml

DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), 
    "config", 
    "config.yaml"
)

def load_config(config_file=DEFAULT_CONFIG_PATH):
    """
    Loads a YAML config file and returns it as a dictionary.
    """
    os.getenv("OPENAI_API_KEY")
    with open(config_file, "r") as f:
        config_data = yaml.safe_load(f)
    return config_data
