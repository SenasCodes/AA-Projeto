"""
Módulo do Motor de Simulação - Gerencia o ciclo de execução dos agentes
"""

import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from agente import Agente, FabricaAgentes
from ambiente import Ambiente, FabricaAmbientes, TipoAmbiente
from FabricaAmbientes import FabricaAmbientes
from typing import Optional


class MotorDeSimulacao:
    """
    Motor principal de simulação SMA
    Gerencia ciclo de tempo, agentes, ambiente e execução
    """

    def __init__(self, parametros: Dict[str, Any] = None):
        """
        Inicializa o motor de simulação

        Args:
            parametros: Dicionário com parâmetros de configuração
        """
        self.parametros = parametros or {}

        # Componentes da simulação
        self.ambiente: Optional[Ambiente] = None
        self.agentes: List[Agente] = []
        self.posicoes_iniciais: Dict[str, Any] = {}  # Armazena posições iniciais dos agentes

        # Controle de execução
        self.em_execucao = False
        self.passo_atual = 0
        self.passos_totais = self.parametros.get('passos_totais', 1000)
        self.delay_entre_passos = self.parametros.get('delay_entre_passos', 0.1)
        self.num_episodios = self.parametros.get('num_episodios', 1)
        self.episodio_atual = 0

        # Métricas
        self.metricas = {
            'inicio_execucao': None,
            'fim_execucao': None,
            'tempo_execucao': 0,
            'passos_executados': 0,
            'recompensa_total': 0
        }
        
        # Métricas por episódio
        self.historico_episodios = []
        
        # Visualização
        self.visualizador = None
        self.usar_visualizacao = self.parametros.get('usar_visualizacao', False)

    @staticmethod
    def cria(nome_do_ficheiro_parametros: str) -> 'MotorDeSimulacao':
        """
        Método estático para criar uma simulação a partir de ficheiro

        Args:
            nome_do_ficheiro_parametros: Caminho para ficheiro JSON

        Returns:
            Instância configurada do MotorDeSimulacao
        """
        try:
            with open(nome_do_ficheiro_parametros, 'r', encoding='utf-8') as f:
                parametros = json.load(f)

            # Criar instância do motor
            motor = MotorDeSimulacao(parametros)

            # Configurar ambiente
            motor._configurar_ambiente(parametros.get('ambiente', {}))

            # Configurar agentes
            motor._configurar_agentes(parametros.get('agentes', []))
            
            # Inicializar visualização se solicitado
            if motor.usar_visualizacao:
                motor._inicializar_visualizacao()

            print(f"✅ Simulação criada a partir de {nome_do_ficheiro_parametros}")
            print(f"   Ambiente: {type(motor.ambiente).__name__}")
            print(f"   Agentes: {len(motor.agentes)}")
            if motor.usar_visualizacao:
                print(f"   Visualização: Ativada")

            return motor

        except FileNotFoundError:
            raise FileNotFoundError(f"Ficheiro de parâmetros não encontrado: {nome_do_ficheiro_parametros}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Erro ao ler ficheiro JSON: {e}")

    def _configurar_ambiente(self, config_ambiente: Dict[str, Any]):
        """Configura o ambiente baseado nos parâmetros"""
        tipo_ambiente_str = config_ambiente.get('tipo', 'FAROL')

        try:
            tipo_ambiente = TipoAmbiente[tipo_ambiente_str.upper()]
        except KeyError:
            raise ValueError(f"Tipo de ambiente não suportado: {tipo_ambiente_str}")

        # Criar ambiente usando a fábrica
        self.ambiente = FabricaAmbientes.criar_ambiente(
            tipo_ambiente,
            config_ambiente.get('parametros', {})
        )

    def _configurar_agentes(self, configs_agentes: List[Dict[str, Any]]):
        """Configura os agentes baseado nos parâmetros"""
        self.agentes = []

        for i, config in enumerate(configs_agentes):
            tipo = config.get('tipo', 'reativo')
            agente_id = config.get('id', f'agente_{i}')

            # Criar agente usando a fábrica
            agente = FabricaAgentes.criar_agente(
                tipo,
                agente_id,
                config.get('parametros', {})
            )

            # Registrar agente no ambiente
            posicao_inicial = config.get('posicao_inicial', {'x': 0, 'y': 0})
            from ambiente import Posicao
            pos = Posicao(posicao_inicial['x'], posicao_inicial['y'])

            self.ambiente.registar_agente(agente_id, pos)
            self.posicoes_iniciais[agente_id] = pos  # Armazenar posição inicial

            self.agentes.append(agente)

            print(f"   ✅ Agente {agente_id} ({tipo}) registado em {pos}")
    
    def _inicializar_visualizacao(self):
        """Inicializa o visualizador"""
        try:
            from visualizacao import Visualizador
            self.visualizador = Visualizador(self.ambiente)
            print("   ✅ Visualização inicializada")
        except ImportError:
            print("   ⚠️  Pygame não disponível. Visualização desativada.")
            self.usar_visualizacao = False
        except Exception as e:
            print(f"   ⚠️  Erro ao inicializar visualização: {e}")
            self.usar_visualizacao = False

    def listaAgentes(self) -> List[Agente]:
        """
        Retorna lista de agentes na simulação

        Returns:
            Lista de agentes
        """
        return self.agentes.copy()

    def executa(self):
        """
        Executa a simulação completa (múltiplos episódios se configurado)
        """
        if self.em_execucao:
            print("⚠️  Simulação já está em execução")
            return

        print("\n" + "="*60)
        print("🚀 INICIANDO SIMULAÇÃO SMA")
        print("="*60)
        
        if self.num_episodios > 1:
            print(f"📚 Modo Multi-Episódio: {self.num_episodios} episódios")
            self._executar_multi_episodio()
        else:
            print(f"📖 Modo Episódio Único")
            self._executar_episodio_unico()
    
    def _executar_multi_episodio(self):
        """Executa múltiplos episódios de treino"""
        inicio_tempo_total = time.time()
        
        for episodio in range(1, self.num_episodios + 1):
            self.episodio_atual = episodio
            
            # Reset para novo episódio
            self._reset_episodio()
            
            # Executar episódio
            print(f"\n{'─'*60}")
            print(f"📖 Episódio {episodio}/{self.num_episodios}")
            print(f"{'─'*60}")
            
            inicio_episodio = time.time()
            recompensa_episodio = 0
            
            # Ciclo do episódio
            while (self.passo_atual < self.passos_totais and
                   not self.ambiente.terminado and
                   self.em_execucao):
                self._executar_passo()
                if self.delay_entre_passos > 0 and episodio == self.num_episodios:
                    time.sleep(self.delay_entre_passos)
            
            # Finalizar episódio
            fim_episodio = time.time()
            tempo_episodio = fim_episodio - inicio_episodio
            recompensa_episodio = self.metricas['recompensa_total']
            
            # Notificar agentes do fim do episódio
            for agente in self.agentes:
                if hasattr(agente, 'fim_episodio'):
                    agente.fim_episodio()
            
            # Guardar métricas do episódio
            self.historico_episodios.append({
                'episodio': episodio,
                'passos': self.passo_atual,
                'recompensa_total': recompensa_episodio,
                'tempo': tempo_episodio,
                'agentes_no_farol': self.ambiente.metricas.get('agentes_no_farol', 0)
            })
            
            # Mostrar progresso
            if episodio % 10 == 0 or episodio == self.num_episodios:
                media_reward = sum(e['recompensa_total'] for e in self.historico_episodios[-10:]) / min(10, len(self.historico_episodios))
                print(f"  ✅ Recompensa: {recompensa_episodio:.1f} | Média (últimos 10): {media_reward:.1f}")
                
                # Mostrar epsilon se disponível
                for agente in self.agentes:
                    if hasattr(agente, 'epsilon'):
                        print(f"     {agente.agente_id}: epsilon={agente.epsilon:.3f}, Q-table={len(getattr(agente, 'Q', {}))}")
        
        # Finalização
        self.metricas['tempo_execucao'] = time.time() - inicio_tempo_total
        
        # Fechar visualização
        if self.usar_visualizacao and self.visualizador:
            self.visualizador.fechar()
        
        self._mostrar_resultados_multi_episodio()
    
    def _executar_episodio_unico(self):
        """Executa um único episódio (comportamento original)"""
        self.em_execucao = True
        self.metricas['inicio_execucao'] = datetime.now()
        inicio_tempo = time.time()

        # Ciclo principal de simulação
        while (self.passo_atual < self.passos_totais and
               not self.ambiente.terminado and
               self.em_execucao):

            self._executar_passo()

            # Pequena pausa para visualização (se configurado)
            if self.delay_entre_passos > 0:
                time.sleep(self.delay_entre_passos)

        # Finalização
        self.em_execucao = False
        fim_tempo = time.time()
        self.metricas['fim_execucao'] = datetime.now()
        self.metricas['tempo_execucao'] = fim_tempo - inicio_tempo
        
        # Fechar visualização
        if self.usar_visualizacao and self.visualizador:
            self.visualizador.fechar()

        self._mostrar_resultados()
    
    def _reset_episodio(self):
        """Reset do ambiente e agentes para novo episódio"""
        self.em_execucao = True
        self.passo_atual = 0
        self.metricas['recompensa_total'] = 0
        
        # Reset ambiente
        self.ambiente.reset()
        
        # Reset agentes
        for agente in self.agentes:
            agente.reset()
            # Re-registrar agente no ambiente com posição inicial
            pos_inicial = self.posicoes_iniciais.get(agente.agente_id)
            self.ambiente.registar_agente(agente.agente_id, pos_inicial)
            agente.instala(self.ambiente, pos_inicial)

    def _executar_passo(self):
        """Executa um único passo de simulação"""
        self.passo_atual += 1

        if self.passo_atual % 10 == 0:
            print(f"⏱️  Passo {self.passo_atual}/{self.passos_totais}")

        # Para cada agente na simulação
        for agente in self.agentes:
            if not self.em_execucao:
                break

            self._processar_agente(agente)

        # Atualizar ambiente
        self.ambiente.atualizacao()
        
        # Atualizar visualização
        if self.usar_visualizacao and self.visualizador:
            continuar = self.visualizador.atualizar(self.passo_atual, self.agentes)
            if not continuar:
                self.em_execucao = False

        # Atualizar métricas
        self.metricas['passos_executados'] = self.passo_atual

    def _processar_agente(self, agente: Agente):
        """Processa um agente individual num passo"""
        agente_id = agente.agente_id

        # 1. Obter observação do ambiente
        obs = self.ambiente.observacao_para(agente_id)

        # 2. Agente decide ação (baseado na observação anterior)
        acao = agente.age()
        acao.agente_id = agente_id

        # 3. Executar ação no ambiente
        recompensa = self.ambiente.agir(acao, agente_id)

        # 4. Agente processa nova observação COM recompensa
        nova_obs = self.ambiente.observacao_para(agente_id)
        agente.observacao(nova_obs, recompensa)

        # 5. Registar ação
        agente.historico_acoes.append(acao)

        # 6. Atualizar métricas
        self.metricas['recompensa_total'] += recompensa

    def pausar(self):
        """Pausa a execução da simulação"""
        self.em_execucao = False
        print("⏸️  Simulação pausada")

    def retomar(self):
        """Retoma a execução da simulação"""
        if not self.em_execucao and self.passo_atual < self.passos_totais:
            self.em_execucao = True
            print("▶️  Simulação retomada")
            self.executa()

    def parar(self):
        """Para completamente a simulação"""
        self.em_execucao = False
        print("⏹️  Simulação parada")

    def _mostrar_resultados(self):
        """Mostra resultados finais da simulação"""
        print("\n" + "="*60)
        print("📊 RESULTADOS DA SIMULAÇÃO")
        print("="*60)

        print(f"\n📈 ESTATÍSTICAS GERAIS:")
        print(f"  Tempo de execução: {self.metricas['tempo_execucao']:.2f} segundos")
        print(f"  Passos executados: {self.metricas['passos_executados']}")
        print(f"  Recompensa total: {self.metricas['recompensa_total']:.2f}")
        print(f"  Ambiente terminado: {self.ambiente.terminado}")

        print(f"\n👥 ESTATÍSTICAS DOS AGENTES:")
        for agente in self.agentes:
            stats = agente.obter_estatisticas()
            print(f"  {agente.agente_id}:")
            print(f"    Recompensa: {stats['recompensa_acumulada']:.2f}")
            print(f"    Ações executadas: {stats['num_acoes']}")
            print(f"    Espaços explorados: {stats['espacos_explorados']}")

        # Métricas do ambiente
        metricas_ambiente = self.ambiente.obter_metricas()
        if metricas_ambiente:
            print(f"\n🌍 MÉTRICAS DO AMBIENTE:")
            for chave, valor in metricas_ambiente.items():
                print(f"  {chave}: {valor}")
    
    def _mostrar_resultados_multi_episodio(self):
        """Mostra resultados consolidados de múltiplos episódios"""
        print("\n" + "="*60)
        print("📊 RESULTADOS DO TREINO MULTI-EPISÓDIO")
        print("="*60)
        
        print(f"\n📈 ESTATÍSTICAS GERAIS:")
        print(f"  Episódios executados: {len(self.historico_episodios)}")
        print(f"  Tempo total: {self.metricas['tempo_execucao']:.2f} segundos")
        
        # Estatísticas de recompensa
        recompensas = [e['recompensa_total'] for e in self.historico_episodios]
        print(f"\n💰 EVOLUÇÃO DA RECOMPENSA:")
        print(f"  Primeiro episódio: {recompensas[0]:.2f}")
        print(f"  Último episódio: {recompensas[-1]:.2f}")
        print(f"  Melhor episódio: {max(recompensas):.2f}")
        print(f"  Média (últimos 10): {sum(recompensas[-10:])/min(10, len(recompensas)):.2f}")
        melhoria = recompensas[-1] - recompensas[0]
        percentual = (melhoria/abs(recompensas[0])*100) if recompensas[0] != 0 else 0
        print(f"  Melhoria total: {melhoria:.2f} ({percentual:.1f}%)")
        
        # Estatísticas dos agentes
        print(f"\n👥 ESTADO FINAL DOS AGENTES:")
        for agente in self.agentes:
            stats = agente.obter_estatisticas()
            print(f"  {agente.agente_id}:")
            
            # Q-Learning específico
            if hasattr(agente, 'epsilon'):
                print(f"    Epsilon: {agente.epsilon:.4f}")
                print(f"    Estados aprendidos: {len(getattr(agente, 'Q', {}))}")
            
            print(f"    Recompensa final: {stats['recompensa_acumulada']:.2f}")
            print(f"    Espaços explorados: {stats['espacos_explorados']}")
        
        # Taxa de sucesso
        sucessos = sum(1 for e in self.historico_episodios if e['agentes_no_farol'] > 0)
        taxa = sucessos/len(self.historico_episodios)*100 if self.historico_episodios else 0
        print(f"\n🎯 TAXA DE SUCESSO:")
        print(f"  Episódios com chegada ao farol: {sucessos}/{len(self.historico_episodios)} ({taxa:.1f}%)")
        
        print("\n" + "="*60)

    def obter_metricas(self) -> Dict[str, Any]:
        """
        Retorna métricas da simulação

        Returns:
            Dicionário com métricas
        """
        return self.metricas.copy()

    def __str__(self):
        status = "Em execução" if self.em_execucao else "Parado"
        return (f"MotorDeSimulacao[status={status}, "
                f"passo={self.passo_atual}/{self.passos_totais}, "
                f"agentes={len(self.agentes)}]")


# Função de conveniência para compatibilidade
def cria(nome_do_ficheiro_parametros: str) -> MotorDeSimulacao:
    """Alias para MotorDeSimulacao.cria()"""
    return MotorDeSimulacao.cria(nome_do_ficheiro_parametros)