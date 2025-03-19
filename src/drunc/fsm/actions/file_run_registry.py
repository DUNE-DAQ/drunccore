import os

from daqconf.consolidate import consolidate_db

from drunc.fsm.core import FSMAction


class FileRunRegistry(FSMAction):
    def __init__(self, configuration):
        super().__init__(name="file-run-registry")
        self.configuration = configuration

    def pre_start(self, _input_data, _context, **kwargs):
        run_number = _input_data["run"]
        dest = os.getcwd() + "/run_conf" + str(run_number) + ".data.xml"
        consolidate_db(_context.configuration.initial_data.split(":")[1], f"{dest}")

        return _input_data
