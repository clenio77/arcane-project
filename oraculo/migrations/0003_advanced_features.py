# Generated manually for advanced features

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('oraculo', '0002_datatreinamento_pergunta'),
    ]

    operations = [
        # Adicionar campos ao modelo Treinamentos
        migrations.AddField(
            model_name='treinamentos',
            name='tipo',
            field=models.CharField(choices=[('site', 'Site Web'), ('documento', 'Documento'), ('texto', 'Texto Manual')], default='texto', max_length=20),
        ),
        migrations.AddField(
            model_name='treinamentos',
            name='status',
            field=models.CharField(choices=[('pendente', 'Pendente'), ('processando', 'Processando'), ('concluido', 'Concluído'), ('erro', 'Erro')], default='pendente', max_length=20),
        ),
        migrations.AddField(
            model_name='treinamentos',
            name='usuario',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='treinamentos',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='treinamentos',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='treinamentos',
            name='erro_detalhes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='treinamentos',
            name='total_chunks',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='treinamentos',
            name='qualidade_score',
            field=models.FloatField(default=0.0),
        ),

        # Modificar campos do modelo Treinamentos
        migrations.AlterField(
            model_name='treinamentos',
            name='site',
            field=models.URLField(blank=True),
        ),
        migrations.AlterField(
            model_name='treinamentos',
            name='conteudo',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='treinamentos',
            name='documento',
            field=models.FileField(blank=True, upload_to='documentos'),
        ),

        # Adicionar campos ao modelo DataTreinamento
        migrations.AddField(
            model_name='datatreinamento',
            name='treinamento',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='chunks', to='oraculo.treinamentos'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='datatreinamento',
            name='embedding_hash',
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name='datatreinamento',
            name='qualidade_score',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='datatreinamento',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),

        # Criar modelo ConversaSession
        migrations.CreateModel(
            name='ConversaSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(blank=True, max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ativa', models.BooleanField(default=True)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Sessão de Conversa',
                'verbose_name_plural': 'Sessões de Conversa',
                'ordering': ['-updated_at'],
            },
        ),

        # Modificar modelo Pergunta
        migrations.AddField(
            model_name='pergunta',
            name='conversa',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='perguntas', to='oraculo.conversasession'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='pergunta',
            name='resposta',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='pergunta',
            name='categoria',
            field=models.CharField(choices=[('geral', 'Geral'), ('tecnica', 'Técnica'), ('conceitual', 'Conceitual'), ('procedural', 'Procedural'), ('factual', 'Factual')], default='geral', max_length=20),
        ),
        migrations.AddField(
            model_name='pergunta',
            name='confianca_score',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='pergunta',
            name='tempo_resposta',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='pergunta',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='pergunta',
            name='pergunta_anterior',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='oraculo.pergunta'),
        ),

        # Modificar relacionamento data_treinamento
        migrations.AlterField(
            model_name='pergunta',
            name='data_treinamento',
            field=models.ManyToManyField(blank=True, to='oraculo.datatreinamento'),
        ),

        # Criar modelo FeedbackResposta
        migrations.CreateModel(
            name='FeedbackResposta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('avaliacao', models.IntegerField(choices=[(1, 'Muito Ruim'), (2, 'Ruim'), (3, 'Regular'), (4, 'Bom'), (5, 'Excelente')])),
                ('comentario', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('pergunta', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='feedback', to='oraculo.pergunta')),
            ],
            options={
                'verbose_name': 'Feedback de Resposta',
                'verbose_name_plural': 'Feedbacks de Respostas',
            },
        ),

        # Criar modelo CacheEmbedding
        migrations.CreateModel(
            name='CacheEmbedding',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('texto_hash', models.CharField(db_index=True, max_length=64, unique=True)),
                ('embedding', models.JSONField()),
                ('modelo', models.CharField(default='text-embedding-ada-002', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('hits', models.IntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Cache de Embedding',
                'verbose_name_plural': 'Cache de Embeddings',
            },
        ),

        # Criar modelo AnalyticsQuery
        migrations.CreateModel(
            name='AnalyticsQuery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pergunta_texto', models.TextField()),
                ('documentos_encontrados', models.IntegerField(default=0)),
                ('tempo_busca', models.FloatField(default=0.0)),
                ('score_medio', models.FloatField(default=0.0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Analytics de Query',
                'verbose_name_plural': 'Analytics de Queries',
            },
        ),

        # Adicionar índices
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS oraculo_datatreinamento_embedding_hash_idx ON oraculo_datatreinamento (embedding_hash);",
            reverse_sql="DROP INDEX IF EXISTS oraculo_datatreinamento_embedding_hash_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS oraculo_datatreinamento_qualidade_score_idx ON oraculo_datatreinamento (qualidade_score);",
            reverse_sql="DROP INDEX IF EXISTS oraculo_datatreinamento_qualidade_score_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS oraculo_cacheembedding_texto_hash_modelo_idx ON oraculo_cacheembedding (texto_hash, modelo);",
            reverse_sql="DROP INDEX IF EXISTS oraculo_cacheembedding_texto_hash_modelo_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS oraculo_analyticsquery_created_at_idx ON oraculo_analyticsquery (created_at);",
            reverse_sql="DROP INDEX IF EXISTS oraculo_analyticsquery_created_at_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS oraculo_analyticsquery_score_medio_idx ON oraculo_analyticsquery (score_medio);",
            reverse_sql="DROP INDEX IF EXISTS oraculo_analyticsquery_score_medio_idx;"
        ),
    ]
