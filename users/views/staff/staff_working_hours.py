from rest_framework import viewsets
from organisation.models import WorkingHours

from organisation.serializers import WorkingHourSerializer
from common.swagger.documentation import (
    swagger_auto_schema,
    staff_working_hours_create_api,
)
from common.helpers.response_helper import API_RESPONSE


class StaffWorkingHoursAPI(viewsets.ViewSet):
    http_method_names = ["get", "put", "head", "options"]
    serializer_class = WorkingHourSerializer

    @swagger_auto_schema(manual_parameters=[], tags=["staff"])
    def retrieve(self, request, *args, **kwargs):
        try:
            staff_id = kwargs["pk"]
            try:
                working_hours_info = WorkingHours.objects.filter(
                    ref_id=staff_id,
                    organisation=request.userinfo["organisation"],
                    type=WorkingHours.WorkingHourTypes.USER,
                )
                if working_hours_info.count() < 7:
                    return API_RESPONSE.Return404Error("No record found")
            except:
                days = []
                org_working_hours = WorkingHours.objects.filter(
                    ref_id=request.userinfo["organisation"],
                    organisation=request.userinfo["organisation"],
                    type=WorkingHours.WorkingHourTypes.ORGANISATION,
                )
                for iterator in org_working_hours:
                    days.append(
                        WorkingHours(
                            days=iterator.days,
                            slots=iterator.slots,
                            type=WorkingHours.WorkingHourTypes.USER,
                            ref_id=staff_id,
                            organisation=request.userinfo["organisation"],
                        )
                    )
                working_hours_info = WorkingHours.objects.bulk_create(days)

            return_data = self.serializer_class(working_hours_info, many=True).data

            return API_RESPONSE.Return200Success("User working hours", return_data)
        except:
            return API_RESPONSE.Return400Error(
                "Internal error, try again after sometime"
            )

    @staff_working_hours_create_api
    def update(self, request, *args, **kwargs):  # [TODO]: slot validations
        try:
            staff_id = kwargs["pk"]
            try:
                working_hours_info = WorkingHours.objects.filter(
                    ref_id=staff_id,
                    organisation=request.userinfo["organisation"],
                    type=WorkingHours.WorkingHourTypes.USER,
                )
                if working_hours_info.count() < 7:
                    return API_RESPONSE.Return404Error("No record found")

                for wh in working_hours_info:
                    wh.slots = request.data[wh.days]["slots"]
                    wh.status = request.data[wh.days]["status"]

                WorkingHours.objects.bulk_update(
                    working_hours_info, ["slots", "status"]
                )

            except:
                days = []
                for iterator in WorkingHours.DayTypes:
                    days.append(
                        WorkingHours(
                            days=iterator,
                            slots=request.data[iterator]["slots"],
                            status=request.data[iterator]["status"],
                            type=WorkingHours.WorkingHourTypes.USER,
                            ref_id=staff_id,
                            organisation=request.userinfo["organisation"],
                        )
                    )
                working_hours_info = WorkingHours.objects.bulk_create(days)

            return_data = self.serializer_class(working_hours_info, many=True).data

            return API_RESPONSE.Return200Success(
                "User working hours updated successfully", return_data
            )
        except:
            return API_RESPONSE.Return400Error(
                "Internal error, try again after sometime."
            )
