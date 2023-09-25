from rest_framework import viewsets
from drf_yasg import openapi
from common.grpc.actions.user_service_action import (
    get_organisation_data,
    get_organisation_locations,
    get_organisation_settings,
    get_organisation_staff,
    get_organisation_working_hours,
    get_user_data,
    get_user_additional_data,
    get_user_address,
    get_user_permissions,
    get_user_working_hours,
)

from common.swagger.documentation import (
    swagger_wrapper,
    swagger_auto_schema,
    id_param,
    org_param,
)
from common.helpers.response_helper import API_RESPONSE
from users.models import CustomerProfile, User, UserProfiles
from users.helper import getContactPayloadForCrmService
from users.serializers import (
    CustomerProfilesSerializer,
    UserProfilesSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from common.events.publishers.user_service_publisher import publish_event
from common.configs.config import config as cfg
import logging


class UserInfoAPI(viewsets.ViewSet):
    http_method_names = ["get", "post", "head", "options"]
    serializer_class = UserUpdateSerializer

    @swagger_auto_schema(manual_parameters=[], tags=["profile"])
    def list(self, request, *args, **kwargs):
        try:
            user_info = User.objects.get(id=request.userinfo["id"])
            try:
                if request.userinfo["utype"] == "ENDUSER":
                    user_information = CustomerProfile.objects.get(user=user_info)
                else:
                    user_information = UserProfiles.objects.get(user=user_info)

            except Exception as err:
                if request.userinfo["utype"] == "ENDUSER":
                    user_information = CustomerProfile(
                        user=user_info, organisation=request.userinfo["organisation"]
                    )
                else:
                    user_information = UserProfiles(
                        user=user_info, organisation=request.userinfo["organisation"]
                    )
                user_information.save()

            user_data = UserSerializer(user_info).data
            if request.userinfo["utype"] == "ENDUSER":
                user_information_data = CustomerProfilesSerializer(
                    user_information
                ).data
            else:
                user_information_data = UserProfilesSerializer(user_information).data

            return_data = {
                **user_information_data,
                **user_data,
                "email": user_info.email,
            }
        except Exception as err:
            logging.error(f"UserInfoAPI first exception: {err}", exc_info=True)
            return API_RESPONSE.Return400Error("Invalid user token provided")

        return API_RESPONSE.Return200Success("User info", return_data)

    @swagger_wrapper(
        {
            "fname": openapi.TYPE_STRING,
            "lname": openapi.TYPE_STRING,
            "phone_number": openapi.TYPE_STRING,
            "ccode": openapi.TYPE_STRING,
            "image": openapi.TYPE_STRING,
            "date_of_birth": openapi.TYPE_STRING,
            "gender": openapi.TYPE_STRING,
            "email": openapi.TYPE_STRING,
        },
        ["profile"],
    )
    def create(self, request, *args, **kwargs):

        # phone_number = request.data["phone_number"]
        # ccode = request.data["ccode"]
        try:
            user_info = User.objects.get(id=request.userinfo["id"])
            # Check whether phone number exists
            # try:
            #     user_count = (
            #         User.objects.filter(phone_number=phone_number, ccode=ccode)
            #         .exclude(id=request.userinfo["id"])
            #         .count()
            #     )
            #     if user_count > 0:
            #         return API_RESPONSE.Return400Error("User with phone number already exists")
            # except:
            #     pass

            serializer = self.serializer_class(
                user_info, data=request.data, partial=True
            )

            if serializer.is_valid():
                serializer.save()
            else:
                return API_RESPONSE.Return400Error("Invalid Data")

            if request.userinfo["utype"] == "ENDUSER":
                if (
                    "email" in request.data
                    and user_info.email == ""
                    and User.objects.filter(email=request.data["email"])
                    .exclude(id=request.userinfo["id"])
                    .count()
                    == 0
                ):
                    user_info.email = request.data["email"]
                    user_info.save()
                # if "date_of_birth" in request.data and "gender" in request.data:
                customer_profile_info = CustomerProfile.objects.get(
                    user=request.userinfo["id"]
                )
                profile_serializer = CustomerProfilesSerializer(
                    customer_profile_info,
                    data={
                        "date_of_birth": request.data.get("date_of_birth", None),
                        "gender": request.data.get("gender", None),
                    },
                    partial=True,
                )
                if profile_serializer.is_valid():
                    profile_serializer.save()
                else:
                    return API_RESPONSE.Return400Error("Invalid Data")

                if request.data.get("is_new_user", False):
                    # Publishing event to CRM for creating contact
                    customer_payload = getContactPayloadForCrmService(user_info)
                    if customer_payload != None:
                        event_status = publish_event(
                            customer_payload,
                            cfg.get("events", "CRM_SERVICE_EXCHANGE"),
                            cfg.get("events", "CRM_SERVICE_CONTACT_CREATE_ROUTING_KEY"),
                        )
                        if not event_status:
                            # Handle the failed the case
                            pass
        except Exception as err:
            logging.error(f"UserInfoAPI create: {err}", exc_info=True)
            return API_RESPONSE.Return400Error("Invalid Data Provided")
        return API_RESPONSE.Return200Success(
            "User info updated successfully", UserSerializer(user_info).data
        )


class TestAPIs(viewsets.ViewSet):
    @swagger_auto_schema(manual_parameters=[id_param, org_param], tags=["profile"])
    def list(self, request, *args, **kwargs):
        id = request.query_params.get("id", "")
        org = request.query_params.get("org", "")
        orgdata = get_organisation_data(org)
        orgsettings = get_organisation_settings(org)
        orgloc = get_organisation_locations(org)
        orgstaff = get_organisation_staff(org)
        orghours = get_organisation_working_hours(org)
        user = get_user_data(id, True, True, True, True)
        useradd = get_user_additional_data(id)
        userhrs = get_user_working_hours(id)
        useraddress = get_user_address(id)
        userper = get_user_permissions(id)
        return API_RESPONSE.Return200Success(
            "",
            {
                "status": 200,
                "id": id,
                "org": org,
                "org_data": orgdata,
                "org_loc": orgloc,
                "orgsettings": orgsettings,
                "orgstaff": orgstaff,
                "orghours": orghours,
                "user": user,
                "useradd": useradd,
                "userhrs": userhrs,
                "useraddress": useraddress,
                "userper": userper,
            },
        )
