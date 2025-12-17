from ambiente import Ambiente, Posicao, Observacao, Direcao, Acao
from typing import Set, List
import numpy as np
import random


class AmbienteFarol(Ambiente):
    """Ambiente do problema do Farol"""

    def __init__(self, largura: int = 10, altura: int = 10,
                 pos_farol: Posicao = None, com_obstaculos: bool = False,
                 mover_farol: bool = True, mover_obstaculos: bool = True,
                 intervalo_movimento: int = 20):
        super().__init__(largura, altura)

        # Posição do farol (objetivo)
        self.pos_farol = pos_farol or Posicao(largura // 2, altura // 2)
        self.pos_farol_inicial = Posicao(self.pos_farol.x, self.pos_farol.y)

        # Obstáculos (opcionais)
        self.obstaculos: Set[Posicao] = set()
        self.com_obstaculos = com_obstaculos
        if com_obstaculos:
            self._gerar_obstaculos()

        # Configuração de movimento
        self.mover_farol = mover_farol
        self.mover_obstaculos = mover_obstaculos
        self.intervalo_movimento = intervalo_movimento  # A cada N passos
        self.ultimo_movimento = 0

        # Métricas específicas
        self.metricas.update({
            'agentes_no_farol': 0,
            'distancias_medias': [],
            'tempos_chegada': {}
        })

    def _obter_posicoes_ocupadas(self) -> Set[Posicao]:
        """Retorna conjunto de posições ocupadas (farol + agentes)"""
        ocupadas = {self.pos_farol}
        for agente_id, info in self.agentes.items():
            ocupadas.add(info['posicao'])
        return ocupadas
    
    def _gerar_obstaculos(self):
        """Gera obstáculos aleatórios no ambiente, evitando farol e agentes"""
        posicoes_ocupadas = self._obter_posicoes_ocupadas()
        num_obstaculos = (self.largura * self.altura) // 10
        tentativas = 0
        max_tentativas = num_obstaculos * 10
        
        self.obstaculos.clear()
        while len(self.obstaculos) < num_obstaculos and tentativas < max_tentativas:
            x = random.randint(0, self.largura - 1)
            y = random.randint(0, self.altura - 1)
            pos = Posicao(x, y)
            if pos not in posicoes_ocupadas:
                self.obstaculos.add(pos)
            tentativas += 1
    
    def _mover_farol(self):
        """Move o farol para uma nova posição aleatória"""
        posicoes_ocupadas = self._obter_posicoes_ocupadas()
        tentativas = 0
        max_tentativas = 100
        
        while tentativas < max_tentativas:
            x = random.randint(0, self.largura - 1)
            y = random.randint(0, self.altura - 1)
            nova_pos = Posicao(x, y)
            
            # Verificar se posição é válida (não ocupada e não tem obstáculo)
            if nova_pos not in posicoes_ocupadas and nova_pos not in self.obstaculos:
                self.pos_farol = nova_pos
                return True
            tentativas += 1
        
        return False  # Não conseguiu mover
    
    def _mover_obstaculos(self):
        """Move obstáculos para novas posições"""
        if not self.com_obstaculos:
            return
        
        posicoes_ocupadas = self._obter_posicoes_ocupadas()
        novos_obstaculos = set()
        num_obstaculos = len(self.obstaculos)
        tentativas = 0
        max_tentativas = num_obstaculos * 10
        
        while len(novos_obstaculos) < num_obstaculos and tentativas < max_tentativas:
            x = random.randint(0, self.largura - 1)
            y = random.randint(0, self.altura - 1)
            pos = Posicao(x, y)
            
            # Verificar se posição é válida (não ocupada, não é farol, não é obstáculo existente)
            if (pos not in posicoes_ocupadas and 
                pos != self.pos_farol and 
                pos not in novos_obstaculos):
                novos_obstaculos.add(pos)
            tentativas += 1
        
        self.obstaculos = novos_obstaculos

    def observacao_para(self, agente_id: str) -> Observacao:
        pos_agente = self.obter_posicao_agente(agente_id)
        if not pos_agente:
            return Observacao({}, agente_id)

        # Calcular direção para o farol
        dx = self.pos_farol.x - pos_agente.x
        dy = self.pos_farol.y - pos_agente.y

        # Detetar obstáculos nas direções adjacentes
        obstaculos_vizinhos = {}
        for direcao in [Direcao.NORTE, Direcao.SUL, Direcao.ESTE, Direcao.OESTE]:
            pos_vizinha = pos_agente.mover(direcao)
            obstaculos_vizinhos[direcao.name] = (
                    not self.posicao_valida(pos_vizinha) or
                    pos_vizinha in self.obstaculos
            )

        dados_obs = {
            'direcao_farol': (dx, dy),
            'distancia_farol': pos_agente.distancia(self.pos_farol),
            'obstaculos_vizinhos': obstaculos_vizinhos,
            'posicao_atual': (pos_agente.x, pos_agente.y),
            'no_farol': pos_agente == self.pos_farol
        }

        return Observacao(dados_obs, agente_id)

    def agir(self, accao: Acao, agente_id: str) -> float:
        if agente_id not in self.agentes:
            return 0.0

        agente = self.agentes[agente_id]
        pos_atual = agente['posicao']
        recompensa = 0.0

        if accao.tipo == "mover":
            direcao = accao.parametros.get('direcao', Direcao.PARADO)
            nova_pos = pos_atual.mover(direcao)

            # Verificar se movimento é válido
            if (self.posicao_valida(nova_pos) and
                    nova_pos not in self.obstaculos):

                agente['posicao'] = nova_pos
                agente['historico_posicoes'].append(nova_pos)

                # Recompensa baseada na aproximação ao farol
                dist_antiga = pos_atual.distancia(self.pos_farol)
                dist_nova = nova_pos.distancia(self.pos_farol)

                if dist_nova < dist_antiga:
                    recompensa = 2.0  # Recompensa maior por aproximação
                elif dist_nova > dist_antiga:
                    recompensa = -1.0  # Penalização maior por afastamento
                else:
                    recompensa = -0.1  # Pequena penalização por não progredir

                # Grande recompensa por alcançar o farol
                if nova_pos == self.pos_farol:
                    recompensa = 50.0  # Recompensa muito maior por chegar
                    if agente_id not in self.metricas['tempos_chegada']:
                        self.metricas['tempos_chegada'][agente_id] = self.passo_atual
                        self.metricas['agentes_no_farol'] += 1
            else:
                # Penalização por movimento inválido (obstáculo/parede)
                recompensa = -0.5  # Penalização maior para desencorajar

        return recompensa

    def atualizacao(self):
        self.passo_atual += 1

        # Mover farol e obstáculos periodicamente
        if self.passo_atual - self.ultimo_movimento >= self.intervalo_movimento:
            if self.mover_farol:
                self._mover_farol()
            if self.mover_obstaculos and self.com_obstaculos:
                self._mover_obstaculos()
            self.ultimo_movimento = self.passo_atual

        # Atualizar métricas de distâncias médias
        distancias = []
        for agente_id, info in self.agentes.items():
            pos = info['posicao']
            distancias.append(pos.distancia(self.pos_farol))

        if distancias:
            self.metricas['distancias_medias'].append(np.mean(distancias))

        # Condição de terminação: todos os agentes no farol
        if (len(self.agentes) > 0 and
                self.metricas['agentes_no_farol'] == len(self.agentes)):
            self.terminar_episodio()

    def reset(self):
        """Reinicia o ambiente para o estado inicial"""
        super().reset()
        
        # Restaurar posição inicial do farol
        self.pos_farol = Posicao(self.pos_farol_inicial.x, self.pos_farol_inicial.y)
        self.ultimo_movimento = 0
        
        # Regenerar obstáculos se necessário
        if self.com_obstaculos:
            self._gerar_obstaculos()
        
        # Reinicializar métricas específicas do AmbienteFarol
        self.metricas.update({
            'agentes_no_farol': 0,
            'distancias_medias': [],
            'tempos_chegada': {}
        })