from rest_framework import viewsets
from django.utils import timezone
import logging

from drf_yasg import openapi
from organisation.models import Locations

from organisation.serializers import LocationsSerializer
from users.models import StaffLocations, User
from common.swagger.documentation import swagger_auto_schema, swagger_wrapper
from common.helpers.response_helper import API_RESPONSE


class OrganisationLocationsAPI(viewsets.ViewSet):
    http_method_names = ["get", "post", "put", "delete", "head", "options"]
    serializer_class = LocationsSerializer

    @swagger_auto_schema(manual_parameters=[], tags=["locations"])
    def list(self, request, *args, **kwargs):
        try:
            locations_info = Locations.objects.filter(
                organisation=request.userinfo["organisation"],
                is_active=True,
                ltype=Locations.LocationTypes.ORGANISATION,
                ref_id=request.userinfo["organisation"],
            ).order_by("name")
            locations_data = self.serializer_class(locations_info, many=True).data
            return API_RESPONSE.Return200Success(
                "Organisation locations", locations_data
            )
        except Exception as err:
            logging.error(f"OrganisationLocationsAPI list: {err}", exc_info=True)
            return API_RESPONSE.Return400Error(
                "Internal error, try again after some time."
            )

    @swagger_wrapper(
        {
            "name": openapi.TYPE_STRING,
            "location": openapi.TYPE_STRING,
            "email": openapi.TYPE_STRING,
            "phone_number": openapi.TYPE_STRING,
            "ccode": openapi.TYPE_STRING,
        },
        ["locations"],
    )
    def create(self, request, *args, **kwargs):
        try:
            name = request.data["name"]
            location = request.data["location"]
            user = request.userinfo["id"]
            organisation = request.userinfo["organisation"]
            email = request.data.get("email")
            phone_number = request.data.get("phone_number")
            ccode = request.data.get("ccode")

            try:
                check_locations = Locations.objects.filter(
                    name=name,
                    ref_id=organisation,
                    organisation=organisation,
                    ltype=Locations.LocationTypes.ORGANISATION,
                    is_active=True,
                ).count()
                if check_locations > 0:
                    return API_RESPONSE.Return400Error(
                        "Location with name already exists"
                    )
            except Exception:
                return API_RESPONSE.Return400Error("Location with name already exists")

            location_info = Locations(
                name=name,
                location=location,
                ref_id=organisation,
                email=email,
                phone_number=phone_number,
                ccode=ccode,
                organisation=organisation,
                created_by=user,
                updated_by=user,
                ltype=Locations.LocationTypes.ORGANISATION,
            )
            location_info.save()
            if (
                Locations.objects.filter(
                    ltype=Locations.LocationTypes.ORGANISATION,
                    organisation=organisation,
                    is_active=True,
                ).count()
                == 1
            ):
                # Inserting admin location
                admin = User.objects.get(
                    id=user, organisation=organisation, is_active=True
                )
                admin_location = StaffLocations(
                    user=admin,
                    location=location_info,
                    organisation=request.data.get("organisation"),
                    created_by=request.data.get("user_id"),
                )
                admin_location.save()
                location_info.default = True
                location_info.save()

            location_data = self.serializer_class(location_info).data
            return API_RESPONSE.Return201Created(
                "Location Created successfully", location_data
            )
        except Exception as err:
            logging.error(f"OrganisationLocationsAPI create: {err}", exc_info=True)
            location_info.delete()
            return API_RESPONSE.Return400Error(
                "Internal error, try again after sometime."
            )

    @swagger_auto_schema(manual_parameters=[], tags=["locations"])
    def retrieve(self, request, *args, **kwargs):
        try:
            location_id = kwargs["pk"]
            try:

                locations_info = Locations.objects.get(
                    id=location_id,
                    is_active=True,
                    ref_id=request.userinfo["organisation"],
                    organisation=request.userinfo["organisation"],
                    ltype=Locations.LocationTypes.ORGANISATION,
                )
            except:
                return API_RESPONSE.Return404Error("Invalid Location Id")
            locations_data = self.serializer_class(locations_info).data
            return API_RESPONSE.Return200Success(
                "Organisation locations", locations_data
            )
        except Exception as err:
            logging.error(f"OrganisationLocationsAPI retrieve: {err}", exc_info=True)
            return API_RESPONSE.Return400Error(
                "Internal error, try again after some time."
            )

    @swagger_wrapper(
        {
            "name": openapi.TYPE_STRING,
            "location": openapi.TYPE_STRING,
            "default": openapi.TYPE_BOOLEAN,
            "status": openapi.TYPE_BOOLEAN,
            "email": openapi.TYPE_STRING,
            "phone_number": openapi.TYPE_STRING,
            "ccode": openapi.TYPE_STRING,
        },
        ["locations"],
    )
    def update(self, request, *args, **kwargs):
        try:
            location_id = kwargs["pk"]
            organisation = request.userinfo["organisation"]

            try:
                location_info = Locations.objects.get(
                    id=location_id,
                    organisation=organisation,
                    ref_id=organisation,
                    is_active=True,
                    ltype=Locations.LocationTypes.ORGANISATION,
                )
                location_status = location_info.status
            except:
                return API_RESPONSE.Return404Error("Invalid location id sent")

            try:
                if (
                    "default" in request.data
                    and location_info.default != request.data.get("default")
                ):
                    my_queryset = Locations.objects.filter(
                        organisation=organisation,
                        is_active=True,
                        ltype=Locations.LocationTypes.ORGANISATION,
                    )
                    my_queryset.update(default=False)
            except:
                return API_RESPONSE.Return404Error("Failed to make it default")

            try:
                if "name" in request.data:
                    check_locations = (
                        Locations.objects.filter(
                            name=request.data["name"],
                            organisation=organisation,
                            is_active=True,
                            ref_id=request.userinfo["organisation"],
                        )
                        .exclude(id=location_id)
                        .count()
                    )
                    if check_locations > 0:
                        return API_RESPONSE.Return400Error("location already exists")
            except:
                return API_RESPONSE.Return400Error("location with name already exists")

            if location_info.default:
                if location_status != request.data.get("status"):
                    return API_RESPONSE.Return400Error(
                        "Default location status cannot be changed"
                    )

            serializer = self.serializer_class(
                location_info, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                location_info.updated_by = request.userinfo["id"]
                location_info.save()
            else:
                return API_RESPONSE.Return404Error("Invalid location payload sent")

            if location_status != request.data.get("status", location_status):
                if request.data.get("status"):
                    return API_RESPONSE.Return200Success("Location enabled")
                else:
                    return API_RESPONSE.Return200Success("Location disabled")
            return API_RESPONSE.Return200Success(
                "Location updated successfully", serializer.data
            )
        except Exception as err:
            logging.error(f"OrganisationLocationsAPI update: {err}", exc_info=True)
            return API_RESPONSE.Return400Error(
                "Internal error, try again after sometime."
            )

    @swagger_auto_schema(manual_parameters=[], tags=["locations"])
    def destroy(self, request, *args, **kwargs):
        try:
            location_id = kwargs["pk"]
            try:
                locations_info = Locations.objects.get(
                    id=location_id,
                    is_active=True,
                    ref_id=request.userinfo["organisation"],
                    organisation=request.userinfo["organisation"],
                    ltype=Locations.LocationTypes.ORGANISATION,
                )
                if locations_info.default:
                    return API_RESPONSE.Return400Error("Cannot delete default location")
                staff_locations = StaffLocations.objects.filter(
                    location=locations_info,
                    is_active=True,
                    status=True,
                    organisation=request.userinfo["organisation"],
                )
                if staff_locations.count() >= 1:
                    return API_RESPONSE.Return400Error("Cannot delete location")
            except:
                return API_RESPONSE.Return404Error("Invalid Location Id")

            locations_info.is_active = False
            locations_info.deleted_by = request.userinfo["id"]
            locations_info.updated_by = request.userinfo["id"]
            locations_info.deleted_at = timezone.now()
            locations_info.save()

            return API_RESPONSE.Return200Success(
                "Location deleted successfully",
            )
        except Exception as err:
            logging.error(f"OrganisationLocationsAPI destroy: {err}", exc_info=True)
            return API_RESPONSE.Return400Error(
                "Internal error, try again after some time."
            )


class LocationByIdAPI(viewsets.ViewSet):
    http_method_names = ["get", "head", "options"]
    serializer_class = LocationsSerializer

    def retrieve(self, request, *args, **kwargs):
        try:
            location = Locations.objects.get(
                id=kwargs["pk"],
                is_active=True,
            )
            return API_RESPONSE.Return200Success(
                "Locations info", self.serializer_class(location).data
            )
        except Exception as err:
            logging.error(f"LocationByIdAPI retrieve: {err}", exc_info=True)
            return API_RESPONSE.Return400Error("Location not found")
