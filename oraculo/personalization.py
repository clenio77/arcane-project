"""
Sistema de Personalização Avançada
Adapta respostas baseado no perfil e histórico do usuário
"""

import json
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
from django.contrib.auth.models import User
from django.db.models import Avg, Count
from .models import Pergunta, FeedbackResposta, ConversaSession, AnalyticsQuery

class UserProfiler:
    """Criador de perfis de usuário baseado em comportamento"""
    
    def __init__(self):
        self.expertise_levels = {
            'iniciante': 0.3,
            'intermediario': 0.6,
            'avancado': 0.9
        }
    
    def get_user_profile(self, user: User) -> Dict[str, Any]:
        """Gera perfil completo do usuário"""
        
        profile = {
            'user_id': user.id,
            'username': user.username,
            'expertise_level': self._calculate_expertise_level(user),
            'preferred_categories': self._get_preferred_categories(user),
            'communication_style': self._detect_communication_style(user),
            'learning_pattern': self._analyze_learning_pattern(user),
            'quality_standards': self._analyze_quality_standards(user),
            'activity_metrics': self._get_activity_metrics(user),
            'personalization_settings': self._get_personalization_settings(user)
        }
        
        return profile
    
    def _calculate_expertise_level(self, user: User) -> Dict[str, Any]:
        """Calcula nível de expertise baseado no histórico"""
        
        perguntas = Pergunta.objects.filter(conversa__usuario=user)
        
        if not perguntas.exists():
            return {'level': 'iniciante', 'score': 0.3, 'confidence': 0.0}
        
        # Analisar complexidade das perguntas
        complexity_scores = []
        technical_terms = 0
        total_questions = perguntas.count()
        
        for pergunta in perguntas:
            # Calcular complexidade baseada em fatores
            text = pergunta.pergunta.lower()
            
            # Fatores de complexidade
            length_factor = min(len(text.split()) / 20, 1.0)
            technical_factor = self._count_technical_terms(text) / 10
            
            complexity = (length_factor + technical_factor) / 2
            complexity_scores.append(complexity)
            
            if technical_factor > 0.3:
                technical_terms += 1
        
        avg_complexity = sum(complexity_scores) / len(complexity_scores)
        technical_ratio = technical_terms / total_questions
        
        # Determinar nível
        combined_score = (avg_complexity * 0.6 + technical_ratio * 0.4)
        
        if combined_score >= 0.7:
            level = 'avancado'
        elif combined_score >= 0.4:
            level = 'intermediario'
        else:
            level = 'iniciante'
        
        return {
            'level': level,
            'score': combined_score,
            'confidence': min(total_questions / 10, 1.0),
            'metrics': {
                'avg_complexity': avg_complexity,
                'technical_ratio': technical_ratio,
                'total_questions': total_questions
            }
        }
    
    def _count_technical_terms(self, text: str) -> float:
        """Conta termos técnicos no texto"""
        technical_terms = [
            'api', 'framework', 'database', 'algoritmo', 'função', 'método',
            'classe', 'objeto', 'variável', 'loop', 'array', 'json', 'sql',
            'python', 'javascript', 'html', 'css', 'react', 'django'
        ]
        
        count = sum(1 for term in technical_terms if term in text)
        return min(count / 5, 1.0)  # Normalizar
    
    def _get_preferred_categories(self, user: User) -> List[Dict[str, Any]]:
        """Identifica categorias preferidas do usuário"""
        
        categorias = Pergunta.objects.filter(conversa__usuario=user).values('categoria').annotate(
            count=Count('categoria'),
            avg_confidence=Avg('confianca_score')
        ).order_by('-count')
        
        return list(categorias)
    
    def _detect_communication_style(self, user: User) -> Dict[str, Any]:
        """Detecta estilo de comunicação preferido"""
        
        perguntas = Pergunta.objects.filter(conversa__usuario=user)
        
        if not perguntas.exists():
            return {'style': 'balanced', 'confidence': 0.0}
        
        # Analisar padrões nas perguntas
        total_length = 0
        question_count = 0
        direct_questions = 0
        detailed_questions = 0
        
        for pergunta in perguntas:
            text = pergunta.pergunta
            words = text.split()
            total_length += len(words)
            question_count += 1
            
            # Perguntas diretas (curtas e objetivas)
            if len(words) <= 10 and any(word in text.lower() for word in ['o que', 'como', 'quando', 'onde']):
                direct_questions += 1
            
            # Perguntas detalhadas (longas e contextualizadas)
            if len(words) > 20:
                detailed_questions += 1
        
        avg_length = total_length / question_count if question_count > 0 else 0
        
        # Determinar estilo
        if direct_questions / question_count > 0.6:
            style = 'concise'  # Prefere respostas concisas
        elif detailed_questions / question_count > 0.4:
            style = 'detailed'  # Prefere respostas detalhadas
        else:
            style = 'balanced'  # Estilo balanceado
        
        return {
            'style': style,
            'confidence': min(question_count / 5, 1.0),
            'metrics': {
                'avg_question_length': avg_length,
                'direct_ratio': direct_questions / question_count if question_count > 0 else 0,
                'detailed_ratio': detailed_questions / question_count if question_count > 0 else 0
            }
        }
    
    def _analyze_learning_pattern(self, user: User) -> Dict[str, Any]:
        """Analisa padrão de aprendizado do usuário"""
        
        conversas = ConversaSession.objects.filter(usuario=user).order_by('created_at')
        
        if conversas.count() < 2:
            return {'pattern': 'explorer', 'confidence': 0.0}
        
        # Analisar padrões
        session_lengths = []
        follow_up_questions = 0
        topic_switches = 0
        
        for conversa in conversas:
            perguntas = conversa.perguntas.all()
            session_lengths.append(perguntas.count())
            
            # Contar perguntas de follow-up
            for pergunta in perguntas:
                if pergunta.pergunta_anterior:
                    follow_up_questions += 1
        
        avg_session_length = sum(session_lengths) / len(session_lengths)
        total_questions = sum(session_lengths)
        follow_up_ratio = follow_up_questions / total_questions if total_questions > 0 else 0
        
        # Determinar padrão
        if follow_up_ratio > 0.4 and avg_session_length > 5:
            pattern = 'deep_diver'  # Gosta de aprofundar tópicos
        elif avg_session_length < 3:
            pattern = 'quick_learner'  # Aprende rápido, perguntas pontuais
        else:
            pattern = 'explorer'  # Explora diversos tópicos
        
        return {
            'pattern': pattern,
            'confidence': min(total_questions / 20, 1.0),
            'metrics': {
                'avg_session_length': avg_session_length,
                'follow_up_ratio': follow_up_ratio,
                'total_sessions': conversas.count()
            }
        }
    
    def _analyze_quality_standards(self, user: User) -> Dict[str, Any]:
        """Analisa padrões de qualidade do usuário"""
        
        feedbacks = FeedbackResposta.objects.filter(pergunta__conversa__usuario=user)
        
        if not feedbacks.exists():
            return {'standard': 'medium', 'avg_rating': 3.0, 'confidence': 0.0}
        
        avg_rating = feedbacks.aggregate(avg=Avg('avaliacao'))['avg'] or 3.0
        rating_distribution = Counter(feedbacks.values_list('avaliacao', flat=True))
        
        # Determinar padrão de qualidade
        if avg_rating >= 4.0:
            standard = 'high'  # Padrões altos de qualidade
        elif avg_rating <= 2.5:
            standard = 'low'  # Mais tolerante com qualidade
        else:
            standard = 'medium'  # Padrão médio
        
        return {
            'standard': standard,
            'avg_rating': avg_rating,
            'confidence': min(feedbacks.count() / 10, 1.0),
            'distribution': dict(rating_distribution)
        }
    
    def _get_activity_metrics(self, user: User) -> Dict[str, Any]:
        """Obtém métricas de atividade do usuário"""
        
        total_conversations = ConversaSession.objects.filter(usuario=user).count()
        total_questions = Pergunta.objects.filter(conversa__usuario=user).count()
        total_feedbacks = FeedbackResposta.objects.filter(pergunta__conversa__usuario=user).count()
        
        return {
            'total_conversations': total_conversations,
            'total_questions': total_questions,
            'total_feedbacks': total_feedbacks,
            'engagement_score': min((total_feedbacks / max(total_questions, 1)) * 2, 1.0)
        }
    
    def _get_personalization_settings(self, user: User) -> Dict[str, Any]:
        """Obtém configurações de personalização (placeholder para futuras implementações)"""
        
        return {
            'response_length': 'auto',  # auto, short, medium, long
            'technical_level': 'auto',  # auto, basic, intermediate, advanced
            'include_examples': True,
            'include_sources': True,
            'preferred_format': 'structured'  # structured, narrative, bullet_points
        }

class ResponsePersonalizer:
    """Personaliza respostas baseado no perfil do usuário"""
    
    def __init__(self):
        self.profiler = UserProfiler()
    
    def personalize_prompt(self, base_prompt: str, user: User, query: str) -> str:
        """Personaliza o prompt baseado no perfil do usuário"""
        
        profile = self.profiler.get_user_profile(user)
        
        # Adaptações baseadas no perfil
        adaptations = []
        
        # Nível de expertise
        expertise = profile['expertise_level']
        if expertise['level'] == 'iniciante':
            adaptations.append("Use linguagem simples e explique conceitos básicos.")
            adaptations.append("Inclua exemplos práticos e analogias quando útil.")
        elif expertise['level'] == 'avancado':
            adaptations.append("Use terminologia técnica apropriada.")
            adaptations.append("Foque em detalhes técnicos e nuances avançadas.")
        
        # Estilo de comunicação
        comm_style = profile['communication_style']
        if comm_style['style'] == 'concise':
            adaptations.append("Seja conciso e direto ao ponto.")
        elif comm_style['style'] == 'detailed':
            adaptations.append("Forneça explicações detalhadas e abrangentes.")
        
        # Padrão de aprendizado
        learning = profile['learning_pattern']
        if learning['pattern'] == 'deep_diver':
            adaptations.append("Inclua informações adicionais para aprofundamento.")
        elif learning['pattern'] == 'quick_learner':
            adaptations.append("Foque nos pontos principais de forma eficiente.")
        
        # Padrões de qualidade
        quality = profile['quality_standards']
        if quality['standard'] == 'high':
            adaptations.append("Garanta alta precisão e cite fontes quando possível.")
        
        # Construir prompt personalizado
        if adaptations:
            personalization_instructions = "\n".join([f"- {adaptation}" for adaptation in adaptations])
            
            personalized_prompt = f"""{base_prompt}

INSTRUÇÕES DE PERSONALIZAÇÃO para {user.username}:
{personalization_instructions}

Adapte sua resposta considerando que o usuário tem:
- Nível de expertise: {expertise['level']} (confiança: {expertise['confidence']:.1f})
- Estilo de comunicação: {comm_style['style']}
- Padrão de aprendizado: {learning['pattern']}
- Padrão de qualidade: {quality['standard']} (média: {quality['avg_rating']:.1f}/5)
"""
        else:
            personalized_prompt = base_prompt
        
        return personalized_prompt
    
    def suggest_follow_up_questions(self, user: User, current_query: str, response: str) -> List[str]:
        """Sugere perguntas de follow-up personalizadas"""
        
        profile = self.profiler.get_user_profile(user)
        suggestions = []
        
        # Baseado no padrão de aprendizado
        learning_pattern = profile['learning_pattern']['pattern']
        
        if learning_pattern == 'deep_diver':
            suggestions.extend([
                f"Pode explicar mais detalhes sobre {self._extract_key_concept(current_query)}?",
                "Quais são as implicações avançadas disso?",
                "Como isso se relaciona com outros conceitos?"
            ])
        elif learning_pattern == 'explorer':
            suggestions.extend([
                "Quais são tópicos relacionados que eu deveria conhecer?",
                "Onde posso aplicar isso na prática?",
                "Existem alternativas para essa abordagem?"
            ])
        elif learning_pattern == 'quick_learner':
            suggestions.extend([
                "Qual é o próximo passo?",
                "Resumindo, qual é o ponto principal?",
                "Como posso implementar isso rapidamente?"
            ])
        
        return suggestions[:3]  # Limitar a 3 sugestões
    
    def _extract_key_concept(self, query: str) -> str:
        """Extrai conceito principal da query"""
        # Implementação simplificada
        words = query.split()
        # Retornar palavras mais longas (provavelmente conceitos)
        key_words = [word for word in words if len(word) > 4]
        return key_words[0] if key_words else "isso"

# Instâncias globais
user_profiler = UserProfiler()
response_personalizer = ResponsePersonalizer()
