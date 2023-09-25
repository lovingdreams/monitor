from rest_framework import viewsets
from django.db.models import Q
from common.helpers.response_helper import API_RESPONSE
from organisation.models import Badge
from organisation.serializers import BadgeListSerializer, BadgeUpdateSerializer
from organisation.helper import (
    getDeletedTime,
    check_name,
    check_badge_type,
    insert_default_badges,
)
from common.swagger.documentation import (
    swagger_wrapper,
    swagger_auto_schema,
    type_param,
)
from drf_yasg import openapi
import logging


class BadgeAPI(viewsets.ViewSet):
    http_method_names = ["get", "post", "put", "delete"]

    @swagger_auto_schema(
        manual_parameters=[type_param],
        tags=["badge"],
    )
    def list(self, request, *args, **kwargs):
        query_set = Q(
            organisation=request.data.get("organisation", None),
            is_active=True,
        )
        type_param = self.request.query_params.get("type", None)
        if Badge.objects.filter(query_set).count() == 0:
            insertion_status = insert_default_badges(
                request.data.get("organisation", None), request.userinfo["id"]
            )
            if not insertion_status:
                return API_RESPONSE.Return400Error("Failed to insert default badges")
        if type_param not in ["", " ", None, "null"]:
            query_set &= Q(
                type=type_param,
                status=True,
            )
        badges_list = Badge.objects.filter(query_set)
        return API_RESPONSE.Return200Success(
            "Badges info", BadgeListSerializer(badges_list, many=True).data
        )

    @swagger_wrapper(
        {
            "name": openapi.TYPE_STRING,
            "colour": openapi.TYPE_STRING,
            "text_colour": openapi.TYPE_STRING,
            "type": openapi.TYPE_STRING,
        },
        ["badge"],
    )
    def create(self, request, *args, **kwargs):
        if request.data.get("role") != "ADMIN":
            return API_RESPONSE.Return400Error("You don't have permission")

        badges_list = Badge.objects.filter(
            type=request.data.get("type"),
            name=request.data.get("name"),
            is_active=True,
            organisation=request.userinfo["organisation"],
        )
        if badges_list.count() >= 1:
            return API_RESPONSE.Return400Error("name already exist")

        error = check_name(request.data.get("name"))
        if error:
            return API_RESPONSE.Return400Error("Invalid badge name")

        error = check_badge_type(request.data.get("type"))
        if error:
            return API_RESPONSE.Return400Error("Invalid badge provided")

        badge = Badge(
            name=request.data.get("name"),
            colour=request.data.get("colour"),
            text_colour=request.data.get("text_colour"),
            created_by=request.userinfo["id"],
            type=request.data.get("type"),
            organisation=request.userinfo["organisation"],
        )
        badge.save()
        return API_RESPONSE.Return201Created(
            "Badge Created Successfully", BadgeListSerializer(badge).data
        )

    @swagger_wrapper(
        {
            "name": openapi.TYPE_STRING,
            "colour": openapi.TYPE_STRING,
            "text_colour": openapi.TYPE_STRING,
        },
        ["badge"],
    )
    def update(self, request, *args, **kwargs):
        try:
            if request.data.get("role") != "ADMIN":
                return API_RESPONSE.Return400Error("You don't have permission")

            badge_obj = Badge.objects.get(
                id=kwargs.get("pk"),
                organisation=request.data.get("organisation", None),
                is_active=True,
            )
            if "name" in request.data:
                try:
                    error = check_name(request.data.get("name"))
                    if error:
                        return API_RESPONSE.Return400Error("Invalid tag name")

                    existing_badge_obj = Badge.objects.get(
                        name=request.data.get("name"),
                        type=badge_obj.type,
                        is_active=True,
                        organisation=request.data.get("organisation"),
                    )
                    if existing_badge_obj.id != badge_obj.id:
                        return API_RESPONSE.Return400Error("Name already exist")
                except Exception:
                    pass

            request.data["updated_by"] = request.userinfo["id"]
            serializer = BadgeUpdateSerializer(badge_obj, request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return API_RESPONSE.Return200Success("Badge updated", serializer.data)
            return API_RESPONSE.Return400Error("Invalid data")
        except Exception as err:
            logging.error(f"BadgeAPI update: {err}", exc_info=True)
            return API_RESPONSE.Return400Error("Not found")

    def destroy(self, request, *args, **kwargs):
        try:
            if request.data.get("role") != "ADMIN":
                return API_RESPONSE.Return400Error("You don't have permission")

            badge_obj = Badge.objects.get(
                id=kwargs.get("pk"),
                organisation=request.data.get("organisation", None),
                is_active=True,
            )
            badge_obj.is_active = False
            badge_obj.deleted_by = request.data.get("user_id")
            badge_obj.deleted_at = getDeletedTime()
            badge_obj.save()
            return API_RESPONSE.Return200Success(
                "Badge deleted",
            )
        except Exception as err:
            logging.error(f"BadgeAPI destroy: {err}", exc_info=True)
            return API_RESPONSE.Return400Error("Not found")
