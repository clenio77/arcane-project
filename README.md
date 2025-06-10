# 🔮 Arcane Project

Sistema de IA conversacional com treinamento personalizado usando RAG (Retrieval-Augmented Generation).

## 🚀 Funcionalidades

### 🧠 IA Avançada
- **Análise Semântica**: Detecção automática de intenções e entidades
- **Chat Inteligente**: Conversas contextualizadas com memória
- **Prompts Otimizados**: Templates adaptativos baseados no tipo de pergunta
- **Avaliação de Qualidade**: Scoring automático de respostas
- **Sugestões Inteligentes**: Perguntas relacionadas geradas automaticamente

### 📚 Gestão de Conhecimento
- **Treinamento Multi-Modal**: Upload de documentos (PDF, TXT) e conteúdo web
- **Chunking Inteligente**: Divisão otimizada de documentos
- **Cache de Embeddings**: Performance otimizada com cache inteligente
- **Busca Semântica Avançada**: FAISS com re-ranking e filtros

### 📊 Analytics & Monitoramento
- **Dashboard Completo**: Métricas de qualidade e performance
- **Feedback dos Usuários**: Sistema de avaliação de respostas
- **Analytics de Queries**: Monitoramento de uso e performance
- **Insights Automáticos**: Recomendações baseadas em dados

### 🎯 Experiência do Usuário
- **Sessões de Conversa**: Histórico e contexto persistente
- **Interface Moderna**: Design responsivo com TailwindCSS
- **Streaming de Respostas**: Respostas em tempo real
- **Sistema de Permissões**: Controle de acesso por roles
- **Exportação de Dados**: Download de conversas e métricas

## 🛠️ Tecnologias

- **Backend**: Django 5.2.1
- **IA**: OpenAI GPT + Embeddings
- **Busca**: FAISS (Facebook AI Similarity Search)
- **Frontend**: HTML + TailwindCSS + JavaScript
- **Banco**: SQLite (desenvolvimento)

## 📋 Pré-requisitos

- Python 3.8+
- Chave da API OpenAI

## ⚡ Instalação Rápida

1. **Clone o repositório**
```bash
git clone <repository-url>
cd arcane-project
```

2. **Instale as dependências**
```bash
pip install -r requirements.txt
```

3. **Configure as variáveis de ambiente**
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

4. **Configure o projeto**
```bash
python setup.py
```

5. **Inicie o servidor**
```bash
python manage.py runserver
```

## 🔧 Configuração

### Variáveis de Ambiente (.env)

```env
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
OPENAI_API_KEY=sua-chave-openai-aqui
OPENAI_MODEL=gpt-3.5-turbo
```

### Credenciais Padrão

- **Admin**: `admin` / `admin123`
- **Gerente**: `gerente` / `gerente123`

## 📖 Como Usar

### 1. Treinamento da IA

1. Faça login como gerente ou admin
2. Acesse "Treinamento da IA"
3. Adicione conteúdo via:
   - **Site**: URL de página web
   - **Conteúdo**: Texto manual
   - **Documento**: Upload de PDF/TXT

### 2. Chat Inteligente

1. Acesse "🧠 Chat Inteligente"
2. Digite sua pergunta (análise automática de intenção)
3. Receba resposta contextualizada em tempo real
4. Avalie a qualidade da resposta (1-5 estrelas)
5. Use sugestões inteligentes para perguntas relacionadas
6. Visualize fontes e analytics

### 3. Analytics e Monitoramento

1. Acesse "📊 Analytics"
2. Monitore métricas de qualidade
3. Visualize distribuição de categorias
4. Acompanhe insights automáticos
5. Exporte dados para análise

## 🏗️ Arquitetura

```
arcane-project/
├── core/                 # Configurações Django
├── usuarios/             # Autenticação e usuários
├── oraculo/             # IA e chat
│   ├── models.py        # Modelos de dados
│   ├── views.py         # Views da API
│   ├── utils.py         # Utilitários de IA
│   └── signals.py       # Processamento automático
├── templates/           # Templates HTML
└── requirements.txt     # Dependências
```

## 🔄 Fluxo de Dados

1. **Upload** → Processamento automático via signals
2. **Chunking** → Divisão em pedaços menores
3. **Embedding** → Vetorização com OpenAI
4. **Indexação** → Armazenamento no FAISS
5. **Consulta** → Busca semântica + GPT

## 🛡️ Segurança

- Validação de tipos de arquivo
- Limite de tamanho de upload (10MB)
- Sanitização de conteúdo
- Controle de permissões por role
- Configuração segura para produção

## 🚀 Deploy

Para produção, configure:

```env
DEBUG=False
ALLOWED_HOSTS=seu-dominio.com
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
```

## 📝 Licença

Este projeto está sob a licença MIT.

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📞 Suporte

Para dúvidas ou problemas, abra uma issue no repositório.
