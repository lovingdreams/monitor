# Generated by Django 4.1.5 on 2023-07-18 07:13

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("organisation", "0002_organisations_api_key_organisations_terms_conditions"),
    ]

    operations = [
        migrations.CreateModel(
            name="Setup",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("status", models.BooleanField(default=True)),
                ("is_active", models.BooleanField(default=True)),
                ("organisation", models.CharField(max_length=100)),
                ("deleted_by", models.CharField(blank=True, max_length=100, null=True)),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Deleted at"
                    ),
                ),
                ("created_by", models.CharField(default="NULL", max_length=100)),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created at"),
                ),
                ("updated_by", models.CharField(default="NULL", max_length=100)),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Updated at"),
                ),
                ("info", models.JSONField(blank=True, default=dict, null=True)),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField()),
                ("image", models.CharField(max_length=150)),
                ("route_link", models.CharField(blank=True, max_length=150, null=True)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Tags",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("status", models.BooleanField(default=True)),
                ("is_active", models.BooleanField(default=True)),
                ("organisation", models.CharField(max_length=100)),
                ("deleted_by", models.CharField(blank=True, max_length=100, null=True)),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Deleted at"
                    ),
                ),
                ("created_by", models.CharField(default="NULL", max_length=100)),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created at"),
                ),
                ("updated_by", models.CharField(default="NULL", max_length=100)),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Updated at"),
                ),
                ("info", models.JSONField(blank=True, default=dict, null=True)),
                ("name", models.CharField(max_length=100)),
                ("colour", models.CharField(max_length=150)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="organisations",
            name="business_type",
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
        migrations.AddField(
            model_name="organisations",
            name="other_type_name",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="departments",
            name="description",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="generalsettings",
            name="ccode",
            field=models.CharField(default="+91", max_length=150),
        ),
        migrations.AlterField(
            model_name="generalsettings",
            name="country",
            field=models.CharField(default="India", max_length=150),
        ),
        migrations.AlterField(
            model_name="generalsettings",
            name="currency",
            field=models.CharField(default="INR, ₹", max_length=150),
        ),
        migrations.AlterField(
            model_name="generalsettings",
            name="dateformat",
            field=models.CharField(default="dd/MM/YYYY", max_length=150),
        ),
        migrations.AlterField(
            model_name="generalsettings",
            name="timeformat",
            field=models.CharField(default="H:MM", max_length=150),
        ),
        migrations.AlterField(
            model_name="generalsettings",
            name="timezone",
            field=models.CharField(default="Asia/Kolkata", max_length=150),
        ),
    ]
