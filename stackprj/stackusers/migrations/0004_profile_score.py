# Generated by Django 4.2.2 on 2023-08-21 15:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stackusers', '0003_alter_profile_phone'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='score',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
