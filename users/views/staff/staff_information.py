from rest_framework import viewsets, generics, mixins
from rest_framework.pagination import PageNumberPagination
from drf_yasg import openapi
from django.utils import timezone
from django.db.models import Q

from common.helpers.common_helper import random_string_generator, send_mail
from common.swagger.documentation import (
    swagger_auto_schema,
    swagger_wrapper,
    page_param,
    offset_param,
    active_status,
    booking_status,
    email_param,
    staff_id,
    search,
    department,
    role,
)
from common.helpers.response_helper import API_RESPONSE
from common.events.publishers.user_service_publisher import publish_event
from common.configs.config import config as cfg
from users.helper import (
    getStaffCreationEmailPayload,
    getStaffPayloadForAudit,
    getPayloadForCalendarService,
    makeCalendarServiceCall,
    getTimezoneUpdatePayloadForCalendarService,
)
from organisation.models import Departments, RolesPermissions, Badge, Locations
from organisation.serializers import LocationsSerializer
from users.models import User, UserDepartments, UserProfiles, UserOTPs, StaffLocations
from users.serializers import (
    StaffSerializer,
    UserUpdateSerializer,
    UserProfilesSerializer,
    UserSerializer,
    StaffListSerializer,
    UserProfilesUpdateSerializer,
)
import logging


class StaffInformationAPI(viewsets.ViewSet):
    http_method_names = ["post", "get", "delete", "put", "head", "options"]
    serializer_class = StaffSerializer

    @swagger_auto_schema(
        manual_parameters=[
            page_param,
            offset_param,
            active_status,
            booking_status,
            email_param,
            search,
            department,
            role,
        ],
        tags=["staff"],
    )
    def list(self, request, *args, **kwargs):
        page = int(self.request.query_params.get(page_param.name, 0))
        # Offset is 10 fixed only 10 records added
        offset = int(self.request.query_params.get(offset_param.name, 20))
        # offset = 10
        active_status = self.request.query_params.get("active")
        booking_status = self.request.query_params.get("booking")
        email_param = self.request.query_params.get("email")
        search = self.request.query_params.get("search")
        department = self.request.query_params.get("department")
        role = self.request.query_params.get("role")
        staffs_data = []

        # Search based on fname and lname
        if search not in ["", " ", None]:
            if page <= 0:
                return API_RESPONSE.Return400Error("Invalid page")

            if request.data.get("role") == "ADMIN":
                # fname_search_guery_ser = Q(
                #     fname__icontains=search,
                #     organisation=request.userinfo["organisation"],
                #     is_active=True,
                # )
                # lname_search_guery_ser = Q(
                #     lname__icontains=search,
                #     organisation=request.userinfo["organisation"],
                #     is_active=True,

                # users = (
                #     User.objects.filter(lname_search_guery_ser | fname_search_guery_ser)
                #     .exclude(utype=User.UserTypes.ENDUSER)
                #     .distinct()
                #     .order_by("-created_at")
                # )
                query = (
                    Q(user__fname__icontains=search)
                    | Q(user__lname__icontains=search)
                    | Q(department__name__icontains=search)
                    | Q(role__name__icontains=search)
                )

                matching_user_profiles = UserProfiles.objects.filter(query)
                # Retrieve the users associated with matching UserProfiles
                users = (
                    User.objects.filter(
                        user_info_user__in=matching_user_profiles,
                        organisation=request.userinfo["organisation"],
                        is_active=True,
                    )
                    .exclude(utype=User.UserTypes.ENDUSER)
                    .distinct()
                    .order_by("-created_at")
                )

            elif request.data.get("role") in ["MANAGER", "STAFF", "AGENT"]:
                manager_profile = UserProfiles.objects.get(
                    user=request.userinfo["id"],
                    is_active=True,
                    organisation=request.userinfo["organisation"],
                )
                query = (
                    Q(user__fname__icontains=search)
                    | Q(user__lname__icontains=search)
                    | Q(department__name__icontains=search)
                    | Q(role__name__icontains=search)
                )

                matching_user_profiles = UserProfiles.objects.filter(
                    query, department=manager_profile.department
                )
                users = (
                    User.objects.filter(
                        user_info_user__in=matching_user_profiles,
                        organisation=request.userinfo["organisation"],
                        is_active=True,
                    )
                    .exclude(utype=User.UserTypes.ENDUSER)
                    .distinct()
                    .order_by("-created_at")
                )
                # users_list = (
                #     UserProfiles.objects.filter(department=manager_profile.department)
                #     .select_related("user")
                #     .filter(user__is_active=True)
                #     .values_list("user__id")
                # )
                # fname_search_guery_ser = Q(
                #     id__in=users_list,
                #     fname__icontains=search,
                #     organisation=request.userinfo["organisation"],
                #     is_active=True,
                # )
                # lname_search_guery_ser = Q(
                #     id__in=users_list,
                #     lname__icontains=search,
                #     organisation=request.userinfo["organisation"],
                #     is_active=True,
                # )
                # users = (
                #     User.objects.filter(fname_search_guery_ser | lname_search_guery_ser)
                #     .order_by("-created_at")
                #     .distinct()
                # )
            else:
                users = []

            staff_data = StaffListSerializer(users, many=True).data
            pagination = PageNumberPagination()
            pagination.page_size = offset
            pagination.page_query_param = cfg.get("common", "PAGE")
            query_set = pagination.paginate_queryset(queryset=users, request=request)
            staff_serializer = StaffListSerializer(query_set, many=True)
            pagination_response = pagination.get_paginated_response(
                staff_serializer.data
            )
            pagination_response.data["count"] = len(staff_data)
            pagination_response.data["status"] = 200
            pagination_response.data["message"] = "Staff info"
            pagination_response.data["data"] = pagination_response.data["results"]
            pagination_response.data["page"] = page
            del pagination_response.data["results"]
            return pagination_response

        # Search based on department
        if department not in ["", " ", None]:
            if page <= 0:
                return API_RESPONSE.Return400Error("Invalid page")

            if request.data.get("role") == "ADMIN":
                users_list = (
                    UserProfiles.objects.filter(department=department)
                    .select_related("user")
                    .filter(user__is_active=True)
                    .values_list("user__id")
                )
                users = User.objects.filter(id__in=users_list).order_by("-created_at")
            elif request.data.get("role") in ["MANAGER", "STAFF", "AGENT"]:
                manager_profile = UserProfiles.objects.get(
                    user=request.userinfo["id"],
                    is_active=True,
                    organisation=request.userinfo["organisation"],
                )
                if department != str(manager_profile.department.id):
                    return API_RESPONSE.Return400Error("You don't have permission")
                users_list = (
                    UserProfiles.objects.filter(department=manager_profile.department)
                    .select_related("user")
                    .filter(user__is_active=True)
                    .values_list("user__id")
                )
                users = User.objects.filter(id__in=users_list).order_by("-created_at")
            else:
                users = []
            staff_data = StaffListSerializer(users, many=True).data
            pagination = PageNumberPagination()
            pagination.page_size = offset
            pagination.page_query_param = cfg.get("common", "PAGE")
            query_set = pagination.paginate_queryset(queryset=users, request=request)
            staff_serializer = StaffListSerializer(query_set, many=True)
            pagination_response = pagination.get_paginated_response(
                staff_serializer.data
            )
            pagination_response.data["count"] = len(staff_data)
            pagination_response.data["status"] = 200
            pagination_response.data["message"] = "Staff info"
            pagination_response.data["data"] = pagination_response.data["results"]
            pagination_response.data["page"] = page
            del pagination_response.data["results"]
            return pagination_response

        # Search based on role
        if role not in ["", " ", None]:
            if page <= 0:
                return API_RESPONSE.Return400Error("Invalid page")

            if request.data.get("role") == "ADMIN":
                users_list = (
                    UserProfiles.objects.filter(role=role)
                    .select_related("user")
                    .filter(user__is_active=True)
                    .values_list("user__id")
                )
                users = User.objects.filter(id__in=users_list).order_by("-created_at")

            elif request.data.get("role") == "MANAGER":
                users_list = (
                    UserProfiles.objects.filter(
                        role=role, department=request.data.get("dept")
                    )
                    .select_related("user")
                    .filter(user__is_active=True)
                    .values_list("user__id")
                )
                users = User.objects.filter(id__in=users_list).order_by("-created_at")

            else:
                return API_RESPONSE.Return400Error("You don't have permission")

            staff_data = StaffListSerializer(users, many=True).data
            pagination = PageNumberPagination()
            pagination.page_size = offset
            pagination.page_query_param = cfg.get("common", "PAGE")
            query_set = pagination.paginate_queryset(queryset=users, request=request)
            staff_serializer = StaffListSerializer(query_set, many=True)
            pagination_response = pagination.get_paginated_response(
                staff_serializer.data
            )
            pagination_response.data["count"] = len(staff_data)
            pagination_response.data["status"] = 200
            pagination_response.data["message"] = "Staff info"
            pagination_response.data["data"] = pagination_response.data["results"]
            pagination_response.data["page"] = page
            del pagination_response.data["results"]
            return pagination_response

        # Staff list
        if page > 0:
            if request.data.get("role") == "ADMIN":
                staff_query_set = Q(
                    is_active=True,
                    organisation=request.userinfo["organisation"],
                    utype=User.UserTypes.STAFF,
                )
                staffs_information = User.objects.filter(staff_query_set).order_by(
                    "-created_at"
                )
            elif request.data.get("role") in ["MANAGER", "STAFF", "AGENT"]:
                users_list = (
                    UserProfiles.objects.filter(department=request.data.get("dept"))
                    .select_related("user")
                    .filter(user__is_active=True)
                    .values_list("user__id")
                )
                staffs_information = User.objects.filter(id__in=users_list).order_by(
                    "-created_at"
                )
            else:
                staffs_information = []
            staffs_data = StaffListSerializer(staffs_information, many=True).data
            try:
                pagination = PageNumberPagination()
                pagination.page_size = offset
                pagination.page_query_param = cfg.get("common", "PAGE")
                query_set = pagination.paginate_queryset(
                    queryset=staffs_information, request=request
                )
                appointments_serializer = StaffListSerializer(query_set, many=True)
                pagination_response = pagination.get_paginated_response(
                    appointments_serializer.data
                )
                pagination_response.data["count"] = len(staffs_data)
                pagination_response.data["status"] = 200
                pagination_response.data["message"] = "Staff info"
                pagination_response.data["data"] = pagination_response.data["results"]
                if page == 1:
                    if request.data.get("role") == "ADMIN":
                        try:
                            admin_query_set = Q(
                                is_active=True,
                                organisation=request.userinfo["organisation"],
                                utype=User.UserTypes.ADMIN,
                            )
                            admin_information = User.objects.get(admin_query_set)
                            admin_data = StaffListSerializer(admin_information).data
                            # pagination_response.data["data"].append(admin_data)
                            pagination_response.data["data"].insert(0, admin_data)
                            pagination_response.data["count"] += 1
                        except Exception as err:
                            pass
                pagination_response.data["page"] = page
                del pagination_response.data["results"]
                return pagination_response
            except Exception as err:
                logging.error(f"StaffInformationAPI list: {err}", exc_info=True)
                pass

        # Staff list based on active status
        if active_status == "true" or active_status == "True":
            staff_query_set = Q(
                is_active=True,
                status=True,
                organisation=request.userinfo["organisation"],
                utype=User.UserTypes.STAFF,
            )
            staffs_information = User.objects.filter(staff_query_set).order_by(
                "-created_at"
            )
            staffs_data = StaffListSerializer(staffs_information, many=True).data
            try:
                admin_query_set = Q(
                    is_active=True,
                    organisation=request.userinfo["organisation"],
                    utype=User.UserTypes.ADMIN,
                )
                admin_information = User.objects.get(admin_query_set)
                admin_data = StaffListSerializer(admin_information).data
                staffs_data.insert(0, admin_data)
            except Exception:
                pass

            return API_RESPONSE.Return200Success("Staff list", staffs_data)

        # Staff list based on booking status
        if booking_status in ["true", "True"]:
            staff_query_set = Q(
                is_active=True,
                status=True,
                enable_for_booking=True,
                organisation=request.userinfo["organisation"],
                utype=User.UserTypes.STAFF,
            )
            staffs_information = User.objects.filter(staff_query_set).order_by(
                "-created_at"
            )
            staffs_data = StaffListSerializer(staffs_information, many=True).data
            try:
                admin_query_set = Q(
                    is_active=True,
                    organisation=request.userinfo["organisation"],
                    utype=User.UserTypes.ADMIN,
                )
                admin_information = User.objects.get(admin_query_set)
                admin_data = StaffListSerializer(admin_information).data
                staffs_data.insert(0, admin_data)
            except Exception:
                pass

        # Staff details based on email
        if email_param not in ["", " ", None]:
            users = User.objects.filter(
                email=email_param,
                organisation=request.userinfo["organisation"],
                is_active=True,
            )
            if users.count() == 0:
                return API_RESPONSE.Return400Error("No records found")
            if users.count() > 1:
                return API_RESPONSE.Return400Error("Multiple records found")
            staffs_data = StaffListSerializer(users[0]).data

        return API_RESPONSE.Return200Success("Staff list", staffs_data)

    @swagger_wrapper(
        {
            "fname": openapi.TYPE_STRING,
            "lname": openapi.TYPE_STRING,
            "email": openapi.TYPE_STRING,
            "password": openapi.TYPE_STRING,
            "phone_number": openapi.TYPE_STRING,
            "ccode": openapi.TYPE_STRING,
            "department": openapi.TYPE_STRING,
            "role_id": openapi.TYPE_STRING,
            "enable_for_booking": openapi.TYPE_BOOLEAN,
            "badge": openapi.TYPE_STRING,
            "time_zone": openapi.TYPE_STRING,
        },
        ["staff"],
    )
    def create(self, request, *args, **kwargs):
        try:
            fname = request.data["fname"]
            lname = request.data["lname"]
            email = request.data["email"]
            password = request.data["password"]
            role = request.data["role_id"]
            phone_number = request.data["phone_number"]
            ccode = request.data["ccode"]
            organisation = request.userinfo["organisation"]

            if password is None or len(password) == 0:
                return API_RESPONSE.Return400Error("Password should not be empty")

            # Check whether email exists
            try:
                User.objects.get(email=email)
                return API_RESPONSE.Return400Error("User with mail already exists")
            except:
                pass

            # Check whether phone number exists
            # try:
            #     User.objects.get(phone_number=phone_number, ccode=ccode)
            #     return API_RESPONSE.Return400Error("User with phone number already exists")
            # except:
            #     pass

            # Check whether role exists
            try:
                if "role_id" in request.data and request.data["role_id"] != "":

                    role = RolesPermissions.objects.get(
                        id=request.data["role_id"],
                        status=True,
                        is_active=True,
                        organisation=request.userinfo["organisation"],
                    )
                else:
                    role = ""
            except Exception as err:
                logging.error(f"Staff creation role exception: {err}", exc_info=True)
                return API_RESPONSE.Return400Error("Invalid role sent")

            # Check whether department exists
            try:
                department = Departments.objects.get(
                    id=request.data["department"], status=True, is_active=True
                )
            except Exception as err:
                return API_RESPONSE.Return400Error("Invalid department sent")

            if role.name == "MANAGER":
                user_profiles_list = UserProfiles.objects.filter(
                    role=role,
                    department=department,
                    is_active=True,
                    organisation=request.userinfo["organisation"],
                )
                if user_profiles_list.count() >= 1:
                    return API_RESPONSE.Return400Error("Manager already exist")

            # create username
            username = (
                email.split("@")[0]
                + "--STAFF--"
                + str(organisation)
                + "@"
                + email.split("@")[1]
            )

            staff_info = User(
                fname=fname,
                lname=lname,
                email=email,
                phone_number=phone_number,
                ccode=ccode,
                organisation=organisation,
                username=username,
                utype=User.UserTypes.STAFF,
                source=User.SourceTypes.MANUAL,
                created_by=request.userinfo["id"],
                updated_by=request.userinfo["id"],
                verified=True,
                enable_for_booking=request.data.get("enable_for_booking", False),
            )

            staff_info.set_password(password)
            staff_info.save()

            # create user information
            user_information = UserProfiles(
                user=staff_info,
                organisation=organisation,
                role=role,
                department=department,
                time_zone=request.data.get("time_zone", None),
            )
            user_information.save()

            # create user locations
            staff_locations_list = []
            for location_id in request.data.get("locations"):
                try:
                    location = Locations.objects.get(
                        id=location_id,
                        status=True,
                        is_active=True,
                        organisation=request.userinfo["organisation"],
                    )
                    staff_locations_list.append(
                        StaffLocations(
                            user=staff_info,
                            location=location,
                            organisation=request.data.get("organisation"),
                            created_by=request.data.get("user_id"),
                        )
                    )
                except Exception:
                    user_information.delete()
                    staff_info.delete()
                    return API_RESPONSE.Return400Error("Invalid locations provided")
            StaffLocations.objects.bulk_create(staff_locations_list)

            if "badge" in request.data:
                try:
                    badge = Badge.objects.get(
                        id=request.data.get("badge"),
                        status=True,
                        is_active=True,
                        organisation=organisation,
                    )
                    user_information.badge = badge
                    user_information.save()
                except Exception:
                    pass

            # create and send activation code
            otp = random_string_generator(16)
            user_otp = UserOTPs(
                user=staff_info,
                organisation=organisation,
                created_by=staff_info,
                otp=otp,
                sent_to=email,
                used_for=UserOTPs.UsedTypes.ACTIVATE,
                sent_type=UserOTPs.SentTypes.MAIL,
            )
            user_otp.save()

            # send_mail(email, otp, str(staff_info))  # send email to user
            mail_status = publish_event(
                getStaffCreationEmailPayload(staff_info, password),
                cfg.get("events", "COMMUNICATION_EXCHANGE"),
                cfg.get("events", "STAFF_REGISTER_ROUTING_KEY"),
            )
            if not mail_status:
                # Mail sending is failed Handle the case
                pass

            # staff_flag = False
            # if "departments" in request.data and len(request.data["departments"]) != 0:
            #     try:
            #         departments_list = []
            #         for department in set(request.data["departments"]):
            #             try:
            #                 department_info = Departments.objects.get(
            #                     id=department,
            #                     organisation=organisation,
            #                     is_active=True,
            #                     status=True,
            #                 )
            #                 departments_list.append(
            #                     UserDepartments(
            #                         user=staff_info,
            #                         department=department_info,
            #                         organisation=organisation,
            #                         created_by=request.userinfo["id"],
            #                         updated_by=request.userinfo["id"],
            #                     )
            #                 )
            #             except:
            #                 staff_flag = True

            #         UserDepartments.objects.bulk_create(departments_list)
            #     except:
            #         staff_flag = True

            staff_data = self.serializer_class(staff_info).data

            audit_payload = getStaffPayloadForAudit(staff_info)
            if audit_payload is not None:
                event_status = publish_event(
                    audit_payload,
                    cfg.get("events", "AUDIT_SERVICE_EXCHANGE"),
                    cfg.get("events", "AUDIT_SERVICE_STAFF_CREATE_ROUTING_KEY"),
                )
                if not event_status:
                    # Handle the failed the case
                    pass
            else:
                # Handle the failed the case
                pass

            staff_payload = getPayloadForCalendarService(
                staff_info, User.UserTypes.STAFF, request.data.get("time_zone", None)
            )
            if staff_payload is not None:
                event_status = publish_event(
                    staff_payload,
                    cfg.get("events", "CALENDAR_SERVICE_EXCHANGE"),
                    cfg.get("events", "WORKING_HOUR_CREATE_ROUTING_KEY"),
                )
                if not event_status:
                    # Handle the failed the case
                    pass
            else:
                # Handle the failed the case
                pass

            # api_status = makeCalendarServiceCall(
            #     staff_info, request.headers.get("Authorization")
            # )
            # if not api_status:
            #     # Handle the failed case
            #     pass

            return API_RESPONSE.Return201Created(
                "Staff created successfully", staff_data
            )
        except Exception as err:
            logging.error(f"StaffInformationAPI create: {err}", exc_info=True)
            return API_RESPONSE.Return400Error(
                "Internal error, try again after some time."
            )

    @swagger_auto_schema(manual_parameters=[], tags=["staff"])
    def retrieve(self, request, *args, **kwargs):
        try:
            staff_id = kwargs["pk"]
            try:
                staff_info = User.objects.get(
                    id=staff_id,
                    is_active=True,
                    organisation=request.userinfo["organisation"],
                )
            except:
                return API_RESPONSE.Return404Error("Staff not found")

            try:
                user_information = UserProfiles.objects.get(user=staff_info)
            except:
                user_information = UserProfiles(
                    user=staff_info, organisation=request.userinfo["organisation"]
                )
                user_information.save()

            user_data = StaffListSerializer(staff_info).data
            user_information_data = UserProfilesSerializer(user_information).data

            return_data = {**user_information_data, **user_data}
            # return_data = {**user_data}
            return_data["locations"] = list(
                StaffLocations.objects.filter(
                    user=staff_info,
                    is_active=True,
                    organisation=request.userinfo["organisation"],
                ).values_list("location", flat=True)
            )

            return API_RESPONSE.Return200Success("User info", return_data)
        except:
            return API_RESPONSE.Return400Error(
                "Internal error, try again after some time."
            )

    @swagger_wrapper(
        {
            "fname": openapi.TYPE_STRING,
            "lname": openapi.TYPE_STRING,
            "phone_number": openapi.TYPE_STRING,
            "ccode": openapi.TYPE_STRING,
            "department": openapi.TYPE_STRING,
            "role_id": openapi.TYPE_STRING,
            "date_of_birth": openapi.TYPE_STRING,
            "gender": openapi.TYPE_STRING,
            "designation": openapi.TYPE_STRING,
            "specialisation": openapi.TYPE_STRING,
            "age": openapi.TYPE_STRING,
            "experience": openapi.TYPE_STRING,
            "qualification": openapi.TYPE_STRING,
            "description": openapi.TYPE_STRING,
            "time_zone": openapi.TYPE_STRING,
        },
        ["staff"],
    )
    def update(self, request, *args, **kwargs):
        try:
            staff_id = kwargs["pk"]
            try:
                staff_info = User.objects.get(
                    id=staff_id,
                    is_active=True,
                    organisation=request.userinfo["organisation"],
                )
                user_info = UserProfiles.objects.get(
                    user=staff_info,
                    organisation=request.userinfo["organisation"],
                )
            except:
                return API_RESPONSE.Return400Error("Staff not found")

            if request.data.get("role") == "MANAGER":
                try:
                    manager_profile = UserProfiles.objects.get(
                        user=request.userinfo["id"],
                        organisation=request.userinfo["organisation"],
                    )
                    if manager_profile.department != user_info.department:
                        return API_RESPONSE.Return400Error("You don't have permission")
                except Exception:
                    return API_RESPONSE.Return400Error("Something went wrong")

            if request.data.get("role") in ["STAFF", "AGENT"]:
                if str(staff_info.id) != request.data.get("user_id"):
                    return API_RESPONSE.Return400Error("You don't have permission")

            if "status" in request.data and len(request.data) == 6:
                staff_info.status = request.data.get("status")
                staff_info.save()
                event_status = publish_event(
                    getStaffPayloadForAudit(staff_info),
                    cfg.get("events", "AUDIT_SERVICE_EXCHANGE"),
                    cfg.get("events", "AUDIT_SERVICE_STAFF_UPDATE_ROUTING_KEY"),
                )
                if not event_status:
                    # Handle the failed the case
                    pass
                return API_RESPONSE.Return200Success("User status updated successfully")

            phone_number = request.data["phone_number"]
            ccode = request.data["ccode"]

            # Check whether phone number exists
            # try:
            #     User.objects.get(phone_number=phone_number, ccode=ccode).exclude(
            #         id=staff_id
            #     )
            #     return API_RESPONSE.Return400Error(
            #         "User with phone number already exists"
            #     )
            # except:
            #     pass

            # Check whether department exists
            try:
                if (
                    "department" in request.data
                    and staff_info.utype != User.UserTypes.ADMIN
                ):
                    Departments.objects.get(
                        id=request.data["department"],
                        status=True,
                        is_active=True,
                        organisation=request.userinfo["organisation"],
                    )
            except:
                return API_RESPONSE.Return400Error("Invalid department sent")

            # Check whether role exists
            try:
                if (
                    "role_id" in request.data
                    and staff_info.utype != User.UserTypes.ADMIN
                ):
                    RolesPermissions.objects.get(
                        id=request.data["role_id"],
                        status=True,
                        is_active=True,
                        organisation=request.userinfo["organisation"],
                    )
            except:
                return API_RESPONSE.Return400Error("Invalid role sent")

            try:
                if "badge" in request.data and staff_info.utype != User.UserTypes.ADMIN:
                    Badge.objects.get(
                        id=request.data["badge"],
                        status=True,
                        is_active=True,
                        organisation=request.userinfo["organisation"],
                    )
            except:
                return API_RESPONSE.Return400Error("Invalid badge sent")

            if request.data.get("role_id"):
                request.data["role"] = request.data.get("role_id")

            serializer = UserUpdateSerializer(
                staff_info, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()

            if request.data.get("role") == "ADMIN":
                try:
                    del request.data["role_id"]
                    del request.data["role"]
                except Exception:
                    pass

            staff_time_zone = user_info.time_zone
            user_info_serializer = UserProfilesUpdateSerializer(
                user_info, data=request.data, partial=True
            )
            if user_info_serializer.is_valid():
                user_info_serializer.save()

            # Updating Staff locations
            StaffLocations.objects.filter(
                user=staff_info, organisation=request.userinfo["organisation"]
            ).delete()
            staff_locations_list = []
            for location_id in request.data.get("locations", []):
                try:
                    if location_id:
                        location = Locations.objects.get(
                            id=location_id,
                            status=True,
                            is_active=True,
                            organisation=request.userinfo["organisation"],
                        )
                        staff_locations_list.append(
                            StaffLocations(
                                user=staff_info,
                                location=location,
                                organisation=request.data.get("organisation"),
                                created_by=request.data.get("user_id"),
                                updated_by=request.data.get("user_id"),
                            )
                        )
                except Exception:
                    return API_RESPONSE.Return400Error("Invalid locations provided")
            StaffLocations.objects.bulk_create(staff_locations_list)

            return_data = {**serializer.data, **user_info_serializer.data}
            event_status = publish_event(
                getStaffPayloadForAudit(staff_info),
                cfg.get("events", "AUDIT_SERVICE_EXCHANGE"),
                cfg.get("events", "AUDIT_SERVICE_STAFF_UPDATE_ROUTING_KEY"),
            )
            if not event_status:
                # Handle the failed the case
                pass

            if staff_time_zone != request.data.get("time_zone"):
                calendar_payload = getTimezoneUpdatePayloadForCalendarService(
                    "appointment",
                    request.data.get("time_zone"),
                    request.data.get("organisation"),
                    str(staff_info.id),
                )
                if calendar_payload is not None:
                    event_status = publish_event(
                        calendar_payload,
                        cfg.get("events", "CALENDAR_SERVICE_EXCHANGE"),
                        cfg.get("events", "WORKING_HOUR_UPDATE_ROUTING_KEY"),
                    )
                    if not event_status:
                        # Handle the failed the case
                        pass
                else:
                    # Handle the failed the case
                    pass

            return API_RESPONSE.Return200Success(
                "User info updated successfully", return_data
            )
        except Exception as err:
            logging.error(f"StaffInformationAPI update: {err}", exc_info=True)
            return API_RESPONSE.Return400Error(
                "Internal error, try again after sometime."
            )

    @swagger_auto_schema(manual_parameters=[], tags=["staff"])
    def destroy(
        self, request, *args, **kwargs
    ):  # [TODO] check few paramter before deleting them.
        try:
            staff_id = kwargs["pk"]
            try:
                staff_info = User.objects.get(
                    id=staff_id,
                    is_active=True,
                    organisation=request.userinfo["organisation"],
                ).exclude(utype=User.UserTypes.ADMIN)
                user_info = UserProfiles.objects.get(user=staff_info)
            except:
                return API_RESPONSE.Return404Error("Staff not found")

            staff_info.is_active = False
            staff_info.deleted_by = request.userinfo["id"]
            staff_info.deleted_at = timezone.now()
            staff_info.save()

            user_info.is_active = False
            user_info.deleted_by = request.userinfo["id"]
            user_info.deleted_at = timezone.now()
            user_info.save()

            event_status = publish_event(
                getStaffPayloadForAudit(staff_info),
                cfg.get("events", "AUDIT_SERVICE_EXCHANGE"),
                cfg.get("events", "AUDIT_SERVICE_STAFF_DELETE_ROUTING_KEY"),
            )
            if not event_status:
                # Handle the failed the case
                pass

            return API_RESPONSE.Return200Success("User deleted successfully")
        except:
            return API_RESPONSE.Return400Error("Internal error, try after some time")


class GetUsersInfo(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView,
    mixins.CreateModelMixin,
):
    serializer_class = StaffListSerializer

    def get_queryset(self, request):
        try:
            queryset = User.objects.filter()
            id = self.request.data.get("id", None)
            if id is not None:
                queryset = queryset.filter(id__in=id)
                return queryset
            return queryset
        except Exception as err:
            logging.error(f" userservice/GetusersInfo: {err}", exc_info=True)

    def post(self, request):
        users_data = self.get_queryset(request)
        serialiser = self.serializer_class(users_data, many=True)
        return API_RESPONSE.Return200Success(
            "Assignee data fetched",
            serialiser.data,
            "",
            "",
            {
                "count": len(users_data),
            },
        )


class StaffStatusAPI(viewsets.ViewSet):
    http_method_names = ["get", "put", "head", "options"]

    def list(self, request, *args, **kwargs):
        try:
            user = User.objects.get(
                id=request.userinfo["id"],
                is_active=True,
                organisation=request.userinfo["organisation"],
            )
            return API_RESPONSE.Return200Success(
                "Status updated", {"active_status": user.active_status}
            )
        except Exception as err:
            logging.error(f"StaffStatusUpdateAPI list: {err}", exc_info=True)
            return API_RESPONSE.Return400Error("Not found")

    @swagger_wrapper(
        {
            "active_status": openapi.TYPE_BOOLEAN,
        },
        "",
    )
    def update(self, request, *args, **kwargs):
        try:
            user = User.objects.get(
                id=request.userinfo["id"],
                is_active=True,
                organisation=request.userinfo["organisation"],
            )
            user.active_status = request.data.get("active_status")
            user.save()
            return API_RESPONSE.Return200Success("Status updated")
        except Exception as err:
            logging.error(f"StaffStatusUpdateAPI update: {err}", exc_info=True)
            return API_RESPONSE.Return400Error("Not found")


class StaffLocationsAPI(viewsets.ViewSet):
    http_method_names = ["get", "head", "options"]

    @swagger_auto_schema(manual_parameters=[staff_id])
    def list(self, request, *args, **kwargs):
        staff_id = self.request.query_params.get("staff_id", None)
        staff_locations = []
        if staff_id != None:
            staff_locations = (
                StaffLocations.objects.filter(
                    user=staff_id,
                    status=True,
                    is_active=True,
                    organisation=request.userinfo["organisation"],
                )
                .values_list("location", flat=True)
                .distinct()
            )
            locations = Locations.objects.filter(id__in=staff_locations)
        return API_RESPONSE.Return200Success(
            "Staff locations",
            LocationsSerializer(locations, many=True).data,
        )
