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

        # Controle de execução
        self.em_execucao = False
        self.passo_atual = 0
        self.passos_totais = self.parametros.get('passos_totais', 1000)
        self.delay_entre_passos = self.parametros.get('delay_entre_passos', 0.1)

        # Métricas
        self.metricas = {
            'inicio_execucao': None,
            'fim_execucao': None,
            'tempo_execucao': 0,
            'passos_executados': 0,
            'recompensa_total': 0
        }

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

            print(f"✅ Simulação criada a partir de {nome_do_ficheiro_parametros}")
            print(f"   Ambiente: {type(motor.ambiente).__name__}")
            print(f"   Agentes: {len(motor.agentes)}")

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

            self.agentes.append(agente)

            print(f"   ✅ Agente {agente_id} ({tipo}) registado em {pos}")

    def listaAgentes(self) -> List[Agente]:
        """
        Retorna lista de agentes na simulação

        Returns:
            Lista de agentes
        """
        return self.agentes.copy()

    def executa(self):
        """
        Executa a simulação completa
        Ciclo principal: observação -> ação -> atualização
        """
        if self.em_execucao:
            print("⚠️  Simulação já está em execução")
            return

        print("\n" + "="*60)
        print("🚀 INICIANDO SIMULAÇÃO SMA")
        print("="*60)

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

        self._mostrar_resultados()

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

        # Atualizar métricas
        self.metricas['passos_executados'] = self.passo_atual

    def _processar_agente(self, agente: Agente):
        """Processa um agente individual num passo"""
        agente_id = agente.agente_id

        # 1. Obter observação do ambiente
        obs = self.ambiente.observacao_para(agente_id)

        # 2. Agente processa observação
        agente.observacao(obs)

        # 3. Agente decide ação
        acao = agente.age()
        acao.agente_id = agente_id

        # 4. Executar ação no ambiente
        recompensa = self.ambiente.agir(acao, agente_id)

        # 5. Agente avalia recompensa
        agente.avaliacaoEstadoAtual(recompensa)

        # 6. REGISTAR AÇÃO (ADICIONAR ESTA LINHA)
        agente.historico_acoes.append(acao)

        # 7. Atualizar métricas
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