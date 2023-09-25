from django.db import models

from common.database.base_model import BaseModel
from src.settings import JWT_SECRET

# Create your models here.
class Organisations(BaseModel):

    slug = models.CharField(max_length=150, blank=False, null=False, unique=True)
    name = models.CharField(max_length=150, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=100, blank=True, null=True)
    ccode = models.CharField(max_length=10, blank=True, null=True)
    image = models.CharField(max_length=150, blank=True, null=True)
    website = models.CharField(max_length=150, blank=True, null=True)
    business_type = models.CharField(max_length=150, blank=True, null=True)
    address = models.CharField(max_length=150, blank=True, null=True)
    identifier = models.CharField(max_length=150, blank=True, null=True)
    registration_id = models.CharField(max_length=150, blank=True, null=True)
    terms_conditions = models.BooleanField(default=False)

    language = models.CharField(max_length=100, blank=True, null=True)
    instagram_url = models.CharField(max_length=100, blank=True, null=True)
    twitter_url = models.CharField(max_length=100, blank=True, null=True)
    linkedin_url = models.CharField(max_length=100, blank=True, null=True)
    youtube_url = models.CharField(max_length=100, blank=True, null=True)

    api_key = models.CharField(max_length=150, blank=True, null=True)
    other_type_name = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        super(Organisations, self).save(*args, **kwargs)
        try:
            payload = {"organisation": self.id}
            import jwt

            api_key = jwt.encode(payload=payload, key=JWT_SECRET, algorithm="HS256")
            self.api_key = api_key
            return self
        except Exception as err:
            print("save method exception --->", err)

    def __str__(self):
        return str(self.id)


class GeneralSettings(BaseModel):
    country = models.CharField(max_length=150, blank=False, null=False, default="India")
    currency = models.CharField(
        max_length=150, blank=False, null=False, default="INR, ₹"
    )
    ccode = models.CharField(max_length=150, blank=False, null=False, default="+91")
    timezone = models.CharField(
        max_length=150, blank=False, null=False, default="Asia/Kolkata"
    )
    dateformat = models.CharField(
        max_length=150, blank=False, null=False, default="dd/MM/YYYY"
    )
    timeformat = models.CharField(
        max_length=150, blank=False, null=False, default="H:MM"
    )
    slot_duration = models.CharField(
        max_length=150, blank=False, null=False, default="30"
    )

    def __str__(self):
        return self.organisation


class Locations(BaseModel):
    class LocationTypes(models.TextChoices):
        USER = "USER", "user"
        ORGANISATION = "ORGANISATION", "organisation"

    class AddressTypes(models.TextChoices):
        BILLING_ADDRESS = "BILLING_ADDRESS"
        SHIPPING_ADDRESS = "SHIPPING_ADDRESS"

    name = models.CharField(max_length=100, blank=False, null=False)
    location = models.TextField(blank=True, null=True)
    latitude = models.CharField(max_length=100, blank=True, null=True)
    longitude = models.CharField(max_length=100, blank=True, null=True)
    default = models.BooleanField(default=False)
    email = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=100, blank=True, null=True)
    ccode = models.CharField(max_length=10, blank=True, null=True)

    contact_person_name = models.CharField(max_length=100, blank=True, null=True)
    contact_person_phone = models.CharField(max_length=100, blank=True, null=True)
    address_one = models.CharField(max_length=100, blank=True, null=True)
    address_two = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    zipcode = models.CharField(max_length=100, blank=True, null=True)

    address_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        choices=AddressTypes.choices,
    )
    ltype = models.CharField(
        max_length=100,
        blank=False,
        null=False,
        choices=LocationTypes.choices,
        default=LocationTypes.USER,
    )
    ref_id = models.CharField(max_length=100, blank=False, null=False)

    def __str__(self):
        return str(self.id)


class WorkingHours(BaseModel):
    class WorkingHourTypes(models.TextChoices):
        USER = "USER", "user"
        ORGANISATION = "ORGANISATION", "organisation"
        LOCATIONS = "LOCATIONS", "locations"

    class DayTypes(models.TextChoices):
        MONDAY = "MONDAY", "monday"
        TUESDAY = "TUESDAY", "tuesday"
        WEDNESDAY = "WEDNESDAY", "wednesday"
        THURSDAY = "THURSDAY", "thursday"
        FRIDAY = "FRIDAY", "friday"
        SATURDAY = "SATURDAY", "saturday"
        SUNDAY = "SUNDAY", "sunday"

    days = models.CharField(max_length=100, blank=False, null=False)
    slots = models.JSONField(blank=False, null=False)

    type = models.CharField(
        max_length=100,
        blank=False,
        null=False,
        choices=WorkingHourTypes.choices,
        default=WorkingHourTypes.USER,
    )
    ref_id = models.CharField(max_length=100, blank=False, null=False)

    class Meta:
        unique_together = ["days", "ref_id"]

    def __str__(self):
        return self.days


class RolesPermissions(BaseModel):
    name = models.CharField(max_length=100, blank=False, null=False)
    description = models.CharField(max_length=100, blank=False, null=False)
    permissions = models.JSONField(blank=False, null=False)

    def __str__(self):
        return str(self.id)


class Departments(BaseModel):
    name = models.CharField(max_length=100, blank=False, null=False)
    description = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return str(self.id)


class Setup(BaseModel):
    name = models.CharField(max_length=100, blank=False, null=False)
    description = models.TextField(blank=False, null=False)
    image = models.CharField(max_length=150, blank=False, null=False)
    route_link = models.CharField(max_length=150, blank=True, null=True)

    def __str__(self):
        return str(self.id)


class Tags(BaseModel):
    class TagTypes(models.TextChoices):
        CONTACTS = "CONTACTS", "contacts"
        ENQUIRIES = "ENQUIRIES", "enquiries"
        COMPANIES = "COMPANIES", "companies"
        PIPELINES = "PIPELINES", "pipelines"
        CLIENT = "CLIENT", "client"
        CLIENT_PROJECTS = "CLIENT_PROJECTS", "client_projects"

    name = models.CharField(max_length=100, blank=False, null=False)
    colour = models.CharField(max_length=150, blank=False, null=False)
    type = models.CharField(
        max_length=150,
        choices=TagTypes.choices,
        blank=True,
        null=True,
        editable=False,
    )

    def __str__(self):
        return str(self.id)


class Badge(BaseModel):
    class BadgeTypes(models.TextChoices):
        APPOINTMENT = "APPOINTMENT", "appointment"
        STAFF = "STAFF", "staff"
        PRODUCTS = "PRODUCTS", "products"

    name = models.CharField(max_length=100, blank=False, null=False)
    colour = models.CharField(max_length=150, blank=False, null=False)
    text_colour = models.CharField(max_length=150, blank=True, null=True)
    type = models.CharField(
        max_length=150,
        choices=BadgeTypes.choices,
        blank=True,
        null=True,
        editable=False,
    )

    def __str__(self):
        return str(self.id)


class PriceSettings(BaseModel):
    currency = models.CharField(
        max_length=50, blank=False, null=False, default="INR, ₹"
    )
    price_symbol_position = models.CharField(
        max_length=50, blank=False, null=False, default="before"
    )
    price_seperator = models.CharField(
        max_length=50, blank=False, null=False, default="Comma-Dot"
    )
    no_of_decimals = models.IntegerField(blank=True, null=True, default=2)
    cod_status = models.BooleanField(default=True)
    currency_name = models.CharField(
        max_length=50, blank=True, null=True, default="India Rupee"
    )

    def __str__(self):
        return str(self.id)
