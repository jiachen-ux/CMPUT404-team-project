# Generated by Django 4.1.2 on 2022-12-07 06:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('post', '0002_remove_post_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='url',
            field=models.URLField(blank=True, max_length=500),
        ),
    ]
