from datetime import date
from rest_framework.permissions import AllowAny
from rest_framework import viewsets
from drf_yasg import openapi
from common.helpers.common_helper import random_string_generator, send_mail
from common.events.publishers.user_service_publisher import publish_event
from common.configs.config import config as cfg


from common.helpers.response_helper import API_RESPONSE
from users.helper import getForgotPasswordEmailPayload
from common.swagger.documentation import swagger_wrapper
from users.models import User, UserOTPs
import logging

MAX_OTP = 5


class ForgotPasswordAPI(viewsets.ViewSet):
    permission_classes = (AllowAny,)
    http_method_names = ["post", "head", "options"]

    @swagger_wrapper({"email": openapi.TYPE_STRING}, ["authorization"])
    def create(self, request, *args, **kwargs):  # [TODO] time based otp verification
        email = request.data.get("email", "")
        if not email:
            return API_RESPONSE.Return400Error("Please provide a valid email")

        try:
            user_info = User.objects.get(
                email=email, is_active=True, status=True, verified=True
            )

            try:
                user_otp = UserOTPs.objects.get(
                    user=user_info,
                    used_for=UserOTPs.UsedTypes.PASSWORDRESET,
                    validated=False,
                    date=date.today(),
                )
                otp = user_otp.otp
            except:
                otp = random_string_generator(16)
                user_otp = UserOTPs(
                    user=user_info,
                    organisation=str(user_info.organisation),
                    created_by=str(user_info),
                    otp=otp,
                    sent_to=email,
                    used_for=UserOTPs.UsedTypes.PASSWORDRESET,
                    sent_type=UserOTPs.SentTypes.MAIL,
                    otp_count=0,
                    date=date.today(),
                )

            otp_count = user_otp.otp_count

            # check max otp request limit
            if otp_count < MAX_OTP:
                user_otp.otp_count = otp_count + 1
            else:
                return API_RESPONSE.Return400Error(
                    "something went wrong try after some time"
                )

            user_otp.save()
            # send_mail(
            #     email, otp, str(user_info), "Forgot Password"
            # )  # send email to user
            mail_status = publish_event(
                getForgotPasswordEmailPayload(user_info, otp),
                cfg.get("events", "COMMUNICATION_EXCHANGE"),
                cfg.get("events", "ADMIN_FORGOT_PASSWORD_ROUTING_KEY"),
            )
            if not mail_status:
                # Mail sending is failed Handle the case
                pass
        except Exception as err:
            logging.error(f"ForgotPasswordAPI create: {err}", exc_info=True)
            pass

        return API_RESPONSE.Return200Success(
            "If a verified user exists, code will be sent to that email",
        )


class ResetPasswordAPI(viewsets.ViewSet):
    permission_classes = (AllowAny,)
    http_method_names = ["post", "head", "options"]

    @swagger_wrapper(
        {
            "id": openapi.TYPE_STRING,
            "code": openapi.TYPE_STRING,
            "password": openapi.TYPE_STRING,
        },
        ["authorization"],
    )
    def create(self, request, *args, **kwargs):
        id = request.data.get("id", "")
        code = request.data.get("code", "")
        password = request.data.get("password", "")

        if not (id and code and password):
            return API_RESPONSE.Return400Error("Some parameter are missing")

        try:
            user_info = User.objects.get(
                id=id, status=True, is_active=True, verified=True
            )
            check_otp = UserOTPs.objects.get(
                otp=code,
                user=user_info,
                used_for=UserOTPs.UsedTypes.PASSWORDRESET,
                validated=False,
            )

            user_info.set_password(password)
            user_info.save()

            check_otp.validated = True
            check_otp.save()

        except:
            return API_RESPONSE.Return400Error(
                "Link expired click on forgot password again to generate a new link"
            )

        return API_RESPONSE.Return200Success("Password reset successfull")
