# Generated by Django 4.2.4 on 2023-08-19 14:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('LittleLemonAPI', '0007_remove_order_delivery_assigned_to'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='delivered',
        ),
    ]