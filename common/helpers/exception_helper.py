from rest_framework.views import exception_handler
from common.helpers.response_helper import API_RESPONSE


def customExceptionHandler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)
    # Now add the HTTP status code to the response.
    if response is None:
        return API_RESPONSE.Return500Error("Something went wrong")
    else:
        return API_RESPONSE.Return500Error(response.data["detail"])
