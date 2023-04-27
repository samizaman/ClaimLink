# Generated by Django 4.2 on 2023-04-25 02:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0018_alter_claim_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="claim",
            name="status",
            field=models.CharField(
                choices=[
                    ("Approved", "Approved"),
                    ("Rejected", "Rejected"),
                    ("To Be Reviewed", "To Be Reviewed"),
                ],
                default="To Be Reviewed",
                max_length=20,
            ),
        ),
    ]