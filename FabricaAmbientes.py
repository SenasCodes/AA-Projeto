from AmbienteFarol import AmbienteFarol
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
                pos_farol=parametros.get('pos_farol'),
                com_obstaculos=parametros.get('com_obstaculos', False)
            )

       #

        else:
            raise ValueError(f"Tipo de ambiente não suportado: {tipo}")