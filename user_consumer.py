import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.settings")
import django

django.setup()


import pika
from common.configs.config import config as cfg
from common.events.consumers.user_service_consumer import (
    clientServiceCallback,
    consultationServiceCallback,
)
from BaseWorke.middlewares.new_relic_middleware import get_logger


logger = get_logger()


credentials = pika.PlainCredentials(
    cfg.get("rabbit_mq", "USER_NAME"), cfg.get("rabbit_mq", "PASSWORD")
)
parameters = pika.ConnectionParameters(
    host=cfg.get("rabbit_mq", "HOST"),
    virtual_host=cfg.get("rabbit_mq", "VIRTUAL_HOST"),
    credentials=credentials,
    frame_max=int(cfg.get("rabbit_mq", "FRAME_MAX")),
    heartbeat=int(cfg.get("rabbit_mq", "HEART_BEAT")),
    connection_attempts=int(cfg.get("rabbit_mq", "CONNECTION_ATTEMPTS")),
)
conn = pika.BlockingConnection(parameters)


while True:
    try:
        channel = conn.channel()

        # Client Service Consumer
        channel.exchange_declare(
            exchange=cfg.get("events", "CLIENT_EXCHANGE"),
            exchange_type="topic",
            durable=True,
        )
        result = channel.queue_declare(
            cfg.get("events", "CLIENT_QUEUE_NAME"), durable=True
        )
        queue_name = result.method.queue
        channel.queue_bind(
            exchange=cfg.get("events", "CLIENT_EXCHANGE"),
            queue=queue_name,
            routing_key=cfg.get("events", "CLIENT_CREATE_ROUTING_KEY"),
        )
        channel.basic_consume(
            queue=queue_name, on_message_callback=clientServiceCallback, auto_ack=True
        )

        # Consultation Service Consumer
        channel.exchange_declare(
            exchange=cfg.get("events", "APPOINTMENT_SERVICE_EXCHANGE"),
            exchange_type="topic",
            durable=True,
        )
        result = channel.queue_declare(
            cfg.get("events", "APPOINTMENT_QUEUE_NAME"), durable=True
        )
        queue_name = result.method.queue
        channel.queue_bind(
            exchange=cfg.get("events", "APPOINTMENT_SERVICE_EXCHANGE"),
            queue=queue_name,
            routing_key=cfg.get("events", "APPOINTMENT_USER_CREATE_ROUTING_KEY"),
        )
        channel.basic_consume(
            queue=queue_name,
            on_message_callback=consultationServiceCallback,
            auto_ack=True,
        )

        try:
            logger.info(f"/users service consumer is started")
            channel.start_consuming()
        except KeyboardInterrupt:
            channel.stop_consuming()
            conn.close()
            break
    except pika.exceptions.ConnectionClosedByBroker:
        # Uncomment this to make the example not attempt recovery
        # from server-initiated connection closure, including
        # when the node is stopped cleanly
        #
        # break
        continue
    # Do not recover on channel errors
    except pika.exceptions.AMQPChannelError as err:
        logger.info(f"{err}")
        break
    # Recover on all other connection errors
    except pika.exceptions.AMQPConnectionError:
        continue
