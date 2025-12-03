#!/usr/bin/env python3
"""
Módulo Principal para Testar o Ambiente FAROL do Simulador SMA
"""

import sys
import time
import numpy as np

# Importar as classes do ambiente Farol
from ambiente import (
    AmbienteFarol, FabricaAmbientes, TipoAmbiente,
    Posicao, Acao, Direcao, Observacao
)


class TestadorFarol:
    """Classe para testar especificamente o ambiente Farol"""

    def __init__(self):
        self.ambiente = None
        self.resultados = {}

    def criar_ambiente(self, config: dict = None):
        """Cria e configura o ambiente Farol"""
        print("🚀 CRIANDO AMBIENTE FAROL...")

        config = config or {
            'largura': 10,
            'altura': 10,
            'com_obstaculos': True
        }

        self.ambiente = FabricaAmbientes.criar_ambiente(
            TipoAmbiente.FAROL,
            config
        )

        print(f"✅ Ambiente criado: {config['largura']}x{config['altura']}")
        print(f"📍 Farol na posição: {self.ambiente.pos_farol}")
        print(f"🚧 Obstáculos: {len(self.ambiente.obstaculos)}")

        return self.ambiente

    def registar_agentes(self, posicoes_agentes: list = None):
        """Regista agentes no ambiente"""
        print("\n👥 REGISTANDO AGENTES...")

        if not posicoes_agentes:
            # Posições padrão - cantos opostos
            posicoes_agentes = [
                Posicao(1, 1),  # Canto superior esquerdo
                Posicao(8, 8)  # Canto inferior direito
            ]

        for i, pos in enumerate(posicoes_agentes):
            agente_id = f"agente{i + 1}"
            self.ambiente.registar_agente(agente_id, pos)
            print(f"✅ {agente_id} registado em {pos}")

        print(f"📊 Total de agentes: {len(self.ambiente.agentes)}")

    def mostrar_estado_inicial(self):
        """Mostra o estado inicial do ambiente"""
        print("\n📋 ESTADO INICIAL DO AMBIENTE:")
        print(f"🎯 Objetivo: Chegar ao farol em {self.ambiente.pos_farol}")
        print(f"⏱️  Passo atual: {self.ambiente.passo_atual}")
        print(f"🏁 Terminado: {self.ambiente.terminado}")

        print("\n🗺️  POSIÇÕES INICIAIS DOS AGENTES:")
        for agente_id, info in self.ambiente.agentes.items():
            pos = info['posicao']
            dist = pos.distancia(self.ambiente.pos_farol)
            print(f"  {agente_id}: {pos} (distância: {dist:.1f})")

    def executar_simulacao_basica(self, max_passos: int = 15):
        """Executa uma simulação básica com movimentos direcionais"""
        print(f"\n🎮 INICIANDO SIMULAÇÃO ({max_passos} passos máximos)")
        print("=" * 50)

        for passo in range(max_passos):
            print(f"\n--- PASSO {passo} ---")

            if self.ambiente.terminado:
                print("🎉 Simulação terminada antecipadamente!")
                break

            # Para cada agente no ambiente
            for agente_id in list(self.ambiente.agentes.keys()):
                self._processar_agente(agente_id, passo)

            # Atualizar ambiente
            self.ambiente.atualizacao()

            # Pequena pausa para melhor visualização
            time.sleep(0.5)

        return self.ambiente.terminado

    def _processar_agente(self, agente_id: str, passo: int):
        """Processa um agente individual num passo de simulação"""
        # 1. Obter observação
        obs = self.ambiente.observacao_para(agente_id)
        pos_atual = self.ambiente.obter_posicao_agente(agente_id)

        print(f"\n🔍 {agente_id} em {pos_atual}:")
        print(f"   📡 Direção farol: {obs.dados['direcao_farol']}")
        print(f"   📏 Distância: {obs.dados['distancia_farol']:.1f}")
        print(f"   🚧 Obstáculos vizinhos: {obs.dados['obstaculos_vizinhos']}")

        # 2. Escolher ação baseada na observação
        acao = self._escolher_acao_inteligente(obs, agente_id)

        # 3. Executar ação
        recompensa = self.ambiente.agir(acao, agente_id)

        # 4. Mostrar resultados
        nova_pos = self.ambiente.obter_posicao_agente(agente_id)
        print(f"   🎯 Ação: {acao.tipo} {acao.parametros.get('direcao', 'PARADO').name}")
        print(f"   📍 Nova posição: {nova_pos}")
        print(f"   💰 Recompensa: {recompensa:.2f}")

        # Verificar se chegou ao farol
        if nova_pos == self.ambiente.pos_farol:
            print(f"   🎉 {agente_id} CHEGOU AO FAROL!")

    def _escolher_acao_inteligente(self, obs: Observacao, agente_id: str) -> Acao:
        """Escolhe uma ação inteligente baseada na observação"""
        dx, dy = obs.dados['direcao_farol']
        obstaculos = obs.dados['obstaculos_vizinhos']

        # Prioridade 1: Mover na direção principal do farol
        direcoes_prioritarias = []

        if abs(dx) > abs(dy):
            # Farol está mais na horizontal
            direcoes_prioritarias.append(Direcao.ESTE if dx > 0 else Direcao.OESTE)
            direcoes_prioritarias.append(Direcao.SUL if dy > 0 else Direcao.NORTE)
        else:
            # Farol está mais na vertical
            direcoes_prioritarias.append(Direcao.SUL if dy > 0 else Direcao.NORTE)
            direcoes_prioritarias.append(Direcao.ESTE if dx > 0 else Direcao.OESTE)

        # Adicionar direções restantes como fallback
        todas_direcoes = [d for d in Direcao if d != Direcao.PARADO]
        for direcao in todas_direcoes:
            if direcao not in direcoes_prioritarias:
                direcoes_prioritarias.append(direcao)

        # Escolher primeira direção válida (sem obstáculo)
        for direcao in direcoes_prioritarias:
            if not obstaculos[direcao.name]:
                return Acao("mover", {'direcao': direcao})

        # Se todas as direções têm obstáculos, ficar parado
        return Acao("mover", {'direcao': Direcao.PARADO})

    def executar_simulacao_avancada(self, max_passos: int = 20):
        """Executa uma simulação mais avançada com diferentes estratégias"""
        print(f"\n🔬 SIMULAÇÃO AVANÇADA - ESTRATÉGIAS DIFERENTES")
        print("=" * 50)

        # Estratégias diferentes para cada agente
        estrategias = {
            "agente1": "direta",  # Sempre tenta ir direto ao farol
            "agente2": "cautelosa"  # Evita obstáculos mais agressivamente
        }

        for passo in range(max_passos):
            print(f"\n--- PASSO {passo} ---")

            if self.ambiente.terminado:
                print("🎉 Todos os agentes chegaram ao farol!")
                break

            for agente_id in list(self.ambiente.agentes.keys()):
                estrategia = estrategias.get(agente_id, "direta")
                self._processar_agente_com_estrategia(agente_id, passo, estrategia)

            self.ambiente.atualizacao()
            time.sleep(0.5)

    def _processar_agente_com_estrategia(self, agente_id: str, passo: int, estrategia: str):
        """Processa agente com estratégia específica"""
        obs = self.ambiente.observacao_para(agente_id)
        pos_atual = self.ambiente.obter_posicao_agente(agente_id)

        print(f"\n🔍 {agente_id} [{estrategia}] em {pos_atual}:")

        if estrategia == "direta":
            acao = self._estrategia_direta(obs)
        else:  # cautelosa
            acao = self._estrategia_cautelosa(obs)

        recompensa = self.ambiente.agir(acao, agente_id)
        nova_pos = self.ambiente.obter_posicao_agente(agente_id)

        print(f"   🎯 Ação: {acao.tipo} {acao.parametros.get('direcao', 'PARADO').name}")
        print(f"   📍 Nova posição: {nova_pos}")
        print(f"   💰 Recompensa: {recompensa:.2f}")

    def _estrategia_direta(self, obs: Observacao) -> Acao:
        """Estratégia: sempre tenta ir direto ao farol"""
        dx, dy = obs.dados['direcao_farol']
        obstaculos = obs.dados['obstaculos_vizinhos']

        if abs(dx) > abs(dy):
            direcao_principal = Direcao.ESTE if dx > 0 else Direcao.OESTE
        else:
            direcao_principal = Direcao.SUL if dy > 0 else Direcao.NORTE

        if not obstaculos[direcao_principal.name]:
            return Acao("mover", {'direcao': direcao_principal})

        # Se obstáculo na direção principal, tentar perpendicular
        if direcao_principal in [Direcao.NORTE, Direcao.SUL]:
            alternativas = [Direcao.ESTE, Direcao.OESTE]
        else:
            alternativas = [Direcao.NORTE, Direcao.SUL]

        for direcao in alternativas:
            if not obstaculos[direcao.name]:
                return Acao("mover", {'direcao': direcao})

        return Acao("mover", {'direcao': Direcao.PARADO})

    def _estrategia_cautelosa(self, obs: Observacao) -> Acao:
        """Estratégia: mais cautelosa, evita ficar preso"""
        dx, dy = obs.dados['direcao_farol']
        obstaculos = obs.dados['obstaculos_vizinhos']

        # Lista de direções ordenadas por preferência
        if dx > 0 and dy > 0:
            # Farol no quadrante SE
            preferencias = [Direcao.ESTE, Direcao.SUL, Direcao.NORTE, Direcao.OESTE]
        elif dx > 0 and dy < 0:
            # Farol no quadrante NE
            preferencias = [Direcao.ESTE, Direcao.NORTE, Direcao.SUL, Direcao.OESTE]
        elif dx < 0 and dy > 0:
            # Farol no quadrante SO
            preferencias = [Direcao.OESTE, Direcao.SUL, Direcao.NORTE, Direcao.ESTE]
        else:
            # Farol no quadrante NO
            preferencias = [Direcao.OESTE, Direcao.NORTE, Direcao.SUL, Direcao.ESTE]

        for direcao in preferencias:
            if not obstaculos[direcao.name]:
                return Acao("mover", {'direcao': direcao})

        return Acao("mover", {'direcao': Direcao.PARADO})

    def mostrar_resultados_detalhados(self):
        """Mostra resultados detalhados da simulação"""
        print("\n" + "=" * 60)
        print("📊 RESULTADOS DETALHADOS - AMBIENTE FAROL")
        print("=" * 60)

        metricas = self.ambiente.obter_metricas()

        print(f"\n⏱️  INFORMAÇÕES GERAIS:")
        print(f"  Passos totais: {self.ambiente.passo_atual}")
        print(f"  Episódio terminado: {self.ambiente.terminado}")
        print(f"  Agentes no farol: {metricas['agentes_no_farol']}/{len(self.ambiente.agentes)}")

        print(f"\n🏆 TEMPOS DE CHEGADA:")
        if metricas['tempos_chegada']:
            for agente_id, tempo in metricas['tempos_chegada'].items():
                print(f"  {agente_id}: passo {tempo}")
        else:
            print("  Nenhum agente chegou ao farol")

        print(f"\n📈 EVOLUÇÃO DAS DISTÂNCIAS:")
        distancias = metricas['distancias_medias']
        if distancias:
            print(f"  Distância inicial: {distancias[0]:.1f}")
            print(f"  Distância final: {distancias[-1]:.1f}")
            print(f"  Melhoria: {distancias[0] - distancias[-1]:.1f}")

            # Mostrar alguns pontos da evolução
            if len(distancias) > 5:
                print(f"  Amostra: {[f'{d:.1f}' for d in distancias[::len(distancias) // 5]]}")

        print(f"\n🗺️  POSIÇÕES FINAIS:")
        for agente_id, info in self.ambiente.agentes.items():
            pos = info['posicao']
            dist = pos.distancia(self.ambiente.pos_farol)
            status = "🎯 NO FAROL" if pos == self.ambiente.pos_farol else f"📏 {dist:.1f} de distância"
            print(f"  {agente_id}: {pos} - {status}")

    def teste_movimentos_manuais(self):
        """Permite testar movimentos manuais para um agente"""
        print("\n🎮 MODO MANUAL - CONTROLAR AGENTE 1")
        print("=" * 40)
        print("Comandos: N (Norte), S (Sul), E (Este), O (Oeste), P (Parar), Q (Sair)")

        agente_id = "agente1"
        passo = 0

        while True:
            print(f"\n--- PASSO {passo} ---")

            # Mostrar estado atual
            obs = self.ambiente.observacao_para(agente_id)
            pos = self.ambiente.obter_posicao_agente(agente_id)
            print(f"📍 Posição: {pos}")
            print(f"🎯 Farol: {self.ambiente.pos_farol} (distância: {obs.dados['distancia_farol']:.1f})")
            print(f"🚧 Obstáculos vizinhos: {obs.dados['obstaculos_vizinhos']}")

            # Verificar se chegou
            if pos == self.ambiente.pos_farol:
                print("🎉 CHEGOU AO FAROL!")
                break

            # Obter comando do utilizador
            comando = input("Direção (N/S/E/O/P/Q): ").strip().upper()

            if comando == 'Q':
                print("Saindo do modo manual...")
                break

            # Converter comando para direção
            direcoes = {'N': Direcao.NORTE, 'S': Direcao.SUL,
                        'E': Direcao.ESTE, 'O': Direcao.OESTE, 'P': Direcao.PARADO}

            if comando in direcoes:
                acao = Acao("mover", {'direcao': direcoes[comando]})
                recompensa = self.ambiente.agir(acao, agente_id)
                print(f"💰 Recompensa: {recompensa:.2f}")
            else:
                print("❌ Comando inválido!")
                continue

            self.ambiente.atualizacao()
            passo += 1


def main():
    """Função principal"""
    print("🧭 SIMULADOR SMA - TESTE DO AMBIENTE FAROL")
    print("=" * 50)

    # Inicializar testador
    testador = TestadorFarol()

    try:
        # 1. Criar ambiente
        testador.criar_ambiente({
            'largura': 8,
            'altura': 8,
            'com_obstaculos': True
        })

        # 2. Registar agentes
        testador.registar_agentes([
            Posicao(1, 1),
            Posicao(6, 6)
        ])

        # 3. Mostrar estado inicial
        testador.mostrar_estado_inicial()

        # Pequena pausa
        time.sleep(1)

        # 4. Executar simulação básica
        terminado = testador.executar_simulacao_basica(max_passos=12)

        if not terminado:
            # 5. Se não terminou, mostrar opções adicionais
            print("\n" + "=" * 50)
            print("O que deseja fazer a seguir?")
            print("1. Continuar com simulação avançada")
            print("2. Testar modo manual")
            print("3. Ver resultados e terminar")

            opcao = input("\nEscolha (1-3): ").strip()

            if opcao == "1":
                testador.executar_simulacao_avancada(max_passos=10)
            elif opcao == "2":
                testador.teste_movimentos_manuais()

        # 6. Mostrar resultados finais
        testador.mostrar_resultados_detalhados()

        print("\n🎊 TESTE DO FAROL CONCLUÍDO COM SUCESSO!")

    except Exception as e:
        print(f"\n❌ ERRO durante execução: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    # Pequeno delay para melhor visualização
    print("Iniciando teste do Farol em 2 segundos...")
    time.sleep(2)
    sys.exit(main())