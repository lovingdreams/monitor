from rest_framework import viewsets
from drf_yasg import openapi

from common.helpers.response_helper import API_RESPONSE
from common.swagger.documentation import swagger_wrapper, swagger_auto_schema
from organisation.models import PriceSettings
from organisation.serializers import PriceSettingsSerializer
import logging


class PriceSettingsAPI(viewsets.ViewSet):
    http_method_names = ["get", "post", "head", "options"]
    serializer_class = PriceSettingsSerializer

    @swagger_auto_schema(manual_parameters=[], tags=["price_settings"])
    def list(self, request, *args, **kwargs):
        try:
            price_settings_info = PriceSettings.objects.get(
                organisation=request.userinfo["organisation"]
            )
        except:
            price_settings_info = PriceSettings(
                organisation=request.userinfo["organisation"]
            )
            price_settings_info.save()

        serializer = self.serializer_class(price_settings_info)
        return API_RESPONSE.Return200Success(
            "Organisation price settings", serializer.data
        )

    @swagger_wrapper(
        {
            "currency": openapi.TYPE_STRING,
            "price_symbol_position": openapi.TYPE_STRING,
            "price_seperator": openapi.TYPE_STRING,
            "no_of_decimals": openapi.TYPE_INTEGER,
            "cod_status": openapi.TYPE_BOOLEAN,
            "currency_name": openapi.TYPE_STRING,
        },
        ["price_settings"],
    )
    def create(self, request, *args, **kwargs):
        try:
            try:
                price_settings_info = PriceSettings.objects.get(
                    organisation=request.userinfo["organisation"]
                )
            except:
                price_settings_info = PriceSettings(
                    organisation=request.userinfo["organisation"]
                )
                price_settings_info.save()

            if request.data.get("no_of_decimals") <= 0:
                return API_RESPONSE.Return400Error(
                    "No of decimals cannot be less than or equal 0"
                )
            serializer = self.serializer_class(
                price_settings_info, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
            else:
                return API_RESPONSE.Return400Error("Invalid parameters sent")

            return API_RESPONSE.Return200Success(
                "Details updated successfully", serializer.data
            )
        except Exception as err:
            logging.error(f"PriceSettingsAPI create: {err}", exc_info=True)
            return API_RESPONSE.Return400Error(
                "Internal Error, Try again after some time"
            )
