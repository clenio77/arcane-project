from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Treinamentos, DataTreinamento
from .utils import gerar_documentos, base_conhecimento
import threading

@receiver(post_save, sender=Treinamentos)
def signals_treinamento_ia(sender, instance, created, **kwargs):
    """
    Tarefa 2 - Desenvolver o signals
    Processa automaticamente novos treinamentos
    """
    if created:
        print(f"Novo treinamento criado: {instance.id}")
        # Executar treinamento em thread separada para não bloquear
        thread = threading.Thread(target=task_treinar_ia, args=(instance.id,))
        thread.daemon = True
        thread.start()

def task_treinar_ia(instance_id):
    """
    Tarefa 3 - Desenvolver o treinamento da IA
    Processa o treinamento e adiciona à base de conhecimento
    """
    try:
        instance = Treinamentos.objects.get(id=instance_id)
        print(f"Iniciando treinamento para instância {instance_id}")

        # Gerar documentos estruturados
        documentos = gerar_documentos(instance)

        if documentos:
            # Salvar no banco de dados
            for doc in documentos:
                data_treinamento = DataTreinamento.objects.create(
                    metadata=doc['metadata'],
                    texto=doc['texto']
                )
                print(f"DataTreinamento criado: {data_treinamento.id}")

            # Adicionar à base de conhecimento FAISS
            base_conhecimento.adicionar_documentos(documentos)

            print(f"Treinamento concluído: {len(documentos)} documentos processados")
        else:
            print("Nenhum documento foi gerado para o treinamento")

    except Treinamentos.DoesNotExist:
        print(f"Treinamento {instance_id} não encontrado")
    except Exception as e:
        print(f"Erro no treinamento {instance_id}: {e}")