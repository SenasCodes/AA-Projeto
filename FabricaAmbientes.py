from AmbienteFarol import AmbienteFarol
from AmbienteForaging import AmbienteForaging
from AmbienteLabirinto import AmbienteLabirinto
from ambiente import Posicao
from ambiente import TipoAmbiente, Ambiente
from typing import List, Dict, Any, Optional


class FabricaAmbientes:
    """Fábrica para criar ambientes baseados em parâmetros"""

    @staticmethod
    def criar_ambiente(tipo: TipoAmbiente, parametros: Dict[str, Any] = None) -> Ambiente:
        parametros = parametros or {}

        if tipo == TipoAmbiente.FAROL:
            pos_farol_param = parametros.get('pos_farol')
            if pos_farol_param:
                pos_farol = Posicao(pos_farol_param['x'], pos_farol_param['y'])
            else:
                pos_farol = None

            return AmbienteFarol(
                largura=parametros.get('largura', 10),
                altura=parametros.get('altura', 10),
                pos_farol=pos_farol,
                com_obstaculos=parametros.get('com_obstaculos', False),
                mover_farol=parametros.get('mover_farol', True),
                mover_obstaculos=parametros.get('mover_obstaculos', True),
                intervalo_movimento=parametros.get('intervalo_movimento', 20)
            )

        elif tipo == TipoAmbiente.FORAGING:
            return AmbienteForaging(
                largura=parametros.get('largura', 15),
                altura=parametros.get('altura', 15),
                num_recursos=parametros.get('num_recursos', 20),
                num_ninhos=parametros.get('num_ninhos', 1),
                com_obstaculos=parametros.get('com_obstaculos', False)
            )

        elif tipo == TipoAmbiente.LABIRINTO:
            pos_inicio_param = parametros.get('pos_inicio')
            pos_inicio = None
            if pos_inicio_param:
                pos_inicio = Posicao(pos_inicio_param['x'], pos_inicio_param['y'])
            
            pos_fim_param = parametros.get('pos_fim')
            pos_fim = None
            if pos_fim_param:
                pos_fim = Posicao(pos_fim_param['x'], pos_fim_param['y'])

            return AmbienteLabirinto(
                largura=parametros.get('largura', 10),
                altura=parametros.get('altura', 10),
                densidade_paredes=parametros.get('densidade_paredes', 0.3),
                pos_inicio=pos_inicio,
                pos_fim=pos_fim
            )

        else:
            raise ValueError(f"Tipo de ambiente não suportado: {tipo}")