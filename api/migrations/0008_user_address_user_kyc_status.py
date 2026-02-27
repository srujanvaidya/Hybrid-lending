# Generated manually - adds address and kyc_status fields to User model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_alter_loanrequest_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='address',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='kyc_status',
            field=models.CharField(
                choices=[('Pending', 'Pending'), ('Verified', 'Verified'), ('Rejected', 'Rejected')],
                default='Pending',
                max_length=10,
            ),
        ),
    ]
