import os
import re
import json
import PyPDF2
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from django.conf import settings
import openai
import numpy as np
import faiss
import pickle

# Configurar OpenAI
openai.api_key = settings.OPENAI_API_KEY

def html_para_texto_rag(html_str: str) -> str:
    """
    Tarefa 5 - Transformar HTML em texto para IA
    Remove tags HTML e extrai texto limpo
    """
    if not html_str:
        return ""

    # Parse HTML
    soup = BeautifulSoup(html_str, 'html.parser')

    # Remove scripts e styles
    for script in soup(["script", "style"]):
        script.decompose()

    # Extrair texto
    text = soup.get_text()

    # Limpar texto
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)

    return text

def extrair_texto_pdf(file_path: str) -> str:
    """
    Extrai texto de arquivo PDF
    """
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Erro ao extrair texto do PDF: {e}")
    return text

def extrair_texto_arquivo(file_path: str) -> str:
    """
    Extrai texto de diferentes tipos de arquivo
    """
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == '.pdf':
        return extrair_texto_pdf(file_path)
    elif file_extension in ['.txt', '.md']:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()
    else:
        return ""

def chunkar_texto(texto: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Divide texto em chunks menores com sobreposição
    """
    if len(texto) <= chunk_size:
        return [texto]

    chunks = []
    start = 0

    while start < len(texto):
        end = start + chunk_size

        # Tentar quebrar em uma frase completa
        if end < len(texto):
            # Procurar por ponto final próximo
            last_period = texto.rfind('.', start, end)
            if last_period > start + chunk_size // 2:
                end = last_period + 1

        chunk = texto[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap
        if start >= len(texto):
            break

    return chunks

def gerar_embedding(texto: str) -> List[float]:
    """
    Gera embedding usando OpenAI com cache inteligente
    """
    from .ai_advanced import gerenciador_cache

    # Tentar obter do cache primeiro
    embedding_cache = gerenciador_cache.obter_embedding_cache(texto)
    if embedding_cache:
        return embedding_cache

    try:
        response = openai.embeddings.create(
            model="text-embedding-ada-002",
            input=texto
        )
        embedding = response.data[0].embedding

        # Salvar no cache
        gerenciador_cache.salvar_embedding_cache(texto, embedding)

        return embedding
    except Exception as e:
        print(f"Erro ao gerar embedding: {e}")
        return []

def gerar_documentos(instance) -> List[Dict[str, Any]]:
    """
    Tarefa 4 - Gerar uma lista de documentos
    Processa uma instância de Treinamento e gera documentos estruturados
    """
    documentos = []

    # Processar conteúdo de texto
    if instance.conteudo:
        chunks = chunkar_texto(instance.conteudo)
        for i, chunk in enumerate(chunks):
            documento = {
                'id': f"{instance.id}_texto_{i}",
                'texto': chunk,
                'metadata': {
                    'source': 'texto_manual',
                    'site': instance.site,
                    'chunk_index': i,
                    'total_chunks': len(chunks)
                }
            }
            documentos.append(documento)

    # Processar arquivo
    if instance.documento:
        file_path = instance.documento.path
        texto_arquivo = extrair_texto_arquivo(file_path)

        if texto_arquivo:
            chunks = chunkar_texto(texto_arquivo)
            for i, chunk in enumerate(chunks):
                documento = {
                    'id': f"{instance.id}_arquivo_{i}",
                    'texto': chunk,
                    'metadata': {
                        'source': 'arquivo',
                        'site': instance.site,
                        'filename': os.path.basename(file_path),
                        'chunk_index': i,
                        'total_chunks': len(chunks)
                    }
                }
                documentos.append(documento)

    # Processar conteúdo web (se site for fornecido)
    if instance.site and instance.site.startswith('http'):
        try:
            response = requests.get(instance.site, timeout=10)
            if response.status_code == 200:
                texto_web = html_para_texto_rag(response.text)
                if texto_web:
                    chunks = chunkar_texto(texto_web)
                    for i, chunk in enumerate(chunks):
                        documento = {
                            'id': f"{instance.id}_web_{i}",
                            'texto': chunk,
                            'metadata': {
                                'source': 'web',
                                'site': instance.site,
                                'chunk_index': i,
                                'total_chunks': len(chunks)
                            }
                        }
                        documentos.append(documento)
        except Exception as e:
            print(f"Erro ao processar site {instance.site}: {e}")

    return documentos

class BaseConhecimento:
    """
    Classe para gerenciar a base de conhecimento usando FAISS
    """

    def __init__(self):
        self.index = None
        self.documentos = []
        self.dimension = 1536  # Dimensão do embedding da OpenAI
        self.index_path = os.path.join(settings.MEDIA_ROOT, 'faiss_index.bin')
        self.docs_path = os.path.join(settings.MEDIA_ROOT, 'documentos.pkl')
        self.carregar_base()

    def carregar_base(self):
        """Carrega índice FAISS e documentos existentes"""
        try:
            if os.path.exists(self.index_path) and os.path.exists(self.docs_path):
                self.index = faiss.read_index(self.index_path)
                with open(self.docs_path, 'rb') as f:
                    self.documentos = pickle.load(f)
                print(f"Base carregada: {len(self.documentos)} documentos")
            else:
                self.index = faiss.IndexFlatL2(self.dimension)
                self.documentos = []
                print("Nova base de conhecimento criada")
        except Exception as e:
            print(f"Erro ao carregar base: {e}")
            self.index = faiss.IndexFlatL2(self.dimension)
            self.documentos = []

    def salvar_base(self):
        """Salva índice FAISS e documentos"""
        try:
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
            faiss.write_index(self.index, self.index_path)
            with open(self.docs_path, 'wb') as f:
                pickle.dump(self.documentos, f)
            print("Base salva com sucesso")
        except Exception as e:
            print(f"Erro ao salvar base: {e}")

    def adicionar_documentos(self, documentos: List[Dict[str, Any]]):
        """Adiciona documentos à base de conhecimento"""
        if not documentos:
            return

        embeddings = []
        docs_validos = []

        for doc in documentos:
            embedding = gerar_embedding(doc['texto'])
            if embedding:
                embeddings.append(embedding)
                docs_validos.append(doc)

        if embeddings:
            embeddings_array = np.array(embeddings).astype('float32')
            self.index.add(embeddings_array)
            self.documentos.extend(docs_validos)
            self.salvar_base()
            print(f"Adicionados {len(docs_validos)} documentos à base")

    def buscar_documentos(self, query: str, k: int = 5, filtro_score: float = 0.8) -> List[Dict[str, Any]]:
        """Busca documentos similares à query com filtros avançados"""
        from .ai_advanced import analisador_semantico, analytics_ia
        import time

        inicio = time.time()

        if not query or self.index.ntotal == 0:
            return []

        # Análise semântica da query
        intencao = analisador_semantico.detectar_intencao(query)
        entidades = analisador_semantico.extrair_entidades(query)

        query_embedding = gerar_embedding(query)
        if not query_embedding:
            return []

        # Buscar mais documentos para depois filtrar
        k_expandido = min(k * 3, self.index.ntotal)
        query_vector = np.array([query_embedding]).astype('float32')
        scores, indices = self.index.search(query_vector, k_expandido)

        resultados = []
        scores_validos = []

        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.documentos):
                doc = self.documentos[idx].copy()
                doc['score'] = float(score)
                doc['intencao_detectada'] = intencao

                # Filtrar por score mínimo
                if score <= filtro_score:  # FAISS usa distância L2, menor é melhor
                    resultados.append(doc)
                    scores_validos.append(score)

        # Re-ranking baseado em entidades encontradas
        if entidades:
            for doc in resultados:
                bonus = 0
                for entidade in entidades:
                    if entidade.lower() in doc['texto'].lower():
                        bonus += 0.1
                doc['score'] -= bonus  # Diminuir score (melhor ranking)

        # Ordenar por score e limitar
        resultados.sort(key=lambda x: x['score'])
        resultados_finais = resultados[:k]

        # Registrar analytics
        tempo_busca = time.time() - inicio
        score_medio = np.mean(scores_validos) if scores_validos else 0.0

        try:
            analytics_ia.registrar_query(
                pergunta=query,
                usuario=None,  # Será preenchido na view
                documentos_encontrados=len(resultados_finais),
                tempo_busca=tempo_busca,
                score_medio=float(score_medio)
            )
        except Exception as e:
            print(f"Erro ao registrar analytics: {e}")

        return resultados_finais

    def obter_estatisticas(self) -> Dict[str, Any]:
        """Obtém estatísticas da base de conhecimento"""
        return {
            'total_documentos': len(self.documentos),
            'dimensao_embedding': self.dimension,
            'tamanho_indice': self.index.ntotal if self.index else 0,
            'tipos_fonte': self._contar_tipos_fonte(),
            'qualidade_media': self._calcular_qualidade_media()
        }

    def _contar_tipos_fonte(self) -> Dict[str, int]:
        """Conta documentos por tipo de fonte"""
        tipos = {}
        for doc in self.documentos:
            fonte = doc.get('metadata', {}).get('source', 'desconhecido')
            tipos[fonte] = tipos.get(fonte, 0) + 1
        return tipos

    def _calcular_qualidade_media(self) -> float:
        """Calcula qualidade média dos documentos"""
        if not self.documentos:
            return 0.0

        scores = []
        for doc in self.documentos:
            # Score baseado no tamanho do texto e presença de metadados
            score = min(len(doc.get('texto', '')) / 500, 1.0)  # Normalizar por 500 chars
            if doc.get('metadata'):
                score += 0.2
            scores.append(min(score, 1.0))

        return sum(scores) / len(scores) if scores else 0.0

# Instância global da base de conhecimento
base_conhecimento = BaseConhecimento()