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
    ]
