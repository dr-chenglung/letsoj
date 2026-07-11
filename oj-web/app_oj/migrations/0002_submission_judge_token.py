from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app_oj", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="submission",
            name="judge_token",
            field=models.CharField(
                blank=True, db_index=True, max_length=64, null=True
            ),
        ),
    ]
