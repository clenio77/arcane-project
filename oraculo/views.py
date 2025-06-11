from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.messages import constants
# from rolepermissions.checkers import has_permission  # Disabled for Heroku
from django.http import Http404, JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Treinamentos, Pergunta, DataTreinamento
from .utils import base_conhecimento
import openai
import json
import os

# Configurar OpenAI
openai.api_key = settings.OPENAI_API_KEY

def treinar_ia(request):
    # if not has_permission(request.user, 'treinar_ia'):  # Disabled for Heroku
    #     raise Http404()
    if not request.user.is_authenticated:
        raise Http404()

    if request.method == 'GET':
        # Buscar treinamentos existentes para exibir
        treinamentos = Treinamentos.objects.all().order_by('-id')[:10]
        return render(request, 'treinar_ia.html', {'treinamentos': treinamentos})

    elif request.method == 'POST':
        # Tarefa 1 - Desenvolver o salvamento do arquivo
        site = request.POST.get('site', '').strip()
        conteudo = request.POST.get('conteudo', '').strip()
        documento = request.FILES.get('documento')

        # Validações
        if not site and not conteudo and not documento:
            messages.add_message(request, constants.ERROR, 'Pelo menos um campo deve ser preenchido.')
            return redirect('treinar_ia')

        # Validar arquivo se fornecido
        if documento:
            # Verificar tamanho
            if documento.size > settings.MAX_UPLOAD_SIZE:
                messages.add_message(request, constants.ERROR, 'Arquivo muito grande. Máximo 10MB.')
                return redirect('treinar_ia')

            # Verificar tipo
            file_extension = os.path.splitext(documento.name)[1].lower().replace('.', '')
            if file_extension not in settings.ALLOWED_FILE_TYPES:
                messages.add_message(request, constants.ERROR, f'Tipo de arquivo não permitido. Use: {", ".join(settings.ALLOWED_FILE_TYPES)}')
                return redirect('treinar_ia')

        # Adicionar https:// se necessário
        if site and not site.startswith('http'):
            site = 'https://' + site

        try:
            # Criar treinamento
            treinamento = Treinamentos.objects.create(
                site=site or '',
                conteudo=conteudo,
                documento=documento
            )

            messages.add_message(request, constants.SUCCESS, 'Treinamento iniciado! O processamento será feito em segundo plano.')
            return redirect('treinar_ia')

        except Exception as e:
            messages.add_message(request, constants.ERROR, f'Erro ao salvar treinamento: {str(e)}')
            return redirect('treinar_ia')


@csrf_exempt
def chat(request):
    if request.method == 'GET':
        return render(request, 'chat.html')
    elif request.method == 'POST':
        # Tarefa 6 - Criar uma pergunta
        try:
            data = json.loads(request.body)
            pergunta_texto = data.get('pergunta', '').strip()

            if not pergunta_texto:
                return JsonResponse({'error': 'Pergunta não pode estar vazia'}, status=400)

            # Buscar documentos relevantes
            documentos_relevantes = base_conhecimento.buscar_documentos(pergunta_texto, k=5)

            # Criar contexto para a IA
            contexto = ""
            fontes = []

            if documentos_relevantes:
                contexto = "\n\n".join([doc['texto'] for doc in documentos_relevantes])
                fontes = [doc['metadata'] for doc in documentos_relevantes]

            # Salvar pergunta no banco
            pergunta_obj = Pergunta.objects.create(pergunta=pergunta_texto)

            # Associar documentos de treinamento relevantes
            for doc in documentos_relevantes:
                # Buscar DataTreinamento correspondente
                data_treinamentos = DataTreinamento.objects.filter(
                    texto=doc['texto']
                )
                for dt in data_treinamentos:
                    pergunta_obj.data_treinamento.add(dt)

            return JsonResponse({
                'pergunta_id': pergunta_obj.id,
                'contexto': contexto,
                'fontes': fontes
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def stream_response(request):
    """
    Usar IA para obter a resposta e enviar em tempo real
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        data = json.loads(request.body)
        pergunta_texto = data.get('pergunta', '')
        contexto = data.get('contexto', '')

        if not pergunta_texto:
            return JsonResponse({'error': 'Pergunta não fornecida'}, status=400)

        # Usar otimizador de prompt avançado
        from .ai_advanced import analisador_semantico, otimizador_prompt, avaliador_qualidade

        # Detectar intenção da pergunta
        intencao = analisador_semantico.detectar_intencao(pergunta_texto)

        # Preparar prompt otimizado
        if contexto:
            prompt = otimizador_prompt.gerar_prompt_otimizado(pergunta_texto, contexto, intencao)
        else:
            prompt = f"""Responda à seguinte pergunta de forma clara e precisa:

Pergunta: {pergunta_texto}

Resposta:"""

        def generate_response():
            resposta_completa = ""
            try:
                response = openai.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "Você é um assistente especializado que responde perguntas baseado no contexto fornecido. Seja preciso, estruturado e cite fontes quando relevante."},
                        {"role": "user", "content": prompt}
                    ],
                    stream=True,
                    max_tokens=1500,
                    temperature=0.6  # Menos criativo, mais factual
                )

                for chunk in response:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        resposta_completa += content
                        yield f"data: {json.dumps({'content': content})}\n\n"

                # Avaliar qualidade da resposta
                if resposta_completa and contexto:
                    score_relevancia = avaliador_qualidade.calcular_score_relevancia(
                        pergunta_texto, resposta_completa, contexto
                    )
                    score_completude = avaliador_qualidade.avaliar_completude(resposta_completa)

                    # Salvar resposta e scores na pergunta (se existir)
                    try:
                        from .models import Pergunta
                        pergunta_obj = Pergunta.objects.filter(pergunta=pergunta_texto).last()
                        if pergunta_obj:
                            pergunta_obj.resposta = resposta_completa
                            pergunta_obj.confianca_score = (score_relevancia + score_completude) / 2
                            pergunta_obj.save(update_fields=['resposta', 'confianca_score'])
                    except Exception as e:
                        print(f"Erro ao salvar resposta: {e}")

                yield f"data: {json.dumps({'done': True, 'qualidade': {'relevancia': score_relevancia if 'score_relevancia' in locals() else 0.5, 'completude': score_completude if 'score_completude' in locals() else 0.5}})}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingHttpResponse(
            generate_response(),
            content_type='text/event-stream'
        )

    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def ver_fontes(request, id):
    try:
        pergunta = Pergunta.objects.get(id=id)
        data_treinamentos = pergunta.data_treinamento.all()
        return render(request, 'ver_fontes.html', {
            'pergunta': pergunta,
            'data_treinamentos': data_treinamentos
        })
    except Pergunta.DoesNotExist:
        raise Http404("Pergunta não encontrada")