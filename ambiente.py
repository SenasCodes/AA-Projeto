from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum
import numpy as np


class TipoAmbiente(Enum):
    FAROL = "farol"
    FORAGING = "foraging"
    LABIRINTO = "labirinto"


class Direcao(Enum):
    NORTE = (0, -1)
    SUL = (0, 1)
    ESTE = (1, 0)
    OESTE = (-1, 0)
    PARADO = (0, 0)


class Observacao:
    """Representa a perceção que um agente tem do ambiente"""

    def __init__(self, dados: Dict[str, Any], agente_id: str):
        self.dados = dados  # Informações sensoriais
        self.agente_id = agente_id
        self.passo_temporal: int = 0

    def __str__(self):
        return f"Obs[Agente:{self.agente_id}, Dados:{self.dados}]"


class Acao:
    """Representa uma ação que um agente pode executar"""

    def __init__(self, tipo: str, parametros: Dict[str, Any] = None):
        self.tipo = tipo  # "mover", "recolher", "depositar", etc.
        self.parametros = parametros or {}
        self.agente_id: Optional[str] = None

    def __str__(self):
        return f"Acao[{self.tipo}, Params:{self.parametros}]"


class Posicao:
    """Representa uma posição no ambiente 2D"""

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def mover(self, direcao: Direcao) -> 'Posicao':
        dx, dy = direcao.value
        return Posicao(self.x + dx, self.y + dy)

    def distancia(self, other: 'Posicao') -> float:
        return abs(self.x - other.x) + abs(self.y - other.y)

    def __str__(self):
        return f"({self.x}, {self.y})"


class Ambiente(ABC):
    """Classe abstrata base para todos os ambientes"""

    def __init__(self, largura: int, altura: int, parametros: Dict[str, Any] = None):
        self.largura = largura
        self.altura = altura
        self.parametros = parametros or {}
        self.passo_atual: int = 0
        self.agentes: Dict[str, Any] = {}  # id_agente -> informações
        self.terminado: bool = False
        self.metricas: Dict[str, Any] = {}

    @abstractmethod
    def observacao_para(self, agente_id: str) -> Observacao:
        """Retorna a observação/perceção para um agente específico"""
        pass

    @abstractmethod
    def agir(self, accao: Acao, agente_id: str) -> float:
        """
        Executa uma ação de um agente no ambiente
        Retorna recompensa obtida
        """
        pass

    @abstractmethod
    def atualizacao(self):
        """Atualiza o estado do ambiente (crescimento de recursos, etc.)"""
        pass

    def registar_agente(self, agente_id: str, posicao: Posicao):
        """Regista um novo agente no ambiente"""
        self.agentes[agente_id] = {
            'posicao': posicao,
            'recursos': 0,
            'historico_posicoes': [posicao]
        }

    def posicao_valida(self, posicao: Posicao) -> bool:
        """Verifica se uma posição está dentro dos limites do ambiente"""
        return (0 <= posicao.x < self.largura and
                0 <= posicao.y < self.altura)

    def obter_posicao_agente(self, agente_id: str) -> Optional[Posicao]:
        """Retorna a posição atual de um agente"""
        if agente_id in self.agentes:
            return self.agentes[agente_id]['posicao']
        return None

    def terminar_episodio(self):
        """Marca o episódio como terminado"""
        self.terminado = True

    def obter_metricas(self) -> Dict[str, Any]:
        """Retorna métricas atuais do ambiente"""
        return self.metricas.copy()

    def reset(self):
        """Reinicia o ambiente para o estado inicial"""
        self.passo_atual = 0
        self.terminado = False
        self.metricas = {}
        # Mantém agentes mas reseta suas posições e estado
        for agente_id in self.agentes:
            pos_inicial = self.agentes[agente_id]['historico_posicoes'][0]
            self.agentes[agente_id].update({
                'posicao': pos_inicial,
                'recursos': 0,
                'historico_posicoes': [pos_inicial]
            })


class FabricaAmbientes:
    @staticmethod
    def criar_ambiente(tipo: TipoAmbiente, parametros: Dict[str, Any] = None) -> 'Ambiente':
        """
        Método stub - a implementação real está no ficheiro FabricaAmbientes.py
        """
        raise NotImplementedError("Use a implementação completa em FabricaAmbientes.py")