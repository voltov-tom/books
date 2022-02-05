# Generated by Django 3.2.7 on 2021-09-19 18:51

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('store', '0006_alter_book_readers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='readers',
            field=models.ManyToManyField(related_name='books', through='store.UserBookRelation', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='userbookrelation',
            name='rate',
            field=models.PositiveSmallIntegerField(choices=[(1, 'ok'), (2, 'fine'), (3, 'good'), (4, 'amazing'), (5, 'incredible')], null=True),
        ),
    ]