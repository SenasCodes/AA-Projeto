"""
Módulo de Agente - Classes base para agentes autónomos

Interface obrigatória (6 métodos):
1. age() 2. observacao() 3. instala() 4. avaliacaoEstadoAtual() 5. cria() 6. comunica()

Implementações específicas: agenteqlearning.py, agentegenetico.py
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Set, Tuple
from threading import Thread, Lock
import json
import random
from ambiente import Observacao, Acao, Posicao, Direcao


# ============================================================================
# SENSORES E COMUNICAÇÃO
# ============================================================================

class Sensor(ABC):
    """Sensor abstrato"""
    def __init__(self, nome: str):
        self.nome = nome
        self.ativo = True
    
    @abstractmethod
    def processar(self, observacao: Observacao) -> Dict[str, Any]:
        pass


class SensorDistancia(Sensor):
    """Sensor de distâncias"""
    def __init__(self):
        super().__init__("sensor_distancia")
    
    def processar(self, observacao: Observacao) -> Dict[str, Any]:
        dados = {}
        if 'distancia_farol' in observacao.dados:
            dados['distancia'] = observacao.dados['distancia_farol']
        if 'direcao_farol' in observacao.dados:
            dx, dy = observacao.dados['direcao_farol']
            dados['direcao_x'] = dx
            dados['direcao_y'] = dy
        return dados


class SensorObstaculos(Sensor):
    """Sensor de obstáculos"""
    def __init__(self):
        super().__init__("sensor_obstaculos")
    
    def processar(self, observacao: Observacao) -> Dict[str, Any]:
        dados = {}
        if 'obstaculos_vizinhos' in observacao.dados:
            dados['obstaculos'] = observacao.dados['obstaculos_vizinhos']
        return dados


class Mensagem:
    """Mensagem entre agentes"""
    def __init__(self, remetente: str, destinatario: str, conteudo: Any, tipo: str = "info"):
        self.remetente = remetente
        self.destinatario = destinatario
        self.conteudo = conteudo
        self.tipo = tipo


# ============================================================================
# AGENTE BASE
# ============================================================================

class Agente(ABC, Thread):
    """Classe base para todos os agentes"""
    
    def __init__(self, agente_id: str, parametros: Dict[str, Any] = None, genotype: List[Direcao] = None):
        Thread.__init__(self)
        self.agente_id = agente_id
        self.parametros = parametros or {}
        self.genotype = genotype
        
        # Estado
        self.ambiente = None
        self.posicao_atual: Optional[Posicao] = None
        self.observacao_atual: Optional[Observacao] = None
        
        # Histórico
        self.historico_observacoes: List[Observacao] = []
        self.historico_acoes: List[Acao] = []
        self.recompensa_acumulada: float = 0.0
        
        # Comportamento (Novelty Search)
        self.behavior: Set[Tuple[int, int]] = set()
        self.path: List[Tuple[int, int]] = []
        
        # Fitness
        self.novelty_score: float = 0.0
        self.objective_fitness: float = 0.0
        self.fitness_total: float = 0.0
        
        # Sensores e comunicação
        self.sensores: List[Sensor] = []
        self.mensagens: List[Mensagem] = []
        self.lock = Lock()
        
        self.num_steps = parametros.get('num_steps', 100) if parametros else 100
    
    @abstractmethod
    def age(self) -> Acao:
        """Decide próxima ação"""
        pass
    
    def observacao(self, obs: Observacao, recompensa: float = 0.0):
        """Recebe observação e recompensa"""
        self.observacao_atual = obs
        self.historico_observacoes.append(obs)
        self.recompensa_acumulada += recompensa
        
        if 'posicao_atual' in obs.dados:
            pos = tuple(obs.dados['posicao_atual'])
            self.behavior.add(pos)
            self.path.append(pos)
            self.posicao_atual = Posicao(*pos)
    
    def instala(self, ambiente, posicao: Posicao = None) -> Observacao:
        """Instala agente no ambiente"""
        self.ambiente = ambiente
        if posicao:
            self.posicao_atual = posicao
        obs_inicial = ambiente.observacao_para(self.agente_id)
        self.observacao(obs_inicial)
        return obs_inicial
    
    def avaliacaoEstadoAtual(self, recompensa: float = None) -> float:
        """Avalia estado atual (opcionalmente processa recompensa)"""
        if recompensa is not None:
            self.recompensa_acumulada += recompensa
        return self.fitness_total
    
    @classmethod
    def cria(cls, ficheiro_parametros: str):
        """Cria agente de ficheiro JSON"""
        with open(ficheiro_parametros, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return cls(config.get('agente_id', 'agente_default'), config.get('parametros', {}))
    
    def comunica(self, mensagem: Mensagem):
        """Recebe mensagem"""
        with self.lock:
            self.mensagens.append(mensagem)
    
    def adicionar_sensor(self, sensor: Sensor):
        """Adiciona sensor"""
        self.sensores.append(sensor)
    
    def processar_sensores(self) -> Dict[str, Any]:
        """Processa sensores ativos"""
        dados = {}
        if self.observacao_atual:
            for sensor in self.sensores:
                if sensor.ativo:
                    dados[sensor.nome] = sensor.processar(self.observacao_atual)
        return dados
    
    def reset(self):
        """Reinicia estado"""
        self.historico_observacoes.clear()
        self.historico_acoes.clear()
        self.recompensa_acumulada = 0.0
        self.behavior.clear()
        self.path.clear()
        self.novelty_score = 0.0
        self.objective_fitness = 0.0
        self.fitness_total = 0.0
        self.observacao_atual = None
        with self.lock:
            self.mensagens.clear()
    
    def obter_estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas do agente"""
        return {
            'recompensa_acumulada': self.recompensa_acumulada,
            'num_acoes': len(self.historico_acoes),
            'espacos_explorados': len(self.behavior),
            'distancia_percorrida': len(self.path),
            'novelty_score': self.novelty_score,
            'objective_fitness': self.objective_fitness,
            'fitness_total': self.fitness_total
        }
    
    def calculate_novelty(self, populacao: List['Agente'], k_vizinhos: int = 15):
        """Calcula novelty score (k-NN + Jaccard)"""
        if not self.behavior:
            self.novelty_score = 0.0
            return
        
        distancias = [self._jaccard_distance(self.behavior, a.behavior) 
                      for a in populacao 
                      if a.agente_id != self.agente_id and a.behavior]
        
        if distancias:
            k_proximos = sorted(distancias)[:min(k_vizinhos, len(distancias))]
            self.novelty_score = sum(k_proximos) / len(k_proximos)
        else:
            self.novelty_score = 0.0
    
    @staticmethod
    def _jaccard_distance(set1: Set, set2: Set) -> float:
        """Distância de Jaccard"""
        if not set1 and not set2:
            return 0.0
        intersecao = len(set1 & set2)
        uniao = len(set1 | set2)
        return 1.0 - (intersecao / uniao) if uniao > 0 else 0.0
    
    def calculate_fitness(self, peso_novidade: float = 0.5):
        """Calcula fitness total"""
        self.fitness_total = (self.novelty_score * peso_novidade + 
                             self.objective_fitness * (1 - peso_novidade))


# ============================================================================
# AGENTE REATIVO
# ============================================================================

class AgenteReativo(Agente):
    """Agente com política fixa"""
    
    def __init__(self, agente_id: str, parametros: Dict[str, Any] = None):
        super().__init__(agente_id, parametros)
        self.politica_fixa = parametros.get('politica', 'ir_para_farol') if parametros else 'ir_para_farol'
        # Memória para evitar loops
        self.ultimas_posicoes = []  # Últimas 5 posições
        self.max_memoria = 5
    
    def _evitar_loop(self, direcao: Direcao, dados: Dict) -> Optional[Direcao]:
        """Verifica se movimento causaria loop e sugere alternativa"""
        if not self.posicao_atual:
            return direcao
        
        # Calcular próxima posição
        nova_pos = self.posicao_atual.mover(direcao)
        nova_pos_tupla = (nova_pos.x, nova_pos.y)
        
        # Verificar se já esteve nesta posição recentemente
        if nova_pos_tupla in self.ultimas_posicoes:
            # Tentar direções alternativas que não causem loop
            obstaculos = dados.get('obstaculos_vizinhos', {})
            direcoes_ordenadas = [Direcao.NORTE, Direcao.SUL, Direcao.ESTE, Direcao.OESTE]
            
            for dir_alt in direcoes_ordenadas:
                if dir_alt == direcao:
                    continue
                pos_alt = self.posicao_atual.mover(dir_alt)
                pos_alt_tupla = (pos_alt.x, pos_alt.y)
                if (not obstaculos.get(dir_alt.name, False) and 
                    pos_alt_tupla not in self.ultimas_posicoes):
                    return dir_alt
        
        return direcao
    
    def age(self) -> Acao:
        """Decide ação baseada na política fixa"""
        if not self.observacao_atual:
            return Acao("mover", {'direcao': Direcao.PARADO})
        
        dados = self.observacao_atual.dados
        
        # Atualizar memória de posições
        if self.posicao_atual:
            pos_tupla = (self.posicao_atual.x, self.posicao_atual.y)
            self.ultimas_posicoes.append(pos_tupla)
            if len(self.ultimas_posicoes) > self.max_memoria:
                self.ultimas_posicoes.pop(0)
        
        # Política para ambiente Farol ou Labirinto
        if 'direcao_farol' in dados or 'direcao_fim' in dados:
            direcao_alvo = dados.get('direcao_farol') or dados.get('direcao_fim')
            dx, dy = direcao_alvo
            
            # Se já chegou, parar
            if dx == 0 and dy == 0:
                return Acao("mover", {'direcao': Direcao.PARADO})
            
            # Escolher direção principal (priorizar maior componente)
            if abs(dx) > abs(dy):
                direcao_principal = Direcao.ESTE if dx > 0 else Direcao.OESTE
                direcao_secundaria = Direcao.SUL if dy > 0 else Direcao.NORTE
            else:
                direcao_principal = Direcao.SUL if dy > 0 else Direcao.NORTE
                direcao_secundaria = Direcao.ESTE if dx > 0 else Direcao.OESTE
            
            obstaculos = dados.get('obstaculos_vizinhos', {})
            
            # Tentar direção principal
            if not obstaculos.get(direcao_principal.name, False):
                direcao_final = self._evitar_loop(direcao_principal, dados)
                if direcao_final:
                    return Acao("mover", {'direcao': direcao_final})
            
            # Tentar direção secundária
            if not obstaculos.get(direcao_secundaria.name, False):
                direcao_final = self._evitar_loop(direcao_secundaria, dados)
                if direcao_final:
                    return Acao("mover", {'direcao': direcao_final})
            
            # Se ambas bloqueadas, tentar outras direções (evitando loops)
            for dir_alt in [Direcao.NORTE, Direcao.SUL, Direcao.ESTE, Direcao.OESTE]:
                if (not obstaculos.get(dir_alt.name, False) and
                    dir_alt != direcao_principal and dir_alt != direcao_secundaria):
                    direcao_final = self._evitar_loop(dir_alt, dados)
                    if direcao_final and direcao_final != dir_alt:
                        return Acao("mover", {'direcao': direcao_final})
                    elif direcao_final:
                        return Acao("mover", {'direcao': direcao_final})
        
        # Política para ambiente Foraging
        elif 'recursos_proximos' in dados or 'ninhos_proximos' in dados:
            recursos_carregados = dados.get('recursos_carregados', 0)
            
            # Se tem recurso, ir para o ninho
            if recursos_carregados > 0:
                ninhos = dados.get('ninhos_proximos', [])
                if ninhos and dados.get('pode_depositar', False):
                    return Acao("depositar", {})
                elif ninhos:
                    # Mover em direção ao ninho mais próximo
                    ninho_mais_proximo = min(ninhos, key=lambda n: n['distancia'])
                    nx, ny = ninho_mais_proximo['posicao']
                    pos_atual = dados['posicao_atual']
                    dx = nx - pos_atual[0]
                    dy = ny - pos_atual[1]
                    
                    if abs(dx) > abs(dy):
                        direcao = Direcao.ESTE if dx > 0 else Direcao.OESTE
                    else:
                        direcao = Direcao.SUL if dy > 0 else Direcao.NORTE
                    
                    obstaculos = dados.get('obstaculos_vizinhos', {})
                    if not obstaculos.get(direcao.name, False):
                        return Acao("mover", {'direcao': direcao})
            else:
                # Se não tem recurso, procurar recursos
                if dados.get('pode_recolher', False):
                    return Acao("recolher", {})
                else:
                    recursos = dados.get('recursos_proximos', [])
                    if recursos:
                        recurso_mais_proximo = min(recursos, key=lambda r: r['distancia'])
                        rx, ry = recurso_mais_proximo['posicao']
                        pos_atual = dados['posicao_atual']
                        dx = rx - pos_atual[0]
                        dy = ry - pos_atual[1]
                        
                        if abs(dx) > abs(dy):
                            direcao = Direcao.ESTE if dx > 0 else Direcao.OESTE
                        else:
                            direcao = Direcao.SUL if dy > 0 else Direcao.NORTE
                        
                        obstaculos = dados.get('obstaculos_vizinhos', {})
                        if not obstaculos.get(direcao.name, False):
                            return Acao("mover", {'direcao': direcao})
        
        # Fallback: movimento aleatório (evitando loops)
        direcoes_validas = []
        obstaculos = dados.get('obstaculos_vizinhos', {})
        for dir in [Direcao.NORTE, Direcao.SUL, Direcao.ESTE, Direcao.OESTE]:
            if not obstaculos.get(dir.name, False):
                direcao_final = self._evitar_loop(dir, dados)
                if direcao_final:
                    direcoes_validas.append(direcao_final)
        
        if direcoes_validas:
            return Acao("mover", {'direcao': random.choice(direcoes_validas)})
        else:
            return Acao("mover", {'direcao': Direcao.PARADO})
    
    def reset(self):
        """Reinicia estado incluindo memória de posições"""
        super().reset()
        self.ultimas_posicoes.clear()


# ============================================================================
# FÁBRICA DE AGENTES
# ============================================================================

class FabricaAgentes:
    """Fábrica para criação de agentes"""
    
    @staticmethod
    def criar_agente(tipo: str, agente_id: str, parametros: Dict[str, Any] = None) -> Agente:
        """Cria agente por tipo"""
        if tipo == "reativo":
            return AgenteReativo(agente_id, parametros)
        elif tipo in ["aprendizagem", "qlearning"]:
            from agenteqlearning import AgenteQLearning
            return AgenteQLearning(agente_id, parametros)
        elif tipo in ["evolucionario", "genetico"]:
            from agentegenetico import AgenteEvolucionario
            return AgenteEvolucionario(agente_id, parametros)
        else:
            raise ValueError(f"Tipo não suportado: {tipo}")
    
    @staticmethod
    def criar_de_ficheiro(tipo: str, ficheiro_parametros: str) -> Agente:
        """Cria agente de ficheiro"""
        if tipo == "reativo":
            return AgenteReativo.cria(ficheiro_parametros)
        elif tipo in ["aprendizagem", "qlearning"]:
            from agenteqlearning import AgenteQLearning
            return AgenteQLearning.cria(ficheiro_parametros)
        elif tipo in ["evolucionario", "genetico"]:
            from agentegenetico import AgenteEvolucionario
            return AgenteEvolucionario.cria(ficheiro_parametros)
        else:
            raise ValueError(f"Tipo não suportado: {tipo}")
