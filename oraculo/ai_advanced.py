"""
Módulo de IA Avançada para o Sistema Arcane
Funcionalidades inteligentes e análise semântica
"""

import re
import hashlib
import time
from typing import List, Dict, Any, Tuple, Optional
from django.conf import settings
from django.utils import timezone
import openai
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .models import CacheEmbedding, AnalyticsQuery, FeedbackResposta, Pergunta

# Configurar OpenAI
openai.api_key = settings.OPENAI_API_KEY

class AnalisadorSemantico:
    """Análise semântica avançada de perguntas"""
    
    CATEGORIAS_INTENCAO = {
        'definicao': ['o que é', 'defina', 'conceito', 'significado', 'definição'],
        'como_fazer': ['como', 'passos', 'procedimento', 'tutorial', 'guia'],
        'comparacao': ['diferença', 'comparar', 'versus', 'vs', 'melhor'],
        'listagem': ['liste', 'quais são', 'exemplos', 'tipos de'],
        'explicacao': ['explique', 'por que', 'porque', 'razão', 'motivo'],
        'solucao': ['resolver', 'solução', 'problema', 'erro', 'corrigir']
    }
    
    @classmethod
    def detectar_intencao(cls, pergunta: str) -> str:
        """Detecta a intenção da pergunta"""
        pergunta_lower = pergunta.lower()
        
        for categoria, palavras_chave in cls.CATEGORIAS_INTENCAO.items():
            for palavra in palavras_chave:
                if palavra in pergunta_lower:
                    return categoria
        
        return 'geral'
    
    @classmethod
    def extrair_entidades(cls, pergunta: str) -> List[str]:
        """Extrai entidades importantes da pergunta"""
        # Palavras técnicas e conceitos importantes
        entidades = []
        
        # Regex para encontrar termos técnicos (palavras em maiúscula, siglas, etc.)
        termos_tecnicos = re.findall(r'\b[A-Z]{2,}\b|\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\b', pergunta)
        entidades.extend(termos_tecnicos)
        
        # Palavras entre aspas
        palavras_aspas = re.findall(r'"([^"]*)"', pergunta)
        entidades.extend(palavras_aspas)
        
        return list(set(entidades))
    
    @classmethod
    def calcular_complexidade(cls, pergunta: str) -> float:
        """Calcula a complexidade da pergunta (0-1)"""
        fatores = {
            'tamanho': min(len(pergunta.split()) / 20, 1.0),
            'termos_tecnicos': min(len(cls.extrair_entidades(pergunta)) / 5, 1.0),
            'palavras_interrogativas': len(re.findall(r'\b(como|quando|onde|por que|qual|quais)\b', pergunta.lower())) * 0.2
        }
        
        return min(sum(fatores.values()) / len(fatores), 1.0)

class GerenciadorCache:
    """Gerenciamento inteligente de cache para embeddings"""
    
    @staticmethod
    def gerar_hash(texto: str) -> str:
        """Gera hash único para o texto"""
        return hashlib.sha256(texto.encode()).hexdigest()
    
    @classmethod
    def obter_embedding_cache(cls, texto: str, modelo: str = 'text-embedding-ada-002') -> Optional[List[float]]:
        """Obtém embedding do cache se existir"""
        texto_hash = cls.gerar_hash(texto)
        
        try:
            cache_obj = CacheEmbedding.objects.get(texto_hash=texto_hash, modelo=modelo)
            cache_obj.hits += 1
            cache_obj.save(update_fields=['hits'])
            return cache_obj.embedding
        except CacheEmbedding.DoesNotExist:
            return None
    
    @classmethod
    def salvar_embedding_cache(cls, texto: str, embedding: List[float], modelo: str = 'text-embedding-ada-002'):
        """Salva embedding no cache"""
        texto_hash = cls.gerar_hash(texto)
        
        CacheEmbedding.objects.update_or_create(
            texto_hash=texto_hash,
            modelo=modelo,
            defaults={
                'embedding': embedding,
                'hits': 1
            }
        )

class OtimizadorPrompt:
    """Otimização inteligente de prompts baseada no contexto"""
    
    TEMPLATES_PROMPT = {
        'definicao': """Baseado no contexto fornecido, forneça uma definição clara e precisa para: {pergunta}

Contexto:
{contexto}

Estruture sua resposta da seguinte forma:
1. Definição principal
2. Características importantes
3. Exemplos práticos (se aplicável)

Resposta:""",
        
        'como_fazer': """Baseado no contexto fornecido, forneça um guia passo-a-passo para: {pergunta}

Contexto:
{contexto}

Estruture sua resposta da seguinte forma:
1. Visão geral do processo
2. Passos detalhados
3. Dicas importantes
4. Possíveis problemas e soluções

Resposta:""",
        
        'comparacao': """Baseado no contexto fornecido, faça uma comparação detalhada sobre: {pergunta}

Contexto:
{contexto}

Estruture sua resposta da seguinte forma:
1. Resumo das opções
2. Comparação ponto a ponto
3. Vantagens e desvantagens
4. Recomendação (se aplicável)

Resposta:""",
        
        'geral': """Baseado no contexto fornecido, responda à pergunta de forma clara e precisa: {pergunta}

Contexto:
{contexto}

Resposta:"""
    }
    
    @classmethod
    def gerar_prompt_otimizado(cls, pergunta: str, contexto: str, intencao: str = 'geral') -> str:
        """Gera prompt otimizado baseado na intenção"""
        template = cls.TEMPLATES_PROMPT.get(intencao, cls.TEMPLATES_PROMPT['geral'])
        return template.format(pergunta=pergunta, contexto=contexto)

class AvaliadorQualidade:
    """Avaliação automática da qualidade das respostas"""
    
    @staticmethod
    def calcular_score_relevancia(pergunta: str, resposta: str, contexto: str) -> float:
        """Calcula score de relevância da resposta"""
        try:
            # Usar TF-IDF para calcular similaridade
            vectorizer = TfidfVectorizer(stop_words='english')
            
            textos = [pergunta, resposta, contexto]
            tfidf_matrix = vectorizer.fit_transform(textos)
            
            # Similaridade entre pergunta e resposta
            sim_pergunta_resposta = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            # Similaridade entre contexto e resposta
            sim_contexto_resposta = cosine_similarity(tfidf_matrix[2:3], tfidf_matrix[1:2])[0][0]
            
            # Score combinado
            return (sim_pergunta_resposta * 0.6 + sim_contexto_resposta * 0.4)
            
        except Exception:
            return 0.5  # Score neutro em caso de erro
    
    @staticmethod
    def avaliar_completude(resposta: str) -> float:
        """Avalia a completude da resposta"""
        fatores = {
            'tamanho': min(len(resposta.split()) / 100, 1.0),
            'estrutura': 1.0 if any(char in resposta for char in ['1.', '2.', '-', '•']) else 0.5,
            'conclusao': 1.0 if any(palavra in resposta.lower() for palavra in ['portanto', 'assim', 'conclusão', 'resumo']) else 0.7
        }
        
        return sum(fatores.values()) / len(fatores)

class SugestorPerguntas:
    """Gerador de sugestões inteligentes de perguntas"""
    
    @staticmethod
    def gerar_sugestoes_relacionadas(pergunta_atual: str, historico_conversa: List[str]) -> List[str]:
        """Gera sugestões de perguntas relacionadas"""
        sugestoes = []
        
        # Extrair entidades da pergunta atual
        analisador = AnalisadorSemantico()
        entidades = analisador.extrair_entidades(pergunta_atual)
        
        # Templates de sugestões baseadas em entidades
        templates = [
            "Como {entidade} funciona?",
            "Quais são os tipos de {entidade}?",
            "Qual a diferença entre {entidade} e...",
            "Como implementar {entidade}?",
            "Quais são as vantagens de {entidade}?"
        ]
        
        for entidade in entidades[:3]:  # Máximo 3 entidades
            for template in templates[:2]:  # Máximo 2 templates por entidade
                sugestao = template.format(entidade=entidade.lower())
                if sugestao not in sugestoes:
                    sugestoes.append(sugestao)
        
        return sugestoes[:5]  # Máximo 5 sugestões

class AnalyticsIA:
    """Analytics e métricas do sistema de IA"""
    
    @staticmethod
    def registrar_query(pergunta: str, usuario, documentos_encontrados: int, tempo_busca: float, score_medio: float):
        """Registra analytics da query"""
        AnalyticsQuery.objects.create(
            pergunta_texto=pergunta,
            usuario=usuario,
            documentos_encontrados=documentos_encontrados,
            tempo_busca=tempo_busca,
            score_medio=score_medio
        )
    
    @staticmethod
    def obter_metricas_qualidade() -> Dict[str, float]:
        """Obtém métricas de qualidade do sistema"""
        feedbacks = FeedbackResposta.objects.all()
        
        if not feedbacks.exists():
            return {'avaliacao_media': 0.0, 'total_feedbacks': 0}
        
        avaliacao_media = feedbacks.aggregate(
            media=models.Avg('avaliacao')
        )['media'] or 0.0
        
        return {
            'avaliacao_media': round(avaliacao_media, 2),
            'total_feedbacks': feedbacks.count(),
            'distribuicao': {
                i: feedbacks.filter(avaliacao=i).count() 
                for i in range(1, 6)
            }
        }
    
    @staticmethod
    def obter_perguntas_populares(limite: int = 10) -> List[Dict[str, Any]]:
        """Obtém as perguntas mais populares"""
        from django.db.models import Count
        
        return list(
            AnalyticsQuery.objects.values('pergunta_texto')
            .annotate(count=Count('pergunta_texto'))
            .order_by('-count')[:limite]
        )

# Instâncias globais
analisador_semantico = AnalisadorSemantico()
gerenciador_cache = GerenciadorCache()
otimizador_prompt = OtimizadorPrompt()
avaliador_qualidade = AvaliadorQualidade()
sugestor_perguntas = SugestorPerguntas()
analytics_ia = AnalyticsIA()
