from django.db.models import Q
from common.configs.config import config as cfg
from django.template.loader import render_to_string
from common.helpers.auth_helper import get_tokens_for_user
from users.models import User, UserProfiles
from organisation.models import WorkingHours, Setup, Organisations, GeneralSettings
from organisation.serializers import WorkingHourSerializer
import requests
import logging


def checkCustomerPayload(login_type, data, ccode, organisation):
    if login_type == "email":
        users_count = User.objects.filter(
            email=data,
            organisation=organisation,
            is_active=True,
        ).exclude(utype=User.UserTypes.ENDUSER)
        if users_count.count() >= 1:
            return "Email already exists"
    elif login_type == "phone":
        users_count = User.objects.filter(
            phone_number=data,
            ccode=ccode,
            organisation=organisation,
            is_active=True,
        ).exclude(utype=User.UserTypes.ENDUSER)
        if users_count.count() >= 1:
            return "Phone number already exists"
    return None


def getAdminCreationEmailBody(otp, admin_info):
    name = ""
    if admin_info.lname in ["", " ", None]:
        name = admin_info.fname
    else:
        name = admin_info.fname + " " + admin_info.lname
    user_data = {"name": name, "otp": otp}
    template_pdfRenderer = "welcome.html"
    html_string = render_to_string(
        template_name=template_pdfRenderer, context=user_data
    )
    return html_string


def getStaffCreationEmailBody(data, password):
    name = ""
    if data.lname in ["", " ", None]:
        name = data.fname
    else:
        name = data.fname + " " + data.lname
    user_data = {
        "name": name,
        "user_name": data.email,
        "password": password,
        "link": cfg.get("http", "LOGIN_URL"),
    }
    template_pdfRenderer = "staff-creation-credentials.html"
    html_string = render_to_string(
        template_name=template_pdfRenderer, context=user_data
    )
    return html_string


def getForgotPasswordEmailBody(data, code):
    name = ""
    if data.lname in ["", " ", None]:
        name = data.fname
    else:
        name = data.fname + " " + data.lname
    user_data = {
        "name": name,
        "link": cfg.get("http", "RESET_PASSWORD_LINK") + str(data.id) + f"&code={code}",
    }
    template_pdfRenderer = "forgot-password.html"
    html_string = render_to_string(
        template_name=template_pdfRenderer, context=user_data
    )
    return html_string


def getEndUserOTPEmailBody(organisation, otp):
    try:
        org = Organisations.objects.get(id=organisation)
        user_data = {"otp": otp, "organisation_name": org.name}
        template_pdfRenderer = "enduser-otp.html"
        html_string = render_to_string(
            template_name=template_pdfRenderer, context=user_data
        )
        return html_string
    except Exception as err:
        logging.error(f"getEndUserOTPEmailBody exception: {err}", exc_info=True)
        return False


def getAdminEmailPayload(user_data, organisation_data, otp):
    return {
        "type": "EMAIL",  # email,calendar,both
        "message": {
            "to": user_data.email,
            "from": cfg.get("email", "FROM_MAIL"),
            "subject": cfg.get("email", "REGISTER_SUBJECT"),
            "body": getAdminCreationEmailBody(otp, user_data),
        },
        "media_url": "",
        "organisation": str(organisation_data),
        "department": str(organisation_data),
        "source_type": "USER",  # Activity,Form Builder,Appointments,Order,User
        "source_id": str(user_data.id),
        "start_time": "",  # down 3 fields are required when type is calender invite
        "end_time": "",
        "time_zone": "",
        "info": "",
        "from_Staff": True,
    }


def getForgotPasswordEmailPayload(user_data, code):
    return {
        "type": "EMAIL",  # email,calendar,both
        "message": {
            "to": user_data.email,
            "from": cfg.get("email", "FROM_MAIL"),
            "subject": cfg.get("email", "FORGOT_PASSWORD_SUBJECT"),
            "body": getForgotPasswordEmailBody(user_data, code),
        },
        "media_url": "",
        "organisation": str(user_data.organisation),
        "department": "check",
        "source_type": "USER",  # Activity,Form Builder,Appointments,Order,User
        "source_id": str(user_data.id),
        "start_time": "",  # down 3 fields are required when type is calender invite
        "end_time": "",
        "time_zone": "",
        "info": "",
        "from_Staff": True,
    }


def getStaffCreationEmailPayload(staff_info, password):
    return {
        "type": "EMAIL",  # email,calendar,both
        "message": {
            "to": staff_info.email,
            "from": cfg.get("email", "FROM_MAIL"),
            "subject": cfg.get("email", "STAFF_CREATION_SUBJECT"),
            "body": getStaffCreationEmailBody(staff_info, password),
        },
        "media_url": "",
        "organisation": str(staff_info.organisation),
        "department": "check",
        "source_type": "USER",  # Activity,Form Builder,Appointments,Order,User
        "source_id": str(staff_info.id),
        "start_time": "",  # down 3 fields are required when type is calender invite
        "end_time": "",
        "time_zone": "",
        "info": "",
    }


def getEndUserOTPEmailPayload(email, organisation, otp):
    body = getEndUserOTPEmailBody(organisation, otp)
    if body:
        return {
            "type": "EMAIL",  # email,calendar,both
            "message": {
                "to": email,
                "from": cfg.get("email", "FROM_MAIL"),
                "subject": cfg.get("email", "ENDUSER_CREATION_SUBJECT"),
                "body": body,
            },
            "media_url": "",
            "organisation": str(organisation),
            "department": "check",
            "source_type": "USER",  # Activity,Form Builder,Appointments,Order,User
            "source_id": str(organisation),
            "start_time": "",  # down 3 fields are required when type is calender invite
            "end_time": "",
            "time_zone": "",
            "info": "",
            "from_Staff": True,
        }
    return False


def getStaffPayloadForAudit(staff_info):
    try:
        department = UserProfiles.objects.get(
            user=staff_info,
            organisation=staff_info.organisation,
            status=True,
            is_active=True,
        )
        updated_by = ""
        deleted_by = ""
        if staff_info.updated_by != None or staff_info.updated_by == "NULL":
            updated_by = str(staff_info.updated_by)
        if staff_info.deleted_by != None or staff_info.deleted_by == "NULL":
            deleted_by = str(staff_info.deleted_by)
        return {
            "organisation": str(staff_info.organisation),
            "department": str(department.id),
            "source_id": str(staff_info.id),
            "source_type": "user",
            "created_by": str(staff_info.created_by),
            "updated_by": updated_by,
            "deleted_by": deleted_by,
            "staff_id": str(staff_info.id),
        }
    except Exception as err:
        logging.error(f"getStaffPayloadForAudit exception: {err}", exc_info=True)
        return None


def getWorkingHours(organisation):
    working_hours = WorkingHours.objects.filter(
        ref_id=organisation,
        organisation=organisation,
        type=WorkingHours.WorkingHourTypes.ORGANISATION,
    ).order_by("created_at")
    return WorkingHourSerializer(working_hours, many=True).data


def getPayloadForCalendarService(user_info, user_type, timezone=""):
    try:
        admin_id = ""
        if user_type == User.UserTypes.ADMIN:
            department = user_info.organisation
            staff_id = user_info.organisation
            type = "organisation"
            admin_id = str(user_info.id)
        elif user_type == User.UserTypes.STAFF:
            user_profile = UserProfiles.objects.get(
                user=user_info,
                organisation=user_info.organisation,
                status=True,
                is_active=True,
            )
            department = str(user_profile.department.id)
            staff_id = str(user_info.id)
            type = "appointment"
        else:
            return None
        return {
            "type": type,
            "admin_id": admin_id,
            "staff_id": staff_id,
            "time_zone": timezone,
            "organisation": user_info.organisation,
            "department": department,
            "created_by": user_info.created_by,
        }
    except Exception as err:
        logging.error(
            f"getStaffPayloadForCalenderService exception: {err}", exc_info=True
        )
        return None


def getTimezoneUpdatePayloadForCalendarService(type, timezone, organisation, staff_id):
    return {
        "type": type,
        "time_zone": timezone,
        "organisation": organisation,
        "staff_id": staff_id,
    }


def makeCalendarServiceCall(user_info, token):
    if token is None:
        url = cfg.get("http", "CALENDAR_POST_OPEN_API")
        payload = {
            "staff_id": str(user_info.id),
            "working_hours": getWorkingHours(user_info.organisation),
        }
        resp = requests.post(url, data=payload)
        if resp.status_code != 201:
            return False
    headers = {"Authorization": token}
    url = cfg.get("http", "CALENDAR_POST")
    payload = {
        "staff_id": str(user_info.id),
        "working_hours": getWorkingHours(user_info.organisation),
    }
    resp = requests.post(url=url, json=payload, headers=headers)
    if resp.status_code != 201:
        return False


def getContactPayloadForCrmService(user_data):
    try:
        admin = User.objects.get(
            is_active=True,
            status=True,
            utype=User.UserTypes.ADMIN,
            organisation=user_data.organisation,
        )
        # TODO: Adding admin token because with enduser token permission issues will come need to modify in future
        token = get_tokens_for_user(
            admin, {"organisation": admin.organisation, "utype": admin.utype}
        )
        last_name = ""
        if user_data.lname not in ["", " ", None]:
            last_name = user_data.lname
        return {
            "user_id": str(user_data.id),
            "first_name": user_data.fname,
            "last_name": last_name,
            "phone": user_data.phone_number,
            "email": user_data.email,
            "organisation": user_data.organisation,
            "department": user_data.organisation,
            "owner": str(admin.id),
            "ccode": user_data.ccode,
            "token": "Bearer " + token["access"],
        }
    except Exception as err:
        logging.error(f"getContactPayloadForCrmService exception: {err}", exc_info=True)
        return None


def checkSlugName(name):
    if not name.isalnum():
        return False
    if not name.islower():
        return False
    if not name[0].isalpha():
        return False
    return True


def insertSetupData(organisation_id, user_id):
    setup_data = [
        {
            "name": cfg.get("setup", "APPOINTMENTS_SETUP_NAME"),
            "description": cfg.get("setup", "APPOINTMENTS_SETUP_DESCRIPTION"),
            # "image": cfg.get("setup", "APPOINTMENTS_SETUP_IMAGE"),
            "image": "https://workes3bucket.s3.amazonaws.com/image-62bfc2bf-d0a7-4e55-89b2-5901817e0006-1685364523.svg%2Bxml",
            "route_link": cfg.get("setup", "APPOINTMENTS_SETUP_ROUTE_LINK"),
        },
        {
            "name": cfg.get("setup", "MEETINGS_SETUP_NAME"),
            "description": cfg.get("setup", "MEETINGS_SETUP_DESCRIPTION"),
            # "image": cfg.get("setup", "MEETINGS_SETUP_IMAGE"),
            "image": "https://workes3bucket.s3.amazonaws.com/image-7db8362e-86fe-43d5-8495-24c6b3858aef-1685364793.svg%2Bxml",
            "route_link": cfg.get("setup", "MEETINGS_SETUP_ROUTE_LINK"),
        },
        {
            "name": cfg.get("setup", "PRODUCTS_AND_SERVICES_SETUP_NAME"),
            "description": cfg.get("setup", "PRODUCTS_AND_SERVICES_SETUP_DESCRIPTION"),
            # "image": cfg.get("setup", "PRODUCTS_AND_SERVICES_SETUP_IMAGE"),
            "image": "https://workes3bucket.s3.amazonaws.com/image-be154307-1572-4f88-8f96-7c71daaf1435-1685364885.svg%2Bxml",
            "route_link": cfg.get("setup", "PRODUCTS_AND_SERVICES_SETUP_ROUTE_LINK"),
        },
        {
            "name": cfg.get("setup", "SMARTPOP_UPS_SETUP_NAME"),
            "description": cfg.get("setup", "SMARTPOP_UPS_SETUP_DESCRIPTION"),
            # "image": cfg.get("setup", "SMARTPOP_UPS_SETUP_IMAGE"),
            "image": "https://workes3bucket.s3.amazonaws.com/image-bc061e49-ae9f-45dc-9163-bbfc46b65e44-1685364837.svg%2Bxml",
            "route_link": cfg.get("setup", "SMARTPOP_UPS_SETUP_ROUTE_LINK"),
        },
        {
            "name": cfg.get("setup", "FORM_BUILDER_SETUP_NAME"),
            "description": cfg.get("setup", "FORM_BUILDER_SETUP_DESCRIPTION"),
            # "image": cfg.get("setup", "FORM_BUILDER_SETUP_IMAGE"),
            "image": "https://workes3bucket.s3.amazonaws.com/image-4a747213-6534-4888-a1eb-9c41a1a51c28-1685364672.svg%2Bxml",
            "route_link": cfg.get("setup", "FORM_BUILDER_SETUP_ROUTE_LINK"),
        },
        {
            "name": cfg.get("setup", "BOT_SETUP_NAME"),
            "description": cfg.get("setup", "BOT_SETUP_DESCRIPTION"),
            # "image": cfg.get("setup", "BOT_SETUP_IMAGE"),
            "image": "https://workes3bucket.s3.amazonaws.com/image-b59a323b-db36-4985-80bb-513c47324056-1685364601.svg%2Bxml",
            "route_link": cfg.get("setup", "BOT_SETUP_ROUTE_LINK"),
        },
        {
            "name": cfg.get("setup", "KNOWLEDGE_BASE_SETUP_NAME"),
            "description": cfg.get("setup", "KNOWLEDGE_BASE_SETUP_DESCRIPTION"),
            # "image": cfg.get("setup", "KNOWLEDGE_BASE_SETUP_IMAGE"),
            "image": "https://workes3bucket.s3.amazonaws.com/image-fe130ab0-b58b-4e95-ad64-a75fe5e8875b-1685364729.svg%2Bxml",
            "route_link": cfg.get("setup", "KNOWLEDGE_SETUP_ROUTE_LINK"),
        },
        {
            "name": cfg.get("setup", "ANNOUNCEMENTS_SETUP_NAME"),
            "description": cfg.get("setup", "ANNOUNCEMENTS_SETUP_DESCRIPTION"),
            # "image": cfg.get("setup", "ANNOUNCEMENTS_SETUP_IMAGE"),
            "image": "https://workes3bucket.s3.amazonaws.com/image-8ca15636-9cd0-403c-ab88-182b7cd0f81f-1685364400.svg%2Bxml",
            "route_link": cfg.get("setup", "ANNOUNCEMENTS_SETUP_ROUTE_LINK"),
        },
        {
            "name": cfg.get("setup", "AUTOMATION_SETUP_NAME"),
            "description": cfg.get("setup", "AUTOMATION_SETUP_DESCRIPTION"),
            # "image": cfg.get("setup", "ANNOUNCEMENTS_SETUP_IMAGE"),
            "image": "https://workes3bucket.s3.amazonaws.com/image-8ca15636-9cd0-403c-ab88-182b7cd0f81f-1685364400.svg%2Bxml",
            "route_link": cfg.get("setup", "AUTOMATION_SETUP_ROUTE_LINK"),
        },
    ]
    set_up_list = []
    for data in setup_data:
        set_up_list.append(
            Setup(
                name=data["name"],
                description=data["description"],
                image=data["image"],
                route_link=data["route_link"],
                status=False,
                organisation=organisation_id,
                created_by=user_id,
            )
        )
    Setup.objects.bulk_create(set_up_list)


def getPipelineCreationPayload(user_data):
    return {"user": str(user_data.id), "organisation": user_data.organisation}


def getActivityCreationPayload(user_data):
    return {
        "organisation": user_data.organisation,
        "department": user_data.organisation,
        "created_by": str(user_data.id),
        "info": {},
    }
