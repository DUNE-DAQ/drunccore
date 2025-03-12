import os
from enum import Enum
from importlib.resources import path
from urllib.parse import urlparse

from drunc.broadcast.server.configuration import KafkaBroadcastSenderConfData
from drunc.process_manager.exceptions import UnknownProcessManagerType
from drunc.utils.configuration import ConfHandler
from drunc.utils.utils import get_logger


class ProcessManagerTypes(Enum):
    Unknown = 0
    SSH = 1
    K8s = 2


class ProcessManagerConfData:
    def __init__(self):
        self.broadcaster = None
        self.authoriser = None
        self.type = ProcessManagerTypes.Unknown
        self.command_address = ""
        self.environment = {}


class ProcessManagerConfHandler(ConfHandler):
    def __init__(self, log_path: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log_path = log_path
        self.log = get_logger("process_manager.conf_handler")

    def _parse_dict(self, data):
        new_data = ProcessManagerConfData()
        if data.get("broadcaster"):
            new_data.broadcaster = KafkaBroadcastSenderConfData.from_dict(
                data.get("broadcaster")
            )
        else:
            new_data.broadcaster = None
        new_data.authoriser = None
        new_data.environment = data.get("environment", {})
        match data["type"].lower():
            case "ssh":
                new_data.type = ProcessManagerTypes.SSH
                new_data.kill_timeout = data.get("kill_timeout", 0.5)
            case "k8s":
                new_data.type = ProcessManagerTypes.K8s
                new_data.image = data.get("image", "ghcr.io/dune-daq/alma9:latest")
            case _:
                raise UnknownProcessManagerType(data["type"])

        return new_data


def get_commandline_parameters(db, config_filename, session_id, session_name, obj):
    runs_on = obj.runs_on.runs_on.id
    control_service_port = -1
    control_service_protocol = ""
    for svc in obj.exposes_service:
        if svc.id.endswith("_control"):
            control_service_port = svc.port
            control_service_protocol = svc.protocol
            break

    return [
        "-s",
        session_name,
        "-k",
        session_id,
        "-n",
        obj.id,
        "-c",
        f"{control_service_protocol}://{runs_on}:{control_service_port}",
        "-d",
        f"oksconflibs:{config_filename}",
    ]


def get_process_manager_configuration(process_manager_conf_filename: str) -> str:
    ## Make the configuration name finding easier
    if os.path.splitext(process_manager_conf_filename)[1] != ".json":
        process_manager_conf_filename += ".json"
    ## If no scheme is provided, assume that it is an internal packaged configuration.
    ## First check it's not an existing external file
    if os.path.isfile(process_manager_conf_filename):
        if urlparse(process_manager_conf_filename).scheme == "":
            process_manager_conf_filename = "file://" + process_manager_conf_filename
    else:
        ## Check if the file is in the list of packaged configurations
        packaged_configurations = os.listdir(path("drunc.data.process_manager", ""))
        if process_manager_conf_filename in packaged_configurations:
            process_manager_conf_filename = (
                "file://"
                + str(path("drunc.data.process_manager", ""))
                + "/"
                + process_manager_conf_filename
            )
        else:
            log = get_logger("process_manager.ConfHandler")
            log.error(
                f"Configuration [red]{process_manager_conf_filename}[/red] not found, check filename spelling or use a packaged configuration as one of [green]{'[/green], [green]'.join(packaged_configurations)}[/green]."
            )
            exit()
    return process_manager_conf_filename
