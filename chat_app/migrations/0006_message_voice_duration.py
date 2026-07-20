from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat_app', '0005_pushsubscription'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='voice_duration',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='message',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='message',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['is_deleted'], name='chat_app_me_is_dele_3b9225_idx'),
        ),
    ]
