# Generated by Django 4.1.7 on 2023-03-12 23:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_remove_claim_date_added_remove_customer_date_added_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='phone_number',
            field=models.CharField(default=None, max_length=15, null=True),
        ),
    ]