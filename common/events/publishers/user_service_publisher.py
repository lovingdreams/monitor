import pika, json
from common.configs.config import config as cfg
from BaseWorke.middlewares.new_relic_middleware import get_logger


logger = get_logger()


def publish_event(message, exchange_name, routing_key):
    try:
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
        channel = conn.channel()
        channel.exchange_declare(
            exchange=exchange_name, exchange_type="topic", durable=True
        )
        channel.basic_publish(
            exchange=exchange_name, routing_key=routing_key, body=json.dumps(message)
        )
        logger.info(
            f"/users published to--> "
            + exchange_name
            + " "
            + "RoutingKey--> "
            + routing_key
            + " "
            + "Payload--> "
            + str(message)
        )
        conn.close()
        return True
    except Exception as err:
        logger.info(
            f"/users publish Failed—> "
            + {exchange_name}
            + "RoutingKey--> "
            + f"{routing_key}"
        )
        return False
