import random, string, uuid, re
import pika, json
import logging
from common.helpers.modules import (
    check_manager_create_modules,
    check_manager_update_modules,
    check_staff_create_modules,
    check_agent_create_modules,
    check_staff_common_modules,
    check_staff_update_modules,
    check_agent_update_modules,
)
from common.configs.config import config as cfg

from common.events.subscrider.send_email_subscriber import send_email_async


def random_string_generator(N, otp_type="alphanumeric"):
    if otp_type == "alpha":
        data_type = string.ascii_uppercase
    elif otp_type == "numeric":
        data_type = string.digits
    else:
        data_type = string.ascii_uppercase + string.digits

    return "".join(random.SystemRandom().choice(data_type) for _ in range(N))


def get_variables(data, values, default_value=None):
    return [data.get(key, default_value) for key in values]


def send_mail(message, routing_key, exchange_name):
    # def send_mail(email, code, user="1", subject="Registration"):
    # send_email_async.delay(code, email, user, subject)
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
        logging.info(f"conn: {conn}")
        channel = conn.channel()
        channel.exchange_declare(exchange=exchange_name, exchange_type="topic")
        channel.basic_publish(
            exchange=exchange_name, routing_key=routing_key, body=json.dumps(message)
        )
        conn.close()
        return True
    except Exception as err:
        logging.error(f"clientServiceCallback exception: {err}", exc_info=True)
        return None


def is_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


def not_uuid(val):
    try:
        uuid.UUID(str(val))
        return False
    except ValueError:
        return True


def check_mail(email):
    regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,10}\b"
    if re.fullmatch(regex, email):
        return True
    else:
        return False


def check_number(number):
    regex = r"\b[0-9+]{6,14}\b"
    if re.fullmatch(regex, number):
        return True
    else:
        return False


def get_type(path):
    permission_type = path.split("/")[1]
    return permission_type


def check_end_user_permissions(request):
    if request.method in ["GET", "POST", "PUT", "DELETE"]:
        if (
            "/users/profile/address/" in request.path
            or "/users/aws_utils/pre_signed_url/" in request.path
        ):
            return True
        elif (
            request.method in ["GET", "POST"] and "/users/profile/info/" == request.path
        ):
            return True
        elif (
            request.method in ["GET"]
            and "/users/organisation/price_settings/" == request.path
        ):
            return True
    return False


def check_staff_permissions(request):
    if request.method in ["OPTIONS", "HEAD"]:
        return True
    elif check_staff_common_modules(request):
        return True
    elif request.data.get("role") == cfg.get("user_types", "MANAGER"):
        if request.method == "GET":
            return True
        elif request.method == "POST":
            return check_manager_create_modules(request.path)
        elif request.method == "PUT" or request.method == "PATCH":
            return check_manager_update_modules(request.path)
        return False
    elif request.data.get("role") == cfg.get("user_types", "STAFF"):
        if request.method in ["GET"]:
            return True
        elif request.method in ["POST"]:
            return check_staff_create_modules(request.path)
        elif request.method == "PUT" or request.method == "PATCH":
            return check_staff_update_modules(request.path)
    elif request.data.get("role") == cfg.get("user_types", "AGENT"):
        if request.method in ["GET"]:
            return True
        elif request.method in ["POST"]:
            return check_agent_create_modules(request.path)
        elif request.method == "PUT" or request.method == "PATCH":
            return check_agent_update_modules(request.path)
    return False
