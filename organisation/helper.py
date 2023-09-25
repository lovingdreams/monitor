import pytz
from datetime import datetime
from common.configs.config import config as cfg
from users.models import UserProfiles, User
from organisation.models import Tags
from organisation.models import Badge
from common.data.static import (
    default_staff_badges_data,
    default_appointment_badges_data,
    default_product_badges_data,
)


def getDeletedTime():
    # In future get timezone from Company settings
    time_zone = pytz.timezone(cfg.get("common", "TIME_ZONE"))
    return datetime.now(time_zone)


def getSerializerError(errors):
    if "non_field_errors" in errors:
        for error in errors["non_field_errors"]:
            return error
    if "organisation" in errors:
        return "Organisation is mandatory"
    if "created_by" in errors:
        return "Created by is mandatory"
    return "Something went wrong"


def check_name(name):
    name = name.strip()
    if not name[0].isalpha():
        return True
    elements = name.split(" ")
    for element in elements:
        if element.isnumeric():
            return True
        if not element.isalnum():
            return True
    return False


def check_tag_type(type):
    if type not in [
        Tags.TagTypes.CLIENT,
        Tags.TagTypes.CLIENT_PROJECTS,
        Tags.TagTypes.COMPANIES,
        Tags.TagTypes.CONTACTS,
        Tags.TagTypes.ENQUIRIES,
        Tags.TagTypes.PIPELINES,
    ]:
        return True
    return False


def check_badge_type(type):
    if type not in [
        Badge.BadgeTypes.APPOINTMENT,
        Badge.BadgeTypes.STAFF,
        Badge.BadgeTypes.PRODUCTS,
    ]:
        return True
    return False


def insert_default_badges(organisation, user_id):
    try:
        default_badges_list = []
        for data in default_staff_badges_data:
            default_badges_list.append(
                Badge(
                    name=data.get("name"),
                    colour=data.get("colour"),
                    text_colour=data.get("text_colour"),
                    type=data.get("type"),
                    created_by=user_id,
                    organisation=organisation,
                )
            )
        for data in default_appointment_badges_data:
            default_badges_list.append(
                Badge(
                    name=data.get("name"),
                    colour=data.get("colour"),
                    text_colour=data.get("text_colour"),
                    type=data.get("type"),
                    created_by=user_id,
                    organisation=organisation,
                )
            )
        for data in default_product_badges_data:
            default_badges_list.append(
                Badge(
                    name=data.get("name"),
                    colour=data.get("colour"),
                    text_colour=data.get("text_colour"),
                    type=data.get("type"),
                    created_by=user_id,
                    organisation=organisation,
                )
            )
        Badge.objects.bulk_create(default_badges_list)
        return default_badges_list
    except Exception:
        return False


def getAuditPayloadForSetp(setup_obj, role, user_id):
    try:
        action = "disabled"
        if setup_obj.status:
            action = "enabled"
        department = setup_obj.organisation
        if role in [
            cfg.get("user_types", "STAFF"),
            cfg.get("user_types", "AGENT"),
            cfg.get("user_types", "MANAGER"),
        ]:
            user_profile = UserProfiles.objects.get(
                organisation=setup_obj.organisation,
                user=user_id,
            )
            department = str(user_profile.department)
        return {
            "organisation": setup_obj.organisation,
            "department": department,
            "action": action,
            "user_id": user_id,
            "source": setup_obj.name,
        }
    except Exception:
        return False


def getUsersActiveCount(manager_profile, data):
    users_list = (
        UserProfiles.objects.filter(
            department=manager_profile.department, role=data["id"]
        )
        .select_related("user")
        .filter(user__status=True)
        .values_list("user__id")
    )
    return User.objects.filter(id__in=users_list).count()


def getUsersActiveCount(manager_profile, data):
    users_list = (
        UserProfiles.objects.filter(
            department=manager_profile.department, role=data["id"]
        )
        .select_related("user")
        .filter(user__status=True)
        .values_list("user__id")
    )
    return User.objects.filter(id__in=users_list).count()


def getUsersInactiveCount(manager_profile, data):
    users_list = (
        UserProfiles.objects.filter(
            department=manager_profile.department, role=data["id"]
        )
        .select_related("user")
        .filter(user__status=False)
        .values_list("user__id")
    )
    return User.objects.filter(id__in=users_list).count()


def getUsersActiveCountForAdmin(data):
    users_list = (
        UserProfiles.objects.filter(role=data["id"])
        .select_related("user")
        .filter(user__status=True)
        .values_list("user__id")
    )
    return User.objects.filter(id__in=users_list).count()


def getUsersInactiveCountForAdmin(data):
    users_list = (
        UserProfiles.objects.filter(role=data["id"])
        .select_related("user")
        .filter(user__status=False)
        .values_list("user__id")
    )
    return User.objects.filter(id__in=users_list).count()
