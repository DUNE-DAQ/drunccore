import getpass
import logging
import threading

from drunc_messages.broadcast_pb2 import BroadcastType
from drunc_messages.generic_pb2 import PlainText
from google.protobuf import text_format
from kafka import KafkaConsumer

from drunc_core.broadcast.client.broadcast_handler_implementation import (
    BroadcastHandlerImplementation,
)
from drunc_core.broadcast.utils import (
    broadcast_types_loglevels,
    get_broadcast_level_from_broadcast_type,
)
from drunc_core.utils.grpc_utils import unpack_any
from drunc_core.utils.utils import get_random_string, now_str


class KafkaStdoutBroadcastHandler(BroadcastHandlerImplementation):
    def __init__(self, message_format, conf):
        self.broadcast_types_loglevels = (
            broadcast_types_loglevels  # in this case, we stick with default
        )
        self.conf = conf

        self.kafka_address = self.conf.data.address
        self.topic = self.conf.data.topic

        self.message_format = message_format

        self._log = logging.getLogger("Broadcast")

        group_id = f"drunc-stdout-broadcasthandler-{getpass.getuser()}-{now_str(True)}-{get_random_string(5)}"

        self.consumer = KafkaConsumer(
            self.topic,
            client_id="run_control",
            bootstrap_servers=[self.kafka_address],
            group_id=group_id,
        )

        self.run = True

        self.thread = threading.Thread(target=self.consume)
        self.thread.start()

    def stop(self):
        self._log.info(f"Stopping listening to '{self.topic}'")
        self.run = False
        self.thread.join()

    def consume(self):
        while self.run:
            for messages in self.consumer.poll(timeout_ms=500).values():
                for message in messages:
                    decoded = ""
                    try:
                        decoded = self.message_format()
                        decoded.ParseFromString(message.value)
                        self._log.debug(f"{decoded=}, {type(decoded)=}")
                    except Exception as e:
                        self._log.error(
                            f"Unhandled broadcast message: {message} (error: {e!s})"
                        )
                        pass

                    try:
                        if decoded.data.Is(PlainText.DESCRIPTOR):
                            txt = unpack_any(decoded.data, PlainText).text
                        else:
                            txt = decoded.data

                        bt = BroadcastType.Name(decoded.type)

                        get_broadcast_level_from_broadcast_type(
                            decoded.type, self._log, self.broadcast_types_loglevels
                        )(f"'{bt}' {txt}")

                    except Exception as e:
                        self._log.error(
                            f"Weird broadcast message: {message} (error: {e!s})"
                        )
                        text_proto = text_format.MessageToString(decoded)
                        self._log.info(text_proto)
                        pass
