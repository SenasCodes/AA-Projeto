#!/usr/bin/env python3
"""
Script de teste para o Motor de Simulação
"""

import sys
from MotorDeSimulacao import MotorDeSimulacao, cria

def main():
    """Função principal de teste"""
    print("🧪 TESTE DO MOTOR DE SIMULAÇÃO")
    print("=" * 50)

    try:
        # 1. Criar simulação a partir de ficheiro
        print("\n1. Criando simulação...")
        simulacao = cria("config_simulacao.json")

        # 2. Listar agentes
        print("\n2. Agentes na simulação:")
        agentes = simulacao.listaAgentes()
        for agente in agentes:
            print(f"   - {agente.agente_id} ({type(agente).__name__})")

        # 3. Executar simulação
        print("\n3. Executando simulação...")
        simulacao.executa()

        # 4. Obter métricas
        print("\n4. Métricas finais:")
        metricas = simulacao.obter_metricas()
        for chave, valor in metricas.items():
            if chave not in ['inicio_execucao', 'fim_execucao']:
                print(f"   {chave}: {valor}")

        print("\n✅ Teste concluído com sucesso!")

    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())