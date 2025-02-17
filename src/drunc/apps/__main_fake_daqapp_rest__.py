'''
This is a fake DAQ application that doesn't do anything, but should talk in the same way to the run control
'''

import argparse
import copy as cp
from flask import Flask, Response, request
from flask_restful import Api, Resource
import random
import requests
import signal
import threading
import time
from urllib.parse import urlparse

from drunc.connectivity_service.client import ConnectivityServiceClient
from drunc.utils.utils import get_logger, get_new_port, setup_root_logger, setup_standard_loggers

__version__='1.0.0'

# Logger

class AppState:
    def __init__(self, app_name:str):
        self.appname = app_name
        self.state = 'INITIAL'
        self.executing_command = False

    def send_response(self, address:str, txt:str, success:bool=True, data:dict={}):
        try:
            requests.post(
                address,
                data = {
                    'success': success,
                    'result': txt,
                    'appname': self.appname,
                    'data': data,
                }
            )
        except Exception as e:
            log = get_logger("fake_daqapp_rest.AppState")
            log.error(f'Couldn\'t send response to response listener')
            log.exception(e)

    def execute_command(self, req_data, answer_port, answer_host, remote_host) -> Response:
        reply_address = f'{answer_host}:{answer_port}/response' if answer_host else f'{remote_host}:{answer_port}/response'

        entry_state = req_data['entry_state']
        exit_state  = req_data['exit_state']
        command_id  = req_data['id']
        data        = req_data.get('data', {})
        log = get_logger("fake_daqapp_rest.AppState")

        if self.executing_command:
            response_txt = 'Already executing a command!!'
            log.info(response_txt)
            self.send_response(
                address = reply_address,
                txt = response_txt,
                success = False,
            )
            return

        time_spent = data.get('execution-time', random.randint(1, 10))

        worries = random.randint(0, time_spent)

        if entry_state != '*' and self.state != entry_state.upper():
            info = f'DAQ Application is in state {self.state} and command {command_id} requires to be in state {entry_state.upper()} to execute. Not executing'
            log.info(info)
            self.send_response(
                success = False,
                address = reply_address,
                txt = info,
            )
            return

        log.info(f'Executing {command_id}')

        self.executing_command = True

        if data.get('seg_fault'):
            time.sleep(worries)
            info = '<seeeeeeeeeg fauuuuuuuult message>'
            log.info(info)
            self.send_response(
                success = False,
                address = reply_address,
                txt = info,
            )
            self.executing_command = False
            exit(data['seg_fault'])

        if data.get('throw'):
            time.sleep(worries)
            what = 'This is an eRrOr, YoU hAvE bEeN vErY nAuGhTy (aka task failed successfully)',
            log.info(what)
            self.send_response(
                success = False,
                address = reply_address,
                txt = what,
            )
            self.executing_command = False
            return



        time.sleep(time_spent)
        info = f'Executed {command_id} successfully'
        self.send_response(
            success = True,
            address = reply_address,
            txt = info,
        )
        self.state = exit_state.upper()
        self.executing_command = False
        return

app_state = AppState('unknown')

'''
Resources for Flask app
'''
class AppCommand(Resource):
    def post(self):
        try:
            data = request.get_json(force=True)
        except:
            return "Not a JSON command!\n", 406
        log = get_logger("fake_daqapp_rest.AppCommand")
        log.debug(f'GET request with args: {data}')
        thread = threading.Thread(
            target = app_state.execute_command,
            kwargs = {
                'req_data'   : cp.deepcopy(data),
                'answer_port': request.headers['X-Answer-Port'],
                'answer_host': request.headers.get('X-Answer-Host'),
                'remote_host': request.remote_addr,
            }
        )
        thread.start()

        return "Command received\n", 202

def get_address_for_conn_srv(hostname):
    return f"rest://{hostname}:{get_new_port()}"

'''
Main flask app
'''
app = Flask(__name__)
api = Api(app)
api.add_resource(AppCommand, "/command", methods=['POST'])

def update_connectivity_service(
    name,
    connectivity_service,
    interval
):
    while True:
        connectivity_service.publish(
            name + "_control",
            connectivity_service.address,
            'RunControlMessage',
        )
        time.sleep(interval)

@app.route('/')
def index():
  return f'Fake DAQ app v{__version__}'


def main():
    parser = argparse.ArgumentParser(
        prog = 'FakeApplication',
        description = 'This is a fake application that communicate in the same way with the RunControl as the DAQApplication (thru REST)',
    )
    parser.add_argument('-n', '--name',                 required=True,              help='The name of the app in the response')
    parser.add_argument('-d', '--configurationService', required=True,              help='This is a dummy argument in this case')
    parser.add_argument('-c', '--commandFacility',      required=False,             help='Where the fake app should get its command from')
    parser.add_argument('-i', '--informationService',   default='stdout://flat',    help='This is a dummy argument in this case')
    parser.add_argument('-l', '--log_level',            default="info",             help='Logging level minimum threshold')
    parser.add_argument('-p', '--partition',            default='global',           help='This is a dummy argument in this case')
    parser.add_argument('-s', '--session',              default="test",             help='name of session')
    args = parser.parse_args()

    name = args.name
    app_state.app_name = name

    root_logger = setup_root_logger(args.log_level)
    setup_standard_loggers()
    log = get_logger(
        "fake_daqapp_rest",
        rich_handler=True
    )

    if not args.commandFacility:
        log.error("No command facility passed, exiting")
        exit(1)

    url = urlparse(args.commandFacility)
    if urlparse(url).scheme != "rest":
        log.exception("DAQApplication communication scheme must be rest")
        exit(1)

    log.debug(f"Initializing fake_daq_application with address {url}")
    if (url.port == 0):
        url = get_address_for_conn_srv(url.hostname)
    log.info(f"Communication address is {url}")

    interval = 2
    connectivity_service = ConnectivityServiceClient(
        session=name,
        address=url,
    )
    connectivity_service_thread = threading.Thread(
        target = update_connectivity_service,
        args = (name, connectivity_service, interval),
        name = 'connectivity_service_updating_thread'
    )

    def terminate(signum, sigframe):
        connectivity_service_thread.join()
    for sig in [signal.SIGINT, signal.SIGHUP, signal.SIGTERM, signal.SIGQUIT]:
        signal.signal(sig, terminate)

    # connectivity_service_thread.start()
    log.info(f"Starting FakeDAQ app on {url}, communicating through rest://{url.hostname}:{url.port}")
    # app.run(host=url.hostname, port=url.port, debug=True)

if __name__ == '__main__':
    main()
