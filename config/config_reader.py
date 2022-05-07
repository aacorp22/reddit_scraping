'''file for reading config from yml'''
import yaml


def read_config() -> dict:
    """
    function to read config and return as a dict
    """
    with open("config/config.yml", "r", encoding="utf8") as file:
        config = yaml.safe_load(file)

    return config
