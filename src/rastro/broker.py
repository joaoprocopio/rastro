from taskiq import AsyncBroker, ZeroMQBroker, async_shared_broker

from rastro.settings import Settings


def create_broker(settings: Settings) -> AsyncBroker:
    # The process that sends tasks binds the publish address, and a worker connects.
    broker = ZeroMQBroker(
        zmq_pub_host=settings.zeromq_publish_address,
        zmq_sub_host=settings.zeromq_subscribe_address,
    )
    # Tasks declare themselves on the shared broker, so they never import this module.
    async_shared_broker.default_broker(broker)
    return broker
