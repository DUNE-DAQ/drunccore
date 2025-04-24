from importlib.metadata import entry_points

from drunc_core.utils.utils import get_logger


def load_entry_point_plugins():
    _logger = get_logger("controller.action_loader")
    _logger.debug("Loading entry point plugins")
    try:
        eps = entry_points(group="drunc.plugins")
    except TypeError:
        # Older Python versions
        eps = entry_points().get("drunc.plugins", [])

    _logger.debug(f"Found {len(eps)} entry points")

    for ep in eps:
        _logger.debug(f"Loading plugin: {ep.name} from {ep.value}")
        plugin_func = ep.load()
        plugin_func()
