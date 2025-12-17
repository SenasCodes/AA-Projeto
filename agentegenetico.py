"""
Módulo de Agente Genético - Algoritmo Genético com Novelty Search
Implementa evolução de populações com busca por novidade
"""

from typing import Dict, Any, List, Set, Tuple
import random
from agente import Agente
from ambiente import Observacao, Acao, Direcao, Posicao


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
        self.taxa_mutacao = parametros.get('taxa_mutacao', 0.05) if parametros else 0.05
        
        # Garantir que num_steps está definido
        if not hasattr(self, 'num_steps') or self.num_steps is None:
            self.num_steps = parametros.get('num_steps', 100) if parametros else 100
        
        # Gerar genótipo aleatório se não fornecido
        if self.genotype is None:
            self.genotype = [random.choice(self.acoes_disponiveis) for _ in range(self.num_steps)]
        
        self.passo_atual = 0
        
        # Métricas específicas do genético
        self.recursos_coletados = 0
        self.objetivos_alcancados = 0
        
        # Histórico de desempenho para evolução
        self.historico_fitness: List[float] = []
        self.episodio_atual = 0
        self.melhor_fitness = float('-inf')
        self.genotipo_melhor = None
    
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
    
    def avaliacaoEstadoAtual(self, recompensa: float = None) -> float:
        """
        Avalia estado atual e rastreia objetivos alcançados
        
        Args:
            recompensa: Recompensa recebida
            
        Returns:
            Fitness total
        """
        # Chamar método da classe base
        fitness = super().avaliacaoEstadoAtual(recompensa)
        
        # Rastrear objetivos alcançados (baseado em recompensas altas de chegada)
        # Com as novas recompensas escalonadas, threshold ajustado
        if recompensa is not None and recompensa >= 8.0:  # Recompensa de chegada
            self.objetivos_alcancados += 1
        
        return fitness
    
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
    
    def mutate(self, taxa_mutacao: float):
        """
        Aplica mutação ao genótipo
        
        Args:
            taxa_mutacao: Probabilidade de mutação por gene
        """
        for i in range(len(self.genotype)):
            if random.random() < taxa_mutacao:
                self.genotype[i] = random.choice(self.acoes_disponiveis)
    
    @property
    def combined_fitness(self) -> float:
        """Retorna fitness combinado (novidade + objetivo)"""
        return self.fitness_total
    
    @combined_fitness.setter
    def combined_fitness(self, value: float):
        """Define fitness combinado"""
        self.fitness_total = value
    
    def reset(self):
        """Reinicia o agente incluindo o contador de passos"""
        super().reset()
        self.passo_atual = 0
        self.recursos_coletados = 0
        self.objetivos_alcancados = 0
    
    def fim_episodio(self):
        """
        Chamado no final de cada episódio
        Calcula fitness e evolui o genótipo se necessário
        """
        self.episodio_atual += 1
        
        # Calcular fitness objetivo
        self.calculate_objective_fitness()
        fitness_atual = self.objective_fitness
        
        # Guardar histórico
        self.historico_fitness.append(fitness_atual)
        
        # Atualizar melhor genótipo
        if fitness_atual > self.melhor_fitness:
            self.melhor_fitness = fitness_atual
            self.genotipo_melhor = self.genotype.copy()
        
        # Evoluir genótipo baseado no desempenho
        self._evoluir_genotipo()
    
    def _evoluir_genotipo(self):
        """
        Evolui o genótipo baseado no desempenho
        Usa estratégia simples: mutação adaptativa + elitismo
        """
        # Se não há histórico suficiente, não evolui
        if len(self.historico_fitness) < 2:
            return
        
        # Calcular média de fitness dos últimos episódios
        episodios_recentes = min(5, len(self.historico_fitness))
        fitness_medio = sum(self.historico_fitness[-episodios_recentes:]) / episodios_recentes
        fitness_atual = self.historico_fitness[-1]
        
        # Se desempenho está piorando, aumentar mutação
        if len(self.historico_fitness) >= 3:
            fitness_anterior = self.historico_fitness[-2]
            if fitness_atual < fitness_anterior:
                # Aumentar taxa de mutação temporariamente
                taxa_mutacao_adaptativa = self.taxa_mutacao * 2.0
            else:
                taxa_mutacao_adaptativa = self.taxa_mutacao
        else:
            taxa_mutacao_adaptativa = self.taxa_mutacao
        
        # Se fitness atual está abaixo da média, aplicar mutação mais agressiva
        if fitness_atual < fitness_medio:
            # Mutação mais agressiva: 30% dos genes
            num_mutacoes = max(1, int(len(self.genotype) * 0.3))
            indices = random.sample(range(len(self.genotype)), min(num_mutacoes, len(self.genotype)))
            for i in indices:
                self.genotype[i] = random.choice(self.acoes_disponiveis)
        else:
            # Mutação normal
            self.mutate(taxa_mutacao_adaptativa)
        
        # Elitismo: se fitness caiu muito, restaurar melhor genótipo
        if self.genotipo_melhor and fitness_atual < self.melhor_fitness * 0.5:
            # Restaurar 50% do melhor genótipo
            # Garantir que genotipo_melhor tem tamanho compatível
            tamanho_atual = len(self.genotype)
            tamanho_melhor = len(self.genotipo_melhor)
            
            if tamanho_melhor > 0:
                # Usar o tamanho mínimo para evitar index out of range
                tamanho_usar = min(tamanho_atual, tamanho_melhor)
                num_genes_restaurar = tamanho_usar // 2
                
                if num_genes_restaurar > 0:
                    indices = random.sample(range(tamanho_usar), num_genes_restaurar)
                    for i in indices:
                        if i < len(self.genotype) and i < len(self.genotipo_melhor):
                            self.genotype[i] = self.genotipo_melhor[i]
        
        # Ajustar tamanho do genótipo se necessário (crescer se muito curto)
        if self.passo_atual >= len(self.genotype) - 5 and len(self.historico_fitness) % 10 == 0:
            # Adicionar mais genes se genótipo está muito curto
            genes_extras = [random.choice(self.acoes_disponiveis) for _ in range(10)]
            self.genotype.extend(genes_extras)


# Alias para compatibilidade (AgenteGenetico = AgenteEvolucionario)
AgenteGenetico = AgenteEvolucionario


# --- Funções Auxiliares para Evolução ---

def crossover(parent1: AgenteEvolucionario, parent2: AgenteEvolucionario) -> Tuple[AgenteEvolucionario, AgenteEvolucionario]:
    """
    Realiza crossover de dois pontos entre dois pais
    
    Args:
        parent1: Primeiro pai
        parent2: Segundo pai
        
    Returns:
        Tupla com dois filhos
    """
    if len(parent1.genotype) < 2:
        # Genótipo muito pequeno, retornar clones
        return parent1.clonar(f"{parent1.agente_id}_child1"), parent2.clonar(f"{parent2.agente_id}_child2")
    
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


def selecao_torneio(populacao: List[AgenteEvolucionario], tamanho_torneio: int = 3) -> AgenteEvolucionario:
    """
    Seleciona um pai usando seleção por torneio baseada em fitness combinado
    
    Args:
        populacao: População de agentes
        tamanho_torneio: Tamanho do torneio
        
    Returns:
        Agente selecionado
    """
    if len(populacao) < tamanho_torneio:
        tamanho_torneio = len(populacao)
    
    torneio = random.sample(populacao, tamanho_torneio)
    torneio.sort(key=lambda x: x.combined_fitness, reverse=True)
    return torneio[0]


class PopulacaoEvolucionaria:
    """
    Gerencia uma população de agentes evolucionários com Novelty Search
    
    Características:
    - Avaliação de fitness combinado (novidade + objetivo)
    - Seleção por torneio
    - Crossover e mutação
    - Elitismo
    - Arquivo de comportamentos
    """
    
    def __init__(self, ambiente, parametros: Dict[str, Any] = None):
        """
        Inicializa população evolucionária
        
        Args:
            ambiente: Instância do ambiente para simulação
            parametros: Parâmetros da evolução
        """
        parametros = parametros or {}
        
        self.ambiente = ambiente
        self.tamanho_populacao = parametros.get('tamanho_populacao', 50)
        self.num_geracoes = parametros.get('num_geracoes', 30)
        self.num_steps = parametros.get('num_steps', 100)
        
        # Parâmetros evolutivos
        self.taxa_mutacao = parametros.get('taxa_mutacao', 0.05)
        self.taxa_crossover = parametros.get('taxa_crossover', 0.8)
        self.tamanho_torneio = parametros.get('tamanho_torneio', 5)
        self.taxa_elitismo = parametros.get('taxa_elitismo', 0.1)
        
        # Parâmetros de Novelty Search
        self.k_vizinhos = parametros.get('k_vizinhos', 15)
        self.peso_novidade = parametros.get('peso_novidade', 0.7)
        
        # População e arquivo
        self.populacao: List[AgenteEvolucionario] = []
        self.arquivo: List[Set[Tuple[int, int]]] = []
        self.geracao_atual = 0
        
        # Estatísticas
        self.fitness_total_media: List[float] = []
        self.fitness_total_maximo: List[float] = []
        self.novidade_media: List[float] = []
        self.objetivo_medio: List[float] = []
        self.diversidade_comportamental: List[int] = []
        
        # Inicializar população
        self._inicializar_populacao()
    
    def _inicializar_populacao(self):
        """Cria população inicial com genótipos aleatórios"""
        self.populacao = []
        for i in range(self.tamanho_populacao):
            agente = AgenteEvolucionario(
                f"gen_{i}",
                {
                    'num_steps': self.num_steps,
                    'taxa_mutacao': self.taxa_mutacao
                }
            )
            self.populacao.append(agente)
    
    def evoluir(self):
        """
        Executa o processo completo de evolução
        """
        print(f"\nIniciando evolução de {self.num_geracoes} gerações...")
        print(f"População: {self.tamanho_populacao} | Peso Novidade: {self.peso_novidade}")
        print("-" * 60)
        
        for geracao in range(self.num_geracoes):
            self.geracao_atual = geracao
            self._evoluir_geracao()
            
            # Log progresso
            if (geracao + 1) % 5 == 0 or geracao == 0:
                stats = self.obter_estatisticas()
                print(f"Geração {geracao+1:3d} | "
                      f"Fitness: {stats['fitness_total_medio']:6.1f} (max: {stats['fitness_total_max']:6.1f}) | "
                      f"Novidade: {stats['novidade_media']:5.2f} | "
                      f"Diversidade: {stats['diversidade']}")
        
        print("-" * 60)
        print(f"Evolução concluída! Arquivo: {len(self.arquivo)} comportamentos")
    
    def _evoluir_geracao(self):
        """Evolui uma geração completa"""
        # 1. Avaliar população
        self._avaliar_populacao()
        
        # 2. Ordenar por fitness combinado
        self.populacao.sort(key=lambda x: x.combined_fitness, reverse=True)
        
        # 3. Registar estatísticas
        self._registar_estatisticas()
        
        # 4. Atualizar arquivo com comportamentos mais novos
        self._atualizar_arquivo()
        
        # 5. Criar nova geração
        self._criar_nova_geracao()
    
    def _avaliar_populacao(self):
        """Avalia fitness de todos os indivíduos"""
        for agente in self.populacao:
            # Resetar agente
            agente.reset()
            
            # Simular no ambiente
            self._simular_agente(agente)
            
            # Calcular fitness objetivo
            agente.calculate_objective_fitness()
            
            # Calcular novidade (usando arquivo de comportamentos)
            if self.arquivo and agente.behavior:
                # Calcular distância média aos k vizinhos mais próximos no arquivo
                distancias = []
                for comportamento_arquivo in self.arquivo:
                    dist = agente._jaccard_distance(agente.behavior, comportamento_arquivo)
                    distancias.append(dist)
                
                if distancias:
                    k_proximos = sorted(distancias)[:min(self.k_vizinhos, len(distancias))]
                    agente.novelty_score = sum(k_proximos) / len(k_proximos) if k_proximos else 0.0
                else:
                    agente.novelty_score = 1.0  # Comportamento único se arquivo vazio
            elif agente.behavior:
                agente.novelty_score = 1.0  # Primeiro comportamento é sempre novo
            else:
                agente.novelty_score = 0.0
            
            # Fitness combinado
            agente.combined_fitness = (
                agente.novelty_score * self.peso_novidade +
                agente.objective_fitness * (1.0 - self.peso_novidade)
            )
    
    def _simular_agente(self, agente: AgenteEvolucionario):
        """
        Simula um agente no ambiente
        
        Args:
            agente: Agente a simular
        """
        # Reset ambiente
        self.ambiente.reset()
        
        # Instalar agente
        obs_inicial = agente.instala(self.ambiente)
        
        # Executar passos
        for passo in range(agente.num_steps):
            # Agente decide ação
            acao = agente.age()
            acao.agente_id = agente.agente_id
            
            # Ambiente processa ação
            recompensa = self.ambiente.agir(acao, agente.agente_id)
            
            # Obter nova observação
            obs = self.ambiente.observacao_para(agente.agente_id)
            
            # Agente recebe observação
            agente.observacao(obs, recompensa)
            
            # Atualizar ambiente
            self.ambiente.atualizacao()
            
            if self.ambiente.terminado:
                break
    
    def _registar_estatisticas(self):
        """Registra estatísticas da geração atual"""
        fitness_totais = [a.combined_fitness for a in self.populacao]
        novidades = [a.novelty_score for a in self.populacao]
        objetivos = [a.objective_fitness for a in self.populacao]
        
        self.fitness_total_media.append(sum(fitness_totais) / len(fitness_totais))
        self.fitness_total_maximo.append(max(fitness_totais))
        self.novidade_media.append(sum(novidades) / len(novidades))
        self.objetivo_medio.append(sum(objetivos) / len(objetivos))
        
        # Diversidade: número de comportamentos únicos
        behaviors_unicos = set()
        for agente in self.populacao:
            behaviors_unicos.add(frozenset(agente.behavior))
        self.diversidade_comportamental.append(len(behaviors_unicos))
    
    def _atualizar_arquivo(self):
        """Adiciona melhores comportamentos ao arquivo"""
        # Ordenar por novelty puro
        pop_ordenada_novelty = sorted(
            self.populacao,
            key=lambda x: x.novelty_score,
            reverse=True
        )
        
        # Adicionar top N ao arquivo
        n_adicionar = min(5, len(pop_ordenada_novelty))
        for i in range(n_adicionar):
            self.arquivo.append(pop_ordenada_novelty[i].behavior.copy())
    
    def _criar_nova_geracao(self):
        """Cria nova geração através de seleção, crossover e mutação"""
        nova_populacao: List[AgenteEvolucionario] = []
        
        # Elitismo: manter melhores
        num_elite = int(self.tamanho_populacao * self.taxa_elitismo)
        elite = self.populacao[:num_elite]
        nova_populacao.extend([ag.clonar(f"{ag.agente_id}_elite") for ag in elite])
        
        # Breeding: preencher resto da população
        while len(nova_populacao) < self.tamanho_populacao:
            # Seleção
            parent1 = selecao_torneio(self.populacao, self.tamanho_torneio)
            parent2 = selecao_torneio(self.populacao, self.tamanho_torneio)
            
            # Crossover
            if random.random() < self.taxa_crossover:
                child1, child2 = crossover(parent1, parent2)
            else:
                child1 = parent1.clonar(f"{parent1.agente_id}_clone")
                child2 = parent2.clonar(f"{parent2.agente_id}_clone")
            
            # Mutação
            child1.mutate(self.taxa_mutacao)
            child2.mutate(self.taxa_mutacao)
            
            # Adicionar à nova população
            nova_populacao.append(child1)
            if len(nova_populacao) < self.tamanho_populacao:
                nova_populacao.append(child2)
        
        # Atualizar população
        self.populacao = nova_populacao[:self.tamanho_populacao]
    
    def obter_melhor_agente(self) -> AgenteEvolucionario:
        """
        Retorna o melhor agente da população atual
        
        Returns:
            Melhor agente
        """
        return max(self.populacao, key=lambda x: x.combined_fitness)
    
    def obter_estatisticas(self) -> Dict[str, Any]:
        """
        Retorna estatísticas da evolução
        
        Returns:
            Dicionário com estatísticas
        """
        return {
            'geracao_atual': self.geracao_atual,
            'fitness_total_medio': self.fitness_total_media[-1] if self.fitness_total_media else 0,
            'fitness_total_max': self.fitness_total_maximo[-1] if self.fitness_total_maximo else 0,
            'novidade_media': self.novidade_media[-1] if self.novidade_media else 0,
            'objetivo_medio': self.objetivo_medio[-1] if self.objetivo_medio else 0,
            'diversidade': self.diversidade_comportamental[-1] if self.diversidade_comportamental else 0,
            'tamanho_arquivo': len(self.arquivo),
            'fitness_total_media': self.fitness_total_media,
            'fitness_total_maximo': self.fitness_total_maximo,
            'novidade_media': self.novidade_media,
            'objetivo_medio': self.objetivo_medio,
            'diversidade_comportamental': self.diversidade_comportamental
        }
    
    def visualizar_evolucao(self):
        """Visualiza a evolução usando matplotlib"""
        try:
            import matplotlib.pyplot as plt
            
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            
            # Fitness total
            axes[0, 0].plot(self.fitness_total_media, label='Média')
            axes[0, 0].plot(self.fitness_total_maximo, label='Máximo', linestyle='--')
            axes[0, 0].set_title('Fitness Total')
            axes[0, 0].set_xlabel('Geração')
            axes[0, 0].set_ylabel('Fitness')
            axes[0, 0].legend()
            axes[0, 0].grid(True, alpha=0.3)
            
            # Novidade vs Objetivo
            axes[0, 1].plot(self.novidade_media, label='Novidade')
            axes[0, 1].plot(self.objetivo_medio, label='Objetivo')
            axes[0, 1].set_title('Novidade vs Objetivo')
            axes[0, 1].set_xlabel('Geração')
            axes[0, 1].set_ylabel('Score')
            axes[0, 1].legend()
            axes[0, 1].grid(True, alpha=0.3)
            
            # Diversidade
            axes[1, 0].plot(self.diversidade_comportamental, color='green')
            axes[1, 0].set_title('Diversidade Comportamental')
            axes[1, 0].set_xlabel('Geração')
            axes[1, 0].set_ylabel('Comportamentos Únicos')
            axes[1, 0].grid(True, alpha=0.3)
            
            # Arquivo
            axes[1, 1].plot(range(len(self.arquivo)), label='Tamanho Arquivo')
            axes[1, 1].set_title('Crescimento do Arquivo')
            axes[1, 1].set_xlabel('Adições')
            axes[1, 1].set_ylabel('Tamanho')
            axes[1, 1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig('evolucao_genetica.png', dpi=150, bbox_inches='tight')
            print("\nGráfico salvo: evolucao_genetica.png")
            plt.show()
            
        except ImportError:
            print("matplotlib não disponível. Instale com: pip install matplotlib")
