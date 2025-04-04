import pytest

from drunc.connectivity_service.client import ConnectivityServiceClient
from drunc.controller.controller_driver import ControllerDriver
from drunc.exceptions import DruncException
from drunc.utils.shell_utils import create_dummy_token_from_uname


def setup_controller_driver(processes_and_logs, dal, session_name) -> ControllerDriver:
    connectivity_service_port = dal.connectivity_service.service.port

    csc = ConnectivityServiceClient(
        session_name,
        f"localhost:{connectivity_service_port}",
    )

    token = create_dummy_token_from_uname()
    controller_address = None
    try:
        controller_address = csc.resolve(
            "controller-0_control", "RunControlMessage", ntries=20
        )
    except DruncException as e:
        pytest.fail(f"Controller did not advertise its address in time: {e!s}")

    controller_driver = ControllerDriver(
        controller_address[0]["uri"].replace("grpc://", ""),
        token,
    )

    return controller_driver


def test_controller_driver(one_controller_running):
    controller_driver = setup_controller_driver(*one_controller_running)
    description = controller_driver.describe()
    assert description is not None


def test_controller_driver_describe(many_controllers_running):
    controller_driver = setup_controller_driver(*many_controllers_running)
    description = controller_driver.describe()
    assert description is not None
