"""
Módulo de Agente - Define a interface e classes base para agentes autónomos
Incorpora conceitos de Novelty Search e Algoritmos Evolutivos

Para implementações específicas, veja:
- agenteqlearning.py: Agente Q-Learning
- agentegenetico.py: Agente Genético/Evolucionário
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Set, Tuple
from threading import Thread, Lock
import json
import random
import numpy as np
from ambiente import Observacao, Acao, Direcao


class Sensor(ABC):
    """Classe abstrata para sensores que podem ser instalados em agentes"""
    
    def __init__(self, nome: str):
        self.nome = nome
        self.ativo = True
    
    @abstractmethod
    def processar(self, observacao: Observacao) -> Dict[str, Any]:
        """Processa a observação e retorna dados processados"""
        pass
    
    def ativar(self):
        """Ativa o sensor"""
        self.ativo = True
    
    def desativar(self):
        """Desativa o sensor"""
        self.ativo = False


class SensorDistancia(Sensor):
    """Sensor que calcula distâncias"""
    
    def __init__(self):
        super().__init__("SensorDistancia")
    
    def processar(self, observacao: Observacao) -> Dict[str, Any]:
        """Processa informação de distância da observação"""
        if not self.ativo:
            return {}
        
        return {
            'distancia': observacao.dados.get('distancia_farol', 0),
            'processado_por': self.nome
        }


class SensorObstaculos(Sensor):
    """Sensor que deteta obstáculos"""
    
    def __init__(self):
        super().__init__("SensorObstaculos")
    
    def processar(self, observacao: Observacao) -> Dict[str, Any]:
        """Processa informação de obstáculos da observação"""
        if not self.ativo:
            return {}
        
        obstaculos = observacao.dados.get('obstaculos_vizinhos', {})
        return {
            'num_obstaculos': sum(1 for v in obstaculos.values() if v),
            'direcoes_bloqueadas': [k for k, v in obstaculos.items() if v],
            'processado_por': self.nome
        }


class Mensagem:
    """Representa uma mensagem entre agentes"""
    
    def __init__(self, conteudo: str, remetente_id: str, destinatario_id: str = None):
        self.conteudo = conteudo
        self.remetente_id = remetente_id
        self.destinatario_id = destinatario_id  # None = broadcast
        self.timestamp = 0
    
    def __str__(self):
        dest = self.destinatario_id or "TODOS"
        return f"Msg[De:{self.remetente_id} Para:{dest}]: {self.conteudo}"


class Agente(ABC, Thread):
    """
    Classe abstrata base para todos os agentes.
    Implementa a interface requerida e funciona como Thread.
    Suporta evolução genética e busca por novidade.
    """
    
    def __init__(self, agente_id: str, parametros: Dict[str, Any] = None, genotype: List[Any] = None):
        Thread.__init__(self)
        self.agente_id = agente_id
        self.parametros = parametros or {}
        
        # Genótipo (sequência de ações - para agentes evolucionários)
        self.genotype: Optional[List[Any]] = genotype
        self.num_steps = parametros.get('num_steps', 1000) if parametros else 1000
        
        # Estado interno do agente
        self.observacao_atual: Optional[Observacao] = None
        self.recompensa_acumulada: float = 0.0
        self.recompensa_ultimo_passo: float = 0.0
        
        # Sensores instalados
        self.sensores: List[Sensor] = []
        
        # Sistema de comunicação
        self.caixa_mensagens: List[Mensagem] = []
        self.lock_mensagens = Lock()
        
        # Controle de execução
        self.ativo = True
        self.pausado = False
        
        # Histórico para aprendizagem
        self.historico_observacoes: List[Observacao] = []
        self.historico_acoes: List[Acao] = []
        self.historico_recompensas: List[float] = []
        
        # --- Novelty Search: Behavior Characterization ---
        self.behavior: Set[Tuple[int, int]] = set()  # Conjunto de posições visitadas
        self.path: List[Tuple[int, int]] = []  # Caminho completo
        self.novelty_score: float = 0.0
        
        # --- Objective Fitness (goal-oriented) ---
        self.objective_fitness: float = 0.0
        self.combined_fitness: float = 0.0  # Novelty + Objective
    
    @classmethod
    def cria(cls, nome_do_ficheiro_parametros: str):
        """
        Cria um agente a partir de um ficheiro de parâmetros
        
        Args:
            nome_do_ficheiro_parametros: Caminho para ficheiro JSON com parâmetros
            
        Returns:
            Instância do agente configurado
        """
        try:
            with open(nome_do_ficheiro_parametros, 'r', encoding='utf-8') as f:
                parametros = json.load(f)
            
            agente_id = parametros.get('agente_id', 'agente_default')
            return cls(agente_id, parametros)
        
        except FileNotFoundError:
            raise FileNotFoundError(f"Ficheiro de parâmetros não encontrado: {nome_do_ficheiro_parametros}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Erro ao ler ficheiro JSON: {e}")
    
    def observacao(self, obs: Observacao):
        """
        Recebe e processa uma observação do ambiente
        
        Args:
            obs: Observação recebida do ambiente
        """
        self.observacao_atual = obs
        self.historico_observacoes.append(obs)
        
        # Registrar comportamento (posição atual para Novelty Search)
        if 'posicao_atual' in obs.dados:
            pos = obs.dados['posicao_atual']
            if isinstance(pos, tuple):
                self.behavior.add(pos)
                self.path.append(pos)
        
        # Processar com sensores instalados
        for sensor in self.sensores:
            if sensor.ativo:
                dados_processados = sensor.processar(obs)
                # Adicionar dados processados à observação
                obs.dados[f'sensor_{sensor.nome}'] = dados_processados
    
    @abstractmethod
    def age(self) -> Acao:
        """
        Decide e retorna a próxima ação a executar
        
        Returns:
            Ação escolhida pelo agente
        """
        pass
    
    def avaliacaoEstadoAtual(self, recompensa: float):
        """
        Avalia o estado atual com base na recompensa recebida
        
        Args:
            recompensa: Valor da recompensa recebida
        """
        self.recompensa_ultimo_passo = recompensa
        self.recompensa_acumulada += recompensa
        self.historico_recompensas.append(recompensa)
        
        # Hook para processamento adicional em subclasses
        self._processar_recompensa(recompensa)
    
    def _processar_recompensa(self, recompensa: float):
        """
        Hook para subclasses processarem recompensas (ex: atualizar Q-table)
        
        Args:
            recompensa: Valor da recompensa
        """
        pass
    
    def instala(self, sensor: Sensor):
        """
        Instala um novo sensor no agente
        
        Args:
            sensor: Sensor a ser instalado
        """
        if sensor not in self.sensores:
            self.sensores.append(sensor)
            print(f"[{self.agente_id}] Sensor '{sensor.nome}' instalado com sucesso")
        else:
            print(f"[{self.agente_id}] Sensor '{sensor.nome}' já estava instalado")
    
    def comunica(self, mensagem: str, de_agente: 'Agente'):
        """
        Recebe uma mensagem de outro agente
        
        Args:
            mensagem: Conteúdo da mensagem
            de_agente: Agente que enviou a mensagem
        """
        msg = Mensagem(mensagem, de_agente.agente_id, self.agente_id)
        
        with self.lock_mensagens:
            self.caixa_mensagens.append(msg)
        
        # Hook para processar mensagem
        self._processar_mensagem(msg)
    
    def _processar_mensagem(self, mensagem: Mensagem):
        """
        Hook para subclasses processarem mensagens recebidas
        
        Args:
            mensagem: Mensagem recebida
        """
        pass
    
    def enviar_mensagem(self, mensagem: str, destinatario: 'Agente' = None):
        """
        Envia uma mensagem para outro agente
        
        Args:
            mensagem: Conteúdo da mensagem
            destinatario: Agente destinatário (None = broadcast)
        """
        if destinatario:
            destinatario.comunica(mensagem, self)
        else:
            # Broadcast - implementar em contexto de simulador
            pass
    
    def ler_mensagens(self) -> List[Mensagem]:
        """
        Lê todas as mensagens na caixa de entrada
        
        Returns:
            Lista de mensagens
        """
        with self.lock_mensagens:
            mensagens = self.caixa_mensagens.copy()
            self.caixa_mensagens.clear()
            return mensagens
    
    def pausar(self):
        """Pausa a execução do agente"""
        self.pausado = True
    
    def retomar(self):
        """Retoma a execução do agente"""
        self.pausado = False
    
    def parar(self):
        """Para a execução do agente"""
        self.ativo = False
    
    def obter_estatisticas(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do agente
        
        Returns:
            Dicionário com estatísticas
        """
        return {
            'agente_id': self.agente_id,
            'recompensa_acumulada': self.recompensa_acumulada,
            'recompensa_media': (self.recompensa_acumulada / len(self.historico_recompensas) 
                               if self.historico_recompensas else 0),
            'num_acoes': len(self.historico_acoes),
            'num_observacoes': len(self.historico_observacoes),
            'sensores_ativos': [s.nome for s in self.sensores if s.ativo],
            'mensagens_recebidas': len(self.caixa_mensagens),
            'espacos_explorados': len(self.behavior),
            'novelty_score': self.novelty_score,
            'objective_fitness': self.objective_fitness,
            'combined_fitness': self.combined_fitness
        }
    
    def reset(self):
        """Reinicia o estado do agente"""
        self.observacao_atual = None
        self.recompensa_acumulada = 0.0
        self.recompensa_ultimo_passo = 0.0
        self.historico_observacoes.clear()
        self.historico_acoes.clear()
        self.historico_recompensas.clear()
        self.behavior.clear()
        self.path.clear()
        self.novelty_score = 0.0
        self.objective_fitness = 0.0
        self.combined_fitness = 0.0
        with self.lock_mensagens:
            self.caixa_mensagens.clear()
    
    # --- Novelty Search Methods ---
    
    def calculate_novelty(self, archive: List[Set[Tuple[int, int]]], k: int = 5) -> float:
        """
        Calcula o novelty score baseado na distância de Jaccard para o arquivo
        
        Args:
            archive: Lista de comportamentos (conjuntos de posições) do arquivo
            k: Número de vizinhos mais próximos a considerar
            
        Returns:
            Score de novidade
        """
        if not archive:
            return 1.0  # Primeiro agente é maximamente novel
        
        distances = [self._jaccard_distance(self.behavior, b) for b in archive]
        distances.sort()
        
        self.novelty_score = sum(distances[:k]) / k if len(distances) >= k else sum(distances) / len(distances)
        return self.novelty_score
    
    def _jaccard_distance(self, set1: Set[Tuple[int, int]], set2: Set[Tuple[int, int]]) -> float:
        """
        Calcula distância de Jaccard entre dois conjuntos
        
        Args:
            set1: Primeiro conjunto
            set2: Segundo conjunto
            
        Returns:
            Distância de Jaccard (0-1)
        """
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return 1 - intersection / union if union != 0 else 0
    
    def calculate_objective_fitness(self) -> float:
        """
        Calcula fitness objetivo (orientado a metas)
        Deve ser sobrescrito por subclasses para objetivos específicos
        
        Returns:
            Score de fitness objetivo
        """
        # Base: recompensa acumulada + exploração
        exploration_reward = len(self.behavior) * 1
        self.objective_fitness = self.recompensa_acumulada + exploration_reward
        return self.objective_fitness
    
    def calculate_combined_fitness(self, archive: List[Set[Tuple[int, int]]], 
                                   novelty_weight: float = 1000.0) -> float:
        """
        Calcula fitness combinado (novelty + objetivo)
        
        Args:
            archive: Arquivo de comportamentos
            novelty_weight: Peso da novidade na combinação
            
        Returns:
            Fitness combinado
        """
        novelty = self.calculate_novelty(archive)
        objective = self.calculate_objective_fitness()
        self.combined_fitness = (novelty * novelty_weight) + objective
        return self.combined_fitness
    
    # --- Evolutionary Methods ---
    
    def mutate(self, mutation_rate: float = 0.01):
        """
        Aplica mutação ao genótipo (para agentes evolucionários)
        
        Args:
            mutation_rate: Probabilidade de mutação por gene
        """
        if self.genotype is None:
            return
        
        for i in range(len(self.genotype)):
            if random.random() < mutation_rate:
                self.genotype[i] = self._generate_random_gene()
    
    def _generate_random_gene(self) -> Any:
        """
        Gera um gene aleatório
        Deve ser sobrescrito por subclasses
        
        Returns:
            Gene aleatório
        """
        # Default: ação aleatória
        return random.choice([Direcao.NORTE, Direcao.SUL, Direcao.ESTE, Direcao.OESTE])
    
    def run(self):
        """
        Método principal da Thread - ciclo de vida do agente
        Pode ser sobrescrito por subclasses para comportamento específico
        """
        while self.ativo:
            if not self.pausado and self.observacao_atual:
                # Executar ciclo de ação
                acao = self.age()
                self.historico_acoes.append(acao)
    
    def __str__(self):
        return f"Agente[{self.agente_id}]"
    
    def __repr__(self):
        return f"Agente(id={self.agente_id}, recompensa={self.recompensa_acumulada:.2f})"


class AgenteReativo(Agente):
    """
    Agente reativo simples - responde diretamente a estímulos
    Política fixa (pré-programada)
    """
    
    def __init__(self, agente_id: str, parametros: Dict[str, Any] = None):
        super().__init__(agente_id, parametros)
        self.regras = parametros.get('regras', {}) if parametros else {}
    
    def age(self) -> Acao:
        """
        Ação baseada em regras simples da observação atual
        """
        if not self.observacao_atual:
            return Acao("mover", {'direcao': Direcao.PARADO})
        
        obs = self.observacao_atual.dados
        
        # Exemplo: Mover em direção ao farol
        if 'direcao_farol' in obs:
            dx, dy = obs['direcao_farol']
            obstaculos = obs.get('obstaculos_vizinhos', {})
            
            # Escolher direção principal
            if abs(dx) > abs(dy):
                direcao = Direcao.ESTE if dx > 0 else Direcao.OESTE
            else:
                direcao = Direcao.SUL if dy > 0 else Direcao.NORTE
            
            # Verificar se há obstáculo
            if not obstaculos.get(direcao.name, False):
                return Acao("mover", {'direcao': direcao})
            
            # Tentar direção alternativa
            for d in [Direcao.NORTE, Direcao.SUL, Direcao.ESTE, Direcao.OESTE]:
                if not obstaculos.get(d.name, False):
                    return Acao("mover", {'direcao': d})
        
        return Acao("mover", {'direcao': Direcao.PARADO})


# --- Classes específicas movidas para módulos separados ---
# AgenteQLearning -> agenteqlearning.py
# AgenteEvolucionario/AgenteGenetico -> agentegenetico.py
# PopulacaoEvolucionaria -> agentegenetico.py

# Classe auxiliar para criar agentes
class FabricaAgentes:
    """
    Agente Q-Learning - Aprendizagem por Reforço
    
    Implementa Q-Learning clássico com:
    - Epsilon-greedy para exploração/exploitação
    - Q-table para armazenar valores estado-ação
    - Decaimento de epsilon ao longo do tempo
    - Modos de treino e teste
    """
    
    def __init__(self, agente_id: str, parametros: Dict[str, Any] = None):
        super().__init__(agente_id, parametros)
        
        # Modo de operação
        self.modo_aprendizagem = parametros.get('modo_aprendizagem', True) if parametros else True
        
        # Parâmetros de Q-Learning
        self.alpha = parametros.get('taxa_aprendizagem', 0.1) if parametros else 0.1  # Taxa de aprendizagem
        self.gamma = parametros.get('fator_desconto', 0.95) if parametros else 0.95   # Fator de desconto
        self.epsilon = parametros.get('epsilon', 1.0) if parametros else 1.0          # Taxa de exploração inicial
        self.epsilon_min = parametros.get('epsilon_min', 0.01) if parametros else 0.01
        self.epsilon_decay = parametros.get('epsilon_decay', 0.995) if parametros else 0.995
        
        # Q-table: Dict[estado, Dict[ação, valor_Q]]
        self.Q: Dict[str, Dict[str, float]] = {}
        
        # Estatísticas de aprendizagem
        self.episodio_atual = 0
        self.episodios_totais = parametros.get('episodios_totais', 1000) if parametros else 1000
        self.recompensas_por_episodio: List[float] = []
        self.passos_por_episodio: List[int] = []
        
        # Estado e ação anteriores (para update Q)
        self.estado_anterior: Optional[str] = None
        self.acao_anterior: Optional[str] = None
        
        # Ações disponíveis
        self.acoes_disponiveis = [Direcao.NORTE, Direcao.SUL, Direcao.ESTE, Direcao.OESTE]
    
    def age(self) -> Acao:
        """
        Escolhe ação usando política epsilon-greedy
        
        Returns:
            Ação escolhida
        """
        if not self.observacao_atual:
            return Acao("mover", {'direcao': Direcao.PARADO})
        
        estado = self._extrair_estado(self.observacao_atual)
        
        # Inicializar Q-values para estado novo
        if estado not in self.Q:
            self.Q[estado] = {d.name: 0.0 for d in self.acoes_disponiveis}
        
        # Escolher ação
        if self.modo_aprendizagem and random.random() < self.epsilon:
            # Exploração: ação aleatória
            direcao = random.choice(self.acoes_disponiveis)
        else:
            # Exploitação: melhor ação conhecida
            direcao = self._melhor_acao_q(estado)
        
        # Guardar estado e ação para próximo update
        self.estado_anterior = estado
        self.acao_anterior = direcao.name
        
        return Acao("mover", {'direcao': direcao})
    
    def _extrair_estado(self, obs: Observacao) -> str:
        """
        Extrai representação compacta do estado a partir da observação
        
        Args:
            obs: Observação atual
            
        Returns:
            String representando o estado
        """
        dados = obs.dados
        
        # Estratégia 1: Se tem direção do farol (ambiente Farol)
        if 'direcao_farol' in dados:
            dx, dy = dados['direcao_farol']
            
            # Discretizar direção (9 bins: N, NE, E, SE, S, SO, O, NO, Centro)
            if dx == 0 and dy == 0:
                dir_geral = "C"  # Centro (chegou)
            else:
                angulo = np.arctan2(dy, dx) * 180 / np.pi
                # Dividir em 8 direções
                if -22.5 <= angulo < 22.5:
                    dir_geral = "E"
                elif 22.5 <= angulo < 67.5:
                    dir_geral = "SE"
                elif 67.5 <= angulo < 112.5:
                    dir_geral = "S"
                elif 112.5 <= angulo < 157.5:
                    dir_geral = "SO"
                elif angulo >= 157.5 or angulo < -157.5:
                    dir_geral = "O"
                elif -157.5 <= angulo < -112.5:
                    dir_geral = "NO"
                elif -112.5 <= angulo < -67.5:
                    dir_geral = "N"
                else:  # -67.5 <= angulo < -22.5
                    dir_geral = "NE"
            
            # Discretizar distância (perto, médio, longe)
            dist = dados.get('distancia_farol', 0)
            if dist < 3:
                dist_cat = "P"  # Perto
            elif dist < 10:
                dist_cat = "M"  # Médio
            else:
                dist_cat = "L"  # Longe
            
            # Obstáculos vizinhos (4 bits)
            obstaculos = dados.get('obstaculos_vizinhos', {})
            obs_str = ''.join(['1' if obstaculos.get(d.name, False) else '0' 
                              for d in [Direcao.NORTE, Direcao.SUL, Direcao.ESTE, Direcao.OESTE]])
            
            return f"{dir_geral}_{dist_cat}_{obs_str}"
        
        # Estratégia 2: Posição atual (fallback)
        if 'posicao_atual' in dados:
            x, y = dados['posicao_atual']
            # Discretizar em grid 10x10
            grid_x = min(x // 10, 9)
            grid_y = min(y // 10, 9)
            return f"pos_{grid_x}_{grid_y}"
        
        return "estado_desconhecido"
    
    def _melhor_acao_q(self, estado: str) -> Direcao:
        """
        Retorna a ação com maior valor Q para um estado
        
        Args:
            estado: Estado atual
            
        Returns:
            Melhor ação (direção)
        """
        if estado not in self.Q:
            return random.choice(self.acoes_disponiveis)
        
        # Encontrar ação com maior Q-value
        melhor_acao_nome = max(self.Q[estado], key=self.Q[estado].get)
        return Direcao[melhor_acao_nome]
    
    def _processar_recompensa(self, recompensa: float):
        """
        Atualiza Q-table usando regra de Q-Learning
        
        Q(s,a) ← Q(s,a) + α[r + γ·max Q(s',a') - Q(s,a)]
        
        Args:
            recompensa: Recompensa recebida
        """
        if not self.modo_aprendizagem:
            return
        
        # Precisamos de estado anterior e ação anterior
        if self.estado_anterior is None or self.acao_anterior is None:
            return
        
        # Estado atual
        if not self.observacao_atual:
            return
        
        estado_atual = self._extrair_estado(self.observacao_atual)
        
        # Inicializar Q-values para estado atual se necessário
        if estado_atual not in self.Q:
            self.Q[estado_atual] = {d.name: 0.0 for d in self.acoes_disponiveis}
        
        # Q-Learning update
        Q_sa = self.Q[self.estado_anterior][self.acao_anterior]
        max_Q_next = max(self.Q[estado_atual].values())
        
        novo_Q = Q_sa + self.alpha * (recompensa + self.gamma * max_Q_next - Q_sa)
        
        self.Q[self.estado_anterior][self.acao_anterior] = novo_Q
    
    def fim_episodio(self):
        """
        Chamado no final de cada episódio
        Atualiza epsilon e estatísticas
        """
        self.episodio_atual += 1
        
        # Decair epsilon
        if self.modo_aprendizagem:
            self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        
        # Registar estatísticas
        self.recompensas_por_episodio.append(self.recompensa_acumulada)
        self.passos_por_episodio.append(len(self.historico_acoes))
    
    def definir_modo(self, aprendizagem: bool):
        """
        Define o modo de operação
        
        Args:
            aprendizagem: True para treino, False para teste
        """
        self.modo_aprendizagem = aprendizagem
        if not aprendizagem:
            self.epsilon = 0.0  # No modo teste, sem exploração
        print(f"[{self.agente_id}] Modo: {'Treino' if aprendizagem else 'Teste'}")
    
    def salvar_q_table(self, ficheiro: str):
        """
        Salva Q-table num ficheiro JSON
        
        Args:
            ficheiro: Caminho do ficheiro
        """
        with open(ficheiro, 'w', encoding='utf-8') as f:
            json.dump(self.Q, f, indent=2)
        print(f"[{self.agente_id}] Q-table salva: {ficheiro} ({len(self.Q)} estados)")
    
    def carregar_q_table(self, ficheiro: str):
        """
        Carrega Q-table de um ficheiro JSON
        
        Args:
            ficheiro: Caminho do ficheiro
        """
        with open(ficheiro, 'r', encoding='utf-8') as f:
            self.Q = json.load(f)
        print(f"[{self.agente_id}] Q-table carregada: {ficheiro} ({len(self.Q)} estados)")
    
    def obter_estatisticas_aprendizagem(self) -> Dict[str, Any]:
        """
        Retorna estatísticas de aprendizagem
        
        Returns:
            Dicionário com métricas
        """
        return {
            'episodio_atual': self.episodio_atual,
            'epsilon_atual': self.epsilon,
            'estados_aprendidos': len(self.Q),
            'recompensa_media_ultimos_100': (np.mean(self.recompensas_por_episodio[-100:]) 
                                             if len(self.recompensas_por_episodio) >= 100 
                                             else np.mean(self.recompensas_por_episodio) if self.recompensas_por_episodio else 0),
            'passos_medios_ultimos_100': (np.mean(self.passos_por_episodio[-100:]) 
                                          if len(self.passos_por_episodio) >= 100 
                                          else np.mean(self.passos_por_episodio) if self.passos_por_episodio else 0),
            'total_episodios': len(self.recompensas_por_episodio)
        }


class AgenteEvolucionario(Agente):
    """
    Agente evolucionário com genótipo fixo (sequência de ações)
    Baseado em Novelty Search - explora o espaço de comportamentos
    
    Características:
    - Genótipo: sequência fixa de ações
    - Fitness baseado em novidade e objetivo
    - Evolução via seleção, crossover e mutação
    - Suporta arquivo de comportamentos
    """
    
    def __init__(self, agente_id: str, parametros: Dict[str, Any] = None, genotype: List[Direcao] = None):
        super().__init__(agente_id, parametros, genotype)
        
        self.acoes_disponiveis = [Direcao.NORTE, Direcao.SUL, Direcao.ESTE, Direcao.OESTE]
        
        # Parâmetros genéticos
        self.taxa_mutacao = parametros.get('taxa_mutacao', 0.01) if parametros else 0.01
        
        # Gerar genótipo aleatório se não fornecido
        if self.genotype is None:
            self.genotype = [random.choice(self.acoes_disponiveis) for _ in range(self.num_steps)]
        
        self.passo_atual = 0
        
        # Métricas específicas do genético
        self.recursos_coletados = 0
        self.objetivos_alcancados = 0
    
    def age(self) -> Acao:
        """
        Retorna a próxima ação do genótipo
        
        Returns:
            Ação do genótipo
        """
        if self.passo_atual >= len(self.genotype):
            return Acao("mover", {'direcao': Direcao.PARADO})
        
        direcao = self.genotype[self.passo_atual]
        self.passo_atual += 1
        
        return Acao("mover", {'direcao': direcao})
    
    def _generate_random_gene(self) -> Direcao:
        """
        Gera um gene aleatório (direção)
        
        Returns:
            Direção aleatória
        """
        return random.choice(self.acoes_disponiveis)
    
    def calculate_objective_fitness(self) -> float:
        """
        Calcula fitness objetivo específico para ambientes
        
        Returns:
            Score de fitness objetivo
        """
        # Base: recompensa acumulada
        fitness = self.recompensa_acumulada
        
        # Bonificação por exploração
        exploracao_bonus = len(self.behavior) * 2
        
        # Bonificação por recursos/objetivos
        recursos_bonus = self.recursos_coletados * 50
        objetivos_bonus = self.objetivos_alcancados * 200
        
        # Penalização por movimentos repetitivos
        movimento_unico_ratio = len(self.behavior) / max(len(self.path), 1)
        exploracao_penalty = -100 if movimento_unico_ratio < 0.3 else 0
        
        self.objective_fitness = fitness + exploracao_bonus + recursos_bonus + objetivos_bonus + exploracao_penalty
        
        return self.objective_fitness
    
    def clonar(self, novo_id: str) -> 'AgenteEvolucionario':
        """
        Cria um clone do agente com o mesmo genótipo
        
        Args:
            novo_id: ID para o clone
            
        Returns:
            Clone do agente
        """
        return AgenteEvolucionario(
            novo_id,
            self.parametros,
            self.genotype.copy()
        )
    
    def reset(self):
        """Reinicia o agente incluindo o contador de passos"""
        super().reset()
        self.passo_atual = 0
        self.recursos_coletados = 0
        self.objetivos_alcancados = 0


# Alias para compatibilidade (AgenteGenetico = AgenteEvolucionario)
AgenteGenetico = AgenteEvolucionario


# --- Funções Auxiliares para Evolução ---

def crossover(parent1: AgenteEvolucionario, parent2: AgenteEvolucionario) -> Tuple[AgenteEvolucionario, AgenteEvolucionario]:
    """
    Realiza crossover de um ponto entre dois pais
    
    Args:
        parent1: Primeiro pai
        parent2: Segundo pai
        
    Returns:
        Tupla com dois filhos
    """
    point = random.randint(1, len(parent1.genotype) - 1)
    
    child1_geno = parent1.genotype[:point] + parent2.genotype[point:]
    child2_geno = parent2.genotype[:point] + parent1.genotype[point:]
    
    child1 = AgenteEvolucionario(
        f"{parent1.agente_id}_child1",
        parent1.parametros,
        child1_geno
    )
    child2 = AgenteEvolucionario(
        f"{parent2.agente_id}_child2",
        parent2.parametros,
        child2_geno
    )
    
    return child1, child2


def select_parent(population: List[Agente], tournament_size: int = 3) -> Agente:
    """
    Seleciona um pai usando seleção por torneio baseada em combined_fitness
    
    Args:
        population: População de agentes
        tournament_size: Tamanho do torneio
        
    Returns:
        Agente selecionado
    """
    tournament = random.sample(population, tournament_size)
    tournament.sort(key=lambda x: x.combined_fitness, reverse=True)
    return tournament[0]


class PopulacaoEvolucionaria:
    """
    Gerencia uma população de agentes evolucionários com Novelty Search
    """
    
    def __init__(self, tamanho_populacao: int = 50, num_steps: int = 1000):
        self.tamanho_populacao = tamanho_populacao
        self.num_steps = num_steps
        self.populacao: List[AgenteEvolucionario] = []
        self.arquivo: List[Set[Tuple[int, int]]] = []  # Arquivo de comportamentos
        self.geracao_atual = 0
        
        # Parâmetros evolutivos
        self.taxa_mutacao = 0.01
        self.tamanho_torneio = 3
        self.n_elitismo = tamanho_populacao // 10
        self.n_arquivo_add = 5  # Adicionar top 5 mais novos ao arquivo
        
        # Métricas
        self.fitness_medio_por_geracao: List[float] = []
        self.melhor_fitness_por_geracao: List[float] = []
        self.melhores_agentes_por_geracao: List[AgenteEvolucionario] = []
    
    def inicializar_populacao(self):
        """Cria população inicial com genótipos aleatórios"""
        self.populacao = []
        for i in range(self.tamanho_populacao):
            agente = AgenteEvolucionario(
                f"agente_evo_{i}",
                {'num_steps': self.num_steps}
            )
            self.populacao.append(agente)
    
    def evoluir_geracao(self, ambiente_factory, novelty_weight: float = 1000.0):
        """
        Evolui uma geração completa
        
        Args:
            ambiente_factory: Função que cria uma nova instância do ambiente
            novelty_weight: Peso da novidade no fitness combinado
        """
        # 1. Avaliar população
        total_fitness = 0
        
        for agente in self.populacao:
            # Resetar agente
            agente.reset()
            
            # Criar ambiente fresco
            ambiente = ambiente_factory()
            
            # Simular agente no ambiente
            self._simular_agente(agente, ambiente)
            
            # Calcular fitness combinado
            agente.calculate_combined_fitness(self.arquivo, novelty_weight)
            total_fitness += agente.combined_fitness
        
        # 2. Ordenar por combined_fitness
        self.populacao.sort(key=lambda x: x.combined_fitness, reverse=True)
        
        # 3. Registar métricas
        fitness_medio = total_fitness / self.tamanho_populacao
        self.fitness_medio_por_geracao.append(fitness_medio)
        self.melhor_fitness_por_geracao.append(self.populacao[0].combined_fitness)
        self.melhores_agentes_por_geracao.append(self.populacao[0])
        
        # 4. Atualizar arquivo com comportamentos mais novos
        # Ordenar temporariamente por novelty puro
        pop_ordenada_novelty = sorted(
            self.populacao,
            key=lambda x: x.calculate_novelty(self.arquivo),
            reverse=True
        )
        
        for i in range(self.n_arquivo_add):
            self.arquivo.append(pop_ordenada_novelty[i].behavior)
        
        # Re-ordenar por combined_fitness para breeding
        self.populacao.sort(key=lambda x: x.combined_fitness, reverse=True)
        
        # 5. Criar nova geração
        nova_populacao: List[AgenteEvolucionario] = []
        
        # Elitismo
        nova_populacao.extend(self.populacao[:self.n_elitismo])
        
        # Breeding
        while len(nova_populacao) < self.tamanho_populacao:
            parent1 = select_parent(self.populacao, self.tamanho_torneio)
            parent2 = select_parent(self.populacao, self.tamanho_torneio)
            
            child1, child2 = crossover(parent1, parent2)
            
            child1.mutate(self.taxa_mutacao)
            child2.mutate(self.taxa_mutacao)
            
            nova_populacao.append(child1)
            if len(nova_populacao) < self.tamanho_populacao:
                nova_populacao.append(child2)
        
        self.populacao = nova_populacao
        self.geracao_atual += 1
    
    def _simular_agente(self, agente: AgenteEvolucionario, ambiente):
        """
        Simula um agente num ambiente até terminar ou atingir limite de passos
        
        Args:
            agente: Agente a simular
            ambiente: Ambiente onde simular
        """
        # Registar agente no ambiente (posição inicial padrão)
        from ambiente import Posicao
        ambiente.registar_agente(agente.agente_id, Posicao(0, 0))
        
        passo = 0
        while passo < agente.num_steps and not ambiente.terminado:
            # Observar
            obs = ambiente.observacao_para(agente.agente_id)
            agente.observacao(obs)
            
            # Agir
            acao = agente.age()
            recompensa = ambiente.agir(acao, agente.agente_id)
            agente.avaliacaoEstadoAtual(recompensa)
            
            # Atualizar ambiente
            ambiente.atualizacao()
            
            passo += 1
    
    def obter_melhor_agente(self) -> AgenteEvolucionario:
        """
        Retorna o melhor agente da população atual
        
        Returns:
            Melhor agente
        """
        return max(self.populacao, key=lambda x: x.combined_fitness)
    
    def obter_estatisticas_geracao(self) -> Dict[str, Any]:
        """
        Retorna estatísticas da geração atual
        
        Returns:
            Dicionário com estatísticas
        """
        melhor = self.obter_melhor_agente()
        
        return {
            'geracao': self.geracao_atual,
            'fitness_medio': self.fitness_medio_por_geracao[-1] if self.fitness_medio_por_geracao else 0,
            'melhor_fitness': melhor.combined_fitness,
            'melhor_novelty': melhor.novelty_score,
            'melhor_objective': melhor.objective_fitness,
            'tamanho_arquivo': len(self.arquivo),
            'espacos_explorados_melhor': len(melhor.behavior)
        }


# Classe auxiliar para criar agentes
class FabricaAgentes:
    """Fábrica para criar diferentes tipos de agentes"""
    
    @staticmethod
    def criar_agente(tipo: str, agente_id: str, parametros: Dict[str, Any] = None) -> Agente:
        """
        Cria um agente do tipo especificado
        
        Args:
            tipo: Tipo do agente ('reativo', 'qlearning', 'aprendizagem', 'evolucionario', 'genetico')
            agente_id: Identificador do agente
            parametros: Parâmetros de configuração
            
        Returns:
            Instância do agente
        """
        if tipo == "reativo":
            return AgenteReativo(agente_id, parametros)
        elif tipo in ["aprendizagem", "qlearning"]:
            from agenteqlearning import AgenteQLearning
            return AgenteQLearning(agente_id, parametros)
        elif tipo in ["evolucionario", "genetico"]:
            from agentegenetico import AgenteEvolucionario
            return AgenteEvolucionario(agente_id, parametros)
        else:
            raise ValueError(f"Tipo de agente não suportado: {tipo}")
    
    @staticmethod
    def criar_de_ficheiro(tipo: str, ficheiro_parametros: str) -> Agente:
        """
        Cria um agente a partir de ficheiro de configuração
        
        Args:
            tipo: Tipo do agente
            ficheiro_parametros: Caminho para ficheiro JSON
            
        Returns:
            Instância do agente
        """
        if tipo == "reativo":
            return AgenteReativo.cria(ficheiro_parametros)
        elif tipo in ["aprendizagem", "qlearning"]:
            from agenteqlearning import AgenteQLearning
            return AgenteQLearning.cria(ficheiro_parametros)
        elif tipo in ["evolucionario", "genetico"]:
            from agentegenetico import AgenteEvolucionario
            return AgenteEvolucionario.cria(ficheiro_parametros)
        else:
            raise ValueError(f"Tipo de agente não suportado: {tipo}")
