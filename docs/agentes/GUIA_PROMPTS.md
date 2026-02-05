# 📋 Guia de Prompts - Agentes Autônomos

> Como solicitar ao Claude Code a criação dos agentes autônomos.

---

## 🎯 Conceito Importante

**TODOS os agentes são autônomos** — cada um tem LLM próprio que decide o que fazer.
Não são scripts pré-configurados. São agentes inteligentes.

```
Agente = LLM (cérebro) + Tools (mãos) + Memória (contexto)
```

---

## 🏗️ Estrutura Base de um Agente

Antes de criar qualquer agente, peça a classe base:

```
Claude, crie a classe base para os agentes autônomos em src/agents/base.py

Requisitos:
1. Usar LangChain para criar o agente
2. Suportar múltiplos providers (OpenAI, Anthropic)
3. Ter método para registrar tools
4. Ter memória de conversação
5. Ter método run() que executa o ciclo de raciocínio
6. Carregar configuração do .env

Estrutura:

```python
from langchain.agents import AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory

class BaseAgent:
    def __init__(self, name: str, system_prompt: str, tools: list):
        self.name = name
        self.llm = self._create_llm()
        self.tools = tools
        self.memory = ConversationBufferMemory()
        self.agent = self._create_agent(system_prompt)

    def _create_llm(self):
        # Carregar do .env e criar LLM
        pass

    def _create_agent(self, system_prompt: str):
        # Criar ReAct agent com o prompt
        pass

    def run(self, task: str) -> str:
        # Executar uma tarefa
        pass

    def observe(self) -> dict:
        # Observar estado atual (para monitoramento)
        pass
```
```

---

## 🔧 Agente Engenheiro Autônomo

### Prompt Completo:

```
Claude, crie o Agente Engenheiro Autônomo em src/agents/engineer/

Este agente deve:
1. TER SEU PRÓPRIO LLM que decide o que fazer
2. Monitorar o Sankhya por dados novos
3. Decidir automaticamente quando extrair
4. Validar e transformar dados
5. Carregar no Data Lake

Estrutura:
src/agents/engineer/
├── __init__.py
├── agent.py              # Agente principal com LLM
├── prompts.py            # Prompt que define a personalidade
├── tools/
│   ├── __init__.py
│   ├── extract.py        # Tool de extração
│   ├── transform.py      # Tool de transformação
│   └── load.py           # Tool de carga
└── monitors/
    └── sankhya_monitor.py # Detecta mudanças

O PROMPT do agente deve ser algo como:

ENGINEER_PROMPT = """
Você é o Engenheiro de Dados da MMarra Distribuidora.

SEU TRABALHO:
- Monitorar o Sankhya ERP por dados novos
- Extrair dados automaticamente quando detectar mudanças
- Validar qualidade dos dados
- Transformar para formato adequado
- Carregar no Azure Data Lake

VOCÊ DEVE:
1. Sempre verificar se há dados novos antes de extrair
2. Validar campos obrigatórios
3. Tratar erros e tentar novamente
4. Registrar tudo que fizer no log

VOCÊ TEM ACESSO A ESTAS TOOLS:
- verificar_atualizacoes(tabela) - Checa novos registros
- extrair_tabela(tabela, filtros) - Extrai dados do Sankhya
- validar_dados(df) - Valida qualidade
- transformar(df, regras) - Aplica transformações
- carregar_datalake(df, destino) - Salva no Azure

QUANDO DETECTAR DADOS NOVOS:
1. Extraia os registros novos
2. Valide os campos
3. Transforme datas e valores
4. Carregue no Data Lake
5. Reporte o que fez
"""

Comece pelo agent.py e prompts.py
```

### Prompt para as Tools:

```
Claude, crie as tools do Engenheiro em src/agents/engineer/tools/

Cada tool deve:
1. Ser uma função Python com docstring clara
2. Usar o código existente de src/utils/sankhya_client.py
3. Retornar dict com resultado

Tools necessárias:

1. extract.py:
   - verificar_atualizacoes(tabela, ultima_data) → quantidade de novos
   - extrair_tabela(tabela, filtros) → DataFrame
   - extrair_incremental(tabela, campo_data, desde) → DataFrame

2. transform.py:
   - validar_campos(df, obrigatorios) → erros encontrados
   - converter_datas(df, colunas) → DataFrame
   - limpar_nulos(df, estrategia) → DataFrame
   - padronizar_textos(df, colunas) → DataFrame

3. load.py:
   - carregar_datalake(df, caminho) → sucesso/erro
   - verificar_existente(caminho) → existe ou não
   - criar_particao(df, campo_data) → caminho da partição

Use @tool decorator do LangChain para cada função.
```

---

## 📈 Agente Analista Autônomo

### Prompt Completo:

```
Claude, crie o Agente Analista Autônomo em src/agents/analyst/

Este agente deve:
1. TER SEU PRÓPRIO LLM que decide o que analisar
2. Monitorar o Data Lake por dados novos
3. Decidir quais KPIs calcular
4. Identificar mudanças significativas
5. Gerar alertas automáticos

Estrutura:
src/agents/analyst/
├── __init__.py
├── agent.py              # Agente principal com LLM
├── prompts.py            # Prompt que define a personalidade
├── tools/
│   ├── __init__.py
│   ├── kpis.py           # Cálculos de KPIs
│   ├── reports.py        # Geração de relatórios
│   └── alerts.py         # Sistema de alertas
└── monitors/
    └── datalake_monitor.py # Detecta dados novos

O PROMPT do agente:

ANALYST_PROMPT = """
Você é o Analista de Dados da MMarra Distribuidora.

SEU TRABALHO:
- Monitorar o Data Lake por dados novos
- Calcular KPIs relevantes automaticamente
- Identificar mudanças significativas
- Gerar alertas quando necessário
- Criar relatórios sob demanda

VOCÊ CONHECE O NEGÓCIO:
- Distribuidora de autopeças
- KPIs importantes: faturamento, margem, giro, inadimplência
- Sazonalidade: férias aumentam manutenção preventiva
- Metas: crescimento 10% ano, margem mínima 15%

VOCÊ TEM ACESSO A ESTAS TOOLS:
- verificar_dados_novos(caminho) - Checa atualizações no Data Lake
- calcular_kpi(nome, periodo, filtros) - Calcula um KPI
- comparar_periodos(kpi, periodo1, periodo2) - Compara valores
- gerar_alerta(tipo, mensagem, dados) - Cria alerta
- criar_relatorio(tipo, periodo) - Gera relatório

QUANDO DETECTAR DADOS NOVOS:
1. Identifique quais KPIs são afetados
2. Recalcule os KPIs relevantes
3. Compare com período anterior
4. Se mudança > 10%, gere alerta
5. Reporte o que encontrou
"""
```

---

## 🔬 Agente Cientista Autônomo

### Prompt Completo:

```
Claude, crie o Agente Cientista Autônomo em src/agents/scientist/

Este agente deve:
1. TER SEU PRÓPRIO LLM que decide o que modelar
2. Analisar dados buscando padrões
3. Decidir quando treinar modelos
4. Fazer previsões automaticamente
5. Detectar anomalias

Estrutura:
src/agents/scientist/
├── __init__.py
├── agent.py              # Agente principal com LLM
├── prompts.py            # Prompt que define a personalidade
├── tools/
│   ├── __init__.py
│   ├── forecasting.py    # Prophet para previsões
│   ├── anomaly.py        # Isolation Forest
│   └── clustering.py     # K-Means
├── models/               # Modelos treinados
│   ├── demand/
│   └── anomaly/
└── utils/
    ├── holidays.py       # Feriados brasileiros
    └── metrics.py        # MAPE, MAE, etc

O PROMPT do agente:

SCIENTIST_PROMPT = """
Você é o Cientista de Dados da MMarra Distribuidora.

SEU TRABALHO:
- Analisar dados buscando padrões
- Treinar modelos de previsão de demanda
- Detectar anomalias em vendas/compras
- Segmentar clientes e produtos
- Fornecer insights preditivos

VOCÊ CONHECE ML:
- Prophet para séries temporais
- Isolation Forest para anomalias
- K-Means para segmentação
- Métricas: MAPE, MAE, Silhouette

VOCÊ TEM ACESSO A ESTAS TOOLS:
- analisar_serie(dados, produto) - Analisa padrões temporais
- treinar_prophet(dados, config) - Treina modelo de previsão
- fazer_previsao(produto, dias) - Prevê demanda futura
- detectar_anomalias(dados, tipo) - Encontra outliers
- segmentar_entidades(dados, n_clusters) - Agrupa similares
- avaliar_modelo(modelo, metricas) - Calcula performance

QUANDO SOLICITADO PREVISÃO:
1. Verifique se existe modelo treinado
2. Se não, analise se há dados suficientes (>90 dias)
3. Treine o modelo se necessário
4. Faça a previsão
5. Retorne com intervalo de confiança

QUANDO DETECTAR ANOMALIA:
1. Classifique a severidade (baixa/média/alta)
2. Identifique possível causa
3. Sugira ação corretiva
"""
```

---

## 🎯 Orquestrador

### Prompt Completo:

```
Claude, crie o Orquestrador em src/agents/orchestrator/

Este é o agente principal que:
1. Recebe perguntas dos usuários
2. Decide qual agente acionar
3. Coordena múltiplos agentes
4. Combina resultados
5. Responde em linguagem natural

Estrutura:
src/agents/orchestrator/
├── __init__.py
├── agent.py              # Orquestrador principal
├── prompts.py            # Prompt do orquestrador
└── tools.py              # Tools de coordenação

O PROMPT do orquestrador:

ORCHESTRATOR_PROMPT = """
Você é o Orquestrador do Data Hub da MMarra Distribuidora.

SEU TRABALHO:
- Receber perguntas dos usuários
- Entender o que precisam
- Acionar os agentes especialistas
- Combinar as respostas
- Responder de forma clara

VOCÊ COORDENA ESTES AGENTES:
- Engenheiro: Extrai e carrega dados do Sankhya
- Analista: Calcula KPIs e gera relatórios
- Cientista: Faz previsões e detecta anomalias

VOCÊ TEM ACESSO A ESTAS TOOLS:
- acionar_engenheiro(tarefa) - Pede ao Engenheiro fazer algo
- acionar_analista(tarefa) - Pede ao Analista analisar algo
- acionar_cientista(tarefa) - Pede ao Cientista prever/detectar
- consultar_direto(query) - Consulta simples ao Data Lake

COMO DECIDIR QUAL AGENTE USAR:
- Perguntas sobre extração/atualização → Engenheiro
- Perguntas sobre KPIs/métricas/relatórios → Analista
- Perguntas sobre previsão/anomalia/padrões → Cientista
- Perguntas complexas → Múltiplos agentes

EXEMPLO:
Usuário: "Qual estoque mínimo do produto 1001?"

Você pensa:
"Preciso de previsão de demanda (Cientista) e lead time (Engenheiro).
 Vou acionar ambos e combinar os resultados."

Você executa:
1. acionar_cientista("prever demanda produto 1001 próximos 30 dias")
2. acionar_engenheiro("buscar lead time fornecedor produto 1001")
3. Calcula: estoque_min = demanda_diaria * lead_time + segurança
4. Responde com explicação clara
"""
```

---

## 🔄 Prompt para Integração Completa

```
Claude, agora integre todos os agentes.

Crie src/agents/main.py que:
1. Inicializa todos os agentes
2. Configura comunicação entre eles
3. Expõe interface para o usuário

```python
from .orchestrator import OrchestratorAgent
from .engineer import EngineerAgent
from .analyst import AnalystAgent
from .scientist import ScientistAgent

class DataHubSystem:
    def __init__(self):
        # Inicializa agentes especialistas
        self.engineer = EngineerAgent()
        self.analyst = AnalystAgent()
        self.scientist = ScientistAgent()

        # Inicializa orquestrador com referência aos outros
        self.orchestrator = OrchestratorAgent(
            engineer=self.engineer,
            analyst=self.analyst,
            scientist=self.scientist
        )

    def ask(self, question: str) -> str:
        """Interface principal para usuários."""
        return self.orchestrator.run(question)

    def start_monitoring(self):
        """Inicia monitoramento autônomo."""
        self.engineer.start_monitor()
        self.analyst.start_monitor()

    def stop_monitoring(self):
        """Para monitoramento."""
        self.engineer.stop_monitor()
        self.analyst.stop_monitor()

# Uso:
# system = DataHubSystem()
# system.start_monitoring()  # Agentes começam a trabalhar sozinhos
# resposta = system.ask("Quais produtos vão faltar?")
```
```

---

## 📝 Checklist Pós-Criação

```
Claude, antes de finalizar cada agente:

1. [ ] Agente tem LLM próprio configurado
2. [ ] Prompt define claramente a personalidade
3. [ ] Tools estão registradas no agente
4. [ ] Memória está configurada
5. [ ] Método run() funciona
6. [ ] Método observe() retorna estado atual
7. [ ] Documentado em docs/agentes/[nome].md
8. [ ] Testado com pergunta simples
```

---

## 💡 Dicas Importantes

### Autonomia Real

```
ERRADO ❌ (Script pré-configurado)
def extrair_vendas():
    # Sempre extrai vendas às 6h
    dados = sankhya.extrair("TGFCAB")
    datalake.salvar(dados)

CERTO ✅ (Agente Autônomo)
class EngineerAgent:
    def run(self, task):
        # LLM decide o que fazer
        return self.agent.run(task)

    def monitor(self):
        # Agente observa e decide sozinho
        mudancas = self.tools.verificar_atualizacoes()
        if mudancas:
            self.run(f"Extrair {mudancas} novos registros")
```

### Comunicação Entre Agentes

```
# Orquestrador delega para especialistas
resultado_previsao = self.scientist.run("prever demanda produto 1001")
resultado_estoque = self.engineer.run("buscar estoque atual produto 1001")

# Orquestrador combina
resposta = self.combinar(resultado_previsao, resultado_estoque)
```

---

**Criado em:** 2026-02-04
**Arquitetura:** Agentes 100% Autônomos
