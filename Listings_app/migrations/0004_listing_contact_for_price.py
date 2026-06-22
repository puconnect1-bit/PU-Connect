from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Listings_app', '0003_listing_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='listing',
            name='contact_for_price',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='listing',
            name='image_url',
            field=models.URLField(blank=True, default='', max_length=500),
        ),
    ]
