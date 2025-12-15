# Simulador SMA - Sistema Multi-Agente

Simulador flexível em Python para modelar e executar cenários típicos de sistemas multi-agente (SMA). Implementa três problemas clássicos: Farol, Foraging (Recoleção) e Labirinto.

## Características

- **Arquitetura Modular**: Simulador flexível com interfaces bem definidas
- **Três Ambientes**: Farol, Foraging e Labirinto
- **Múltiplos Tipos de Agentes**: Reativos, Q-Learning e Evolucionários
- **Visualização Pygame**: Visualização em tempo real dos ambientes 2D
- **Modos de Operação**: Aprendizagem e Teste para agentes com capacidade de aprendizado
- **Métricas**: Registro de desempenho (recompensas, passos, taxa de sucesso)

## Estrutura do Projeto

```
AA-Projeto/
├── ambiente.py              # Classes base de ambiente
├── AmbienteFarol.py        # Ambiente do problema do Farol
├── AmbienteForaging.py     # Ambiente de Recoleção
├── AmbienteLabirinto.py    # Ambiente de Labirinto
├── FabricaAmbientes.py     # Fábrica para criar ambientes
├── agente.py               # Classes base de agentes
├── agenteqlearning.py      # Agente com Q-Learning
├── agentegenetico.py        # Agente evolucionário
├── MotorDeSimulacao.py     # Motor principal de simulação
├── visualizacao.py         # Visualização com Pygame
├── main.py                 # Script principal
├── config_simulacao.json   # Configuração exemplo (Farol)
├── config_foraging.json    # Configuração exemplo (Foraging)
└── config_labirinto.json   # Configuração exemplo (Labirinto)
```

## Requisitos

```bash
pip install pygame numpy
```

## Uso

### Execução Básica

```bash
python main.py config_simulacao.json
```

### Com Visualização

```bash
python main.py config_simulacao.json --visualizacao
```

### Sem Visualização

```bash
python main.py config_simulacao.json --sem-visualizacao
```

## Configuração

Os ficheiros JSON de configuração permitem definir:

- **Ambiente**: Tipo (FAROL, FORAGING, LABIRINTO) e parâmetros
- **Agentes**: Tipo (reativo, qlearning, genetico), posição inicial e parâmetros
- **Simulação**: Número de passos, episódios, delay, visualização

### Exemplo de Configuração (Farol)

```json
{
  "passos_totais": 100,
  "delay_entre_passos": 0.1,
  "num_episodios": 50,
  "usar_visualizacao": false,
  
  "ambiente": {
    "tipo": "FAROL",
    "parametros": {
      "largura": 10,
      "altura": 10,
      "com_obstaculos": false
    }
  },
  
  "agentes": [
    {
      "id": "agente1",
      "tipo": "reativo",
      "posicao_inicial": {"x": 1, "y": 1},
      "parametros": {}
    },
    {
      "id": "agente2",
      "tipo": "qlearning",
      "posicao_inicial": {"x": 8, "y": 8},
      "parametros": {
        "alpha": 0.1,
        "gamma": 0.95,
        "epsilon": 1.0,
        "epsilon_decay": 0.995,
        "epsilon_min": 0.01,
        "modo_aprendizagem": true
      }
    }
  ]
}
```

## Ambientes

### 1. Farol
- **Objetivo**: Agentes devem chegar ao farol
- **Observações**: Direção e distância ao farol, obstáculos vizinhos
- **Ações**: Mover (Norte, Sul, Este, Oeste)
- **Recompensas**: Positivas por aproximação, negativas por afastamento, grande recompensa ao chegar

### 2. Foraging (Recoleção)
- **Objetivo**: Recolher recursos e depositá-los no ninho
- **Observações**: Recursos próximos, ninhos próximos, recursos carregados
- **Ações**: Mover, Recolher, Depositar
- **Recompensas**: Por recolher recursos, maior por depositar no ninho

### 3. Labirinto
- **Objetivo**: Encontrar caminho do início ao fim
- **Observações**: Direção ao fim, paredes vizinhas
- **Ações**: Mover (Norte, Sul, Este, Oeste)
- **Recompensas**: Por aproximação ao fim, grande recompensa ao chegar

## Tipos de Agentes

### Agente Reativo
- Política fixa pré-programada
- Comportamento determinístico baseado em observações

### Agente Q-Learning
- Aprendizagem por reforço
- Modos: Aprendizagem (treino) e Teste (avaliação)
- Parâmetros: alpha (taxa de aprendizado), gamma (desconto), epsilon (exploração)

### Agente Evolucionário
- Algoritmo genético com Novelty Search
- Evolução de genótipos (sequências de ações)
- Fitness combinado: novidade + objetivo

## Visualização

A visualização Pygame mostra:
- **Ambiente**: Grid 2D com células
- **Agentes**: Círculos coloridos com IDs
- **Objetivos**: Farol (amarelo), Ninhos (marrom), Início/Fim (verde/vermelho)
- **Recursos**: Círculos verdes com valores
- **Obstáculos/Paredes**: Quadrados cinza
- **Informações**: Passo atual, status, estatísticas dos agentes

**Controles**:
- **Espaço**: Pausar/Retomar
- **Q**: Sair

## Métricas

O simulador registra:
- Recompensa total por episódio
- Número de ações até terminar
- Taxa de sucesso
- Recompensa média e descontada
- Estatísticas por agente (exploração, recursos coletados, etc.)

## Interface do Simulador

```python
# Criar simulação
motor = MotorDeSimulacao.cria("config_simulacao.json")

# Listar agentes
agentes = motor.listaAgentes()

# Executar
motor.executa()

# Obter métricas
metricas = motor.obter_metricas()
```

## Interface do Ambiente

```python
# Observação para agente
obs = ambiente.observacao_para(agente_id)

# Executar ação
recompensa = ambiente.agir(acao, agente_id)

# Atualizar ambiente
ambiente.atualizacao()
```

## Interface do Agente

```python
# Receber observação
agente.observacao(obs, recompensa)

# Decidir ação
acao = agente.age()

# Instalar no ambiente
agente.instala(ambiente, posicao)
```

## Desenvolvimento

O projeto segue uma arquitetura modular:
- **Ambiente**: Abstração para diferentes tipos de ambientes
- **Agente**: Interface comum para todos os agentes
- **Motor**: Gerencia ciclo de simulação e coordenação
- **Visualização**: Módulo independente para exibição

## Licença

Este projeto foi desenvolvido como trabalho prático de Sistemas Multi-Agente.

