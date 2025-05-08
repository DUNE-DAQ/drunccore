from drunccore.utils.utils import get_logger

_registry = {}


def register_action(name: str, cls):
    _logger = get_logger("controller.action_registry")
    _logger.info(f"Registering action: {name}")
    _registry[name] = cls


def create_action(name: str, *args, **kwargs):
    _logger = get_logger("controller.action_registry")
    cls = _registry.get(name)
    if cls is None:
        _logger.error(f"Unknown action: {name}")
        raise ValueError(f"Unknown action: {name}")
    return cls(*args, **kwargs)
