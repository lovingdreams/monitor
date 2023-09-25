from rest_framework import serializers

from organisation.models import (
    GeneralSettings,
    Locations,
    Organisations,
    RolesPermissions,
    WorkingHours,
    Departments,
    # TaxRate,
    Setup,
    Tags,
    Badge,
    PriceSettings,
)
from users.models import UserDepartments, UserProfiles, User
from users.serializers import UserDepartmentSerializer

from src.settings import JWT_SECRET


class GeneralSettingsSerializer(serializers.ModelSerializer):
    currency = serializers.SerializerMethodField("get_currency")

    class Meta:
        model = GeneralSettings
        fields = [
            "country",
            "currency",
            "ccode",
            "timezone",
            "dateformat",
            "timeformat",
            "slot_duration",
        ]

    def get_currency(self, object):
        try:
            price_settings = PriceSettings.objects.get(
                organisation=str(object.organisation)
            )
            return price_settings.currency
        except Exception as err:
            return object.currency


class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisations
        fields = [
            "id",
            "name",
            "description",
            "slug",
            "email",
            "phone_number",
            "ccode",
            "image",
            "website",
            "address",
            "identifier",
            "registration_id",
            "language",
            "instagram_url",
            "twitter_url",
            "linkedin_url",
            "youtube_url",
            "api_key",
            "business_type",
            "other_type_name",
        ]

    def create(self, validated_data):
        obj = Organisations.objects.create(**validated_data)
        obj.save()
        return obj


class OrganisationGRPCSerializer(OrganisationSerializer):
    class Meta:
        model = Organisations


class WorkingHourSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkingHours
        fields = ["days", "slots", "status"]


class RolesPermissionSerializer(serializers.ModelSerializer):

    # staffs_active_count = serializers.SerializerMethodField(
    #     "staffs_active_count_method"
    # )
    # staffs_inactive_count = serializers.SerializerMethodField(
    #     "staffs_inactive_count_method"
    # )

    # def staffs_active_count_method(self, object):
    #     user_poriles_list = UserProfiles.objects.filter(
    #         role=str(object.id),
    #         organisation=str(object.organisation),
    #         is_active=True,
    #         status=True,
    #     )
    #     count = 0
    #     for user_profile in user_poriles_list:
    #         if user_profile.user.status:
    #             count += 1
    #     return count

    # def staffs_inactive_count_method(self, object):
    #     user_poriles_list = UserProfiles.objects.filter(
    #         role=str(object.id),
    #         organisation=str(object.organisation),
    #         is_active=True,
    #         status=True,
    #     )
    #     count = 0
    #     for user_profile in user_poriles_list:
    #         if not user_profile.user.status:
    #             count += 1
    #     return count

    class Meta:
        model = RolesPermissions
        fields = [
            "id",
            "name",
            "description",
            "permissions",
            "status",
            # "staffs_active_count",
            # "staffs_inactive_count",
        ]


class RolesPermissionAdminSerializer(serializers.ModelSerializer):

    staffs_active_count = serializers.SerializerMethodField(
        "staffs_active_count_method"
    )
    staffs_inactive_count = serializers.SerializerMethodField(
        "staffs_inactive_count_method"
    )

    def staffs_active_count_method(self, object):
        user_poriles_list = UserProfiles.objects.filter(
            role=str(object.id),
            organisation=str(object.organisation),
            is_active=True,
            status=True,
        )
        count = 0
        for user_profile in user_poriles_list:
            if user_profile.user.status:
                count += 1
        return count

    def staffs_inactive_count_method(self, object):
        user_poriles_list = UserProfiles.objects.filter(
            role=str(object.id),
            organisation=str(object.organisation),
            is_active=True,
            status=True,
        )
        count = 0
        for user_profile in user_poriles_list:
            if not user_profile.user.status:
                count += 1
        return count

    class Meta:
        model = RolesPermissions
        fields = [
            "id",
            "name",
            "description",
            "permissions",
            "status",
            "staffs_active_count",
            "staffs_inactive_count",
        ]


class DepartmentSerializer(serializers.ModelSerializer):

    # users = serializers.SerializerMethodField()

    # def get_users(self, object):
    #     list_of_users = UserDepartmentSerializer(
    #         UserDepartments.objects.filter(department=object), many=True
    #     ).data
    #     users_list = []
    #     for user in list_of_users:
    #         users_list.append(str(user["user"]))
    #     return users_list

    class Meta:
        model = Departments
        fields = ["id", "name", "description", "status"]


class DepartmentListSerializer(serializers.ModelSerializer):
    users_count = serializers.SerializerMethodField("get_users_count")

    class Meta:
        model = Departments
        fields = ["id", "name", "description", "status", "users_count"]

    def get_users_count(self, obj):
        return UserProfiles.objects.filter(
            department=obj, organisation=obj.organisation, status=True, is_active=True
        ).count()


class LocationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Locations
        fields = [
            "id",
            "name",
            "location",
            "status",
            "default",
            "email",
            "phone_number",
            "ccode",
        ]


# class TaxRateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TaxRate
#         fields = [
#             "name",
#             "rate",
#             "default_tax",
#             "apply_tax",
#             "organisation",
#             "created_by",
#             "updated_by",
#         ]


# class TaxRateUpdateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TaxRate
#         fields = [
#             "name",
#             "rate",
#             "default_tax",
#             "apply_tax",
#             "updated_by",
#         ]


class OrganisationListSerializer(serializers.ModelSerializer):
    default_location = serializers.SerializerMethodField("get_default_location")

    class Meta:
        model = Organisations
        fields = [
            "id",
            "name",
            "description",
            "slug",
            "email",
            "phone_number",
            "ccode",
            "image",
            "website",
            "address",
            "identifier",
            "registration_id",
            "language",
            "instagram_url",
            "twitter_url",
            "linkedin_url",
            "youtube_url",
            "api_key",
            "business_type",
            "default_location",
            "other_type_name",
        ]

    def get_default_location(self, obj):
        try:
            default_location = Locations.objects.get(
                default=True, organisation=obj.id, status=True, is_active=True
            )
            return LocationsSerializer(default_location).data
        except Exception:
            return {}


class SetupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setup
        fields = [
            "id",
            "name",
            "description",
            "image",
            "route_link",
            "status",
        ]


class IframeSetupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setup
        fields = [
            "name",
            "image",
        ]


class TagsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ["id", "name", "colour", "type"]


class TagsUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ["name", "colour", "status", "updated_by"]


class BadgeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ["id", "name", "colour", "text_colour"]


class BadgeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ["name", "colour", "text_colour", "status", "updated_by"]


class PriceSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceSettings
        fields = [
            "id",
            "currency",
            "price_symbol_position",
            "price_seperator",
            "no_of_decimals",
            "cod_status",
            "currency_name",
        ]


class IframeUserProfilesSerializer(serializers.ModelSerializer):
    badge = BadgeListSerializer(read_only=True)

    class Meta:
        model = UserProfiles
        fields = [
            "date_of_birth",
            "gender",
            "designation",
            "specialisation",
            "age",
            "experience",
            "qualification",
            "description",
            "badge",
        ]
