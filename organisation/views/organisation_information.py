from rest_framework import viewsets
from drf_yasg import openapi
from common.helpers.response_helper import API_RESPONSE

from common.swagger.documentation import swagger_auto_schema, swagger_wrapper
from organisation.models import Organisations
from organisation.serializers import OrganisationSerializer, OrganisationListSerializer


class OrganisationInformationAPI(viewsets.ViewSet):
    http_method_names = ["get", "post", "head", "options"]
    serializer_class = OrganisationSerializer

    @swagger_auto_schema(manual_parameters=[], tags=["information"])
    def list(self, request, *args, **kwargs):
        try:
            try:
                organisation_info = Organisations.objects.get(
                    id=request.userinfo["organisation"]
                )
            except:
                return API_RESPONSE.Return400Error("Organisation doesn't exist.")

            serializer = OrganisationListSerializer(organisation_info)

            return API_RESPONSE.Return200Success(
                "Organisation information", serializer.data
            )
        except Exception:
            return API_RESPONSE.Return400Error(
                "Internal Error, Try again after some time"
            )

    @swagger_wrapper(
        {
            "name": openapi.TYPE_STRING,
            "email": openapi.TYPE_STRING,
            "description": openapi.TYPE_STRING,
            "phone_number": openapi.TYPE_STRING,
            "ccode": openapi.TYPE_STRING,
            "image": openapi.TYPE_STRING,
            "website": openapi.TYPE_STRING,
            "address": openapi.TYPE_STRING,
            "identifier": openapi.TYPE_STRING,
            "registration_id": openapi.TYPE_STRING,
            "slug": openapi.TYPE_STRING,
            "language": openapi.TYPE_STRING,
            "instagram_url": openapi.TYPE_STRING,
            "linkedin_url": openapi.TYPE_STRING,
            "twitter_url": openapi.TYPE_STRING,
            "youtube_url": openapi.TYPE_STRING,
        },
        ["information"],
    )
    def create(self, request, *args, **kwargs):
        try:
            try:
                organisation_info = Organisations.objects.get(
                    id=request.userinfo["organisation"]
                )
            except:
                return API_RESPONSE.Return404Error("Organisation doesn't exist.")

            slug_count = (
                Organisations.objects.filter(slug=request.data.get("slug", ""))
                .exclude(id=request.userinfo["organisation"])
                .count()
            )

            if slug_count != 0:
                return API_RESPONSE.Return404Error("Organisation doamin already taken.")

            serializer = self.serializer_class(
                organisation_info, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
            else:
                return API_RESPONSE.Return400Error("Invalid parameters sent")

            return API_RESPONSE.Return200Success(
                "Details updated successfully", serializer.data
            )
        except:
            return API_RESPONSE.Return400Error(
                "Internal error, try again after some time."
            )
