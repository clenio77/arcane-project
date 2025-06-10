"""
Sistema de Auto-Melhoria Contínua
Aprende e melhora automaticamente baseado no feedback e uso
"""

import json
import numpy as np
from typing import Dict, List, Any, Tuple
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg, Count, Q
from .models import (
    Pergunta, FeedbackResposta, AnalyticsQuery, 
    DataTreinamento, Treinamentos, CacheEmbedding
)

class ContinuousLearner:
    """Sistema de aprendizado contínuo"""
    
    def __init__(self):
        self.improvement_threshold = 0.7  # Score mínimo para considerar boa resposta
        self.learning_rate = 0.1
        self.feedback_weight = 0.6
        self.usage_weight = 0.4
    
    def analyze_system_performance(self) -> Dict[str, Any]:
        """Analisa performance geral do sistema"""
        
        # Período de análise (últimos 30 dias)
        cutoff_date = timezone.now() - timedelta(days=30)
        
        # Métricas de qualidade
        recent_feedbacks = FeedbackResposta.objects.filter(created_at__gte=cutoff_date)
        avg_rating = recent_feedbacks.aggregate(avg=Avg('avaliacao'))['avg'] or 0.0
        
        # Métricas de uso
        recent_queries = AnalyticsQuery.objects.filter(created_at__gte=cutoff_date)
        avg_response_time = recent_queries.aggregate(avg=Avg('tempo_busca'))['avg'] or 0.0
        avg_docs_found = recent_queries.aggregate(avg=Avg('documentos_encontrados'))['avg'] or 0.0
        
        # Identificar problemas
        problems = self._identify_problems(recent_feedbacks, recent_queries)
        
        # Sugerir melhorias
        improvements = self._suggest_improvements(problems)
        
        return {
            'period': '30 days',
            'metrics': {
                'avg_rating': round(avg_rating, 2),
                'total_feedbacks': recent_feedbacks.count(),
                'avg_response_time': round(avg_response_time, 3),
                'avg_docs_found': round(avg_docs_found, 1),
                'total_queries': recent_queries.count()
            },
            'problems': problems,
            'improvements': improvements,
            'overall_health': self._calculate_health_score(avg_rating, avg_response_time, avg_docs_found)
        }
    
    def _identify_problems(self, feedbacks, queries) -> List[Dict[str, Any]]:
        """Identifica problemas no sistema"""
        problems = []
        
        # Problema 1: Baixa qualidade de respostas
        if feedbacks.exists():
            low_quality_ratio = feedbacks.filter(avaliacao__lte=2).count() / feedbacks.count()
            if low_quality_ratio > 0.3:
                problems.append({
                    'type': 'low_quality_responses',
                    'severity': 'high' if low_quality_ratio > 0.5 else 'medium',
                    'description': f'{low_quality_ratio:.1%} das respostas têm qualidade baixa',
                    'affected_queries': feedbacks.filter(avaliacao__lte=2).count()
                })
        
        # Problema 2: Tempo de resposta alto
        if queries.exists():
            slow_queries = queries.filter(tempo_busca__gt=2.0).count()
            slow_ratio = slow_queries / queries.count()
            if slow_ratio > 0.2:
                problems.append({
                    'type': 'slow_response_time',
                    'severity': 'medium' if slow_ratio < 0.4 else 'high',
                    'description': f'{slow_ratio:.1%} das queries são lentas (>2s)',
                    'affected_queries': slow_queries
                })
        
        # Problema 3: Poucos documentos encontrados
        if queries.exists():
            no_docs_queries = queries.filter(documentos_encontrados=0).count()
            no_docs_ratio = no_docs_queries / queries.count()
            if no_docs_ratio > 0.15:
                problems.append({
                    'type': 'insufficient_knowledge',
                    'severity': 'high',
                    'description': f'{no_docs_ratio:.1%} das queries não encontram documentos',
                    'affected_queries': no_docs_queries
                })
        
        # Problema 4: Categorias com baixa performance
        category_problems = self._analyze_category_performance()
        problems.extend(category_problems)
        
        return problems
    
    def _analyze_category_performance(self) -> List[Dict[str, Any]]:
        """Analisa performance por categoria"""
        problems = []
        
        # Analisar cada categoria
        categories = Pergunta.objects.values('categoria').annotate(
            count=Count('id'),
            avg_confidence=Avg('confianca_score'),
            avg_feedback=Avg('feedback__avaliacao')
        ).filter(count__gte=5)  # Apenas categorias com dados suficientes
        
        for cat in categories:
            if cat['avg_confidence'] and cat['avg_confidence'] < 0.6:
                problems.append({
                    'type': 'category_low_confidence',
                    'severity': 'medium',
                    'description': f"Categoria '{cat['categoria']}' tem baixa confiança ({cat['avg_confidence']:.2f})",
                    'category': cat['categoria'],
                    'affected_queries': cat['count']
                })
            
            if cat['avg_feedback'] and cat['avg_feedback'] < 3.0:
                problems.append({
                    'type': 'category_low_satisfaction',
                    'severity': 'medium',
                    'description': f"Categoria '{cat['categoria']}' tem baixa satisfação ({cat['avg_feedback']:.1f}/5)",
                    'category': cat['categoria'],
                    'affected_queries': cat['count']
                })
        
        return problems
    
    def _suggest_improvements(self, problems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sugere melhorias baseadas nos problemas identificados"""
        improvements = []
        
        for problem in problems:
            if problem['type'] == 'low_quality_responses':
                improvements.append({
                    'action': 'improve_prompts',
                    'priority': 'high',
                    'description': 'Otimizar templates de prompts baseado no feedback negativo',
                    'implementation': 'Analisar respostas mal avaliadas e ajustar prompts'
                })
                improvements.append({
                    'action': 'expand_knowledge_base',
                    'priority': 'high',
                    'description': 'Adicionar mais documentos de treinamento',
                    'implementation': 'Identificar gaps de conhecimento e adicionar conteúdo'
                })
            
            elif problem['type'] == 'slow_response_time':
                improvements.append({
                    'action': 'optimize_search',
                    'priority': 'medium',
                    'description': 'Otimizar algoritmos de busca e cache',
                    'implementation': 'Implementar cache mais agressivo e otimizar FAISS'
                })
            
            elif problem['type'] == 'insufficient_knowledge':
                improvements.append({
                    'action': 'knowledge_gap_analysis',
                    'priority': 'high',
                    'description': 'Identificar e preencher gaps de conhecimento',
                    'implementation': 'Analisar queries sem resultados e adicionar conteúdo relevante'
                })
            
            elif problem['type'].startswith('category_'):
                improvements.append({
                    'action': 'category_specific_training',
                    'priority': 'medium',
                    'description': f"Melhorar treinamento para categoria {problem.get('category', 'específica')}",
                    'implementation': 'Adicionar documentos especializados e ajustar prompts'
                })
        
        # Remover duplicatas
        unique_improvements = []
        seen_actions = set()
        for imp in improvements:
            if imp['action'] not in seen_actions:
                unique_improvements.append(imp)
                seen_actions.add(imp['action'])
        
        return unique_improvements
    
    def _calculate_health_score(self, avg_rating: float, avg_response_time: float, avg_docs_found: float) -> Dict[str, Any]:
        """Calcula score geral de saúde do sistema"""
        
        # Normalizar métricas (0-1)
        rating_score = avg_rating / 5.0 if avg_rating else 0.5
        
        # Tempo de resposta (melhor = menor)
        time_score = max(0, 1 - (avg_response_time / 5.0)) if avg_response_time else 0.5
        
        # Documentos encontrados (normalizar para 0-1, assumindo 5 como ideal)
        docs_score = min(avg_docs_found / 5.0, 1.0) if avg_docs_found else 0.5
        
        # Score combinado
        overall_score = (rating_score * 0.5 + time_score * 0.3 + docs_score * 0.2)
        
        # Determinar status
        if overall_score >= 0.8:
            status = 'excellent'
        elif overall_score >= 0.6:
            status = 'good'
        elif overall_score >= 0.4:
            status = 'fair'
        else:
            status = 'poor'
        
        return {
            'overall_score': round(overall_score, 2),
            'status': status,
            'components': {
                'quality': round(rating_score, 2),
                'performance': round(time_score, 2),
                'coverage': round(docs_score, 2)
            }
        }
    
    def auto_optimize_prompts(self) -> Dict[str, Any]:
        """Otimiza prompts automaticamente baseado no feedback"""
        
        # Analisar respostas bem e mal avaliadas
        good_responses = FeedbackResposta.objects.filter(avaliacao__gte=4)
        bad_responses = FeedbackResposta.objects.filter(avaliacao__lte=2)
        
        optimizations = []
        
        if good_responses.exists() and bad_responses.exists():
            # Analisar padrões em respostas boas vs ruins
            good_patterns = self._extract_response_patterns(good_responses)
            bad_patterns = self._extract_response_patterns(bad_responses)
            
            # Identificar diferenças
            improvements = self._compare_patterns(good_patterns, bad_patterns)
            optimizations.extend(improvements)
        
        return {
            'optimizations_applied': len(optimizations),
            'details': optimizations,
            'next_review': timezone.now() + timedelta(days=7)
        }
    
    def _extract_response_patterns(self, feedbacks) -> Dict[str, Any]:
        """Extrai padrões das respostas"""
        patterns = {
            'avg_length': 0,
            'common_structures': [],
            'categories': Counter(),
            'confidence_scores': []
        }
        
        total_length = 0
        count = 0
        
        for feedback in feedbacks:
            pergunta = feedback.pergunta
            if pergunta.resposta:
                total_length += len(pergunta.resposta.split())
                count += 1
                patterns['categories'][pergunta.categoria] += 1
                patterns['confidence_scores'].append(pergunta.confianca_score)
        
        if count > 0:
            patterns['avg_length'] = total_length / count
            patterns['avg_confidence'] = sum(patterns['confidence_scores']) / len(patterns['confidence_scores'])
        
        return patterns
    
    def _compare_patterns(self, good_patterns: Dict, bad_patterns: Dict) -> List[Dict[str, Any]]:
        """Compara padrões para identificar melhorias"""
        improvements = []
        
        # Comparar comprimento médio
        if good_patterns.get('avg_length', 0) > bad_patterns.get('avg_length', 0) * 1.2:
            improvements.append({
                'type': 'response_length',
                'recommendation': 'Aumentar detalhamento das respostas',
                'evidence': f"Respostas boas são {good_patterns['avg_length']:.0f} palavras vs {bad_patterns['avg_length']:.0f} palavras ruins"
            })
        
        # Comparar confiança
        good_conf = good_patterns.get('avg_confidence', 0)
        bad_conf = bad_patterns.get('avg_confidence', 0)
        if good_conf > bad_conf + 0.1:
            improvements.append({
                'type': 'confidence_threshold',
                'recommendation': 'Ajustar threshold de confiança mínima',
                'evidence': f"Respostas boas têm confiança {good_conf:.2f} vs {bad_conf:.2f} ruins"
            })
        
        return improvements
    
    def schedule_maintenance_tasks(self) -> List[Dict[str, Any]]:
        """Agenda tarefas de manutenção automática"""
        tasks = []
        
        # Limpeza de cache antigo
        old_cache = CacheEmbedding.objects.filter(
            created_at__lt=timezone.now() - timedelta(days=30),
            hits__lt=5
        )
        if old_cache.exists():
            tasks.append({
                'task': 'cache_cleanup',
                'description': f'Limpar {old_cache.count()} entradas de cache antigas',
                'priority': 'low',
                'estimated_time': '5 minutes'
            })
        
        # Reindexação de documentos com baixa qualidade
        low_quality_docs = DataTreinamento.objects.filter(qualidade_score__lt=0.5)
        if low_quality_docs.exists():
            tasks.append({
                'task': 'reindex_low_quality',
                'description': f'Reprocessar {low_quality_docs.count()} documentos de baixa qualidade',
                'priority': 'medium',
                'estimated_time': '30 minutes'
            })
        
        # Backup de dados importantes
        tasks.append({
            'task': 'backup_analytics',
            'description': 'Backup de dados de analytics e feedback',
            'priority': 'low',
            'estimated_time': '10 minutes'
        })
        
        return tasks

class PerformanceMonitor:
    """Monitor de performance em tempo real"""
    
    def __init__(self):
        self.alert_thresholds = {
            'response_time': 3.0,  # segundos
            'error_rate': 0.05,    # 5%
            'low_quality_rate': 0.3  # 30%
        }
    
    def check_real_time_health(self) -> Dict[str, Any]:
        """Verifica saúde do sistema em tempo real"""
        
        # Últimas 100 queries
        recent_queries = AnalyticsQuery.objects.order_by('-created_at')[:100]
        
        alerts = []
        metrics = {}
        
        if recent_queries.exists():
            # Tempo de resposta médio
            avg_time = recent_queries.aggregate(avg=Avg('tempo_busca'))['avg'] or 0
            metrics['avg_response_time'] = avg_time
            
            if avg_time > self.alert_thresholds['response_time']:
                alerts.append({
                    'type': 'high_response_time',
                    'severity': 'warning',
                    'message': f'Tempo de resposta alto: {avg_time:.2f}s',
                    'threshold': self.alert_thresholds['response_time']
                })
            
            # Taxa de queries sem resultados
            no_results = recent_queries.filter(documentos_encontrados=0).count()
            error_rate = no_results / recent_queries.count()
            metrics['error_rate'] = error_rate
            
            if error_rate > self.alert_thresholds['error_rate']:
                alerts.append({
                    'type': 'high_error_rate',
                    'severity': 'critical',
                    'message': f'Taxa de erro alta: {error_rate:.1%}',
                    'threshold': self.alert_thresholds['error_rate']
                })
        
        # Últimos feedbacks
        recent_feedbacks = FeedbackResposta.objects.order_by('-created_at')[:50]
        if recent_feedbacks.exists():
            low_quality = recent_feedbacks.filter(avaliacao__lte=2).count()
            low_quality_rate = low_quality / recent_feedbacks.count()
            metrics['low_quality_rate'] = low_quality_rate
            
            if low_quality_rate > self.alert_thresholds['low_quality_rate']:
                alerts.append({
                    'type': 'high_low_quality_rate',
                    'severity': 'warning',
                    'message': f'Taxa de baixa qualidade: {low_quality_rate:.1%}',
                    'threshold': self.alert_thresholds['low_quality_rate']
                })
        
        return {
            'status': 'critical' if any(a['severity'] == 'critical' for a in alerts) else 'warning' if alerts else 'healthy',
            'alerts': alerts,
            'metrics': metrics,
            'timestamp': timezone.now().isoformat()
        }

# Instâncias globais
continuous_learner = ContinuousLearner()
performance_monitor = PerformanceMonitor()
