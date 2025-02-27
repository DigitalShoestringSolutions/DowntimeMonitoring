# Generated by Django 5.0.6 on 2025-02-25 21:14

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('state', '0005_remove_machine_sensor_machine_edit_manual_input_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='statusevent',
            name='next_entry',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='previous_entry', to='state.statusevent'),
        ),
    ]
