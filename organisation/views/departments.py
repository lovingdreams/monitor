from django.utils import timezone
from rest_framework import viewsets
from drf_yasg import openapi

from common.swagger.documentation import (
    swagger_auto_schema,
    swagger_wrapper,
    active_status,
)
from organisation.models import Departments
from organisation.serializers import DepartmentSerializer, DepartmentListSerializer
from organisation.helper import check_name
from common.helpers.response_helper import API_RESPONSE
from users.models import User, UserDepartments, UserProfiles


class DepartmentsAPI(viewsets.ViewSet):
    http_method_names = ["get", "post", "put", "delete", "head", "options"]
    serializer_class = DepartmentSerializer

    @swagger_auto_schema(manual_parameters=[active_status], tags=["departments"])
    def list(self, request, *args, **kwargs):
        try:
            active_status = self.request.query_params.get("active")
            if active_status is not None:
                departments_data = []
                if active_status.lower() == "true":
                    if request.data.get("role") == "MANAGER":
                        user_profile = UserProfiles.objects.filter(
                            user=request.userinfo["id"],
                            organisation=request.userinfo["organisation"],
                            is_active=True,
                            status=True,
                        )
                        departments_data.append(
                            DepartmentListSerializer(user_profile[0].department).data
                        )
                    elif request.data.get("role") == "ADMIN":
                        departments_info = Departments.objects.filter(
                            organisation=request.userinfo["organisation"],
                            is_active=True,
                            status=True,
                        )
                        departments_data = DepartmentListSerializer(
                            departments_info, many=True
                        ).data
                    return API_RESPONSE.Return200Success(
                        "Organisation departments", departments_data
                    )
            departments_data = []
            if request.data.get("role") == "ADMIN":
                departments_info = Departments.objects.filter(
                    organisation=request.userinfo["organisation"], is_active=True
                )
                departments_data = DepartmentListSerializer(
                    departments_info, many=True
                ).data
            elif request.data.get("role") in ["MANAGER", "STAFF", "AGENT"]:
                user_profile = UserProfiles.objects.filter(
                    user=request.userinfo["id"],
                    organisation=request.userinfo["organisation"],
                    is_active=True,
                )
                departments_data.append(
                    DepartmentListSerializer(user_profile[0].department).data
                )
            return API_RESPONSE.Return200Success(
                "Organisation departments", departments_data
            )
        except Exception as err:
            return API_RESPONSE.Return400Error(
                "Internal error, try again after some time."
            )

    @swagger_wrapper(
        {
            "name": openapi.TYPE_STRING,
            "description": openapi.TYPE_STRING,
        },
        ["departments"],
    )
    def create(self, request, *args, **kwargs):
        try:
            name = request.data["name"]
            description = request.data["description"]
            organisation = request.userinfo["organisation"]

            error = check_name(request.data.get("name"))
            if error:
                return API_RESPONSE.Return400Error("Invalid department name")
            try:
                check_departments = Departments.objects.filter(
                    name=name, organisation=organisation, is_active=True
                ).count()
                if check_departments > 0:
                    return API_RESPONSE.Return400Error("Department already exists")
            except:
                return API_RESPONSE.Return400Error(
                    "Department with name already exists"
                )

            departments_info = Departments(
                name=name,
                description=description,
                organisation=organisation,
                created_by=request.userinfo["id"],
                updated_by=request.userinfo["id"],
            )
            departments_info.save()

            # if "staff" in request.data and len(request.data["staff"]) > 0:
            #     try:
            #         staff_members = []
            #         staff_flag = False
            #         for staff in set(request.data["staff"]):
            #             try:
            #                 user_info = User.objects.get(
            #                     id=staff, organisation=organisation, is_active=True
            #                 )
            #                 staff_members.append(
            #                     UserDepartments(
            #                         user=user_info,
            #                         department=departments_info,
            #                         organisation=organisation,
            #                         created_by=request.userinfo["id"],
            #                         updated_by=request.userinfo["id"],
            #                     )
            #                 )
            #             except:
            #                 staff_flag = True

            #         UserDepartments.objects.bulk_create(staff_members)
            #     except:
            #         staff_flag = True

            departments_data = self.serializer_class(departments_info).data

            return API_RESPONSE.Return201Created(
                "Department Created successfully", departments_data
            )
        except:
            return API_RESPONSE.Return400Error(
                "Internal error, try again after sometime."
            )

    @swagger_wrapper(
        {
            "name": openapi.TYPE_STRING,
            "description": openapi.TYPE_STRING,
            "status": openapi.TYPE_BOOLEAN,
        },
        ["departments"],
    )
    def update(self, request, *args, **kwargs):
        try:
            department_id = kwargs["pk"]
            organisation = request.userinfo["organisation"]

            try:
                department_info = Departments.objects.get(
                    id=department_id, organisation=organisation, is_active=True
                )
            except:
                return API_RESPONSE.Return400Error("Invalid department sent")

            try:
                if "name" in request.data:
                    error = check_name(request.data.get("name"))
                    if error:
                        return API_RESPONSE.Return400Error("Invalid department name")

                    check_departments = (
                        Departments.objects.filter(
                            name=request.data["name"],
                            organisation=organisation,
                            is_active=True,
                        )
                        .exclude(id=department_id)
                        .count()
                    )
                    if check_departments > 0:
                        return API_RESPONSE.Return400Error("Department already exists")
            except:
                return API_RESPONSE.Return400Error(
                    "Department with name already exists"
                )

            # staff_flag = False

            # if "staff" in request.data and len(request.data["staff"]) > 0:
            #     try:
            #         existing_users = UserDepartments.objects.filter(
            #             department=department_info, organisation=organisation
            #         )
            #         existing_users.delete()

            #         staff_members = []
            #         for staff in set(request.data["staff"]):
            #             try:
            #                 user_info = User.objects.get(
            #                     id=staff, organisation=organisation, is_active=True
            #                 )
            #                 staff_members.append(
            #                     UserDepartments(
            #                         user=user_info,
            #                         department=department_info,
            #                         organisation=organisation,
            #                         created_by=request.userinfo["id"],
            #                         updated_by=request.userinfo["id"],
            #                     )
            #                 )
            #             except:
            #                 staff_flag = True

            #         UserDepartments.objects.bulk_create(staff_members)
            #     except:
            #         staff_flag = True

            serializer = self.serializer_class(
                department_info, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                department_info.updated_by = request.userinfo["id"]
                department_info.save()
            else:
                return API_RESPONSE.Return400Error("Invalid departments payload sent")

            return API_RESPONSE.Return200Success(
                "Department Updated successfully", serializer.data
            )
        except:
            return API_RESPONSE.Return400Error(
                "Internal error, try again after sometime."
            )

    @swagger_auto_schema(manual_parameters=[], tags=["departments"])
    def destroy(self, request, *args, **kwargs):
        try:
            department_id = kwargs["pk"]
            organisation = request.userinfo["organisation"]
            try:
                department_info = Departments.objects.get(
                    id=department_id, organisation=organisation, is_active=True
                )
            except:
                return API_RESPONSE.Return400Error("Invalid department")

            department_info.is_active = False
            department_info.deleted_by = request.userinfo["id"]
            department_info.deleted_at = timezone.now()
            department_info.updated_by = request.userinfo["id"]
            department_info.save()

            # existing_users = UserDepartments.objects.filter(
            #     department=department_info, organisation=organisation
            # )
            # existing_users.delete()

            return API_RESPONSE.Return200Success("Department Deleted successfully")
        except:
            return API_RESPONSE.Return400Error(
                "Internal error, try again after sometime."
            )
