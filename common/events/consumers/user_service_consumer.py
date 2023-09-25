import pika, json
from common.configs.config import config as cfg
from common.grpc.actions.crm_action import getContactInfo
from common.helpers.user_helper import createUser, getUserInfo, getAppointmentPayload
from common.events.http.api_call import makeContactInfoAPICall
from common.events.publishers.user_service_publisher import publish_event
from BaseWorke.middlewares.new_relic_middleware import get_logger


logger = get_logger()


def clientServiceCallback(ch, method, properties, body):
    try:
        json_body = json.loads(body)
        logger.info(f"/users user data ---->{json_body}")
        contact_info = getContactInfo(
            json_body["contact_id"], json_body["department"], json_body["organisation"]
        )
        if contact_info is None:
            # Make http call here
            contact_info = makeContactInfoAPICall(
                json_body["contact_id"], json_body["department"], json_body["token"]
            )
            if contact_info is None:
                # Handle the case
                pass
        if not contact_info is None:
            user_creation_status = createUser(contact_info, json_body["source_id"])
            if not user_creation_status:
                # Handle the case
                pass
        else:
            # Handle the failed case
            logger.info(
                f"/users failed to fetch contact information",
                exc_info=True,
            )
            pass
    except Exception as err:
        logger.info(
            f"/users user creation faild exception : {err}",
            exc_info=True,
        )
        pass


def consultationServiceCallback(ch, method, properties, body):
    try:
        json_body = json.loads(body)
        logger.info(f"/users user data ---->{json_body}")
        user_id = getUserInfo(json_body)
        if user_id != None:
            event_status = publish_event(
                getAppointmentPayload(user_id, json_body),
                cfg.get("events", "CONSULTATION_SERVICE_EXCHANGE"),
                cfg.get("events", "APPOINTMENT_USER_UPDATE_ROUTING_KEY"),
            )
            if not event_status:
                # Handle the failed case
                logger.info(
                    f"/users failed to publish user id to consultation service",
                    exc_info=True,
                )
                pass
        else:
            # Handle the failed case
            logger.info(
                f"/users failed to fetch user information",
                exc_info=True,
            )
    except Exception as err:
        logger.info(
            f"/users user creation faild exception : {err}",
            exc_info=True,
        )
        pass
