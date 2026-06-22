from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Base_app', '0005_add_student_id_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='verificationrequest',
            name='expires_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='Badge expires 1 year after approval. Null = never set.',
            ),
        ),
        migrations.AddField(
            model_name='verificationrequest',
            name='renewal_count',
            field=models.PositiveIntegerField(
                default=0,
                help_text='How many times this badge has been renewed.',
            ),
        ),
    ]
