"""
Ambiente de Foraging (Recoleção)
Agentes recolhem recursos e depositam em ninhos
"""

from ambiente import Ambiente, Posicao, Observacao, Direcao, Acao
import random
from typing import Dict, Set, List


class AmbienteForaging(Ambiente):
    """Ambiente de recolha de recursos (Foraging)"""
    
    def __init__(self, largura: int = 15, altura: int = 15,
                 num_recursos: int = 20, num_ninhos: int = 1,
                 com_obstaculos: bool = False):
        super().__init__(largura, altura)
        
        # Recursos: posição -> valor
        self.recursos: Dict[Posicao, int] = {}
        self.num_recursos = num_recursos
        
        # Ninhos (pontos de entrega)
        self.ninhos: List[Posicao] = []
        self.num_ninhos = num_ninhos
        
        # Obstáculos
        self.obstaculos: Set[Posicao] = set()
        self.com_obstaculos = com_obstaculos
        if com_obstaculos:
            self._gerar_obstaculos()
        
        # Gerar recursos e ninhos
        self._gerar_recursos()
        self._gerar_ninhos()
        
        # Métricas
        self.metricas.update({
            'recursos_coletados': 0,
            'recursos_depositados': 0,
            'valor_total_depositado': 0,
            'tempo_medio_coleta': 0
        })
    
    def _obter_posicoes_ocupadas(self) -> Set[Posicao]:
        """Retorna conjunto de posições ocupadas (recursos + ninhos + agentes)"""
        ocupadas = set()
        ocupadas.update(self.recursos.keys())
        ocupadas.update(self.ninhos)
        for agente_id, info in self.agentes.items():
            ocupadas.add(info['posicao'])
        return ocupadas
    
    def _gerar_obstaculos(self):
        """Gera obstáculos aleatórios, evitando recursos, ninhos e agentes"""
        posicoes_ocupadas = self._obter_posicoes_ocupadas()
        num_obstaculos = (self.largura * self.altura) // 15
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
    
    def _gerar_recursos(self):
        """Gera recursos aleatórios no ambiente"""
        self.recursos.clear()
        for _ in range(self.num_recursos):
            tentativas = 0
            while tentativas < 100:
                x = random.randint(0, self.largura - 1)
                y = random.randint(0, self.altura - 1)
                pos = Posicao(x, y)
                
                # Verificar se posição é válida (não é obstáculo, não tem recurso)
                if (pos not in self.obstaculos and 
                    pos not in self.recursos and
                    pos not in self.ninhos):
                    # Valor aleatório entre 1 e 5
                    self.recursos[pos] = random.randint(1, 5)
                    break
                tentativas += 1
    
    def _gerar_ninhos(self):
        """Gera ninhos (pontos de entrega)"""
        self.ninhos.clear()
        for _ in range(self.num_ninhos):
            tentativas = 0
            while tentativas < 100:
                # Ninhos geralmente nas bordas
                if random.random() < 0.5:
                    # Borda vertical
                    x = random.choice([0, self.largura - 1])
                    y = random.randint(0, self.altura - 1)
                else:
                    # Borda horizontal
                    x = random.randint(0, self.largura - 1)
                    y = random.choice([0, self.altura - 1])
                
                pos = Posicao(x, y)
                
                if (pos not in self.obstaculos and 
                    pos not in self.recursos and
                    pos not in self.ninhos):
                    self.ninhos.append(pos)
                    break
                tentativas += 1
        
        # Se não conseguiu gerar, colocar no centro
        if not self.ninhos:
            centro = Posicao(self.largura // 2, self.altura // 2)
            self.ninhos.append(centro)
    
    def observacao_para(self, agente_id: str) -> Observacao:
        """Retorna observação para o agente"""
        pos_agente = self.obter_posicao_agente(agente_id)
        if not pos_agente:
            return Observacao({}, agente_id)
        
        # Detectar recursos próximos
        recursos_proximos = []
        for recurso_pos, valor in self.recursos.items():
            dist = pos_agente.distancia(recurso_pos)
            if dist <= 2:  # Visão limitada
                recursos_proximos.append({
                    'posicao': (recurso_pos.x, recurso_pos.y),
                    'valor': valor,
                    'distancia': dist
                })
        
        # Detectar ninhos próximos
        ninhos_proximos = []
        for ninho_pos in self.ninhos:
            dist = pos_agente.distancia(ninho_pos)
            if dist <= 3:
                ninhos_proximos.append({
                    'posicao': (ninho_pos.x, ninho_pos.y),
                    'distancia': dist
                })
        
        # Detectar obstáculos vizinhos
        obstaculos_vizinhos = {}
        for direcao in [Direcao.NORTE, Direcao.SUL, Direcao.ESTE, Direcao.OESTE]:
            pos_vizinha = pos_agente.mover(direcao)
            obstaculos_vizinhos[direcao.name] = (
                not self.posicao_valida(pos_vizinha) or
                pos_vizinha in self.obstaculos
            )
        
        # Recursos carregados pelo agente
        recursos_carregados = self.agentes[agente_id].get('recursos', 0)
        
        dados_obs = {
            'posicao_atual': (pos_agente.x, pos_agente.y),
            'recursos_proximos': recursos_proximos,
            'ninhos_proximos': ninhos_proximos,
            'obstaculos_vizinhos': obstaculos_vizinhos,
            'recursos_carregados': recursos_carregados,
            'pode_recolher': pos_agente in self.recursos,
            'pode_depositar': pos_agente in self.ninhos and recursos_carregados > 0
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
                    nova_pos not in self.obstaculos):
                agente_info['posicao'] = nova_pos
                agente_info['historico_posicoes'].append(nova_pos)
                
                recursos_carregados = agente_info.get('recursos', 0)
                
                # Recompensa baseada no objetivo do agente
                # Se tem recurso, deve ir para ninho; se não tem, deve ir para recurso
                if recursos_carregados > 0:
                    # Tem recurso: recompensa maior se está se aproximando de um ninho
                    dist_ninho_min = min([pos_atual.distancia(ninho) for ninho in self.ninhos], default=float('inf'))
                    dist_ninho_nova = min([nova_pos.distancia(ninho) for ninho in self.ninhos], default=float('inf'))
                    if dist_ninho_nova < dist_ninho_min:
                        recompensa = 0.5  # Recompensa por aproximar-se do ninho
                    elif dist_ninho_nova > dist_ninho_min:
                        recompensa = -0.2  # Penalização por afastar-se do ninho
                    else:
                        recompensa = 0.01  # Pequena recompensa por movimento
                else:
                    # Não tem recurso: recompensa maior se está se aproximando de um recurso
                    if self.recursos:
                        dist_recurso_min = min([pos_atual.distancia(recurso) for recurso in self.recursos.keys()], default=float('inf'))
                        dist_recurso_nova = min([nova_pos.distancia(recurso) for recurso in self.recursos.keys()], default=float('inf'))
                        if dist_recurso_nova < dist_recurso_min:
                            recompensa = 0.5  # Recompensa por aproximar-se de recurso
                        elif dist_recurso_nova > dist_recurso_min:
                            recompensa = -0.1  # Pequena penalização por afastar-se
                        else:
                            recompensa = 0.01  # Pequena recompensa por movimento
                    else:
                        # Sem recursos disponíveis, recompensa mínima
                        recompensa = 0.01
            else:
                recompensa = -0.1  # Penalização por movimento inválido
        
        elif accao.tipo == "recolher":
            # Recolher recurso na posição atual
            if pos_atual in self.recursos:
                valor = self.recursos[pos_atual]
                recursos_carregados = agente_info.get('recursos', 0)
                
                # Agente pode carregar apenas 1 recurso por vez
                if recursos_carregados == 0:
                    agente_info['recursos'] = valor
                    del self.recursos[pos_atual]
                    recompensa = 2.0  # Recompensa por recolher
                    self.metricas['recursos_coletados'] += 1
                else:
                    recompensa = -0.5  # Penalização: já tem recurso
            else:
                recompensa = -0.2  # Penalização: não há recurso aqui
        
        elif accao.tipo == "depositar":
            # Depositar recurso no ninho
            if pos_atual in self.ninhos:
                recursos_carregados = agente_info.get('recursos', 0)
                if recursos_carregados > 0:
                    valor = recursos_carregados
                    agente_info['recursos'] = 0
                    recompensa = 5.0 + valor  # Recompensa base + valor do recurso
                    self.metricas['recursos_depositados'] += 1
                    self.metricas['valor_total_depositado'] += valor
                else:
                    recompensa = -0.3  # Penalização: não tem recurso para depositar
            else:
                recompensa = -0.2  # Penalização: não está no ninho
        
        return recompensa
    
    def atualizacao(self):
        """Atualiza o ambiente"""
        self.passo_atual += 1
        
        # NOTA: Recursos e obstáculos são regenerados apenas no reset do episódio
        # Não há mudanças durante a simulação
        
        # Condição de terminação: todos os recursos coletados e depositados
        # (ou tempo limite atingido - controlado externamente)
    
    def reset(self):
        """Reinicia o ambiente e regenera recursos, ninhos e obstáculos"""
        super().reset()
        
        # Regenerar recursos e ninhos (novas posições a cada episódio)
        self._gerar_recursos()
        self._gerar_ninhos()
        
        # Regenerar obstáculos se necessário (garantindo que não tapem recursos, ninhos nem agentes)
        if self.com_obstaculos:
            self._gerar_obstaculos()
        
        # Resetar métricas
        self.metricas.update({
            'recursos_coletados': 0,
            'recursos_depositados': 0,
            'valor_total_depositado': 0,
            'tempo_medio_coleta': 0
        })

