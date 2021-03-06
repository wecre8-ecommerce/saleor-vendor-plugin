# Generated by Django 3.2.10 on 2022-02-28 08:31

import saleor.core.db.fields
import saleor.core.utils.editorjs
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("vendor", "0011_auto_20220228_0826"),
    ]

    operations = [
        migrations.AlterField(
            model_name="vendor",
            name="description",
            field=saleor.core.db.fields.SanitizedJSONField(
                blank=True,
                null=True,
                sanitizer=saleor.core.utils.editorjs.clean_editor_js,
            ),
        ),
    ]
