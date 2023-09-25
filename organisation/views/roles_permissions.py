from django.utils import timezone
from rest_framework import viewsets
from drf_yasg import openapi

from common.swagger.documentation import (
    swagger_auto_schema,
    swagger_wrapper,
    active_status,
)
from organisation.models import RolesPermissions
from organisation.serializers import (
    RolesPermissionSerializer,
    RolesPermissionAdminSerializer,
)
from organisation.helper import (
    getUsersActiveCount,
    getUsersInactiveCount,
    getUsersActiveCountForAdmin,
    getUsersInactiveCountForAdmin,
)
from users.models import User, UserProfiles
from common.helpers.response_helper import API_RESPONSE
import logging


class RolesPermissionsAPI(viewsets.ViewSet):
    http_method_names = ["get", "post", "put", "delete", "head", "options"]
    serializer_class = RolesPermissionSerializer

    # statis_roles = ["ADMIN", "MANAGER", "STAFF", "AGENT"]
    statis_roles = ["MANAGER", "STAFF", "AGENT"]

    @swagger_auto_schema(manual_parameters=[active_status], tags=["roles_permissions"])
    def list(self, request, *args, **kwargs):
        try:
            active_status = self.request.query_params.get("active")
            roles_permissions_info = RolesPermissions.objects.filter(
                organisation=request.userinfo["organisation"], is_active=True
            )
            if roles_permissions_info.count() == 0:
                roles = []
                for iterator in self.statis_roles:
                    roles.append(
                        RolesPermissions(
                            name=iterator,
                            description="",
                            permissions={},
                            organisation=request.userinfo["organisation"],
                        )
                    )
                roles_permissions_info = RolesPermissions.objects.bulk_create(roles)

            if active_status is not None:
                roles_permissions_info = []
                if active_status.lower() == "true":
                    if request.data.get("role") == "MANAGER":
                        roles_permissions = RolesPermissions.objects.filter(
                            status=True,
                            is_active=True,
                            organisation=request.userinfo["organisation"],
                        ).exclude(name="MANAGER")
                        roles_permissions_data = RolesPermissionSerializer(
                            roles_permissions, many=True
                        ).data
                    elif request.data.get("role") == "ADMIN":
                        roles_permissions = RolesPermissions.objects.filter(
                            status=True,
                            is_active=True,
                            organisation=request.userinfo["organisation"],
                        )
                        roles_permissions_data = RolesPermissionSerializer(
                            roles_permissions, many=True
                        ).data
                return API_RESPONSE.Return200Success(
                    "Organisation roles and permissions", roles_permissions_data
                )
            else:
                roles_permissions_data = []
                if request.data.get("role") == "ADMIN":
                    try:
                        roles_permissions_data = self.serializer_class(
                            roles_permissions_info, many=True
                        ).data
                        for data in roles_permissions_data:
                            if data["name"] == "MANAGER":
                                data[
                                    "staffs_active_count"
                                ] = getUsersActiveCountForAdmin(data)
                                data[
                                    "staffs_inactive_count"
                                ] = getUsersInactiveCountForAdmin(data)
                            elif data["name"] == "STAFF":
                                data[
                                    "staffs_active_count"
                                ] = getUsersActiveCountForAdmin(data)
                                data[
                                    "staffs_inactive_count"
                                ] = getUsersInactiveCountForAdmin(data)
                            elif data["name"] == "AGENT":
                                data[
                                    "staffs_active_count"
                                ] = getUsersActiveCountForAdmin(data)
                                data[
                                    "staffs_inactive_count"
                                ] = getUsersInactiveCountForAdmin(data)
                        admin = User.objects.get(
                            utype=User.UserTypes.ADMIN,
                            status=True,
                            is_active=True,
                            organisation=request.userinfo["organisation"],
                        )
                        roles_permissions_data.insert(
                            0,
                            {
                                "id": str(admin.id),
                                "name": "ADMIN",
                                "description": "",
                                "permissions": {},
                                "status": True,
                                "staffs_active_count": 1,
                                "staffs_inactive_count": 0,
                            },
                        )
                    except Exception:
                        pass
                elif request.data.get("role") == "MANAGER":
                    roles_permissions_data = self.serializer_class(
                        roles_permissions_info, many=True
                    ).data
                    manager_profile = UserProfiles.objects.get(
                        user=request.userinfo["id"],
                        is_active=True,
                        organisation=request.userinfo["organisation"],
                    )
                    for data in roles_permissions_data:
                        if data["name"] == "MANAGER":
                            data["staffs_active_count"] = getUsersActiveCount(
                                manager_profile, data
                            )
                            data["staffs_inactive_count"] = getUsersInactiveCount(
                                manager_profile, data
                            )
                        elif data["name"] == "STAFF":
                            data["staffs_active_count"] = getUsersActiveCount(
                                manager_profile, data
                            )
                            data["staffs_inactive_count"] = getUsersInactiveCount(
                                manager_profile, data
                            )
                        elif data["name"] == "AGENT":
                            data["staffs_active_count"] = getUsersActiveCount(
                                manager_profile, data
                            )
                            data["staffs_inactive_count"] = getUsersInactiveCount(
                                manager_profile, data
                            )

            return API_RESPONSE.Return200Success(
                "Organisation roles and permissions", roles_permissions_data
            )
        except Exception as err:
            logging.error(f"RolesPermissionsAPI destroy: {err}", exc_info=True)
            return API_RESPONSE.Return400Error(
                "Internal error, try again after some time."
            )

    @swagger_wrapper(
        {
            "name": openapi.TYPE_STRING,
            "description": openapi.TYPE_STRING,
            "permissions": openapi.TYPE_OBJECT,
        },
        ["roles_permissions"],
    )
    def create(self, request, *args, **kwargs):
        return API_RESPONSE.Return200Success("Currently Inactive")
        try:
            name = request.data["name"]
            description = request.data["description"]
            permissions = request.data["permissions"]
            organisation = request.userinfo["organisation"]

            try:
                check_roles_permissions = RolesPermissions.objects.filter(
                    name=name, organisation=organisation, is_active=True
                ).count()
                if check_roles_permissions > 0:
                    return API_RESPONSE.Return400Error("Role already exists")
            except:
                return API_RESPONSE.Return400Error("Role with name already exists")

            roles_permissions_info = RolesPermissions(
                name=name,
                description=description,
                permissions=permissions,
                organisation=organisation,
                created_by=request.userinfo["id"],
                updated_by=request.userinfo["id"],
            )
            roles_permissions_info.save()

            roles_permissions_data = self.serializer_class(roles_permissions_info).data
            return API_RESPONSE.Return200Success(
                "Role Created successfully", roles_permissions_data
            )
        except:
            return API_RESPONSE.Return400Error(
                "Internal error, try again after sometime."
            )

    @swagger_wrapper(
        {
            "name": openapi.TYPE_STRING,
            "description": openapi.TYPE_STRING,
            "permissions": openapi.TYPE_OBJECT,
            "status": openapi.TYPE_BOOLEAN,
        },
        ["roles_permissions"],
    )
    def update(self, request, *args, **kwargs):
        return API_RESPONSE.Return200Success(
            "Currently Inactive",
        )
        try:
            role_id = kwargs["pk"]
            organisation = request.userinfo["organisation"]

            try:
                roles_permission_info = RolesPermissions.objects.get(
                    id=role_id, organisation=organisation, is_active=True
                )
            except:
                return Return404Error("Invalid role id sent")

            try:
                if "name" in request.data:
                    check_roles_permissions = (
                        RolesPermissions.objects.filter(
                            name=request.data["name"],
                            organisation=organisation,
                            is_active=True,
                        )
                        .exclude(id=role_id)
                        .count()
                    )
                    if check_roles_permissions > 0:
                        return API_RESPONSE.Return400Error("Role already exists")
            except:
                return API_RESPONSE.Return400Error("Role with name already exists")

            serializer = self.serializer_class(
                roles_permission_info, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                roles_permission_info.updated_by = request.userinfo["id"]
                roles_permission_info.save()
            else:
                return Return404Error("Invalid role payload sent")

            return API_RESPONSE.Return200Success(
                "Role Updated successfully", serializer.data
            )
        except:
            return API_RESPONSE.Return400Error(
                "Internal error, try again after sometime."
            )

    @swagger_auto_schema(manual_parameters=[], tags=["roles_permissions"])
    def destroy(self, request, *args, **kwargs):
        return API_RESPONSE.Return200Success("Currently Inactive")
        try:
            role_id = kwargs["pk"]
            organisation = request.userinfo["organisation"]
            try:
                roles_permission_info = RolesPermissions.objects.get(
                    id=role_id, organisation=organisation, is_active=True
                )
            except:
                return Return404Error("Invalid role id sent")

            roles_permission_info.is_active = False
            roles_permission_info.deleted_by = request.userinfo["id"]
            roles_permission_info.deleted_at = timezone.now()
            roles_permission_info.updated_by = request.userinfo["id"]
            roles_permission_info.save()

            return Response(
                {
                    "status": 200,
                    "message": "Role Deleted successfully",
                    "data": [],
                    "reload": "",
                },
                status=status.HTTP_200_OK,
            )

        except:
            return API_RESPONSE.Return400Error(
                "Internal error, try again after sometime."
            )
