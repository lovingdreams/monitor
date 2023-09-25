from rest_framework.permissions import AllowAny
from rest_framework import viewsets
from drf_yasg import openapi
from rest_framework_simplejwt.backends import TokenBackend
from drf_yasg.utils import swagger_auto_schema


from common.helpers.auth_helper import get_tokens_for_user
from common.helpers.response_helper import API_RESPONSE
from common.swagger.documentation import swagger_wrapper, token_param
from users.models import User, UserProfiles
from organisation.models import GeneralSettings
from users.serializers import UserSerializer
import logging


class LoginAPI(viewsets.ViewSet):
    permission_classes = (AllowAny,)
    http_method_names = ["post", "head", "options"]

    @swagger_wrapper(
        {"email": openapi.TYPE_STRING, "password": openapi.TYPE_STRING},
        ["authorization"],
    )
    def create(self, request, *args, **kwargs):

        # required_params = ["email", "password"]
        email = request.data.get("email", "").lower()
        password = request.data.get("password", "")
        if not (email and password):
            return API_RESPONSE.Return400Error("Required params are missing")

        initial_setup = False

        try:
            # check for active user record.
            user_info = User.objects.get(
                email=email, utype=User.UserTypes.ADMIN, is_active=True, status=True
            )
        except Exception as err:
            try:
                logging.error(f"LoginAPI create: {err}", exc_info=True)
                user_info = User.objects.get(
                    email=email, utype=User.UserTypes.STAFF, is_active=True, status=True
                )
            except Exception as err:
                logging.error(f"LoginAPI create: {err}", exc_info=True)
                return API_RESPONSE.Return400Error("Invalid credentials")

        # check whether verified or not.
        if not user_info.verified:
            return API_RESPONSE.Return400Error(
                "Please activate user account.",
                {"id": user_info.id, "email": user_info.email},
                "/verify",
            )

        # validate user password.
        if not user_info.check_password(password):
            return API_RESPONSE.Return400Error("Invalid credentials")

        user = UserSerializer(user_info).data

        # get jwt tokens
        tokens = get_tokens_for_user(
            user_info,
            {"organisation": user["organisation"], "utype": user["utype"]},
        )

        # for redirecting user to onboarding screen
        if user_info.initial_setup:
            user_info.initial_setup = False
            user_info.save()
            initial_setup = True

        role = ""
        if user_info.utype == User.UserTypes.STAFF:
            try:
                user_profile = UserProfiles.objects.get(
                    user=user_info, organisation=user_info.organisation, is_active=True
                )
                role = user_profile.role.name
            except Exception:
                pass
        elif user_info.utype == User.UserTypes.ADMIN:
            role = User.UserTypes.ADMIN

        user["role"] = role

        extra_params = {
            "access_token": tokens["access"],
            "refresh_token": tokens["refresh"],
            "initial_setup": initial_setup,
            "time_zone": "Asia/Kolkata",
        }
        if user_info.utype == User.UserTypes.ADMIN:
            try:
                general_settings = GeneralSettings.objects.get(
                    organisation=user_info.organisation, is_active=True
                )
                extra_params["time_zone"] = general_settings.timezone
            except Exception as err:
                print("Error --->", err)
                pass
        elif user_info.utype == User.UserTypes.STAFF:
            extra_params["time_zone"] = user_profile.time_zone
        return API_RESPONSE.Return200Success(
            "Logged in",
            user,
            "/getting-started" if initial_setup else "/dashboard",
            "",
            extra_params,
        )


class VerifyUserAPI(viewsets.ViewSet):
    permission_classes = (AllowAny,)
    http_method_names = ["get", "head", "options"]

    @swagger_auto_schema(manual_parameters=[], tags=["authorization"])
    def list(self, request, *args, **kwargs):
        # get jwt token from headers
        header = request.headers.get("Authorization", None)
        if not isinstance(header, str):
            return API_RESPONSE.Return400Error("Token not provided.")

        parts = header.split()
        if len(parts) != 2 and parts[0] != "Bearer":
            return API_RESPONSE.Return400Error("Invalid token format")
        token = parts[1]

        try:
            payload = TokenBackend(algorithm="HS256").decode(token, verify=False)
            user_info = User.objects.get(
                id=payload["id"], is_active=True, status=True, verified=True
            )
            return_user_data = UserSerializer(user_info).data
        except:
            return API_RESPONSE.Return400Error("Invalid user or token")

        return API_RESPONSE.Return200Success("user details", return_user_data)


class RefreshTokenAPI(viewsets.ViewSet):
    http_method_names = ["get", "head", "options"]

    @swagger_auto_schema(manual_parameters=[token_param], tags=["authorization"])
    def list(self, request, *args, **kwargs):
        return API_RESPONSE.Return200Success("user details")
