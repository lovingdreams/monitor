# Generated by Django 4.1.5 on 2023-05-02 07:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="user",
            unique_together={("email", "organisation")},
        ),
    ]
