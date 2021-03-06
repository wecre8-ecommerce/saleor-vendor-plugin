# Generated by Django 3.2.10 on 2022-03-27 11:10

import django_countries.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vendor", "0022_alter_vendor_phone_number"),
    ]

    operations = [
        migrations.AddField(
            model_name="billinginfo",
            name="account_holder_name",
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name="billinginfo",
            name="bank_address",
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name="billinginfo",
            name="bank_area",
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name="billinginfo",
            name="bank_city",
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name="billinginfo",
            name="bank_country",
            field=django_countries.fields.CountryField(default=[], max_length=2),
        ),
        migrations.AddField(
            model_name="billinginfo",
            name="bank_zipcode",
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]
