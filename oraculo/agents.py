"""
Sistema de Agentes Inteligentes Especializados
Cada agente tem expertise específica e pode colaborar
"""

import json
import openai
from typing import List, Dict, Any, Optional
from django.conf import settings
from .ai_advanced import analisador_semantico
from .utils import base_conhecimento

class BaseAgent:
    """Classe base para todos os agentes"""
    
    def __init__(self, name: str, expertise: str, personality: str):
        self.name = name
        self.expertise = expertise
        self.personality = personality
        self.conversation_history = []
    
    def can_handle(self, query: str, context: Dict) -> float:
        """Retorna score 0-1 de capacidade de lidar com a query"""
        raise NotImplementedError
    
    def process_query(self, query: str, context: Dict) -> Dict[str, Any]:
        """Processa a query e retorna resposta estruturada"""
        raise NotImplementedError

class TechnicalAgent(BaseAgent):
    """Agente especializado em questões técnicas"""
    
    def __init__(self):
        super().__init__(
            name="TechExpert",
            expertise="Programação, APIs, arquitetura de software, debugging",
            personality="Preciso, detalhista, focado em soluções práticas"
        )
    
    def can_handle(self, query: str, context: Dict) -> float:
        technical_keywords = [
            'código', 'programação', 'api', 'função', 'erro', 'bug',
            'implementar', 'algoritmo', 'database', 'sql', 'python',
            'javascript', 'framework', 'biblioteca', 'debug'
        ]
        
        query_lower = query.lower()
        matches = sum(1 for keyword in technical_keywords if keyword in query_lower)
        return min(matches / 3, 1.0)  # Normalizar para 0-1
    
    def process_query(self, query: str, context: Dict) -> Dict[str, Any]:
        system_prompt = f"""Você é {self.name}, um especialista técnico em {self.expertise}.
        Sua personalidade: {self.personality}
        
        Responda de forma:
        1. Técnica e precisa
        2. Com exemplos de código quando relevante
        3. Incluindo melhores práticas
        4. Mencionando possíveis problemas e soluções
        """
        
        return self._generate_response(query, context, system_prompt)
    
    def _generate_response(self, query: str, context: Dict, system_prompt: str) -> Dict[str, Any]:
        try:
            response = openai.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Contexto: {context.get('contexto', '')}\n\nPergunta: {query}"}
                ],
                temperature=0.3,  # Mais determinístico para questões técnicas
                max_tokens=1500
            )
            
            return {
                'agent': self.name,
                'response': response.choices[0].message.content,
                'confidence': 0.9,
                'reasoning': f"Questão técnica identificada, usando expertise em {self.expertise}"
            }
        except Exception as e:
            return {
                'agent': self.name,
                'response': f"Erro ao processar: {str(e)}",
                'confidence': 0.0,
                'reasoning': "Erro na geração de resposta"
            }

class ConceptualAgent(BaseAgent):
    """Agente especializado em explicações conceituais"""
    
    def __init__(self):
        super().__init__(
            name="ConceptMaster",
            expertise="Explicações conceituais, teorias, fundamentos",
            personality="Didático, claro, usa analogias e exemplos"
        )
    
    def can_handle(self, query: str, context: Dict) -> float:
        conceptual_keywords = [
            'o que é', 'conceito', 'definição', 'teoria', 'princípio',
            'fundamento', 'base', 'explicar', 'entender', 'significado'
        ]
        
        query_lower = query.lower()
        matches = sum(1 for keyword in conceptual_keywords if keyword in query_lower)
        return min(matches / 2, 1.0)
    
    def process_query(self, query: str, context: Dict) -> Dict[str, Any]:
        system_prompt = f"""Você é {self.name}, especialista em {self.expertise}.
        Sua personalidade: {self.personality}
        
        Responda de forma:
        1. Didática e clara
        2. Com analogias quando útil
        3. Estruturada (definição → características → exemplos)
        4. Acessível para diferentes níveis de conhecimento
        """
        
        return self._generate_response(query, context, system_prompt)
    
    def _generate_response(self, query: str, context: Dict, system_prompt: str) -> Dict[str, Any]:
        try:
            response = openai.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Contexto: {context.get('contexto', '')}\n\nPergunta: {query}"}
                ],
                temperature=0.7,  # Mais criativo para explicações
                max_tokens=1500
            )
            
            return {
                'agent': self.name,
                'response': response.choices[0].message.content,
                'confidence': 0.85,
                'reasoning': f"Questão conceitual identificada, usando abordagem didática"
            }
        except Exception as e:
            return {
                'agent': self.name,
                'response': f"Erro ao processar: {str(e)}",
                'confidence': 0.0,
                'reasoning': "Erro na geração de resposta"
            }

class ProblemSolverAgent(BaseAgent):
    """Agente especializado em resolução de problemas"""
    
    def __init__(self):
        super().__init__(
            name="ProblemSolver",
            expertise="Resolução de problemas, troubleshooting, soluções práticas",
            personality="Metódico, orientado a soluções, passo-a-passo"
        )
    
    def can_handle(self, query: str, context: Dict) -> float:
        problem_keywords = [
            'problema', 'erro', 'não funciona', 'como resolver', 'solução',
            'corrigir', 'consertar', 'troubleshoot', 'debug', 'falha'
        ]
        
        query_lower = query.lower()
        matches = sum(1 for keyword in problem_keywords if keyword in query_lower)
        return min(matches / 2, 1.0)
    
    def process_query(self, query: str, context: Dict) -> Dict[str, Any]:
        system_prompt = f"""Você é {self.name}, especialista em {self.expertise}.
        Sua personalidade: {self.personality}
        
        Responda de forma:
        1. Estruturada em passos claros
        2. Identificando possíveis causas
        3. Oferecendo múltiplas soluções quando possível
        4. Incluindo prevenção para o futuro
        """
        
        return self._generate_response(query, context, system_prompt)
    
    def _generate_response(self, query: str, context: Dict, system_prompt: str) -> Dict[str, Any]:
        try:
            response = openai.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Contexto: {context.get('contexto', '')}\n\nPergunta: {query}"}
                ],
                temperature=0.4,  # Balanceado para soluções criativas mas práticas
                max_tokens=1500
            )
            
            return {
                'agent': self.name,
                'response': response.choices[0].message.content,
                'confidence': 0.88,
                'reasoning': f"Problema identificado, usando abordagem metódica de resolução"
            }
        except Exception as e:
            return {
                'agent': self.name,
                'response': f"Erro ao processar: {str(e)}",
                'confidence': 0.0,
                'reasoning': "Erro na geração de resposta"
            }

class AgentOrchestrator:
    """Orquestrador que decide qual agente usar"""
    
    def __init__(self):
        self.agents = [
            TechnicalAgent(),
            ConceptualAgent(),
            ProblemSolverAgent()
        ]
    
    def select_best_agent(self, query: str, context: Dict) -> BaseAgent:
        """Seleciona o melhor agente para a query"""
        scores = []
        
        for agent in self.agents:
            score = agent.can_handle(query, context)
            scores.append((agent, score))
        
        # Ordenar por score e retornar o melhor
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Se nenhum agente tem score alto, usar o conceitual como padrão
        if scores[0][1] < 0.3:
            return ConceptualAgent()
        
        return scores[0][0]
    
    def process_with_collaboration(self, query: str, context: Dict) -> Dict[str, Any]:
        """Processa query com possível colaboração entre agentes"""
        
        # Selecionar agente principal
        primary_agent = self.select_best_agent(query, context)
        primary_response = primary_agent.process_query(query, context)
        
        # Se a confiança for baixa, tentar com agente secundário
        if primary_response['confidence'] < 0.7:
            # Encontrar segundo melhor agente
            scores = [(agent, agent.can_handle(query, context)) for agent in self.agents]
            scores.sort(key=lambda x: x[1], reverse=True)
            
            if len(scores) > 1 and scores[1][1] > 0.4:
                secondary_agent = scores[1][0]
                secondary_response = secondary_agent.process_query(query, context)
                
                # Combinar respostas
                combined_response = self._combine_responses(primary_response, secondary_response)
                return combined_response
        
        return primary_response
    
    def _combine_responses(self, primary: Dict, secondary: Dict) -> Dict[str, Any]:
        """Combina respostas de múltiplos agentes"""
        
        combined_prompt = f"""Combine as seguintes respostas de especialistas diferentes em uma resposta coesa:

Resposta do {primary['agent']}:
{primary['response']}

Resposta do {secondary['agent']}:
{secondary['response']}

Crie uma resposta única que aproveite o melhor de ambas, mantendo clareza e coerência."""
        
        try:
            response = openai.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Você é um especialista em combinar conhecimentos de diferentes áreas."},
                    {"role": "user", "content": combined_prompt}
                ],
                temperature=0.5,
                max_tokens=2000
            )
            
            return {
                'agent': f"{primary['agent']} + {secondary['agent']}",
                'response': response.choices[0].message.content,
                'confidence': (primary['confidence'] + secondary['confidence']) / 2,
                'reasoning': f"Colaboração entre {primary['agent']} e {secondary['agent']}"
            }
        except Exception as e:
            # Em caso de erro, retornar resposta primária
            return primary

# Instância global do orquestrador
agent_orchestrator = AgentOrchestrator()
