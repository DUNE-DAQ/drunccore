from drunc.session_manager.interface.session_manager import session_manager_cli
from drunc.utils.utils import (
    create_logger_handler,
    get_logger,
    print_traceback,
    setup_root_logger,
)


def main():
    try:
        session_manager_cli()
    except Exception as e:
        setup_root_logger("INFO")
        log = get_logger("session_manager")
        create_logger_handler(rich_handler=True)
        log.error("[red bold]:fire::fire: Exception thrown :fire::fire:")
        print_traceback(e)


if __name__ == "__main__":
    main()
