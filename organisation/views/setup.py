from django.db.models import Q
from rest_framework import viewsets
from organisation.models import Setup
from organisation.serializers import SetupSerializer
from organisation.helper import getAuditPayloadForSetp
from common.events.publishers.user_service_publisher import publish_event
from common.configs.config import config as cfg
from common.helpers.response_helper import API_RESPONSE
from common.swagger.documentation import swagger_wrapper
from drf_yasg import openapi
import logging


class SetupAPI(viewsets.ViewSet):
    http_method_names = ["get", "put"]
    serializer_class = SetupSerializer

    def list(self, request, *args, **kwargs):
        query_set = Q(
            organisation=request.data.get("organisation", None),
            is_active=True,
        )
        if request.data.get("role") in [
            cfg.get("user_types", "STAFF"),
            cfg.get("user_types", "AGENT"),
            cfg.get("user_types", "MANAGER"),
        ]:
            query_set &= ~Q(name="APPOINTMENTS")
            query_set &= ~Q(name="PRODUCTS/ SERVICES")
            query_set &= ~Q(name="BOT")
            query_set &= ~Q(name="KNOWLEDGE BASE")
            query_set &= ~Q(name="SMART POP-UPS")
            query_set &= ~Q(name="ANNOUNCEMENTS")

        setup_data = Setup.objects.filter(query_set).order_by("created_at")
        serializer = self.serializer_class(setup_data, many=True).data
        return API_RESPONSE.Return200Success("Organisation setup info", serializer)

    @swagger_wrapper(
        {
            "status": openapi.TYPE_BOOLEAN,
        }
    )
    def update(self, request, *args, **kwargs):
        try:
            setup_obj = Setup.objects.get(
                id=kwargs.get("pk"),
                organisation=request.data.get("organisation", None),
                is_active=True,
            )
            setup_obj.status = request.data.get("status", False)
            setup_obj.updated_by = request.userinfo["id"]
            setup_obj.save()

            audit_payload = getAuditPayloadForSetp(
                setup_obj, request.data.get("role"), request.userinfo["id"]
            )
            if audit_payload:
                event_status = publish_event(
                    audit_payload,
                    cfg.get("events", "AUDIT_SERVICE_EXCHANGE"),
                    cfg.get("events", "AUDIT_SERVICE_SETUP_UPDATE_ROUTING_KEY"),
                )
                if not event_status:
                    # Handle the failed the case
                    pass
            return API_RESPONSE.Return200Success(
                "Status updated",
            )
        except Exception as err:
            logging.error(f"SetupAPI update: {err}", exc_info=True)
            return API_RESPONSE.Return400Error("Not found")
