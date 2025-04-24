import json
import os
from enum import Enum
from typing import Dict, List

import conffwk
import confmodel

from drunc_core.exceptions import DruncException, DruncSetupException
from drunc_core.utils.utils import expand_path, get_logger


class ConfTypes(Enum):
    Unknown = 0

    # End product
    PyObject = 1  # this is the OKS object under the hood, or something that "fakes" it

    # Raw types that need to be converted
    JsonFileName = 2
    ProtobufAny = 3
    OKSFileName = 4


def CLI_to_ConfTypes(scheme: str) -> ConfTypes:
    match scheme:
        case "file":
            return ConfTypes.JsonFileName
        case "oksconflibs" | "":
            return ConfTypes.OKSFileName
        case _:
            raise DruncSetupException(f"{scheme} configuration type is not understood")


def parse_conf_url(url: str) -> tuple[str, ConfTypes]:
    scheme, filename = url.split(":")
    t = CLI_to_ConfTypes(scheme)
    return url, t


class ConfigurationNotFound(DruncSetupException):
    def __init__(self, requested_path):
        super().__init__(
            f"The configuration '{requested_path}' is not in $DUNEDAQ_DB_PATH, perhaps you forgot to 'dbt-workarea-env && dbt-build'?"
        )


class ConfTypeNotSupported(DruncSetupException):
    def __init__(self, conf_type: ConfTypes, class_name: str):
        if not isinstance(class_name, str):
            class_name = class_name.__class__.__name__
        message = f"'{conf_type}' is not supported by '{class_name}'"
        super().__init__(message)


class OKSKey:
    def __init__(self, schema_file: str, class_name: str, obj_uid: str, session: str):
        self.schema_file = schema_file
        self.class_name = class_name
        self.obj_uid = obj_uid
        self.session = session


class ConfHandler:
    def __init__(
        self,
        data=None,
        type=ConfTypes.PyObject,
        oks_key: OKSKey = None,
        *args,
        **kwargs,
    ):
        self.class_name = self.__class__.__name__
        self.log = get_logger("utils." + self.class_name)
        self.initial_type = type
        self.initial_data = data
        self.root_id = 0
        self.controller_id = 0
        self.process_id = 0
        self.process_id_infra = 0

        if type == ConfTypes.OKSFileName and oks_key is None:
            raise DruncSetupException("Need to provide a key for the OKS file")

        self.oks_key = oks_key
        self.validate_and_parse_configuration_location(*args, **kwargs)

    def copy_oks_key(self):
        return self.oks_key

    def _parse_oks_file(self, oks_path):
        try:
            self.oks_path = oks_path
            self.log.debug(f"Using {self.oks_path} to configure")
            self.db = conffwk.Configuration(self.oks_path)
            return self.db.get_dal(
                class_name=self.oks_key.class_name, uid=self.oks_key.obj_uid
            )

        except ImportError as e:
            raise DruncSetupException(
                "OKS is not setup in this python environment, cannot parse OKS configurations"
            ) from e

        except KeyError as e:
            raise DruncSetupException(
                "OKS params where not passed to this ConfigurationHandler, cannot parse OKS configurations"
            ) from e

    def _post_process_oks(self):
        pass

    def _parse_pbany(self, pbany_data):
        raise ConfTypeNotSupported(ConfTypes.ProtobufAny, self)

    def _parse_dict(self, data):
        raise ConfTypeNotSupported(ConfTypes.JsonFileName, self)

    def validate_and_parse_configuration_location(self, *args, **kwargs):
        match self.initial_type:
            case ConfTypes.PyObject:
                self.data = self.initial_data
                self.type = self.initial_type
                self._post_process_oks(*args, **kwargs)

            case ConfTypes.JsonFileName:
                resolved = expand_path(self.initial_data, True)
                if not os.path.exists(expand_path(self.initial_data)):
                    raise DruncSetupException(
                        f"Location {resolved} ({self.initial_data}) is empty!"
                    )

                with open(resolved) as f:
                    data = json.loads(f.read())
                    self.data = self._parse_dict(data)
                    self.type = ConfTypes.PyObject
                    self._post_process_oks(*args, **kwargs)

            case ConfTypes.OKSFileName:
                self.data = self._parse_oks_file(self.initial_data)
                self.type = ConfTypes.PyObject
                self._post_process_oks(*args, **kwargs)

            case ConfTypes.ProtobufAny:
                self.data = self._parse_pbany(self.initial_data)
                self.type = ConfTypes.PyObject
                self._post_process_oks(*args, **kwargs)

            case _:
                raise ConfTypeNotSupported(self.initial_type, self.class_name)


def get_commandline_parameters(db, config_filename, session_id, session_name, obj):
    runs_on = obj.runs_on.runs_on.id
    control_service_port = -1
    control_service_protocol = ""
    for svc in obj.exposes_service:
        if svc.id.endswith("_control"):
            control_service_port = svc.port
            control_service_protocol = svc.protocol
            break

    commandline_parameters = [
        "-s",
        session_name,
        "-k",
        session_id,
        "-n",
        obj.id,
        "-c",
        f"{control_service_protocol}://{runs_on}:{control_service_port}",
        "-d",
        config_filename,
    ]
    if "RCApplication" in obj.oksTypes():
        commandline_parameters += [
            "-l",
            db.get_dal("Session", session_id).controller_log_level,
        ]

    return commandline_parameters


def collect_variables(variables, env_dict: Dict[str, str]) -> None:
    """!Process a dal::Variable object, placing key/value pairs in a dictionary

    @param variables  A Variable/VariableSet object
    @param env_dict   The desitnation dictionary

    """
    for item in variables:
        if item.className() == "VariableSet":
            collect_variables(item.contains, env_dict)
        else:
            if item.className() == "Variable":
                env_dict[item.name] = item.value


class EnvironmentVariableCannotBeSet(DruncException):
    pass


# Recursively process all Segments in given Segment extracting Applications
def collect_apps(
    config_filename,
    session_name,
    db,
    session_obj,
    segment_obj,
    env: Dict[str, str],
    tree_prefix=[
        0,
    ],
) -> List[Dict]:
    """! Recustively collect (daq) application belonging to segment and its subsegments

    @param session_obj  The session the segment belongs to
    @param segment_obj  Segment to collect applications from

    @return The list of dictionaries holding application attributs

    """
    log = get_logger("process_orchestrator.collect_apps")
    # Get default environment from Session
    defenv = env.copy()

    DB_PATH = os.getenv("DUNEDAQ_DB_PATH")
    if DB_PATH is None:
        log.warning("DUNEDAQ_DB_PATH not set in this shell")
    else:
        defenv["DUNEDAQ_DB_PATH"] = DB_PATH

    collect_variables(session_obj.environment, defenv)

    apps = []

    # Add controller for this segment to list of apps
    controller = segment_obj.controller
    rc_env = defenv.copy()
    collect_variables(controller.application_environment, rc_env)
    rc_env["DUNEDAQ_APPLICATION_NAME"] = controller.id
    host = controller.runs_on.runs_on.id

    tree_id_str = ".".join(map(str, tree_prefix))
    apps.append(
        {
            "name": controller.id,
            "type": controller.application_name,
            "args": get_commandline_parameters(
                db=db,
                config_filename=config_filename,
                session_id=session_obj.id,
                session_name=session_name,
                obj=controller,
            ),
            "restriction": host,
            "host": host,
            "env": rc_env,
            "tree_id": tree_id_str,
            "log_path": controller.log_path,
        }
    )

    # Recurse over nested segments
    for idx, sub_segment_obj in enumerate(segment_obj.segments):
        log.debug(f"Considering segment {sub_segment_obj.id}")
        if confmodel.component_disabled(db._obj, session_obj.id, sub_segment_obj.id):
            log.debug(f"Ignoring segment '{sub_segment_obj.id}' as it is disabled")
            continue

        log.debug(f"Collecting apps for segment {sub_segment_obj.id}")
        new_tree_prefix = tree_prefix + [idx]
        try:
            sub_apps = collect_apps(
                session_name=session_name,
                config_filename=config_filename,
                db=db,
                session_obj=session_obj,
                segment_obj=sub_segment_obj,
                env=env,
                tree_prefix=new_tree_prefix,
            )
        except Exception as e:
            log.exception(e)
            raise e
        for app in sub_apps:
            apps.append(app)

    # Get all the enabled applications of this segment
    app_index = 0
    for app in segment_obj.applications:
        log.debug(f"Considering app {app.id}")
        if "Component" in app.oksTypes():
            enabled = not confmodel.component_disabled(db._obj, session_obj.id, app.id)
            log.debug(f"{app.id} {enabled=}")
        else:
            enabled = True
            log.debug(f"{app.id} {enabled=}")

        if not enabled:
            log.debug(f"Ignoring disabled app {app.id}")
            continue

        app_env = defenv.copy()

        # Override with any app specific environment from Application
        collect_variables(app.application_environment, app_env)
        app_env["DUNEDAQ_APPLICATION_NAME"] = app.id

        app_tree_id_str = ".".join(map(str, tree_prefix + [app_index]))

        host = app.runs_on.runs_on.id
        args = get_commandline_parameters(
            db=db,
            config_filename=config_filename,
            session_id=session_obj.id,
            session_name=session_name,
            obj=app,
        )
        log.debug(f"Collecting app {app.id} with args {args}")

        apps.append(
            {
                "name": app.id,
                "type": app.application_name,
                "args": args,
                "restriction": host,
                "host": host,
                "env": app_env,
                "tree_id": app_tree_id_str,
                "log_path": app.log_path,
            }
        )
        app_index += 1

    return apps
