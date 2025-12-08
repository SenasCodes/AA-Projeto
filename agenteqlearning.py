"""
Módulo de Agente Q-Learning - Aprendizagem por Reforço
Implementa Q-Learning com epsilon-greedy e Q-table
"""

from typing import Dict, Any, Optional, List
import json
import random
import numpy as np
from agente import Agente
from ambiente import Observacao, Acao, Direcao


class AgenteQLearning(Agente):
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
    
    def observacao(self, obs: Observacao, recompensa: float = 0.0):
        """
        Recebe observação e recompensa, atualiza Q-table
        
        Args:
            obs: Observação do ambiente
            recompensa: Recompensa recebida
        """
        super().observacao(obs, recompensa)
        
        # Atualizar Q-table se em modo aprendizagem
        if self.modo_aprendizagem and recompensa != 0.0:
            self._processar_recompensa(recompensa)
    
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
