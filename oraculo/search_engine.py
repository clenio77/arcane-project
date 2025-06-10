"""
Sistema de Busca Híbrida Avançada
Combina busca semântica, lexical e por grafos de conhecimento
"""

import re
import math
from typing import List, Dict, Any, Tuple
from collections import defaultdict, Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .utils import base_conhecimento, gerar_embedding
from .models import DataTreinamento, Pergunta

class HybridSearchEngine:
    """Motor de busca híbrido que combina múltiplas estratégias"""
    
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.knowledge_graph = KnowledgeGraph()
        self.query_expander = QueryExpander()
    
    def search(self, query: str, k: int = 10, hybrid_weights: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """
        Busca híbrida combinando múltiplas estratégias
        """
        if hybrid_weights is None:
            hybrid_weights = {
                'semantic': 0.5,    # Busca semântica (embeddings)
                'lexical': 0.3,     # Busca lexical (TF-IDF)
                'graph': 0.2        # Busca por grafo de conhecimento
            }
        
        # Expandir query com termos relacionados
        expanded_query = self.query_expander.expand(query)
        
        # 1. Busca Semântica (embeddings + FAISS)
        semantic_results = self._semantic_search(expanded_query, k * 2)
        
        # 2. Busca Lexical (TF-IDF)
        lexical_results = self._lexical_search(expanded_query, k * 2)
        
        # 3. Busca por Grafo de Conhecimento
        graph_results = self._graph_search(expanded_query, k * 2)
        
        # 4. Combinar resultados com pesos
        combined_results = self._combine_results(
            semantic_results, lexical_results, graph_results, 
            hybrid_weights, k
        )
        
        # 5. Re-ranking final baseado em múltiplos fatores
        final_results = self._final_rerank(combined_results, query)
        
        return final_results[:k]
    
    def _semantic_search(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Busca semântica usando embeddings"""
        results = base_conhecimento.buscar_documentos(query, k)
        
        for result in results:
            result['search_type'] = 'semantic'
            result['semantic_score'] = 1.0 / (1.0 + result['score'])  # Converter distância para similaridade
        
        return results
    
    def _lexical_search(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Busca lexical usando TF-IDF"""
        try:
            # Obter todos os documentos
            all_docs = base_conhecimento.documentos
            if not all_docs:
                return []
            
            # Preparar corpus
            corpus = [doc['texto'] for doc in all_docs]
            corpus.append(query)  # Adicionar query ao corpus
            
            # Calcular TF-IDF
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(corpus)
            
            # Calcular similaridade com a query (último item)
            query_vector = tfidf_matrix[-1]
            doc_vectors = tfidf_matrix[:-1]
            
            similarities = cosine_similarity(query_vector, doc_vectors).flatten()
            
            # Ordenar por similaridade
            top_indices = similarities.argsort()[-k:][::-1]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.1:  # Threshold mínimo
                    doc = all_docs[idx].copy()
                    doc['search_type'] = 'lexical'
                    doc['lexical_score'] = float(similarities[idx])
                    results.append(doc)
            
            return results
            
        except Exception as e:
            print(f"Erro na busca lexical: {e}")
            return []
    
    def _graph_search(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Busca usando grafo de conhecimento"""
        return self.knowledge_graph.search(query, k)
    
    def _combine_results(self, semantic: List, lexical: List, graph: List, 
                        weights: Dict[str, float], k: int) -> List[Dict[str, Any]]:
        """Combina resultados de diferentes estratégias"""
        
        # Criar dicionário para combinar scores por documento
        doc_scores = defaultdict(lambda: {'doc': None, 'scores': {}, 'total_score': 0.0})
        
        # Processar resultados semânticos
        for i, doc in enumerate(semantic):
            doc_id = doc.get('id', f"semantic_{i}")
            doc_scores[doc_id]['doc'] = doc
            doc_scores[doc_id]['scores']['semantic'] = doc.get('semantic_score', 0.0)
        
        # Processar resultados lexicais
        for i, doc in enumerate(lexical):
            doc_id = doc.get('id', f"lexical_{i}")
            if doc_scores[doc_id]['doc'] is None:
                doc_scores[doc_id]['doc'] = doc
            doc_scores[doc_id]['scores']['lexical'] = doc.get('lexical_score', 0.0)
        
        # Processar resultados do grafo
        for i, doc in enumerate(graph):
            doc_id = doc.get('id', f"graph_{i}")
            if doc_scores[doc_id]['doc'] is None:
                doc_scores[doc_id]['doc'] = doc
            doc_scores[doc_id]['scores']['graph'] = doc.get('graph_score', 0.0)
        
        # Calcular score total ponderado
        combined_results = []
        for doc_id, data in doc_scores.items():
            total_score = 0.0
            for search_type, weight in weights.items():
                score = data['scores'].get(search_type, 0.0)
                total_score += score * weight
            
            data['total_score'] = total_score
            doc = data['doc'].copy()
            doc['hybrid_score'] = total_score
            doc['component_scores'] = data['scores']
            combined_results.append(doc)
        
        # Ordenar por score total
        combined_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
        
        return combined_results[:k * 2]  # Retornar mais para re-ranking
    
    def _final_rerank(self, results: List[Dict[str, Any]], original_query: str) -> List[Dict[str, Any]]:
        """Re-ranking final baseado em múltiplos fatores"""
        
        for doc in results:
            # Fatores de re-ranking
            factors = {
                'hybrid_score': doc.get('hybrid_score', 0.0),
                'freshness': self._calculate_freshness_score(doc),
                'quality': doc.get('qualidade_score', 0.5),
                'query_match': self._calculate_query_match_score(doc, original_query),
                'popularity': self._calculate_popularity_score(doc)
            }
            
            # Pesos para cada fator
            weights = {
                'hybrid_score': 0.4,
                'freshness': 0.15,
                'quality': 0.2,
                'query_match': 0.15,
                'popularity': 0.1
            }
            
            # Score final
            final_score = sum(factors[factor] * weights[factor] for factor in factors)
            doc['final_score'] = final_score
            doc['ranking_factors'] = factors
        
        # Ordenar por score final
        results.sort(key=lambda x: x['final_score'], reverse=True)
        
        return results
    
    def _calculate_freshness_score(self, doc: Dict[str, Any]) -> float:
        """Calcula score de frescor do documento"""
        # Implementação simplificada - em produção usaria timestamps reais
        metadata = doc.get('metadata', {})
        if 'created_at' in metadata:
            # Lógica de frescor baseada na data
            return 0.8  # Placeholder
        return 0.5
    
    def _calculate_query_match_score(self, doc: Dict[str, Any], query: str) -> float:
        """Calcula score de match direto com a query"""
        texto = doc.get('texto', '').lower()
        query_lower = query.lower()
        
        # Contar palavras da query que aparecem no texto
        query_words = set(query_lower.split())
        texto_words = set(texto.split())
        
        if not query_words:
            return 0.0
        
        matches = len(query_words.intersection(texto_words))
        return matches / len(query_words)
    
    def _calculate_popularity_score(self, doc: Dict[str, Any]) -> float:
        """Calcula score de popularidade baseado no uso"""
        # Contar quantas vezes este documento foi usado em respostas
        doc_id = doc.get('id', '')
        if doc_id:
            # Implementação simplificada
            return 0.6  # Placeholder
        return 0.5

class KnowledgeGraph:
    """Grafo de conhecimento para busca por relacionamentos"""
    
    def __init__(self):
        self.entities = defaultdict(set)
        self.relationships = defaultdict(list)
        self._build_graph()
    
    def _build_graph(self):
        """Constrói grafo de conhecimento a partir dos documentos"""
        try:
            # Obter todas as perguntas e respostas para construir relacionamentos
            perguntas = Pergunta.objects.all()[:100]  # Limitar para performance
            
            for pergunta in perguntas:
                # Extrair entidades da pergunta e resposta
                entities_pergunta = self._extract_entities(pergunta.pergunta)
                entities_resposta = self._extract_entities(pergunta.resposta or "")
                
                # Criar relacionamentos entre entidades
                for ent1 in entities_pergunta:
                    for ent2 in entities_resposta:
                        if ent1 != ent2:
                            self.relationships[ent1.lower()].append(ent2.lower())
                            self.relationships[ent2.lower()].append(ent1.lower())
        
        except Exception as e:
            print(f"Erro ao construir grafo: {e}")
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extrai entidades do texto"""
        if not text:
            return []
        
        # Regex para encontrar entidades (palavras capitalizadas, termos técnicos)
        entities = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\b', text)
        entities.extend(re.findall(r'\b[A-Z]{2,}\b', text))  # Siglas
        
        return list(set(entities))
    
    def search(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Busca usando relacionamentos do grafo"""
        query_entities = self._extract_entities(query)
        
        if not query_entities:
            return []
        
        # Encontrar entidades relacionadas
        related_entities = set()
        for entity in query_entities:
            related_entities.update(self.relationships.get(entity.lower(), []))
        
        # Buscar documentos que contenham entidades relacionadas
        results = []
        all_docs = base_conhecimento.documentos
        
        for doc in all_docs:
            texto = doc.get('texto', '').lower()
            score = 0.0
            
            # Score baseado em entidades relacionadas encontradas
            for entity in related_entities:
                if entity in texto:
                    score += 1.0
            
            if score > 0:
                doc_copy = doc.copy()
                doc_copy['search_type'] = 'graph'
                doc_copy['graph_score'] = score / len(related_entities) if related_entities else 0.0
                results.append(doc_copy)
        
        # Ordenar por score
        results.sort(key=lambda x: x['graph_score'], reverse=True)
        
        return results[:k]

class QueryExpander:
    """Expansor de queries para melhorar a busca"""
    
    def __init__(self):
        self.synonyms = {
            'erro': ['bug', 'falha', 'problema', 'issue'],
            'função': ['método', 'procedimento', 'rotina'],
            'código': ['script', 'programa', 'implementação'],
            'dados': ['informação', 'data', 'informações'],
            'sistema': ['aplicação', 'software', 'plataforma']
        }
    
    def expand(self, query: str) -> str:
        """Expande a query com sinônimos e termos relacionados"""
        words = query.lower().split()
        expanded_words = words.copy()
        
        for word in words:
            if word in self.synonyms:
                expanded_words.extend(self.synonyms[word])
        
        return ' '.join(expanded_words)

# Instância global do motor de busca
hybrid_search_engine = HybridSearchEngine()
