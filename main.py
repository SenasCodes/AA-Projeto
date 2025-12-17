#!/usr/bin/env python3
"""
Script Principal - Simulador SMA
Executa simulações com visualização pygame
"""

import sys
import argparse
from MotorDeSimulacao import MotorDeSimulacao, cria


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Simulador SMA - Sistema Multi-Agente')
    parser.add_argument('config', nargs='?', default='config_simulacao.json',
                       help='Ficheiro de configuração JSON (padrão: config_simulacao.json)')
    parser.add_argument('--sem-visualizacao', action='store_true',
                       help='Executar sem visualização pygame')
    parser.add_argument('--visualizacao', action='store_true',
                       help='Forçar visualização pygame')
    
    args = parser.parse_args()
    
    print("="*60)
    print("🚀 SIMULADOR SMA - Sistema Multi-Agente")
    print("="*60)
    
    try:
        # Criar simulação
        simulacao = cria(args.config)
        
        # Configurar visualização (flags da linha de comando têm prioridade absoluta)
        if args.visualizacao:
            # Forçar visualização
            simulacao.usar_visualizacao = True
            simulacao._inicializar_visualizacao()
            print("   Visualização: Ativada (via flag --visualizacao)")
        elif args.sem_visualizacao:
            # Desativar visualização explicitamente
            simulacao.usar_visualizacao = False
            if simulacao.visualizador:
                simulacao.visualizador.fechar()
                simulacao.visualizador = None
            print("   Visualização: Desativada (via flag --sem-visualizacao)")
        else:
            # Padrão: sem visualização (ignorar qualquer valor no JSON)
            simulacao.usar_visualizacao = False
            if simulacao.visualizador:
                simulacao.visualizador.fechar()
                simulacao.visualizador = None
        
        # Executar simulação
        simulacao.executa()
        
        print("\n✅ Simulação concluída com sucesso!")
        return 0
        
    except FileNotFoundError as e:
        print(f"\n❌ Erro: Ficheiro não encontrado: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

