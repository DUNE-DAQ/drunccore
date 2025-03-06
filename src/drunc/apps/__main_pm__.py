from drunc.process_manager.interface.process_manager import process_manager_cli
from drunc.utils.utils import (
    create_logger_handler,
    get_logger,
    print_traceback,
    setup_root_logger,
)


def main():
    try:
        process_manager_cli()
    except Exception as e:
        setup_root_logger("INFO")
        log = get_logger("process_manager")
        create_logger_handler(rich_handler=True)
        log.error("[red bold]:fire::fire: Exception thrown :fire::fire:")
        print_traceback(e)
        exit(1)


if __name__ == "__main__":
    main()
