# Generated by Django 4.1.1 on 2022-10-12 13:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('binance', '0002_symbol_users'),
    ]

    operations = [
        migrations.CreateModel(
            name='SizeConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('margin', models.FloatField()),
                ('trade_wallet_percent', models.FloatField()),
                ('leverage', models.IntegerField()),
            ],
        ),
    ]