from logging import getLogger

from druncmessages.broadcast_pb2 import BroadcastMessage

from drunccore.broadcast.client.configuration import BroadcastClientConfHandler
from drunccore.broadcast.client.kafka_stdout_broadcast_handler import (
    KafkaStdoutBroadcastHandler,
)
from drunccore.broadcast.types import BroadcastTypes


class BroadcastHandler:
    def __init__(self, broadcast_configuration: BroadcastClientConfHandler):
        super().__init__()

        self.log = getLogger("BroadcastHandler")

        self.configuration = broadcast_configuration
        self.implementation = None

        match self.configuration.data.type:
            # Being a bit sloppy here, having a Kafka sender doesn't mean we want to dump everything to stdout
            # There could be cases where we want to do other things.
            # For now, 1 server type <-> 1 client type...
            # Maybe in the future some sort of callback-based functionality would be preferable.
            case BroadcastTypes.Kafka:
                self.implementation = KafkaStdoutBroadcastHandler(
                    message_format=BroadcastMessage, conf=self.configuration
                )
            case _:
                self.log.info(
                    "Could not understand the BroadcastHandler technology you want to use, you will get no broadcast!"
                )

    def stop(self):
        if self.implementation:
            self.implementation.stop()
