from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Treinamentos(models.Model):
    TIPO_CHOICES = [
        ('site', 'Site Web'),
        ('documento', 'Documento'),
        ('texto', 'Texto Manual'),
    ]

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('processando', 'Processando'),
        ('concluido', 'Concluído'),
        ('erro', 'Erro'),
    ]

    site = models.URLField(blank=True)
    conteudo = models.TextField(blank=True)
    documento = models.FileField(upload_to='documentos', blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='texto')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    erro_detalhes = models.TextField(blank=True)

    # Métricas de qualidade
    total_chunks = models.IntegerField(default=0)
    qualidade_score = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.site or 'Conteúdo manual'}"

    class Meta:
        verbose_name = "Treinamento"
        verbose_name_plural = "Treinamentos"
        ordering = ['-created_at']

class DataTreinamento(models.Model):
    treinamento = models.ForeignKey(Treinamentos, on_delete=models.CASCADE, related_name='chunks')
    metadata = models.JSONField(null=True, blank=True)
    texto = models.TextField(null=True, blank=True)
    embedding_hash = models.CharField(max_length=64, blank=True)  # Para cache
    qualidade_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Chunk de Treinamento"
        verbose_name_plural = "Chunks de Treinamento"
        indexes = [
            models.Index(fields=['embedding_hash']),
            models.Index(fields=['qualidade_score']),
        ]

class ConversaSession(models.Model):
    """Sessão de conversa para manter contexto"""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ativa = models.BooleanField(default=True)

    def __str__(self):
        return f"Conversa {self.id} - {self.usuario.username}"

    class Meta:
        verbose_name = "Sessão de Conversa"
        verbose_name_plural = "Sessões de Conversa"
        ordering = ['-updated_at']

class Pergunta(models.Model):
    CATEGORIA_CHOICES = [
        ('geral', 'Geral'),
        ('tecnica', 'Técnica'),
        ('conceitual', 'Conceitual'),
        ('procedural', 'Procedural'),
        ('factual', 'Factual'),
    ]

    conversa = models.ForeignKey(ConversaSession, on_delete=models.CASCADE, related_name='perguntas')
    data_treinamento = models.ManyToManyField(DataTreinamento, blank=True)
    pergunta = models.TextField()
    resposta = models.TextField(blank=True)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='geral')
    confianca_score = models.FloatField(default=0.0)
    tempo_resposta = models.FloatField(default=0.0)  # em segundos
    created_at = models.DateTimeField(auto_now_add=True)

    # Contexto da pergunta anterior
    pergunta_anterior = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.pergunta[:50]}..."

    class Meta:
        verbose_name = "Pergunta"
        verbose_name_plural = "Perguntas"
        ordering = ['-created_at']

class FeedbackResposta(models.Model):
    """Feedback dos usuários sobre as respostas"""
    AVALIACAO_CHOICES = [
        (1, 'Muito Ruim'),
        (2, 'Ruim'),
        (3, 'Regular'),
        (4, 'Bom'),
        (5, 'Excelente'),
    ]

    pergunta = models.OneToOneField(Pergunta, on_delete=models.CASCADE, related_name='feedback')
    avaliacao = models.IntegerField(choices=AVALIACAO_CHOICES)
    comentario = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback {self.avaliacao}/5 - Pergunta {self.pergunta.id}"

    class Meta:
        verbose_name = "Feedback de Resposta"
        verbose_name_plural = "Feedbacks de Respostas"

class CacheEmbedding(models.Model):
    """Cache para embeddings calculados"""
    texto_hash = models.CharField(max_length=64, unique=True, db_index=True)
    embedding = models.JSONField()
    modelo = models.CharField(max_length=50, default='text-embedding-ada-002')
    created_at = models.DateTimeField(auto_now_add=True)
    hits = models.IntegerField(default=0)  # Contador de uso

    class Meta:
        verbose_name = "Cache de Embedding"
        verbose_name_plural = "Cache de Embeddings"
        indexes = [
            models.Index(fields=['texto_hash', 'modelo']),
        ]

class AnalyticsQuery(models.Model):
    """Analytics de queries para melhorar o sistema"""
    pergunta_texto = models.TextField()
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    documentos_encontrados = models.IntegerField(default=0)
    tempo_busca = models.FloatField(default=0.0)
    score_medio = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Analytics de Query"
        verbose_name_plural = "Analytics de Queries"
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['score_medio']),
        ]