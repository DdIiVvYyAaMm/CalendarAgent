# configLoader.py
import os
import yaml
from dotenv import load_dotenv

DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), 
    "config", 
    "config.yaml"
)

def load_config(config_file=DEFAULT_CONFIG_PATH):
    """
    Loads a YAML config file and returns it as a dictionary.
    """
    load_dotenv()
    

    with open(config_file, "r") as f:
        config_data = yaml.safe_load(f)

    for k, v in config_data.items():
        if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
            # e.g. "${OPENAI_API_KEY}" -> "OPENAI_API_KEY"
            env_var_name = v.strip("${}")
            config_data[k] = os.getenv(env_var_name, "")
    return config_data
