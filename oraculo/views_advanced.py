"""
Views avançadas para funcionalidades de IA inteligente
"""

import json
import time
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import (
    ConversaSession, Pergunta, FeedbackResposta, 
    AnalyticsQuery, DataTreinamento, Treinamentos
)
from .ai_advanced import (
    analisador_semantico, otimizador_prompt, 
    avaliador_qualidade, sugestor_perguntas, analytics_ia
)
from .utils import base_conhecimento

@login_required
def iniciar_conversa(request):
    """Inicia uma nova sessão de conversa"""
    if request.method == 'POST':
        # Finalizar conversa ativa anterior
        ConversaSession.objects.filter(
            usuario=request.user, 
            ativa=True
        ).update(ativa=False)
        
        # Criar nova conversa
        conversa = ConversaSession.objects.create(
            usuario=request.user,
            titulo=f"Conversa {timezone.now().strftime('%d/%m %H:%M')}"
        )
        
        return JsonResponse({
            'conversa_id': conversa.id,
            'titulo': conversa.titulo
        })
    
    return JsonResponse({'error': 'Método não permitido'}, status=405)

@login_required
def listar_conversas(request):
    """Lista conversas do usuário"""
    conversas = ConversaSession.objects.filter(
        usuario=request.user
    ).prefetch_related('perguntas')[:20]
    
    dados_conversas = []
    for conversa in conversas:
        ultima_pergunta = conversa.perguntas.first()
        dados_conversas.append({
            'id': conversa.id,
            'titulo': conversa.titulo,
            'ativa': conversa.ativa,
            'created_at': conversa.created_at.isoformat(),
            'total_perguntas': conversa.perguntas.count(),
            'ultima_pergunta': ultima_pergunta.pergunta[:100] if ultima_pergunta else None
        })
    
    return JsonResponse({'conversas': dados_conversas})

@csrf_exempt
@login_required
def chat_inteligente(request):
    """Chat com funcionalidades avançadas de IA"""
    if request.method == 'GET':
        # Obter conversa ativa ou criar nova
        conversa = ConversaSession.objects.filter(
            usuario=request.user, 
            ativa=True
        ).first()
        
        if not conversa:
            conversa = ConversaSession.objects.create(
                usuario=request.user,
                titulo=f"Conversa {timezone.now().strftime('%d/%m %H:%M')}"
            )
        
        # Obter histórico da conversa
        perguntas = conversa.perguntas.all()[:10]
        historico = []
        
        for pergunta in perguntas:
            historico.append({
                'pergunta': pergunta.pergunta,
                'resposta': pergunta.resposta,
                'categoria': pergunta.get_categoria_display(),
                'confianca': pergunta.confianca_score,
                'created_at': pergunta.created_at.isoformat()
            })
        
        return render(request, 'chat_inteligente.html', {
            'conversa': conversa,
            'historico': historico
        })
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            pergunta_texto = data.get('pergunta', '').strip()
            conversa_id = data.get('conversa_id')
            
            if not pergunta_texto:
                return JsonResponse({'error': 'Pergunta não pode estar vazia'}, status=400)
            
            # Obter conversa
            conversa = get_object_or_404(ConversaSession, id=conversa_id, usuario=request.user)
            
            # Análise semântica da pergunta
            inicio_analise = time.time()
            intencao = analisador_semantico.detectar_intencao(pergunta_texto)
            entidades = analisador_semantico.extrair_entidades(pergunta_texto)
            complexidade = analisador_semantico.calcular_complexidade(pergunta_texto)
            
            # Buscar contexto relevante
            documentos_relevantes = base_conhecimento.buscar_documentos(
                pergunta_texto, 
                k=7 if complexidade > 0.7 else 5
            )
            
            # Criar contexto otimizado
            contexto = ""
            if documentos_relevantes:
                # Priorizar documentos com melhor score
                textos_contexto = [doc['texto'] for doc in documentos_relevantes[:5]]
                contexto = "\n\n".join(textos_contexto)
            
            # Obter pergunta anterior para contexto
            pergunta_anterior = conversa.perguntas.first()
            
            # Gerar prompt otimizado
            prompt = otimizador_prompt.gerar_prompt_otimizado(
                pergunta_texto, contexto, intencao
            )
            
            # Adicionar contexto da conversa se houver pergunta anterior
            if pergunta_anterior and pergunta_anterior.resposta:
                prompt = f"Contexto da conversa anterior:\nPergunta: {pergunta_anterior.pergunta}\nResposta: {pergunta_anterior.resposta}\n\n{prompt}"
            
            # Criar pergunta no banco
            pergunta_obj = Pergunta.objects.create(
                conversa=conversa,
                pergunta=pergunta_texto,
                categoria=intencao,
                pergunta_anterior=pergunta_anterior,
                tempo_resposta=time.time() - inicio_analise
            )
            
            # Associar documentos relevantes
            for doc in documentos_relevantes:
                try:
                    data_treinamentos = DataTreinamento.objects.filter(
                        texto=doc['texto']
                    )
                    for dt in data_treinamentos:
                        pergunta_obj.data_treinamento.add(dt)
                except Exception as e:
                    print(f"Erro ao associar documento: {e}")
            
            # Gerar sugestões de perguntas relacionadas
            historico_conversa = [p.pergunta for p in conversa.perguntas.all()[:5]]
            sugestoes = sugestor_perguntas.gerar_sugestoes_relacionadas(
                pergunta_texto, historico_conversa
            )
            
            return JsonResponse({
                'pergunta_id': pergunta_obj.id,
                'prompt': prompt,
                'contexto': contexto,
                'analise': {
                    'intencao': intencao,
                    'entidades': entidades,
                    'complexidade': round(complexidade, 2),
                    'documentos_encontrados': len(documentos_relevantes)
                },
                'sugestoes': sugestoes,
                'fontes': [doc['metadata'] for doc in documentos_relevantes]
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@login_required
def avaliar_resposta(request):
    """Permite ao usuário avaliar a qualidade da resposta"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            pergunta_id = data.get('pergunta_id')
            avaliacao = data.get('avaliacao')  # 1-5
            comentario = data.get('comentario', '')
            
            if not pergunta_id or not avaliacao:
                return JsonResponse({'error': 'Dados incompletos'}, status=400)
            
            pergunta = get_object_or_404(Pergunta, id=pergunta_id)
            
            # Verificar se o usuário pode avaliar esta pergunta
            if pergunta.conversa.usuario != request.user:
                return JsonResponse({'error': 'Não autorizado'}, status=403)
            
            # Criar ou atualizar feedback
            feedback, created = FeedbackResposta.objects.update_or_create(
                pergunta=pergunta,
                defaults={
                    'avaliacao': avaliacao,
                    'comentario': comentario
                }
            )
            
            # Calcular score de confiança baseado no feedback
            if pergunta.resposta:
                score_qualidade = avaliador_qualidade.calcular_score_relevancia(
                    pergunta.pergunta, pergunta.resposta, ""
                )
                score_feedback = avaliacao / 5.0
                
                # Score combinado
                pergunta.confianca_score = (score_qualidade * 0.4 + score_feedback * 0.6)
                pergunta.save(update_fields=['confianca_score'])
            
            return JsonResponse({
                'success': True,
                'feedback_id': feedback.id,
                'created': created
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método não permitido'}, status=405)

@login_required
def dashboard_analytics(request):
    """Dashboard com analytics do sistema"""
    # Métricas gerais
    metricas_qualidade = analytics_ia.obter_metricas_qualidade()
    perguntas_populares = analytics_ia.obter_perguntas_populares()
    
    # Estatísticas da base de conhecimento
    stats_base = base_conhecimento.obter_estatisticas()
    
    # Métricas do usuário
    conversas_usuario = ConversaSession.objects.filter(usuario=request.user).count()
    perguntas_usuario = Pergunta.objects.filter(conversa__usuario=request.user).count()
    
    # Atividade recente (últimos 7 dias)
    data_limite = timezone.now() - timedelta(days=7)
    atividade_recente = AnalyticsQuery.objects.filter(
        created_at__gte=data_limite
    ).count()
    
    # Distribuição por categoria
    distribuicao_categorias = Pergunta.objects.values('categoria').annotate(
        count=Count('categoria')
    ).order_by('-count')
    
    context = {
        'metricas_qualidade': metricas_qualidade,
        'perguntas_populares': perguntas_populares,
        'stats_base': stats_base,
        'conversas_usuario': conversas_usuario,
        'perguntas_usuario': perguntas_usuario,
        'atividade_recente': atividade_recente,
        'distribuicao_categorias': list(distribuicao_categorias)
    }
    
    return render(request, 'dashboard_analytics.html', context)

@login_required
def exportar_conversa(request, conversa_id):
    """Exporta conversa em formato JSON"""
    conversa = get_object_or_404(
        ConversaSession, 
        id=conversa_id, 
        usuario=request.user
    )
    
    perguntas = conversa.perguntas.all()
    
    dados_exportacao = {
        'conversa': {
            'id': conversa.id,
            'titulo': conversa.titulo,
            'created_at': conversa.created_at.isoformat(),
            'total_perguntas': perguntas.count()
        },
        'perguntas': []
    }
    
    for pergunta in perguntas:
        dados_exportacao['perguntas'].append({
            'pergunta': pergunta.pergunta,
            'resposta': pergunta.resposta,
            'categoria': pergunta.categoria,
            'confianca_score': pergunta.confianca_score,
            'tempo_resposta': pergunta.tempo_resposta,
            'created_at': pergunta.created_at.isoformat(),
            'feedback': {
                'avaliacao': pergunta.feedback.avaliacao if hasattr(pergunta, 'feedback') else None,
                'comentario': pergunta.feedback.comentario if hasattr(pergunta, 'feedback') else None
            }
        })
    
    response = JsonResponse(dados_exportacao, json_dumps_params={'indent': 2})
    response['Content-Disposition'] = f'attachment; filename="conversa_{conversa_id}.json"'
    
    return response
