# Generated by Django 3.2 on 2021-04-17 20:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hospitals', '0003_auto_20210417_2339'),
    ]

    operations = [
        migrations.AddField(
            model_name='hospital',
            name='address',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='hospitals.address'),
        ),
        migrations.AddField(
            model_name='patient',
            name='last_dose',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.DeleteModel(
            name='AvailabeVaccines',
        ),
    ]
