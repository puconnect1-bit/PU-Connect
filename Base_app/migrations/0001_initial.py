import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('Listings_app', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('boost_fee', models.DecimalField(decimal_places=2, default=10.0, max_digits=8)),
                ('boost_duration_days', models.PositiveIntegerField(default=7)),
                ('platform_name', models.CharField(default='PU-Connect', max_length=100)),
                ('admin_email', models.EmailField(default='admin@pu-connect.edu.gh')),
                ('max_listing_price', models.DecimalField(decimal_places=2, default=10000.0, max_digits=10)),
                ('max_video_size_mb', models.PositiveIntegerField(default=100)),
                ('report_sla_hours', models.PositiveIntegerField(default=2)),
                ('max_listings_per_user', models.PositiveIntegerField(default=50)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'Site Configuration'},
        ),
        migrations.CreateModel(
            name='BoostRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fee_paid', models.DecimalField(decimal_places=2, max_digits=8)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=10)),
                ('admin_note', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='boost_requests', to=settings.AUTH_USER_MODEL)),
                ('listing', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='boost_requests', to='Listings_app.Listing')),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='boost_reviews', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
