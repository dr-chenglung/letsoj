# Generated by Django 4.2.4 on 2025-06-12 07:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_management', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contest',
            name='password',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
