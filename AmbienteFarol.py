from ambiente import Ambiente, Posicao, Observacao, Direcao, Acao
from typing import Set
import numpy as np


class AmbienteFarol(Ambiente):
    """Ambiente do problema do Farol"""

    def __init__(self, largura: int = 10, altura: int = 10,
                 pos_farol: Posicao = None, com_obstaculos: bool = False):
        super().__init__(largura, altura)

        # Posição do farol (objetivo)
        self.pos_farol = pos_farol or Posicao(largura // 2, altura // 2)

        # Obstáculos (opcionais)
        self.obstaculos: Set[Posicao] = set()
        if com_obstaculos:
            self._gerar_obstaculos()

        # Métricas específicas
        self.metricas.update({
            'agentes_no_farol': 0,
            'distancias_medias': [],
            'tempos_chegada': {}
        })

    def _gerar_obstaculos(self):
        """Gera obstáculos aleatórios no ambiente"""
        num_obstaculos = (self.largura * self.altura) // 10
        for _ in range(num_obstaculos):
            x = np.random.randint(0, self.largura)
            y = np.random.randint(0, self.altura)
            pos = Posicao(x, y)
            if pos != self.pos_farol:
                self.obstaculos.add(pos)

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
                    recompensa = 1.0  # Recompensa maior por aproximação
                elif dist_nova > dist_antiga:
                    recompensa = -0.5  # Penalização maior por afastamento
                else:
                    recompensa = 0.1  # Pequena recompensa por explorar

                # Grande recompensa por alcançar o farol
                if nova_pos == self.pos_farol:
                    recompensa = 10.0
                    if agente_id not in self.metricas['tempos_chegada']:
                        self.metricas['tempos_chegada'][agente_id] = self.passo_atual
                        self.metricas['agentes_no_farol'] += 1
            else:
                # Penalização por movimento inválido (obstáculo/parede)
                recompensa = -0.2

        return recompensa

    def atualizacao(self):
        self.passo_atual += 1

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
        # Reinicializar métricas específicas do AmbienteFarol
        self.metricas.update({
            'agentes_no_farol': 0,
            'distancias_medias': [],
            'tempos_chegada': {}
        })