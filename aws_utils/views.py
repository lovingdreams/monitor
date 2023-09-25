from aws_utils.s3_operations import generate_bucket_key, generate_presigned_url
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
import logging
from common.swagger.documentation import content_type
from common.helpers.response_helper import API_RESPONSE
from drf_yasg.utils import swagger_auto_schema


class PreSignedUrlApi(viewsets.ViewSet):
    http_method_names = ["get", "head"]

    @swagger_auto_schema(
        manual_parameters=[
            content_type,
        ]
    )
    def list(self, request, *args, **kwargs):
        try:
            content_type = self.request.query_params.get("content_type", None)
            if not content_type is None:
                bucket_key = generate_bucket_key(content_type)
                pre_signed_url = generate_presigned_url(bucket_key, content_type)
                return API_RESPONSE.Return200Success(
                    "Presigned url", {"file_name": bucket_key, "url": pre_signed_url}
                )
        except Exception as err:
            logging.error(f"PreSignedUrlApi create: {err}", exc_info=True)

        return API_RESPONSE.Return400Error("Failed to generate presigned url")
