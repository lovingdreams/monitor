from datetime import date
from rest_framework.permissions import AllowAny
from rest_framework import viewsets

# from common.helpers.common_helper import send_mail
from common.events.publishers.user_service_publisher import publish_event


from common.helpers.response_helper import API_RESPONSE
from common.swagger.documentation import swagger_auto_schema, email_param, code_param
from users.models import User, UserOTPs
from users.helper import getAdminEmailPayload
from common.configs.config import config as cfg
import logging

MAX_OTP = 5


class ActivateUserAPI(viewsets.ViewSet):
    permission_classes = (AllowAny,)
    http_method_names = ["get", "head", "options"]

    @swagger_auto_schema(manual_parameters=[code_param], tags=["authorization"])
    def retrieve(self, request, *args, **kwargs):
        code = request.query_params.get("code", "")
        user_id = kwargs.get("pk", "")

        if not (code and user_id):
            return API_RESPONSE.Return400Error("Some fields are missing.")

        try:
            # get user information
            user_info = User.objects.get(id=user_id)
            if user_info.verified:
                return API_RESPONSE.Return400Error(
                    "User already activated please login"
                )

            # check for whether code is correct or not
            user_otp_info = UserOTPs.objects.get(
                user=user_id,
                otp=code,
                validated=False,
                used_for=UserOTPs.UsedTypes.ACTIVATE,
            )

            # [TODO]: check for time limit during validation
            # if not user_otp_info:
            #     return API_RESPONSE.Return400Error("Invalid code or link got expired")

            user_otp_info.validated = True
            user_otp_info.save()

            user_info.verified = True  # activate user
            user_info.save()

            return API_RESPONSE.Return200Success(
                "Email verified successfully", [], "/login"
            )
        except Exception as err:
            return API_RESPONSE.Return400Error("Invalid code or link got expired")


class ResendActivationAPI(viewsets.ViewSet):
    permission_classes = (AllowAny,)
    http_method_names = ["get", "head", "options"]

    @swagger_auto_schema(manual_parameters=[email_param], tags=["authorization"])
    def list(self, request, *args, **kwargs):
        email = request.query_params.get("email", "")
        if not email:
            return API_RESPONSE.Return400Error("Invalid Email sent")

        try:
            user_otp = UserOTPs.objects.get(
                sent_to=email,
                used_for=UserOTPs.UsedTypes.ACTIVATE,
                sent_type=UserOTPs.SentTypes.MAIL,
                validated=False,
                # date=date.today(),
            )
            user = User.objects.get(
                id=user_otp.user,
                utype=User.UserTypes.ADMIN,
                organisation=user_otp.organisation,
            )
            otp = user_otp.otp
        except Exception as err:
            logging.error(f"ResendActivationAPI create: {err}", exc_info=True)
            return API_RESPONSE.Return400Error("Invalid Email Sent")

        otp_count = user_otp.otp_count

        # check max otp request limit
        if otp_count >= MAX_OTP:
            return API_RESPONSE.Return400Error("You reached max otp limit for today.")

        user_otp.otp_count = otp_count + 1
        user_otp.save()

        # send_mail(email, otp, user_otp.user, "Account Activation")
        event_status = publish_event(
            getAdminEmailPayload(user, user.organisation, otp),
            cfg.get("events", "COMMUNICATION_EXCHANGE"),
            cfg.get("events", "ADMIN_REGISTER_ROUTING_KEY"),
        )
        if not event_status:
            # Resend failed handle the case
            pass

        return API_RESPONSE.Return200Success("OTP sent Successfully")
