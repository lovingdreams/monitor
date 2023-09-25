from rest_framework.response import Response
from rest_framework import status


def check_staff_common_modules(request):
    end_points = request.path.split("/")
    if request.method == "PUT" or request.method == "PATCH":
        if (
            end_points[1] == "users"
            and end_points[2] == "staff"
            and end_points[3] == "active-status"
            and len(end_points) == 6
        ):
            return True
    if request.method == "GET":
        if (
            end_points[1] == "users"
            and end_points[2] == "organisation"
            and end_points[3] == "location-by-id"
            and len(end_points) == 6
        ):
            return True
    return False


def check_manager_create_modules(path):
    if path in [
        "/users/organisation/general_settings/",
        "/users/organisation/information/",
        "/users/organisation/locations/",
        "/users/organisation/working_hours/",
        "/users/organisation/departments/",
    ]:
        return False
    return True


def check_manager_update_modules(path):
    end_points = path.split("/")
    if (
        end_points[1] == "users"
        and end_points[2] == "organisation"
        and end_points[3] == "locations"
        and len(end_points) == 6
    ):
        return False
    if (
        end_points[1] == "users"
        and end_points[2] == "organisation"
        and end_points[3] == "departments"
        and len(end_points) == 6
    ):
        return False
    return True


def check_staff_create_modules(path):
    if path in [
        "/users/users-info",
    ]:
        return True
    return False


def check_staff_update_modules(path):
    end_points = path.split("/")
    if (
        end_points[1] == "users"
        and end_points[2] == "staff"
        and end_points[3] == "information"
        and len(end_points) == 6
    ):
        return True
    return False


def check_agent_create_modules(path):
    if path in [
        "/users/users-info",
    ]:
        return True
    return False


def check_agent_update_modules(path):
    end_points = path.split("/")
    if (
        end_points[1] == "users"
        and end_points[2] == "staff"
        and end_points[3] == "information"
        and len(end_points) == 6
    ):
        return True
    return False
