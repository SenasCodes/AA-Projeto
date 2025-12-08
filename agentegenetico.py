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
            
            # Calcular novidade
            agente.calculate_novelty(self.arquivo, self.k_vizinhos)
            
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
            
            # Ambiente processa
            obs, recompensa, terminado = self.ambiente.processar_acao(acao)
            
            # Agente recebe observação
            agente.observacao(obs, recompensa)
            
            if terminado:
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
