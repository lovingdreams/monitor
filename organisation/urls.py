from django.urls import path, include
from rest_framework.routers import DefaultRouter
from organisation.views.departments import DepartmentsAPI

from organisation.views.general_settings import GeneralSettingsAPI
from organisation.views.organisation_information import OrganisationInformationAPI
from organisation.views.organisation_locations import (
    OrganisationLocationsAPI,
    LocationByIdAPI,
)
from organisation.views.roles_permissions import RolesPermissionsAPI
from organisation.views.working_hours import WorkingHoursAPI
from organisation.views.setup import SetupAPI
from organisation.views.tags_views import TagsAPI
from organisation.views.badges_views import BadgeAPI
from organisation.views.price_settings import PriceSettingsAPI

# from organisation.views.tax import TaxRateAPI

organisation_router = DefaultRouter()

organisation_router.register("general_settings", GeneralSettingsAPI, "general settings")
organisation_router.register("information", OrganisationInformationAPI, "information")
organisation_router.register("working_hours", WorkingHoursAPI, "working hours")
organisation_router.register(
    "roles_permissions", RolesPermissionsAPI, "roles permissions"
)
organisation_router.register("departments", DepartmentsAPI, "departments")
organisation_router.register("locations", OrganisationLocationsAPI, "locations")
organisation_router.register("location-by-id", LocationByIdAPI, "location by id")
# organisation_router.register("tax_rate", TaxRateAPI, "tax rate")
organisation_router.register("set_up", SetupAPI, "Set Up")
organisation_router.register("tag", TagsAPI, "Tag")
organisation_router.register("badge", BadgeAPI, "Badge")
organisation_router.register("price_settings", PriceSettingsAPI, "Price Settings")


urlpatterns = [
    path("users/organisation/", include(organisation_router.urls), name="User Profile"),
]
