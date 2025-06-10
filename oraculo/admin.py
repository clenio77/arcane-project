from django.contrib import admin
from .models import (
    Treinamentos, DataTreinamento, Pergunta, ConversaSession,
    FeedbackResposta, CacheEmbedding, AnalyticsQuery
)

@admin.register(Treinamentos)
class TreinamentosAdmin(admin.ModelAdmin):
    list_display = ['id', 'tipo', 'status', 'usuario', 'site', 'total_chunks', 'qualidade_score', 'created_at']
    list_filter = ['tipo', 'status', 'created_at', 'usuario']
    search_fields = ['site', 'conteudo']
    readonly_fields = ['id', 'created_at', 'updated_at', 'total_chunks', 'qualidade_score']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('tipo', 'status', 'usuario')
        }),
        ('Conteúdo', {
            'fields': ('site', 'conteudo', 'documento')
        }),
        ('Métricas', {
            'fields': ('total_chunks', 'qualidade_score', 'erro_detalhes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(DataTreinamento)
class DataTreinamentoAdmin(admin.ModelAdmin):
    list_display = ['id', 'treinamento', 'qualidade_score', 'embedding_hash', 'created_at']
    list_filter = ['qualidade_score', 'created_at', 'treinamento__tipo']
    search_fields = ['texto', 'treinamento__site']
    readonly_fields = ['id', 'created_at', 'embedding_hash']
    date_hierarchy = 'created_at'

@admin.register(ConversaSession)
class ConversaSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'titulo', 'usuario', 'ativa', 'total_perguntas', 'created_at']
    list_filter = ['ativa', 'created_at', 'usuario']
    search_fields = ['titulo', 'usuario__username']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'

    def total_perguntas(self, obj):
        return obj.perguntas.count()
    total_perguntas.short_description = 'Total Perguntas'

@admin.register(Pergunta)
class PerguntaAdmin(admin.ModelAdmin):
    list_display = ['id', 'pergunta_resumo', 'categoria', 'conversa', 'confianca_score', 'tempo_resposta', 'created_at']
    list_filter = ['categoria', 'confianca_score', 'created_at', 'conversa__usuario']
    search_fields = ['pergunta', 'resposta', 'conversa__titulo']
    filter_horizontal = ['data_treinamento']
    readonly_fields = ['id', 'created_at', 'tempo_resposta']
    date_hierarchy = 'created_at'

    def pergunta_resumo(self, obj):
        return obj.pergunta[:50] + '...' if len(obj.pergunta) > 50 else obj.pergunta
    pergunta_resumo.short_description = 'Pergunta'

@admin.register(FeedbackResposta)
class FeedbackRespostaAdmin(admin.ModelAdmin):
    list_display = ['id', 'pergunta_resumo', 'avaliacao', 'created_at']
    list_filter = ['avaliacao', 'created_at']
    search_fields = ['pergunta__pergunta', 'comentario']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'

    def pergunta_resumo(self, obj):
        return obj.pergunta.pergunta[:50] + '...' if len(obj.pergunta.pergunta) > 50 else obj.pergunta.pergunta
    pergunta_resumo.short_description = 'Pergunta'

@admin.register(CacheEmbedding)
class CacheEmbeddingAdmin(admin.ModelAdmin):
    list_display = ['id', 'texto_hash', 'modelo', 'hits', 'created_at']
    list_filter = ['modelo', 'created_at', 'hits']
    search_fields = ['texto_hash']
    readonly_fields = ['id', 'created_at', 'texto_hash', 'embedding']
    date_hierarchy = 'created_at'

@admin.register(AnalyticsQuery)
class AnalyticsQueryAdmin(admin.ModelAdmin):
    list_display = ['id', 'pergunta_resumo', 'usuario', 'documentos_encontrados', 'tempo_busca', 'score_medio', 'created_at']
    list_filter = ['documentos_encontrados', 'created_at', 'usuario']
    search_fields = ['pergunta_texto', 'usuario__username']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'

    def pergunta_resumo(self, obj):
        return obj.pergunta_texto[:50] + '...' if len(obj.pergunta_texto) > 50 else obj.pergunta_texto
    pergunta_resumo.short_description = 'Pergunta'
