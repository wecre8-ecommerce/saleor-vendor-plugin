# Generated by Django 3.2.13 on 2022-06-20 12:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("vendor", "0028_auto_20220525_1044"),
    ]

    operations = [
        migrations.RenameField(
            model_name="transaction",
            old_name="status",
            new_name="transaction_status",
        ),
    ]
