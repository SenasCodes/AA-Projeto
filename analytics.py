# analytics.py
"""
Módulo simples para visualização de gráficos em janelas após simulações
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import List
import sys

class VisualizadorResultados:
    """Visualiza resultados das simulações em janelas gráficas"""

    def __init__(self):
        plt.style.use('seaborn-v0_8-darkgrid')
        self.figuras = []

    def mostrar_menu(self) -> str:
        """Mostra menu simples de opções"""
        print("\n" + "="*60)
        print("📊 VISUALIZAÇÃO DE RESULTADOS")
        print("="*60)
        print("\nEscolha os gráficos a visualizar:")
        print("  1. Curva de Aprendizagem (evolução por episódio)")
        print("  2. Comparação entre Agentes")
        print("  3. Evolução do Epsilon (Q-Learning)")
        print("  4. Todos os gráficos em sequência")
        print("  5. Sair")

        return input("\nOpção (1-5): ").strip()

    def plotar_curva_aprendizagem(self, motor):
        """Mostra curva de aprendizagem"""
        if not hasattr(motor, 'historico_episodios') or not motor.historico_episodios:
            print("⚠️ Sem dados de episódios para mostrar curva de aprendizagem")
            return

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        fig.suptitle('📈 CURVA DE APRENDIZAGEM', fontsize=14, fontweight='bold')

        # Dados dos episódios
        episodios = motor.historico_episodios
        recompensas = [e['recompensa_total'] for e in episodios]
        passos = [e['passos'] for e in episodios]

        # Gráfico 1: Recompensa
        ax1.plot(range(len(recompensas)), recompensas, 'b-', linewidth=2, marker='o', markersize=4)
        ax1.set_xlabel('Episódio')
        ax1.set_ylabel('Recompensa Total')
        ax1.set_title('Recompensa por Episódio')
        ax1.grid(True, alpha=0.3)

        # Linha de média móvel
        if len(recompensas) > 5:
            media_movel = pd.Series(recompensas).rolling(5).mean()
            ax1.plot(range(len(media_movel)), media_movel, 'r--', linewidth=2, label='Média (5)')
            ax1.legend()

        # Gráfico 2: Passos
        ax2.plot(range(len(passos)), passos, 'g-', linewidth=2, marker='s', markersize=4)
        ax2.set_xlabel('Episódio')
        ax2.set_ylabel('Passos')
        ax2.set_title('Passos por Episódio')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()

    def plotar_comparacao_agentes(self, motor):
        """Compara desempenho dos agentes baseado no modo de operação"""
        if not motor.agentes:
            print("⚠️ Nenhum agente para comparar")
            return

        # Determinar modo de operação
        modo_operacao = getattr(motor, 'modo_operacao', 'teste').lower()
        
        # Filtrar agentes baseado no modo
        agentes_filtrados = []
        tipos_esperados = []
        
        if modo_operacao == 'aprendizagem':
            # Modo aprendizagem: Genético vs Q-Learning
            tipos_esperados = ['Genético', 'Q-Learning']
            for agente in motor.agentes:
                tipo_classe = type(agente).__name__
                if ('Evolucionario' in tipo_classe or 'Genetico' in tipo_classe or 
                    'QLearning' in tipo_classe or 'Q-Learning' in tipo_classe):
                    agentes_filtrados.append(agente)
            titulo = '👥 COMPARAÇÃO: GENÉTICO vs Q-LEARNING (Modo Aprendizagem)'
        else:
            # Modo teste: Reativo vs Q-Learning (EXCLUIR Genético explicitamente)
            tipos_esperados = ['Reativo', 'Q-Learning']
            for agente in motor.agentes:
                tipo_classe = type(agente).__name__
                
                # EXCLUIR explicitamente agentes genéticos
                is_genetico = ('Evolucionario' in tipo_classe or 
                              'Genetico' in tipo_classe or
                              'genetico' in tipo_classe.lower() or
                              'Evolucionário' in tipo_classe)
                
                if is_genetico:
                    continue  # Pular agentes genéticos no modo teste
                
                # Verificar se é Reativo ou Q-Learning (mais robusto)
                is_reativo = ('Reativo' in tipo_classe or 
                             'reativo' in tipo_classe.lower() or
                             'AgenteReativo' in tipo_classe)
                is_qlearning = ('QLearning' in tipo_classe or 
                               'Q-Learning' in tipo_classe or
                               'Q_Learning' in tipo_classe or
                               'AgenteQLearning' in tipo_classe)
                
                if is_reativo or is_qlearning:
                    agentes_filtrados.append(agente)
            titulo = '👥 COMPARAÇÃO: REATIVO vs Q-LEARNING (Modo Teste)'
        
        if not agentes_filtrados:
            print(f"⚠️ Nenhum agente {', '.join(tipos_esperados)} encontrado para comparar")
            return

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle(titulo, fontsize=14, fontweight='bold')

        # Coletar dados básicos apenas dos agentes filtrados
        dados = []
        for agente in agentes_filtrados:
            stats = agente.obter_estatisticas()
            tipo_classe = type(agente).__name__
            
            # Nome mais amigável para o tipo (mais robusto)
            tipo_nome = tipo_classe
            
            # No modo teste, garantir que apenas Reativo e Q-Learning sejam mapeados
            if modo_operacao != 'aprendizagem':
                # Modo teste: apenas Reativo ou Q-Learning
                if 'Reativo' in tipo_classe or 'reativo' in tipo_classe.lower():
                    tipo_nome = 'Reativo'
                elif 'QLearning' in tipo_classe or 'Q-Learning' in tipo_classe or 'qlearning' in tipo_classe.lower():
                    tipo_nome = 'Q-Learning'
                else:
                    # Se não for Reativo nem Q-Learning, pular este agente
                    continue
            else:
                # Modo aprendizagem: Genético ou Q-Learning
                if 'Evolucionario' in tipo_classe or 'Genetico' in tipo_classe or 'genetico' in tipo_classe.lower():
                    tipo_nome = 'Genético'
                elif 'QLearning' in tipo_classe or 'Q-Learning' in tipo_classe or 'qlearning' in tipo_classe.lower():
                    tipo_nome = 'Q-Learning'
                else:
                    continue
            
            dados.append({
                'id': agente.agente_id,
                'tipo': tipo_nome,
                'recompensa': stats['recompensa_acumulada'],
                'explorados': stats['espacos_explorados'],
                'passos': stats['num_acoes']
            })

        # Agrupar por tipo para melhor visualização
        tipos = [d['tipo'] for d in dados]
        ids = [d['id'] for d in dados]
        recompensas = [d['recompensa'] for d in dados]
        explorados = [d['explorados'] for d in dados]
        
        # Cores diferentes por tipo e modo
        if modo_operacao == 'aprendizagem':
            # Genético (laranja) vs Q-Learning (azul)
            cores = ['#FF9800' if t == 'Genético' else '#2196F3' for t in tipos]
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor='#FF9800', edgecolor='black', label='Genético'),
                Patch(facecolor='#2196F3', edgecolor='black', label='Q-Learning')
            ]
        else:
            # Reativo (verde) vs Q-Learning (azul)
            cores = ['#4CAF50' if t == 'Reativo' else '#2196F3' for t in tipos]
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor='#4CAF50', edgecolor='black', label='Reativo'),
                Patch(facecolor='#2196F3', edgecolor='black', label='Q-Learning')
            ]

        # Gráfico 1: Recompensas
        bars1 = ax1.bar(ids, recompensas, color=cores, edgecolor='black')
        ax1.set_xlabel('Agente')
        ax1.set_ylabel('Recompensa')
        ax1.set_title('Recompensa Total')
        ax1.tick_params(axis='x', rotation=45)
        ax1.legend(handles=legend_elements, loc='upper right')

        # Valores nas barras
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                     f'{height:.1f}', ha='center', va='bottom')

        # Gráfico 2: Exploração
        bars2 = ax2.bar(ids, explorados, color=cores, edgecolor='black')
        ax2.set_xlabel('Agente')
        ax2.set_ylabel('Espaços Explorados')
        ax2.set_title('Capacidade de Exploração')
        ax2.tick_params(axis='x', rotation=45)
        ax2.legend(handles=legend_elements, loc='upper right')

        # Gráfico 3: Eficiência (recompensa/passo)
        eficiencias = [d['recompensa']/max(d['passos'], 1) for d in dados]
        bars3 = ax3.bar(ids, eficiencias, color=cores, edgecolor='black')
        ax3.set_xlabel('Agente')
        ax3.set_ylabel('Recompensa/Passo')
        ax3.set_title('Eficiência')
        ax3.tick_params(axis='x', rotation=45)
        ax3.legend(handles=legend_elements, loc='upper right')

        # Gráfico 4: Scatter plot com cores por tipo
        tipos_unicos = list(set(tipos))
        for tipo in tipos_unicos:
            # No modo teste, garantir que apenas Reativo e Q-Learning apareçam
            if modo_operacao != 'aprendizagem' and tipo == 'Genético':
                continue  # Pular genéticos no modo teste
            
            indices = [i for i, t in enumerate(tipos) if t == tipo]
            x_vals = [explorados[i] for i in indices]
            y_vals = [recompensas[i] for i in indices]
            id_vals = [ids[i] for i in indices]
            # Cor baseada no modo
            if modo_operacao == 'aprendizagem':
                cor = '#FF9800' if tipo == 'Genético' else '#2196F3'
            else:
                # Modo teste: apenas Reativo (verde) e Q-Learning (azul)
                cor = '#4CAF50' if tipo == 'Reativo' else '#2196F3'
            ax4.scatter(x_vals, y_vals, s=150, alpha=0.7, edgecolors='black', color=cor, label=tipo)
            for x, y, id_ in zip(x_vals, y_vals, id_vals):
                ax4.annotate(id_, (x, y), xytext=(5, 5), textcoords='offset points', fontsize=9)
        ax4.set_xlabel('Espaços Explorados')
        ax4.set_ylabel('Recompensa Total')
        ax4.set_title('Exploração vs Recompensa')
        ax4.grid(True, alpha=0.3)
        ax4.legend(loc='best')

        plt.tight_layout()
        plt.show()

    def plotar_evolucao_epsilon(self, motor):
        """Mostra evolução do epsilon para Q-Learning"""
        q_agents = [a for a in motor.agentes if hasattr(a, 'epsilon')]

        if not q_agents:
            print("⚠️ Nenhum agente Q-Learning encontrado")
            return

        fig, ax = plt.subplots(figsize=(10, 6))

        for agente in q_agents:
            # Simular decaimento (em caso real, teria histórico)
            episodios = range(1, 101)
            epsilon_vals = [agente.epsilon * (0.995 ** ep) for ep in episodios]
            ax.plot(episodios, epsilon_vals, label=agente.agente_id, linewidth=2)

        ax.set_xlabel('Episódio')
        ax.set_ylabel('Valor do Epsilon (ε)')
        ax.set_title('📉 Decaimento do Epsilon - Estratégia ε-greedy')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()

    def plotar_todos(self, motor):
        """Mostra todos os gráficos em sequência"""
        input("\n📈 Pressione Enter para ver Curva de Aprendizagem...")
        self.plotar_curva_aprendizagem(motor)

        input("\n👥 Pressione Enter para ver Comparação de Agentes...")
        self.plotar_comparacao_agentes(motor)

        # Verificar se tem agentes Q-Learning
        q_agents = [a for a in motor.agentes if hasattr(a, 'epsilon')]
        if q_agents:
            input("\n📉 Pressione Enter para ver Evolução do Epsilon...")
            self.plotar_evolucao_epsilon(motor)

        print("\n✅ Visualização concluída!")