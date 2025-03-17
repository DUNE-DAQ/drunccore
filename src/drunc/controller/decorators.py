from functools import wraps

from druncschema.generic_pb2 import PlainText
from druncschema.request_response_pb2 import Response, ResponseFlag
from druncschema.addressed_command_pb2 import AddressedCommand
from drunc.utils.grpc_utils import pack_to_any
from drunc.controller.utils import address_command

def in_control(cmd):
    @wraps(cmd)
    def wrap(obj, request):
        if not obj.actor.token_is_current_actor(request.token):
            return Response(
                name=obj.name,
                token=request.token,
                data=pack_to_any(
                    PlainText(
                        text=f"User {request.token.user_name} is not in control of {obj.__class__.__name__}",
                    )
                ),
                flag=ResponseFlag.NOT_EXECUTED_NOT_IN_CONTROL,
                children=[],
            )
        return cmd(obj, request)

    return wrap

def unpack_addressed_command_to(cmd, data_type=None, pass_token=False):
    def decor(cmd):
        @wraps(cmd)
        def wrap(obj, request):
            try:
                command = unpack_any(request.data, AddressedCommand)
            except UnpackingError as e:
                return Response(
                    name=obj.name,
                    token=request.token,
                    data=PlainText(text=str(e)),
                    flag=ResponseFlag.NOT_EXECUTED_BAD_REQUEST_FORMAT,
                    children=[],
                )

            try:
                addressed_commands = address_command(
                    obj=obj,
                    command=command.data,
                    target=command.target,
                    execute_along_path=command.execute_along_path,
                    execute_on_all_subsequent_children_in_path=command.execute_on_all_subsequent_children_in_path
                )
            except DruncCommandException as e:
                return Response(
                    name=obj.name,
                    token=request.token,
                    data=PlainText(text=str(e)),
                    flag=ResponseFlag.FAILED,
                    children=[],
                )
            payload = None
            if data_type is not None:
                try:
                    payload = unpack_any(command.data, data_type)
                except UnpackingError as e:
                    return Response(
                        name=obj.name,
                        token=request.token,
                        data=PlainText(text=str(e)),
                        flag=ResponseFlag.NOT_EXECUTED_BAD_REQUEST_FORMAT,
                        children=[],
                    )

            kwargs = {}
            if pass_token:
                kwargs = {"token": request.token}

            if payload is not None:
                ret = cmd(obj, data, addressed_commands, **kwargs)
            else:
                ret = cmd(obj, addressed_commands, **kwargs)

            return ret

        return wrap

    return decor
