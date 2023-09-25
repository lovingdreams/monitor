from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from organisation.models import Tags
from organisation.serializers import TagsListSerializer, TagsUpdateSerializer
from organisation.helper import getDeletedTime, check_name, check_tag_type
from common.helpers.response_helper import API_RESPONSE
from common.configs.config import config as cfg
from common.swagger.documentation import (
    swagger_wrapper,
    page_param,
    offset_param,
    type_param,
    swagger_auto_schema,
)
from drf_yasg import openapi
import logging


class TagsAPI(viewsets.ViewSet):
    http_method_names = ["get", "post", "put", "delete"]

    @swagger_auto_schema(
        manual_parameters=[page_param, offset_param, type_param], tags=["tags"]
    )
    def list(self, request, *args, **kwargs):
        page = int(self.request.query_params.get(page_param.name, 0))
        offset = 10
        if page > 0:
            try:
                tags_list = Tags.objects.filter(
                    organisation=request.userinfo["organisation"], is_active=True
                ).order_by("-created_at")
                pagination = PageNumberPagination()
                pagination.page_size = offset
                pagination.page_query_param = cfg.get("common", "PAGE")
                query_set = pagination.paginate_queryset(
                    queryset=tags_list, request=request
                )
                appointments_serializer = TagsListSerializer(query_set, many=True)
                pagination_response = pagination.get_paginated_response(
                    appointments_serializer.data
                )
                pagination_response.data["count"] = len(tags_list)
                pagination_response.data["status"] = 200
                pagination_response.data["message"] = "Tags info"
                pagination_response.data["data"] = pagination_response.data["results"]
                pagination_response.data["page"] = page
                del pagination_response.data["results"]
                return pagination_response
            except Exception as err:
                logging.error(f"TagsAPI list: {err}", exc_info=True)
                return API_RESPONSE.Return400Error("Something went wrong")

        tags_list = []
        type_param = self.request.query_params.get("type", None)
        if type_param not in ["", " ", None, "null"]:
            tags_list = Tags.objects.filter(
                type=type_param,
                organisation=request.userinfo["organisation"],
                is_active=True,
                status=True,
            ).order_by("-created_at")
        return API_RESPONSE.Return200Success(
            "Tags info", TagsListSerializer(tags_list, many=True).data
        )

    @swagger_wrapper(
        {
            "name": openapi.TYPE_STRING,
            "colour": openapi.TYPE_STRING,
            "type": openapi.TYPE_STRING,
        },
        ["tags"],
    )
    def create(self, request, *args, **kwargs):
        if request.data.get("role") != "ADMIN":
            return API_RESPONSE.Return400Error("You don't have permission")

        tags_list = Tags.objects.filter(
            type=request.data.get("type"),
            name=request.data.get("name"),
            is_active=True,
            organisation=request.userinfo["organisation"],
        )
        if tags_list.count() >= 1:
            return API_RESPONSE.Return400Error("name already exist")

        error = check_name(request.data.get("name"))
        if error:
            return API_RESPONSE.Return400Error("Invalid tag name")

        error = check_tag_type(request.data.get("type"))
        if error:
            return API_RESPONSE.Return400Error("Invalid type")

        tag = Tags(
            name=request.data.get("name"),
            colour=request.data.get("colour"),
            created_by=request.userinfo["id"],
            organisation=request.userinfo["organisation"],
            type=request.data.get("type"),
        )
        tag.save()
        return API_RESPONSE.Return201Created(
            "Tag Created Successfully", TagsListSerializer(tag).data
        )

    @swagger_wrapper(
        {
            "name": openapi.TYPE_STRING,
            "colour": openapi.TYPE_STRING,
        },
        ["tags"],
    )
    def update(self, request, *args, **kwargs):
        try:
            if request.data.get("role") != "ADMIN":
                return API_RESPONSE.Return400Error("You don't have permission")

            tag_obj = Tags.objects.get(
                id=kwargs.get("pk"),
                organisation=request.data.get("organisation", None),
                is_active=True,
            )
            if "name" in request.data:
                try:
                    error = check_name(request.data.get("name"))
                    if error:
                        return API_RESPONSE.Return400Error("Invalid tag name")
                    existing_tag_obj = Tags.objects.get(
                        name=request.data.get("name"),
                        is_active=True,
                        organisation=request.data.get("organisation"),
                    )
                    if existing_tag_obj.id != tag_obj.id:
                        return API_RESPONSE.Return400Error("Name already exist")
                except Exception as err:
                    pass

            request.data["updated_by"] = request.userinfo["id"]
            serializer = TagsUpdateSerializer(tag_obj, request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return API_RESPONSE.Return200Success("Tag is updated", serializer.data)
            return API_RESPONSE.Return400Error("Invalid data")
        except Exception as err:
            logging.error(f"TagsAPI update: {err}", exc_info=True)
            return API_RESPONSE.Return400Error("Not found")

    def retrieve(self, request, *args, **kwargs):
        try:
            tag_obj = Tags.objects.get(
                id=kwargs.get("pk"),
                organisation=request.data.get("organisation", None),
                is_active=True,
            )
            return API_RESPONSE.Return200Success(
                "Tags info", TagsListSerializer(tag_obj).data
            )
        except Exception as err:
            logging.error(f"TagsAPI retrieve: {err}", exc_info=True)
            return API_RESPONSE.Return400Error("Not found")

    def destroy(self, request, *args, **kwargs):
        try:
            if request.data.get("role") != "ADMIN":
                return API_RESPONSE.Return400Error("You don't have permission")

            tag_obj = Tags.objects.get(
                id=kwargs.get("pk"),
                organisation=request.data.get("organisation", None),
                is_active=True,
            )
            tag_obj.is_active = False
            tag_obj.deleted_by = request.data.get("user_id")
            tag_obj.deleted_at = getDeletedTime()
            tag_obj.save()
            return API_RESPONSE.Return200Success("Tag deleted")
        except Exception as err:
            logging.error(f"TagsAPI destroy: {err}", exc_info=True)
            return API_RESPONSE.Return400Error("Not found")
