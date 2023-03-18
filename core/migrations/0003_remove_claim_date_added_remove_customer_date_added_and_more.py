# Generated by Django 4.1.7 on 2023-03-12 23:31

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_customer_phone_number'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='claim',
            name='date_added',
        ),
        migrations.RemoveField(
            model_name='customer',
            name='date_added',
        ),
        migrations.AddField(
            model_name='claim',
            name='created_on',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False),
        ),
        migrations.AddField(
            model_name='claim',
            name='timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='customer',
            name='created_on',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False),
        ),
        migrations.AddField(
            model_name='customer',
            name='timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='claim',
            name='customer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.customer'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='dob',
            field=models.DateField(help_text='Date of birth in the format YYYY-MM-DD', null=True),
        ),
        migrations.AlterField(
            model_name='customer',
            name='email',
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AlterField(
            model_name='customer',
            name='gender',
            field=models.CharField(choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], default='O', max_length=1),
        ),
        migrations.AlterField(
            model_name='customer',
            name='phone_number',
            field=models.CharField(default=None, max_length=15, null=True, unique=True),
        ),
    ]