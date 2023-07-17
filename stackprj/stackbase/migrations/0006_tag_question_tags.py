# Generated by Django 4.2.2 on 2023-07-11 14:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stackbase', '0005_auto_20211011_2351'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='question',
            name='tags',
            field=models.ManyToManyField(related_name='questions', to='stackbase.tag'),
        ),
    ]