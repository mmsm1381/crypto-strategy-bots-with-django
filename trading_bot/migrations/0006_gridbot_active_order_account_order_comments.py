# Generated by Django 4.1.4 on 2022-12-27 08:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trading_bot', '0005_exchange_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='gridbot',
            name='active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='order',
            name='account',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, to='trading_bot.account'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='comments',
            field=models.TextField(blank=True, null=True),
        ),
    ]
