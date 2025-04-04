import getpass
import os
import time
from pathlib import Path
from subprocess import Popen, run

import pytest

consolidated_conf_path = f"/tmp/drunc-pytests-of-{getpass.getuser()}"


@pytest.fixture
def load_test_config():
    DUNEDAQ_DB_PATH = os.getenv("DUNEDAQ_DB_PATH")
    if DUNEDAQ_DB_PATH is None:
        DUNEDAQ_DB_PATH = ""
    cwd = Path(os.path.abspath(__file__))
    test_configs = cwd.parent / ".." / ".." / ".." / "config" / "tests"
    test_configs = test_configs.resolve()
    os.makedirs(consolidated_conf_path, exist_ok=True)
    # os.remove(f"{consolidated_conf_path}/*")
    DUNEDAQ_DB_PATH += f":{test_configs!s}:{consolidated_conf_path!s}"
    os.environ["DUNEDAQ_DB_PATH"] = DUNEDAQ_DB_PATH


@pytest.fixture
def one_controller_running(load_test_config, request):
    from drunc.process_manager.oks_parser import collect_apps, collect_infra_apps

    req_name = request.node.name
    configuration_name = "one-controller-config"
    configuration_file = f"{configuration_name}.data.xml"
    configuration_consolidated_file = f"{consolidated_conf_path}/{configuration_name}.{req_name}.consolidated.data.xml"
    from daqconf.consolidate import consolidate_db

    consolidate_db(configuration_file, configuration_consolidated_file)
    from daqconf.set_connectivity_service_port import set_connectivity_service_port

    set_connectivity_service_port(configuration_consolidated_file, configuration_name)
    session_name = f"{req_name}-{configuration_name}"

    try:
        import conffwk
    except ImportError:
        pytest.skip("conffwk is not installed")

    env = os.environ.copy()
    env["DUNEDAQ_SESSION"] = session_name
    configuration_consolidated_file = f"oksconflibs:{configuration_consolidated_file}"
    db = conffwk.Configuration(configuration_consolidated_file)
    session_dal = db.get_dal(class_name="Session", uid=configuration_name)

    apps = collect_apps(
        session_name=session_name,
        config_filename=configuration_consolidated_file,
        db=db,
        session_obj=session_dal,
        segment_obj=session_dal.segment,
        env=env,
        tree_prefix=[0],
    )

    next_tree_id = max([int(app["tree_id"].split(".")[0]) for app in apps]) + 1

    apps += collect_infra_apps(session=session_dal, env=env, tree_prefix=[next_tree_id])

    processes = {}
    for app_info in apps:
        args = " ".join([app_info["type"]] + app_info["args"])
        log_file = (
            "log_"
            + getpass.getuser()
            + "_"
            + session_name
            + "_"
            + app_info["name"]
            + ".txt"
        )
        log_file = consolidated_conf_path + "/" + log_file
        args = "{ " + args + "; } &> " + log_file
        print(f"Running {args}")
        process = Popen(
            args=args,
            env=app_info["env"],
            shell=True,
        )

        processes[app_info["name"]] = process, log_file

    for _ in range(10):
        with open(processes["local-connection-server"][1], "r") as f:
            if "[INFO] Starting gunicorn" in f.readline():
                break
        time.sleep(0.1)

    yield processes, session_dal, session_name

    for name, process in processes.items():
        if process[0].poll() is None:
            print(f"Killing {name}: {process[0].pid}")
            process[0].kill()

    run(["killall", "gunicorn", "drunc-controller"])
