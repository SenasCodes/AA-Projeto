"""
Ambiente de Labirinto
Agentes devem encontrar o caminho do início ao fim
"""

from ambiente import Ambiente, Posicao, Observacao, Direcao, Acao
import random
from typing import Set, List, Dict, Tuple


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
        """Gera um labirinto tradicional usando algoritmo de backtracking"""
        # Inicializar: começar com todas as células como paredes
        self.paredes.clear()
        caminhos = set()  # Células que são caminhos (não paredes)
        
        # Garantir que início e fim são caminhos
        caminhos.add(self.pos_inicio)
        caminhos.add(self.pos_fim)
        
        # Usar algoritmo de backtracking para criar labirinto
        visitadas = set()
        pilha = []
        
        # Começar do início
        celula_atual = self.pos_inicio
        visitadas.add(celula_atual)
        caminhos.add(celula_atual)
        
        # Direções possíveis
        direcoes = [Direcao.NORTE, Direcao.SUL, Direcao.ESTE, Direcao.OESTE]
        
        # Criar labirinto usando backtracking
        # Para labirintos pequenos, usar passo de 1; para maiores, passo de 2
        passo = 2 if min(self.largura, self.altura) > 6 else 1
        
        while True:
            # Encontrar células vizinhas não visitadas
            vizinhas_nao_visitadas = []
            for direcao in direcoes:
                # Mover N células na direção
                dx, dy = direcao.value
                vizinha = Posicao(celula_atual.x + passo*dx, celula_atual.y + passo*dy)
                
                if (self.posicao_valida(vizinha) and 
                    vizinha not in visitadas):
                    vizinhas_nao_visitadas.append((vizinha, direcao))
            
            if vizinhas_nao_visitadas:
                # Escolher uma direção aleatória
                vizinha, direcao = random.choice(vizinhas_nao_visitadas)
                
                # Adicionar células intermediárias como caminhos
                dx, dy = direcao.value
                for i in range(1, passo + 1):
                    celula_intermedia = Posicao(celula_atual.x + i*dx, celula_atual.y + i*dy)
                    if self.posicao_valida(celula_intermedia):
                        caminhos.add(celula_intermedia)
                
                # Marcar como visitada e adicionar aos caminhos
                visitadas.add(vizinha)
                caminhos.add(vizinha)
                
                # Adicionar à pilha e continuar
                pilha.append(celula_atual)
                celula_atual = vizinha
            elif pilha:
                # Backtrack
                celula_atual = pilha.pop()
            else:
                break
        
        # Adicionar algumas células aleatórias como caminhos para tornar mais interessante
        # Mas garantir que não bloqueie o caminho principal
        num_caminhos_extras = max(0, int(self.largura * self.altura * 0.15) - len(caminhos))
        tentativas = 0
        caminhos_adicionados = 0
        
        while caminhos_adicionados < num_caminhos_extras and tentativas < 2000:
            x = random.randint(0, self.largura - 1)
            y = random.randint(0, self.altura - 1)
            pos = Posicao(x, y)
            if pos not in caminhos and pos != self.pos_inicio and pos != self.pos_fim:
                caminhos.add(pos)
                caminhos_adicionados += 1
            tentativas += 1
        
        # Todas as células que não são caminhos são paredes
        for x in range(self.largura):
            for y in range(self.altura):
                pos = Posicao(x, y)
                if pos not in caminhos:
                    self.paredes.add(pos)
        
        # Garantir caminho do início ao fim
        if not self._verificar_caminho(self.pos_inicio, self.pos_fim):
            # Se não há caminho, criar um caminho garantido
            self._criar_caminho_garantido()
    
    def _verificar_caminho(self, inicio: Posicao, fim: Posicao) -> bool:
        """Verifica se existe caminho do início ao fim usando BFS"""
        if inicio == fim:
            return True
        
        fila = [inicio]
        visitadas = {inicio}
        direcoes = [Direcao.NORTE, Direcao.SUL, Direcao.ESTE, Direcao.OESTE]
        
        while fila:
            atual = fila.pop(0)
            
            for direcao in direcoes:
                dx, dy = direcao.value
                proxima = Posicao(atual.x + dx, atual.y + dy)
                
                if proxima == fim:
                    return True
                
                if (self.posicao_valida(proxima) and 
                    proxima not in visitadas and
                    proxima not in self.paredes):
                    visitadas.add(proxima)
                    fila.append(proxima)
        
        return False
    
    def _criar_caminho_garantido(self):
        """Cria um caminho garantido do início ao fim"""
        # Criar caminho usando algoritmo simples
        atual = self.pos_inicio
        
        # Caminho em L: primeiro horizontal, depois vertical
        # Ou primeiro vertical, depois horizontal
        if random.random() < 0.5:
            # Primeiro horizontal, depois vertical
            while atual.x < self.pos_fim.x:
                self.paredes.discard(atual)
                atual = Posicao(atual.x + 1, atual.y)
            
            while atual.y < self.pos_fim.y:
                self.paredes.discard(atual)
                atual = Posicao(atual.x, atual.y + 1)
        else:
            # Primeiro vertical, depois horizontal
            while atual.y < self.pos_fim.y:
                self.paredes.discard(atual)
                atual = Posicao(atual.x, atual.y + 1)
            
            while atual.x < self.pos_fim.x:
                self.paredes.discard(atual)
                atual = Posicao(atual.x + 1, atual.y)
        
        # Garantir que fim está acessível
        self.paredes.discard(self.pos_fim)
    
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
        
        # Verificar se agente já chegou ao objetivo
        ja_chegou = agente_id in self.metricas['tempos_chegada']
        
        if accao.tipo == "mover":
            direcao = accao.parametros.get('direcao', Direcao.PARADO)
            nova_pos = pos_atual.mover(direcao)
            
            # Se já chegou, não dar recompensas por ficar parado ou se mover
            if ja_chegou:
                # Se está no fim e tenta sair, pequena penalização
                if pos_atual == self.pos_fim and nova_pos != self.pos_fim:
                    recompensa = -0.1  # Pequena penalização por sair do objetivo
                else:
                    # Se já chegou, recompensa zero (ou muito pequena negativa para desencorajar movimento)
                    recompensa = -0.01 if nova_pos != pos_atual else 0.0
                agente_info['posicao'] = nova_pos
                return recompensa
            
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
                
                # Recompensa por alcançar o fim (escalonada)
                if nova_pos == self.pos_fim:
                    # Contar quantos agentes já chegaram
                    num_ja_chegaram = self.metricas['agentes_no_fim']
                    # Recompensa base reduzida e escalonada
                    recompensa_base = 15.0
                    # Bonus por chegar primeiro
                    bonus_primeiro = 5.0 if num_ja_chegaram == 0 else 0.0
                    # Penalização progressiva para quem chega depois
                    penalizacao_ordem = num_ja_chegaram * 1.5
                    recompensa = recompensa_base + bonus_primeiro - penalizacao_ordem
                    
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

