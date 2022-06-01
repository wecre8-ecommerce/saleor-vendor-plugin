# Generated by Django 3.2.10 on 2022-01-17 21:44

import django.db.models.deletion
import django_iban.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vendor", "0002_auto_20220105_1321"),
    ]

    operations = [
        migrations.CreateModel(
            name="Billing",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("iban_num", django_iban.fields.IBANField(max_length=34)),
                ("bank_name", models.CharField(max_length=256)),
                (
                    "vendors",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="vendor.vendor"
                    ),
                ),
            ],
        ),
    ]
