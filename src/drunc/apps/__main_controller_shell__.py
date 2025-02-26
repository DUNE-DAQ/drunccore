from drunc.controller.interface.context import ControllerContext
from drunc.controller.interface.shell import controller_shell
from drunc.utils.utils import get_logger, setup_root_logger, print_traceback, create_logger_handler


def main() -> None:
    context = ControllerContext()

    try:
        controller_shell(obj = context)

    except Exception as e:
        setup_root_logger("INFO")
        log = get_logger("controller_shell")
        create_logger_handler(rich_handler=True)
        log.error("[red bold]:fire::fire: Exception thrown :fire::fire:")
        print_traceback(e)
        exit(1)

if __name__ == '__main__':
    main()
