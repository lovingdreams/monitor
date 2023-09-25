from rest_framework import viewsets
from organisation.models import Organisations, Locations, GeneralSettings, Setup
from organisation.serializers import (
    OrganisationSerializer,
    LocationsSerializer,
    GeneralSettingsSerializer,
    IframeSetupSerializer,
    IframeUserProfilesSerializer,
)
from users.models import User, UserProfiles
from users.serializers import StaffListSerializer
from rest_framework.permissions import AllowAny
from common.helpers.response_helper import API_RESPONSE
from common.swagger.documentation import (
    swagger_auto_schema,
    org_param,
    id_param,
    org_name,
    staff_id,
)
import logging


class OrganisationSetupAPI(viewsets.ViewSet):
    permission_classes = (AllowAny,)
    serializer_class = IframeSetupSerializer
    http_method_names = ["get", "head", "options"]

    @swagger_auto_schema(manual_parameters=[org_param], tags=["organisation"])
    def list(self, request, *args, **kwargs):
        try:
            org_param = self.request.query_params.get("org")
            if org_param != None:
                set_up_info = Setup.objects.filter(
                    organisation=org_param, status=True, is_active=True
                )
                serializer = self.serializer_class(set_up_info, many=True).data
                return API_RESPONSE.Return200Success(
                    "Organisation setup info", serializer
                )
        except Exception as err:
            logging.error(f"OrganisationSetupAPI list: {err}", exc_info=True)
        return API_RESPONSE.Return400Error("Not found")


class OrganisationIdAPI(viewsets.ViewSet):
    permission_classes = (AllowAny,)
    serializer_class = OrganisationSerializer
    http_method_names = ["get", "head", "options"]

    @swagger_auto_schema(manual_parameters=[org_param], tags=["organisation"])
    def list(self, request, *args, **kwargs):
        try:
            org_param = self.request.query_params.get("org")
            if org_param != None:
                org_info = Organisations.objects.get(
                    id=org_param, status=True, is_active=True
                )
                serializer = self.serializer_class(org_info)
                return API_RESPONSE.Return200Success(
                    "Organisation information", serializer.data
                )
        except Exception as err:
            logging.error(f"OrganisationIdAPI list: {err}", exc_info=True)
        return API_RESPONSE.Return400Error("Organisation not found")


class OrganisationInfoAPI(viewsets.ViewSet):
    http_method_names = ["get", "head", "options"]
    permission_classes = (AllowAny,)
    serializer_class = OrganisationSerializer

    @swagger_auto_schema(manual_parameters=[org_name], tags=["organisation"])
    def list(self, request, *args, **kwargs):
        try:
            org_name = self.request.query_params.get("org_name")
            if org_name != None or org_name != "":
                organisation = Organisations.objects.get(
                    is_active=True, status=True, slug=org_name
                )
                serializer = self.serializer_class(organisation)
                return API_RESPONSE.Return200Success(
                    "Organisation information", serializer.data
                )
        except Exception as err:
            logging.error(f"OrganisationIdAPI list: {err}", exc_info=True)
        return API_RESPONSE.Return400Error("Organisation not found")


class OrganisationGeneralSettingsAPI(viewsets.ViewSet):
    http_method_names = ["get", "head", "options"]
    permission_classes = (AllowAny,)
    serializer_class = GeneralSettingsSerializer

    @swagger_auto_schema(manual_parameters=[org_param], tags=["organisation"])
    def list(self, request, *args, **kwargs):
        try:
            org_id = self.request.query_params.get("org")
            if org_id != None or org_id != "":
                general_settings = GeneralSettings.objects.get(
                    status=True, is_active=True, organisation=org_id
                )
                serializer = self.serializer_class(general_settings)
                return API_RESPONSE.Return200Success(
                    "Organisation information", serializer.data
                )
        except Exception as err:
            logging.error(f"OrganisationGeneralSettingsAPI list: {err}", exc_info=True)
        return API_RESPONSE.Return400Error("General settings info not found")


class AdminInfoAPI(viewsets.ViewSet):
    http_method_names = ["get", "head", "options"]
    permission_classes = (AllowAny,)

    @swagger_auto_schema(manual_parameters=[org_param], tags=["organisation"])
    def list(self, request, *args, **kwargs):
        try:
            org_id = self.request.query_params.get("org")
            if org_id != None:
                admin_info = User.objects.get(
                    utype=User.UserTypes.ADMIN,
                    organisation=org_id,
                    status=True,
                    is_active=True,
                )
                return API_RESPONSE.Return200Success(
                    "Admin info", {"id": str(admin_info.id)}
                )
        except Exception as err:
            logging.error(f"AdminInfoAPI list: {err}", exc_info=True)
        return API_RESPONSE.Return400Error("Admin info not found")


class OrganisationLocationAPI(viewsets.ViewSet):
    http_method_names = ["get", "head", "options"]
    permission_classes = (AllowAny,)
    serializer_class = LocationsSerializer

    @swagger_auto_schema(manual_parameters=[org_param], tags=["organisation"])
    def list(self, request, *args, **kwargs):
        try:
            org_id = self.request.query_params.get("org")
            if org_id != None:
                locations = Locations.objects.filter(
                    organisation=org_id,
                    status=True,
                    is_active=True,
                    ltype=Locations.LocationTypes.ORGANISATION,
                    ref_id=org_id,
                )
                serializer = self.serializer_class(locations, many=True)
                return API_RESPONSE.Return200Success(
                    "Organisation locations", serializer.data
                )
        except Exception as err:
            logging.error(f"OrganisationLocationAPI list: {err}", exc_info=True)
        return API_RESPONSE.Return400Error("Locations not found")


class UsersLocationAPI(viewsets.ViewSet):
    http_method_names = ["get", "head", "options"]
    permission_classes = (AllowAny,)
    serializer_class = LocationsSerializer

    @swagger_auto_schema(manual_parameters=[org_param, id_param], tags=["organisation"])
    def list(self, request, *args, **kwargs):
        try:
            org_id = self.request.query_params.get("org")
            id_param = self.request.query_params.get("id")
            if org_id != None and id_param != None:
                locations = Locations.objects.filter(
                    organisation=org_id,
                    status=True,
                    is_active=True,
                    ltype=Locations.LocationTypes.USER,
                    ref_id=id_param,
                )
                serializer = self.serializer_class(locations, many=True)
                return API_RESPONSE.Return200Success("User locations", serializer.data)
        except Exception as err:
            logging.error(f"UsersLocationAPI list: {err}", exc_info=True)
        return API_RESPONSE.Return400Error("Locations not found")


class StaffInfoAPI(viewsets.ViewSet):
    http_method_names = ["get", "head", "options"]
    permission_classes = (AllowAny,)
    serializer_class = StaffListSerializer

    @swagger_auto_schema(manual_parameters=[org_param, staff_id], tags=["organisation"])
    def list(self, request, *args, **kwargs):
        try:
            org_id = self.request.query_params.get("org")
            staff_id = self.request.query_params.get("staff_id")
            if org_id != None and staff_id != None:
                staff = User.objects.get(
                    id=staff_id,
                    organisation=org_id,
                    status=True,
                    is_active=True,
                    # utype = User.UserTypes.STAFF
                )
                staff_serializer = self.serializer_class(staff).data
                staff_profile = UserProfiles.objects.get(
                    user=staff,
                    organisation=org_id,
                    is_active=True,
                )
                staff_profile_serializer = IframeUserProfilesSerializer(
                    staff_profile
                ).data
                return API_RESPONSE.Return200Success(
                    "Staff info", {**staff_serializer, **staff_profile_serializer}
                )
        except Exception as err:
            logging.error(f"StaffInfoAPI list: {err}", exc_info=True)
        return API_RESPONSE.Return400Error("Staff not found")
