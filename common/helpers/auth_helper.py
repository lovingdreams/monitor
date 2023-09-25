from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User, Departments, UserProfiles


def get_tokens_for_user(user, payload={"organisation": "nodata", "utype": "ENDUSER"}):

    refresh = GetModifiedToken.for_user(user, payload)

    return {"refresh": str(refresh), "access": str(refresh.access_token)}


class GetModifiedToken(RefreshToken):
    @classmethod
    def for_user(cls, user, payload):
        token = super().for_user(user)
        token["organisation"] = payload["organisation"]
        token["utype"] = payload["utype"]
        department = payload["organisation"]
        role = "ADMIN"
        permissions = {}
        admin_id = ""
        if payload["utype"] == User.UserTypes.STAFF:
            user_profile = UserProfiles.objects.get(
                status=True,
                user=user,
                is_active=True,
                organisation=user.organisation,
            )
            department = str(user_profile.department.id)
            role = str(user_profile.role.name)
            permissions = user_profile.role.permissions
        try:
            admin_details = User.objects.get(
                utype=User.UserTypes.ADMIN,
                is_active=True,
                organisation=user.organisation,
            )
            admin_id = str(admin_details.id)
        except Exception:
            pass

        if payload["utype"] == User.UserTypes.ENDUSER:
            role = "ENDUSER"
            department = ""
        token["dept"] = department
        token["role"] = role
        token["permissions"] = permissions
        token["admin_id"] = admin_id
        return token
