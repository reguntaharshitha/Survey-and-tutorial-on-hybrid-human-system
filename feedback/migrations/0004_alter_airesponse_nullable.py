from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0003_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feedback',
            name='ai_response',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to='user_interaction.airesponse'),
        ),
    ]
