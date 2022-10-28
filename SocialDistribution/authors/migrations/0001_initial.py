# Generated by Django 4.1.2 on 2022-10-21 01:53

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('username', models.CharField(max_length=200, primary_key=True, serialize=False, unique=True)),
                ('type', models.CharField(default='author', max_length=200)),
                ('userId', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('url', models.CharField(max_length=200)),
                ('host', models.CharField(max_length=200)),
                ('displayName', models.CharField(max_length=200, null=True)),
                ('github', models.CharField(max_length=200, null=True)),
                ('profileImage', models.CharField(blank=True, max_length=500, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='FollowRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(default='Follow', max_length=200)),
                ('summary', models.TextField()),
                ('actor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_request_sender', to='authors.author')),
                ('object', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_request_receiver', to='authors.author')),
            ],
        ),
        migrations.CreateModel(
            name='Follower',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(default='followers', max_length=200)),
                ('items', models.ManyToManyField(blank=True, related_name='items', to='authors.author')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='authors.author')),
            ],
        ),
    ]
