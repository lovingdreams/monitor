# Generated by Django 4.1.5 on 2023-05-08 10:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_alter_user_unique_together"),
    ]

    operations = [
        migrations.AddField(
            model_name="userotps",
            name="date",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]