from rest_framework.response import Response
from rest_framework import status


class ApiResponse:
    def __init__(self):
        pass

    def Return200Success(self, message, data=[], reload="", function="", extra_data=""):
        if extra_data != "":
            return Response(
                {
                    **{
                        "status": 200,
                        "message": message,
                        "data": data,
                        "reload": reload,
                    },
                    **extra_data,
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {"status": 200, "message": message, "data": data, "reload": reload},
            status=status.HTTP_200_OK,
        )

    def Return201Created(self, message, data=[], reload="", function=""):
        return Response(
            {"status": 201, "message": message, "data": data, "reload": reload},
            status=status.HTTP_201_CREATED,
        )

    def Return400Error(self, message, data=[], reload="", function=""):
        return Response(
            {"status": 400, "message": message, "data": data, "reload": reload},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def Return404Error(self, message, data=[], reload="", function=""):
        return Response(
            {"status": 404, "message": message, "data": data, "reload": reload},
            status=status.HTTP_404_NOT_FOUND,
        )

    def Return500Error(self, message, data=[], reload="", function=""):
        return Response(
            {"status": 500, "message": message, "data": data, "reload": reload},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


API_RESPONSE = ApiResponse()
