from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Base_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='boostrequest',
            name='paystack_reference',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='boostrequest',
            name='paid_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='boostrequest',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending_payment', 'Pending Payment'),
                    ('paid', 'Paid — Awaiting Approval'),
                    ('approved', 'Approved'),
                    ('rejected', 'Rejected'),
                ],
                default='pending_payment',
                max_length=20,
            ),
        ),
    ]
