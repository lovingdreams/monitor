from rest_framework import viewsets
from drf_yasg import openapi

from common.helpers.response_helper import API_RESPONSE
from common.swagger.documentation import swagger_wrapper, swagger_auto_schema
from common.configs.config import config as cfg
from organisation.models import GeneralSettings
from organisation.serializers import GeneralSettingsSerializer
from users.models import User
from users.helper import getTimezoneUpdatePayloadForCalendarService
from common.events.publishers.user_service_publisher import publish_event


class GeneralSettingsAPI(viewsets.ViewSet):
    http_method_names = ["get", "post", "head", "options"]
    serializer_class = GeneralSettingsSerializer

    @swagger_wrapper(
        {
            "country": openapi.TYPE_STRING,
            "currency": openapi.TYPE_STRING,
            "ccode": openapi.TYPE_STRING,
            "timezone": openapi.TYPE_STRING,
            "dateformat": openapi.TYPE_STRING,
            "timeformat": openapi.TYPE_STRING,
            "slot_duration": openapi.TYPE_STRING,
        },
        ["general_settings"],
    )
    def create(self, request, *args, **kwargs):
        try:
            try:
                general_settings_info = GeneralSettings.objects.get(
                    organisation=request.userinfo["organisation"]
                )
            except:
                general_settings_info = GeneralSettings(
                    organisation=request.userinfo["organisation"]
                )
                general_settings_info.save()

            timezone_update = False
            if "timezone" in request.data:
                if request.data["timezone"] != general_settings_info.timezone:
                    admin_user = User.objects.get(
                        organisation=request.userinfo["organisation"],
                        is_active=True,
                        status=True,
                        utype=User.UserTypes.ADMIN,
                    )
                    timezone_update = True
            serializer = self.serializer_class(
                general_settings_info, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                if timezone_update:
                    calendar_payload = getTimezoneUpdatePayloadForCalendarService(
                        "organisation",
                        request.data["timezone"],
                        request.userinfo["organisation"],
                        str(admin_user.id),
                    )
                    if calendar_payload is not None:
                        event_status = publish_event(
                            calendar_payload,
                            cfg.get("events", "CALENDAR_SERVICE_EXCHANGE"),
                            cfg.get("events", "WORKING_HOUR_UPDATE_ROUTING_KEY"),
                        )
                        if not event_status:
                            # Handle the failed the case
                            pass
                    else:
                        # Handle the failed the case
                        pass
            else:
                return API_RESPONSE.Return400Error("Invalid parameters sent")

            return API_RESPONSE.Return200Success(
                "Details updated successfully", serializer.data
            )
        except:
            return API_RESPONSE.Return400Error(
                "Internal Error, Try again after some time"
            )

    @swagger_auto_schema(manual_parameters=[], tags=["general_settings"])
    def list(self, request, *args, **kwargs):
        try:
            try:
                general_settings_info = GeneralSettings.objects.get(
                    organisation=request.userinfo["organisation"]
                )
            except:
                general_settings_info = GeneralSettings(
                    organisation=request.userinfo["organisation"]
                )
                general_settings_info.save()

            serializer = self.serializer_class(general_settings_info)

            return API_RESPONSE.Return200Success(
                "Organisation general settings", serializer.data
            )
        except:
            return API_RESPONSE.Return400Error(
                "Internal Error, Try again after some time"
            )
