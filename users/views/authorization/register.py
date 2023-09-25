from rest_framework.permissions import AllowAny
from rest_framework import viewsets
from drf_yasg import openapi

from django.db import transaction
from common.helpers.common_helper import (
    random_string_generator,
    send_mail,
)
from common.helpers.response_helper import API_RESPONSE
from common.events.publishers.user_service_publisher import publish_event
from common.helpers.user_helper import getAdminCreationPayload
from common.configs.config import config as cfg
from common.swagger.documentation import (
    swagger_wrapper,
)
from django.db.models import Q
from organisation.serializers import OrganisationSerializer
from organisation.models import Organisations
from users.models import User, UserProfiles, UserOTPs
from users.helper import (
    getAdminEmailPayload,
    getPayloadForCalendarService,
    makeCalendarServiceCall,
    checkSlugName,
    insertSetupData,
    getPipelineCreationPayload,
    getActivityCreationPayload,
)
from common.configs.config import config as cfg
import logging


class RegisterAPI(viewsets.ViewSet):
    permission_classes = (AllowAny,)
    http_method_names = ["post", "head", "options"]

    @swagger_wrapper(
        {
            "fname": openapi.TYPE_STRING,
            "lname": openapi.TYPE_STRING,
            "email": openapi.TYPE_STRING,
            "password": openapi.TYPE_STRING,
            "organisation": openapi.TYPE_STRING,
            "phone_number": openapi.TYPE_STRING,
            "ccode": openapi.TYPE_STRING,
            "business_type": openapi.TYPE_STRING,
            "terms_conditions": openapi.TYPE_BOOLEAN,
            "other_type_name": openapi.TYPE_STRING,
        },
        ["authorization"],
    )
    def create(self, request, *args, **kwargs):
        # get all required params and verify them
        required_params = [
            "fname",
            "lname",
            "email",
            "password",
            "organisation",
            "phone_number",
            "ccode",
            "business_type",
        ]
        data = [request.data.get(key, "").strip() for key in required_params]
        if "" in data:
            return API_RESPONSE.Return400Error("Some fields are missing")
        [
            fname,
            lname,
            email,
            password,
            organisation,
            phone_number,
            ccode,
            business_type,
        ] = data

        # Check whether user exists
        query_set1 = Q(email=email, utype=User.UserTypes.ADMIN)
        query_set2 = Q(email=email, utype=User.UserTypes.STAFF)
        if User.objects.filter(query_set1 | query_set2).count() > 0:
            return API_RESPONSE.Return400Error("User with mail already exists")

        # Check whether organisation exists
        if Organisations.objects.filter(slug=organisation).count() > 0:
            return API_RESPONSE.Return400Error("Business name already exists")

        # Check whether phone number exists
        # if User.objects.filter(phone_number=phone_number, ccode=ccode).count() > 0:
        #     return API_RESPONSE.Return400Error("User with phone number already exists")

        if not request.data.get("terms_conditions", False):
            return API_RESPONSE.Return400Error("Please accept terms & conditions")

        if password is None or len(password) == 0:
            return API_RESPONSE.Return400Error("Password should not be empty")

        # if not checkSlugName(organisation):
        #     return API_RESPONSE.Return400Error("Invalid Business name")
        try:
            # with transaction.atomic():
            # create organisation first
            org_data = {
                "slug": organisation,
                "name": organisation,
                "email": email,
                "phone_number": phone_number,
                "ccode": ccode,
                "business_type": business_type,
                "terms_conditions": True,
                "other_type_name": request.data.get("other_type_name", ""),
            }
            organisation_data = OrganisationSerializer(data=org_data)
            if organisation_data.is_valid():
                org_instance = organisation_data.save()
            organisation_id = str(org_instance)

            # create user
            username = (
                email.split("@")[0]
                + "--ADMIN--"
                + organisation_id
                + "@"
                + email.split("@")[1]
            )
            user_data = User(
                fname=fname,
                lname=lname,
                email=email,
                phone_number=phone_number,
                ccode=ccode,
                username=username,
                organisation=organisation_id,
                utype=User.UserTypes.ADMIN,
            )
            user_data.set_password(password)
            user_data.save()
            user_id = str(user_data)
            # create user information
            user_information = UserProfiles(user=user_data, organisation=org_instance)
            user_information.save()
            # update organisation data with user info
            org_instance.created_by = user_id
            org_instance.updated_by = user_id
            org_instance.save()

            user_data.created_by = user_id
            user_data.updated_by = user_id
            user_data.save()

            # create and send activation code
            otp = random_string_generator(6)
            user_otp = UserOTPs(
                user=user_data,
                organisation=organisation_id,
                created_by=user_data,
                otp=otp,
                sent_to=email,
                used_for=UserOTPs.UsedTypes.ACTIVATE,
                sent_type=UserOTPs.SentTypes.MAIL,
            )
            user_otp.save()
            # Publishing an event to communication service for sending OTP
            mail_status = publish_event(
                getAdminEmailPayload(user_data, organisation_id, otp),
                cfg.get("events", "COMMUNICATION_EXCHANGE"),
                cfg.get("events", "ADMIN_REGISTER_ROUTING_KEY"),
            )
            if not mail_status:
                # Mail sending is failed Handle the case
                pass
            # send_mail(
            #     email, otp, user_id, "User Registration"
            # )  # send email to user
        except Exception as err:
            return API_RESPONSE.Return404Error(err)

        # Inserting Setup data
        insertSetupData(str(organisation_id), str(user_data.id))

        event_status = publish_event(
            getAdminCreationPayload(str(org_instance), cfg.get("roles", "ADMIN")),
            cfg.get("events", "USER_EXCHANGE"),
            cfg.get("events", "USER_CREATE_STAGES_ROUTING_KEY"),
        )
        if not event_status:
            # Event publishing is failed Handle the case
            pass

        # Publishing an event to calendar service for slots creation
        staff_payload = getPayloadForCalendarService(
            user_data, User.UserTypes.ADMIN, "Asia/Kolkata"
        )
        if staff_payload is not None:
            event_status = publish_event(
                staff_payload,
                cfg.get("events", "CALENDAR_SERVICE_EXCHANGE"),
                cfg.get("events", "WORKING_HOUR_CREATE_ROUTING_KEY"),
            )
            if not event_status:
                # Handle the failed the case
                pass
        else:
            # Handle the failed the case
            pass

        # Publishing an event to Consultation service for default email templates creation
        default_email_templates_payload = {
            "organisation": str(organisation_id),
            "user_id": str(user_data.id),
        }
        event_status = publish_event(
            default_email_templates_payload,
            cfg.get("events", "CONSULTATION_EXCHANGE"),
            cfg.get("events", "EMAIL_TEMPLATES_CREATE_ROUTING_KEY"),
        )
        if not event_status:
            # Event publishing is failed Handle the case
            pass

        # Publishing an event to CRM service for default pipeline insertion
        event_status = publish_event(
            getPipelineCreationPayload(user_data),
            cfg.get("events", "CRM_SERVICE_EXCHANGE"),
            cfg.get("events", "CRM_SERVICE_PIPELINE_CREATE_ROUTING_KEY"),
        )
        if not event_status:
            # Event publishing is failed Handle the case
            pass

        # Publishing an event to CRM service for default pipeline insertion
        event_status = publish_event(
            getActivityCreationPayload(user_data),
            cfg.get("events", "ACTIVITY_SERVICE_EXCHANGE"),
            cfg.get("events", "DEFAULT_ACTIVITY_CREATE_ROUTING_KEY"),
        )
        if not event_status:
            # Event publishing is failed Handle the case
            pass

        return API_RESPONSE.Return201Created(
            "User Created. Please Verify your mail", {"id": user_id}
        )
