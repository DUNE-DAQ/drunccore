from drunc.process_manager.interface.process_manager import process_manager_cli
from drunc.utils.utils import get_logger, setup_root_logger, print_traceback, create_logger_handler


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

if __name__ == '__main__':
    main()
