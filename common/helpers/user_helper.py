from users.models import User
from common.events.publishers.user_service_publisher import publish_event
from common.configs.config import config as cfg
from BaseWorke.middlewares.new_relic_middleware import get_logger


logger = get_logger()


def getUserPayload(user, source_id):
    return {
        "organisation": str(user.organisation),
        "client_id": str(source_id),
        "user_id": str(user.id),
    }


def createUser(data, client_id):
    try:
        user = User.objects.get(
            email=data["email"],
            organisation=data["organisation"],
            # phone_number=data["phone_number"],
        )
        user.fname = data["first_name"]
        user.lname = data["last_name"]
        user.phone_number = data["phone_number"]
        user.save()
        event_status = publish_event(
            getUserPayload(user, client_id),
            cfg.get("events", "USER_EXCHANGE"),
            cfg.get("events", "USER_CREATE_ROUTING_KEY"),
        )
        if not event_status:
            logger.info(
                f"/users user data publishing is failed",
                exc_info=True,
            )
            return False
        return True
    except Exception:
        pass

    try:
        user = User(
            fname=data["first_name"],
            lname=data["last_name"],
            email=data["email"],
            username=(
                data["email"].split("@")[0]
                + "--ENDUSER--"
                + data["organisation"]
                + "@"
                + data["email"].split("@")[1]
            ),
            utype=User.UserTypes.ENDUSER,
            phone_number=data["phone_number"],
            organisation=data["organisation"],
        )
        user.save()
        logger.info(f"/users User Created")
        event_status = publish_event(
            getUserPayload(user, client_id),
            cfg.get("events", "USER_EXCHANGE"),
            cfg.get("events", "USER_CREATE_ROUTING_KEY"),
        )
        if not event_status:
            logger.info(
                f"/users user data publishing is failed",
                exc_info=True,
            )
            return False
        return True
    except Exception as err:
        logger.info(
            f"/users user creation faild exception : {err}",
            exc_info=True,
        )
        return False


def getAdminCreationPayload(organisation_id, role):
    return {"organisation": organisation_id, "role": role}


def getUserInfo(data):
    try:
        print("data --->", data)
        user = User.objects.get(
            email=data["email"],
            organisation=data["organisation"],
        )
        user.fname = data["fname"]
        user.lname = data["lname"]
        user.phone_number = data["phone_number"]
        user.ccode = data["ccode"]
        user.save()
    except Exception as err:
        print("Exception 99 --->", err)
        try:
            user = User(
                fname=data["fname"],
                lname=data["lname"],
                email=data["email"],
                username=(
                    data["email"].split("@")[0]
                    + "--ENDUSER--"
                    + data["organisation"]
                    + "@"
                    + data["email"].split("@")[1]
                ),
                utype=User.UserTypes.ENDUSER,
                phone_number=data["phone_number"],
                organisation=data["organisation"],
            )
            user.save()
        except Exception as err:
            print("getUserInfo exception --->", err)
            return None
    return str(user.id)


def getAppointmentPayload(user_id, data):
    return {
        "user_id": str(user_id),
        "source_id": data["source_id"],
        "organisation": data["organisation"],
        "token": data["token"],
    }
