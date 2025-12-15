"""
Ambiente de Labirinto
Agentes devem encontrar o caminho do início ao fim
"""

from ambiente import Ambiente, Posicao, Observacao, Direcao, Acao
import random
from typing import Set, List, Dict


class AmbienteLabirinto(Ambiente):
    """Ambiente de labirinto com paredes"""
    
    def __init__(self, largura: int = 10, altura: int = 10,
                 densidade_paredes: float = 0.3,
                 pos_inicio: Posicao = None,
                 pos_fim: Posicao = None):
        super().__init__(largura, altura)
        
        self.densidade_paredes = densidade_paredes
        
        # Posições de início e fim
        if pos_inicio:
            self.pos_inicio = pos_inicio
        else:
            # Canto superior esquerdo
            self.pos_inicio = Posicao(0, 0)
        
        if pos_fim:
            self.pos_fim = pos_fim
        else:
            # Canto inferior direito
            self.pos_fim = Posicao(largura - 1, altura - 1)
        
        # Paredes
        self.paredes: Set[Posicao] = set()
        self._gerar_paredes()
        
        # Garantir que início e fim não são paredes e são acessíveis
        self.paredes.discard(self.pos_inicio)
        self.paredes.discard(self.pos_fim)
        
        # Métricas
        self.metricas.update({
            'agentes_no_fim': 0,
            'tempos_chegada': {},
            'caminhos_encontrados': 0
        })
    
    def _gerar_paredes(self):
        """Gera paredes aleatórias no labirinto"""
        num_paredes = int(self.largura * self.altura * self.densidade_paredes)
        
        for _ in range(num_paredes):
            x = random.randint(0, self.largura - 1)
            y = random.randint(0, self.altura - 1)
            pos = Posicao(x, y)
            
            # Não colocar parede no início ou fim
            if pos != self.pos_inicio and pos != self.pos_fim:
                self.paredes.add(pos)
    
    def observacao_para(self, agente_id: str) -> Observacao:
        """Retorna observação para o agente"""
        pos_agente = self.obter_posicao_agente(agente_id)
        if not pos_agente:
            return Observacao({}, agente_id)
        
        # Direção para o fim
        dx = self.pos_fim.x - pos_agente.x
        dy = self.pos_fim.y - pos_agente.y
        
        # Distância ao fim
        distancia_fim = pos_agente.distancia(self.pos_fim)
        
        # Detectar paredes/obstáculos nas direções adjacentes
        obstaculos_vizinhos = {}
        for direcao in [Direcao.NORTE, Direcao.SUL, Direcao.ESTE, Direcao.OESTE]:
            pos_vizinha = pos_agente.mover(direcao)
            obstaculos_vizinhos[direcao.name] = (
                not self.posicao_valida(pos_vizinha) or
                pos_vizinha in self.paredes
            )
        
        # Verificar se chegou ao fim
        no_fim = pos_agente == self.pos_fim
        
        dados_obs = {
            'posicao_atual': (pos_agente.x, pos_agente.y),
            'direcao_fim': (dx, dy),
            'distancia_fim': distancia_fim,
            'obstaculos_vizinhos': obstaculos_vizinhos,
            'no_fim': no_fim,
            'pos_inicio': (self.pos_inicio.x, self.pos_inicio.y),
            'pos_fim': (self.pos_fim.x, self.pos_fim.y)
        }
        
        return Observacao(dados_obs, agente_id)
    
    def agir(self, accao: Acao, agente_id: str) -> float:
        """Executa ação do agente"""
        if agente_id not in self.agentes:
            return 0.0
        
        agente_info = self.agentes[agente_id]
        pos_atual = agente_info['posicao']
        recompensa = 0.0
        
        if accao.tipo == "mover":
            direcao = accao.parametros.get('direcao', Direcao.PARADO)
            nova_pos = pos_atual.mover(direcao)
            
            # Verificar se movimento é válido
            if (self.posicao_valida(nova_pos) and
                    nova_pos not in self.paredes):
                
                # Calcular recompensa baseada na aproximação ao fim
                dist_antiga = pos_atual.distancia(self.pos_fim)
                dist_nova = nova_pos.distancia(self.pos_fim)
                
                agente_info['posicao'] = nova_pos
                agente_info['historico_posicoes'].append(nova_pos)
                
                if dist_nova < dist_antiga:
                    recompensa = 2.0  # Recompensa maior por aproximação
                elif dist_nova > dist_antiga:
                    recompensa = -1.0  # Penalização maior por afastamento
                else:
                    recompensa = -0.1  # Pequena penalização por não progredir
                
                # Grande recompensa por alcançar o fim
                if nova_pos == self.pos_fim:
                    recompensa = 100.0  # Recompensa muito maior
                    if agente_id not in self.metricas['tempos_chegada']:
                        self.metricas['tempos_chegada'][agente_id] = self.passo_atual
                        self.metricas['agentes_no_fim'] += 1
                        self.metricas['caminhos_encontrados'] += 1
            else:
                # Penalização por movimento inválido (parede)
                recompensa = -0.5  # Penalização maior
        
        return recompensa
    
    def atualizacao(self):
        """Atualiza o ambiente"""
        self.passo_atual += 1
        
        # Condição de terminação: todos os agentes no fim
        if (len(self.agentes) > 0 and
                self.metricas['agentes_no_fim'] == len(self.agentes)):
            self.terminar_episodio()
    
    def reset(self):
        """Reinicia o ambiente"""
        super().reset()
        
        # Regenerar paredes
        self.paredes.clear()
        self._gerar_paredes()
        self.paredes.discard(self.pos_inicio)
        self.paredes.discard(self.pos_fim)
        
        # Resetar métricas
        self.metricas.update({
            'agentes_no_fim': 0,
            'tempos_chegada': {},
            'caminhos_encontrados': 0
        })

