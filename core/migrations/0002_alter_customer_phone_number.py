# Generated by Django 4.1.7 on 2023-03-12 23:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='phone_number',
            field=models.CharField(default='', max_length=20),
        ),
    ]
