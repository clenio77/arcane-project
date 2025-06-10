"""
API REST Completa para Integração Externa
Permite integração com outros sistemas e aplicações
"""

import json
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from .models import (
    Treinamentos, ConversaSession, Pergunta, 
    FeedbackResposta, AnalyticsQuery
)
from .agents import agent_orchestrator
from .search_engine import hybrid_search_engine
from .personalization import response_personalizer
from .auto_improvement import continuous_learner, performance_monitor
from .utils import base_conhecimento

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

# ============ ENDPOINTS DE IA E CHAT ============

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_chat_intelligent(request):
    """
    Endpoint principal para chat inteligente
    
    POST /api/chat/
    {
        "query": "Como implementar autenticação JWT?",
        "conversation_id": 123,
        "use_agents": true,
        "personalize": true
    }
    """
    try:
        data = request.data
        query = data.get('query', '').strip()
        conversation_id = data.get('conversation_id')
        use_agents = data.get('use_agents', True)
        personalize = data.get('personalize', True)
        
        if not query:
            return Response({
                'error': 'Query é obrigatória'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obter ou criar conversa
        if conversation_id:
            try:
                conversa = ConversaSession.objects.get(
                    id=conversation_id, 
                    usuario=request.user
                )
            except ConversaSession.DoesNotExist:
                return Response({
                    'error': 'Conversa não encontrada'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            conversa = ConversaSession.objects.create(
                usuario=request.user,
                titulo=f"API Chat {query[:30]}..."
            )
        
        # Buscar contexto
        if use_agents:
            # Usar sistema de agentes
            context_docs = hybrid_search_engine.search(query, k=7)
            context = "\n\n".join([doc['texto'] for doc in context_docs[:5]])
            
            # Processar com agentes
            agent_response = agent_orchestrator.process_with_collaboration(
                query, {'contexto': context}
            )
            
            response_text = agent_response['response']
            confidence = agent_response['confidence']
            agent_used = agent_response['agent']
            reasoning = agent_response['reasoning']
        else:
            # Busca tradicional
            context_docs = base_conhecimento.buscar_documentos(query, k=5)
            context = "\n\n".join([doc['texto'] for doc in context_docs])
            
            # Resposta simples (implementar chamada OpenAI aqui)
            response_text = "Resposta gerada pelo sistema tradicional"
            confidence = 0.7
            agent_used = "traditional"
            reasoning = "Busca semântica tradicional"
        
        # Personalizar resposta se solicitado
        if personalize:
            # Aplicar personalização (implementar integração)
            pass
        
        # Salvar pergunta
        pergunta = Pergunta.objects.create(
            conversa=conversa,
            pergunta=query,
            resposta=response_text,
            confianca_score=confidence
        )
        
        # Associar documentos
        for doc in context_docs[:5]:
            # Implementar associação com DataTreinamento
            pass
        
        return Response({
            'conversation_id': conversa.id,
            'question_id': pergunta.id,
            'response': response_text,
            'confidence': confidence,
            'agent_used': agent_used,
            'reasoning': reasoning,
            'sources': [doc['metadata'] for doc in context_docs[:3]],
            'context_documents': len(context_docs)
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_chat_stream(request):
    """
    Endpoint para chat com streaming
    
    POST /api/chat/stream/
    """
    def generate_stream():
        try:
            data = json.loads(request.body)
            query = data.get('query', '')
            
            # Simular streaming (implementar integração real com OpenAI)
            words = f"Esta é uma resposta simulada para: {query}".split()
            
            for word in words:
                yield f"data: {json.dumps({'content': word + ' '})}\n\n"
            
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingHttpResponse(
        generate_stream(),
        content_type='text/event-stream'
    )

# ============ ENDPOINTS DE BUSCA ============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_search(request):
    """
    Endpoint de busca avançada
    
    GET /api/search/?q=python&type=hybrid&k=10
    """
    query = request.GET.get('q', '')
    search_type = request.GET.get('type', 'hybrid')  # semantic, lexical, hybrid
    k = int(request.GET.get('k', 10))
    
    if not query:
        return Response({
            'error': 'Parâmetro q (query) é obrigatório'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        if search_type == 'hybrid':
            results = hybrid_search_engine.search(query, k)
        elif search_type == 'semantic':
            results = base_conhecimento.buscar_documentos(query, k)
        else:
            results = base_conhecimento.buscar_documentos(query, k)
        
        return Response({
            'query': query,
            'search_type': search_type,
            'total_results': len(results),
            'results': results
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ============ ENDPOINTS DE TREINAMENTO ============

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_train(request):
    """
    Endpoint para adicionar treinamento
    
    POST /api/train/
    {
        "type": "text",
        "content": "Conteúdo para treinamento...",
        "url": "https://example.com",
        "file": <arquivo>
    }
    """
    try:
        tipo = request.data.get('type', 'text')
        content = request.data.get('content', '')
        url = request.data.get('url', '')
        file = request.FILES.get('file')
        
        if not any([content, url, file]):
            return Response({
                'error': 'Pelo menos um tipo de conteúdo deve ser fornecido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Criar treinamento
        treinamento = Treinamentos.objects.create(
            tipo=tipo,
            conteudo=content,
            site=url,
            documento=file,
            usuario=request.user,
            status='pendente'
        )
        
        return Response({
            'training_id': treinamento.id,
            'status': 'created',
            'message': 'Treinamento criado e será processado em breve'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_training_status(request, training_id):
    """
    Verifica status de um treinamento
    
    GET /api/train/{id}/status/
    """
    try:
        treinamento = get_object_or_404(
            Treinamentos, 
            id=training_id, 
            usuario=request.user
        )
        
        return Response({
            'training_id': treinamento.id,
            'status': treinamento.status,
            'created_at': treinamento.created_at,
            'total_chunks': treinamento.total_chunks,
            'quality_score': treinamento.qualidade_score,
            'error_details': treinamento.erro_detalhes
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ============ ENDPOINTS DE ANALYTICS ============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_analytics_overview(request):
    """
    Visão geral de analytics
    
    GET /api/analytics/overview/
    """
    try:
        # Usar sistema de auto-melhoria para análise
        performance_data = continuous_learner.analyze_system_performance()
        health_data = performance_monitor.check_real_time_health()
        
        return Response({
            'performance': performance_data,
            'health': health_data,
            'timestamp': health_data['timestamp']
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_user_profile(request):
    """
    Perfil do usuário
    
    GET /api/profile/
    """
    try:
        from .personalization import user_profiler
        
        profile = user_profiler.get_user_profile(request.user)
        
        return Response(profile)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ============ ENDPOINTS DE FEEDBACK ============

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_feedback(request):
    """
    Enviar feedback sobre resposta
    
    POST /api/feedback/
    {
        "question_id": 123,
        "rating": 4,
        "comment": "Resposta muito útil!"
    }
    """
    try:
        question_id = request.data.get('question_id')
        rating = request.data.get('rating')
        comment = request.data.get('comment', '')
        
        if not question_id or not rating:
            return Response({
                'error': 'question_id e rating são obrigatórios'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        pergunta = get_object_or_404(
            Pergunta, 
            id=question_id,
            conversa__usuario=request.user
        )
        
        feedback, created = FeedbackResposta.objects.update_or_create(
            pergunta=pergunta,
            defaults={
                'avaliacao': rating,
                'comentario': comment
            }
        )
        
        return Response({
            'feedback_id': feedback.id,
            'created': created,
            'message': 'Feedback registrado com sucesso'
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ============ ENDPOINTS DE SISTEMA ============

@api_view(['GET'])
@permission_classes([AllowAny])
def api_health(request):
    """
    Health check do sistema
    
    GET /api/health/
    """
    try:
        health = performance_monitor.check_real_time_health()
        
        return Response({
            'status': health['status'],
            'timestamp': health['timestamp'],
            'version': '2.0.0',
            'features': {
                'agents': True,
                'hybrid_search': True,
                'personalization': True,
                'auto_improvement': True
            }
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_system_stats(request):
    """
    Estatísticas do sistema
    
    GET /api/system/stats/
    """
    try:
        stats = base_conhecimento.obter_estatisticas()
        
        # Adicionar estatísticas de uso
        stats.update({
            'total_users': User.objects.count(),
            'total_conversations': ConversaSession.objects.count(),
            'total_questions': Pergunta.objects.count(),
            'total_feedbacks': FeedbackResposta.objects.count(),
        })
        
        return Response(stats)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ============ WEBHOOKS ============

@api_view(['POST'])
@permission_classes([AllowAny])  # Implementar autenticação por token
def api_webhook_training_complete(request):
    """
    Webhook para notificar conclusão de treinamento
    
    POST /api/webhooks/training-complete/
    """
    try:
        data = request.data
        training_id = data.get('training_id')
        status_update = data.get('status')
        
        if training_id:
            treinamento = Treinamentos.objects.get(id=training_id)
            treinamento.status = status_update
            treinamento.save()
        
        return Response({'status': 'received'})
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
