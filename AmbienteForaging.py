"""
Ambiente de Foraging (Recoleção)
Agentes recolhem recursos e depositam em ninhos
"""

from ambiente import Ambiente, Posicao, Observacao, Direcao, Acao
import random
from typing import Dict, Set, List
from collections import deque


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
        
        # Gerar ninhos primeiro (para validar acessibilidade)
        self._gerar_ninhos()
        
        # Gerar obstáculos (se habilitado)
        if com_obstaculos:
            self._gerar_obstaculos_validos()
        
        # Gerar recursos
        self._gerar_recursos_acessiveis()
        
        # Métricas
        self.metricas.update({
            'recursos_coletados': 0,
            'recursos_depositados': 0,
            'valor_total_depositado': 0,
            'tempo_medio_coleta': 0
        })
    
    def _gerar_obstaculos_validos(self):
        """Gera obstáculos garantindo acessibilidade aos ninhos"""
        num_obstaculos = (self.largura * self.altura) // 15
        obstaculos_gerados = 0
        tentativas = 0
        max_tentativas = num_obstaculos * 3
        
        while obstaculos_gerados < num_obstaculos and tentativas < max_tentativas:
            x = random.randint(0, self.largura - 1)
            y = random.randint(0, self.altura - 1)
            pos = Posicao(x, y)
            
            # Não colocar obstáculo em ninhos ou recursos
            if pos not in self.ninhos and pos not in self.recursos:
                # Testar se ainda há caminho para os ninhos
                self.obstaculos.add(pos)
                
                # Verificar se todos os ninhos ainda são acessíveis
                todos_acessiveis = True
                for ninho in self.ninhos:
                    if not self._posicao_acessivel(ninho):
                        todos_acessiveis = False
                        break
                
                if todos_acessiveis:
                    obstaculos_gerados += 1
                else:
                    # Remover obstáculo se bloqueou acesso
                    self.obstaculos.discard(pos)
            
            tentativas += 1
        
        print(f"   ✅ Foraging: {obstaculos_gerados} obstáculos gerados (acessíveis)")
    
    def _gerar_recursos_acessiveis(self):
        """Gera recursos aleatórios garantindo que são acessíveis"""
        self.recursos.clear()
        recursos_gerados = 0
        tentativas_totais = 0
        max_tentativas = self.num_recursos * 5
        
        while recursos_gerados < self.num_recursos and tentativas_totais < max_tentativas:
            x = random.randint(0, self.largura - 1)
            y = random.randint(0, self.altura - 1)
            pos = Posicao(x, y)
            
            # Verificar se posição é válida e acessível
            if (pos not in self.obstaculos and 
                pos not in self.recursos and
                pos not in self.ninhos and
                self._posicao_acessivel(pos)):
                # Valor aleatório entre 1 e 5
                self.recursos[pos] = random.randint(1, 5)
                recursos_gerados += 1
            
            tentativas_totais += 1
        
        if recursos_gerados < self.num_recursos:
            print(f"   ⚠️  Foraging: apenas {recursos_gerados}/{self.num_recursos} recursos gerados")
    
    def _posicao_acessivel(self, destino: Posicao) -> bool:
        """Verifica se uma posição é acessível a partir de qualquer ponto livre usando BFS"""
        # Começar de uma posição livre qualquer
        origem = None
        for x in range(self.largura):
            for y in range(self.altura):
                pos = Posicao(x, y)
                if (self.posicao_valida(pos) and 
                    pos not in self.obstaculos and
                    pos != destino):
                    origem = pos
                    break
            if origem:
                break
        
        if not origem:
            return True  # Se não há posições livres, aceitar
        
        # BFS da origem ao destino
        visitados = set()
        fila = deque([origem])
        visitados.add((origem.x, origem.y))
        
        while fila:
            pos_atual = fila.popleft()
            
            if pos_atual == destino:
                return True
            
            # Verificar vizinhos
            for direcao in [Direcao.NORTE, Direcao.SUL, Direcao.ESTE, Direcao.OESTE]:
                pos_vizinha = pos_atual.mover(direcao)
                pos_tuple = (pos_vizinha.x, pos_vizinha.y)
                
                if (self.posicao_valida(pos_vizinha) and
                    pos_vizinha not in self.obstaculos and
                    pos_tuple not in visitados):
                    
                    visitados.add(pos_tuple)
                    fila.append(pos_vizinha)
        
        return False
    
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
                recompensa = 0.01  # Pequena recompensa por movimento
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
        
        # Repor recursos periodicamente (a cada 50 passos)
        if self.passo_atual % 50 == 0 and len(self.recursos) < self.num_recursos:
            recursos_faltantes = self.num_recursos - len(self.recursos)
            for _ in range(min(recursos_faltantes, 5)):
                tentativas = 0
                while tentativas < 50:
                    x = random.randint(0, self.largura - 1)
                    y = random.randint(0, self.altura - 1)
                    pos = Posicao(x, y)
                    
                    if (pos not in self.obstaculos and 
                        pos not in self.recursos and
                        pos not in self.ninhos and
                        pos not in [info['posicao'] for info in self.agentes.values()]):
                        self.recursos[pos] = random.randint(1, 5)
                        break
                    tentativas += 1
        
        # Condição de terminação: todos os recursos coletados e depositados
        # (ou tempo limite atingido - controlado externamente)
    
    def reset(self):
        """Reinicia o ambiente"""
        super().reset()
        
        # Regenerar recursos (acessíveis)
        self._gerar_recursos_acessiveis()
        if not self.ninhos:
            self._gerar_ninhos()
        
        # Resetar métricas
        self.metricas.update({
            'recursos_coletados': 0,
            'recursos_depositados': 0,
            'valor_total_depositado': 0,
            'tempo_medio_coleta': 0
        })

