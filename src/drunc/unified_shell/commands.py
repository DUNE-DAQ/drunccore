import getpass

import click
from druncschema.process_manager_pb2 import ProcessQuery

from drunc.controller.interface.shell_utils import controller_setup
from drunc.process_manager.interface.context import ProcessManagerContext
from drunc.utils.shell_utils import InterruptedCommand
from drunc.utils.utils import get_logger, log_levels, run_coroutine


@click.command("boot")
@click.option(
    "-u",
    "--user",
    type=str,
    default=getpass.getuser(),
    help="Create the processes for a particular user (default $USER)",
)
@click.option(
    "-s",
    "--session-name",
    type=str,
    default=None,
    help="Override the session name",
)
@click.option(
    "-l",
    "--log-level",
    type=click.Choice(log_levels.keys(), case_sensitive=False),
    default="INFO",
    help="Set the log level",
)
@click.option("--override-logs/--no-override-logs", default=True)
@click.pass_obj
@run_coroutine
async def boot(
    obj: ProcessManagerContext,
    user: str,
    session_name: str,
    log_level: str,
    override_logs: bool,
) -> None:
    log = get_logger("unified_shell.boot")

    processes = await obj.get_driver("process_manager").ps(ProcessQuery(user=user, session=session_name))

    if len(processes.data.values) > 0:
        click.confirm(
            f"You already have {len(processes.data.values)} processes running in session {session_name}, are you sure you want to boot a session?",
            abort=True,
        )

    if session_name is None:
        session_name = obj.session_name

    try:
        results = obj.get_driver("process_manager").boot(
            conf_file=obj.configuration_file,
            conf_id=obj.configuration_id,
            user=user,
            session_name=session_name,
            log_level=log_level,
            override_logs=override_logs,
        )
        async for result in results:
            if not result:
                break
            log.debug(
                f"'{result.data.process_description.metadata.name}' ({result.data.uuid.uuid}) started"
            )
    except InterruptedCommand:
        log.warning("Booting interrupted")
        return

    controller_address = obj.get_driver("process_manager").controller_address
    if controller_address:
        log.debug(f"Controller endpoint is '{controller_address}'")
        log.debug("Connecting the unified_shell to the controller endpoint")
        obj.set_controller_driver(controller_address)
        controller_setup(obj, controller_address)

    else:
        log.error("Could not understand where the controller is!")
        return

    log.info("Booted successfully")
