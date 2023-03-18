from django.db import migrations, models
from uuid import uuid4

def generate_claim_reference_number():
    return "CL-{}".format(uuid4().hex[:6].upper())

def set_claim_reference_numbers(apps, schema_editor):
    Claim = apps.get_model('core', 'Claim')
    claim_ref_nums = []
    for claim in Claim.objects.all():
        claim_ref_num = generate_claim_reference_number()
        claim_ref_nums.append(claim_ref_num)
        claim.claim_reference_number = claim_ref_num
        claim.save()
    print("Claim reference numbers:", claim_ref_nums)

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_block_claim_block_customer_alter_block_blockchain'),  # Replace this with the correct migration name
    ]

    operations = [
        migrations.AddField(
            model_name='claim',
            name='claim_reference_number',
            field=models.CharField(default='', max_length=255, unique=False),  # Temporarily set unique=False
        ),
        migrations.RunPython(set_claim_reference_numbers),
        # Add a separate AlterField operation to set unique=True
        migrations.AlterField(
            model_name='claim',
            name='claim_reference_number',
            field=models.CharField(default='', max_length=255, unique=True),
        ),
    ]
