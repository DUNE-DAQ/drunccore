# https://github.com/DUNE-DAQ/drunc/issues/363

from drunc.controller.configuration import ControllerConfHandler
from drunc.utils.utils import setup_root_logger


def test_issue363(load_test_config):
    setup_root_logger("INFO")
    from drunc.utils.configuration import parse_conf_url, OKSKey
    conf_path, conf_type = parse_conf_url('oksconflibs://many_recursive_segments.data.xml')
    controller_id = "controller-3"
    controller_configuration = ControllerConfHandler(
        type = conf_type,
        data = conf_path,
        oks_key = OKSKey(
            schema_file = 'schema/confmodel/dunedaq.schema.xml',
            class_name = "RCApplication",
            obj_uid = controller_id,
            session = "deep-segments-config", # some of the function for enable/disable require the full dal of the session
        ),
    )

    assert(controller_configuration.data.controller.id == controller_id)