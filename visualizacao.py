"""
Módulo de Visualização - Pygame
Visualiza ambientes 2D, agentes, objetivos e recursos em tempo real
"""

import pygame
import sys
from typing import Dict, Any, Optional, List
from ambiente import Ambiente, Posicao, TipoAmbiente
from agente import Agente


class Visualizador:
    """Visualizador de simulações SMA usando Pygame"""
    
    # Cores
    COR_FUNDO = (240, 240, 240)
    COR_GRID = (200, 200, 200)
    COR_AGENTE = (50, 150, 255)
    COR_FAROL = (255, 200, 0)
    COR_OBSTACULO = (100, 100, 100)
    COR_RECURSO = (0, 200, 0)
    COR_NINHO = (139, 69, 19)
    COR_INICIO = (0, 255, 0)
    COR_FIM = (255, 0, 0)
    COR_TEXTO = (0, 0, 0)
    
    def __init__(self, ambiente: Ambiente, largura_janela: int = 800, altura_janela: int = 600):
        """
        Inicializa o visualizador
        
        Args:
            ambiente: Ambiente a visualizar
            largura_janela: Largura da janela em pixels
            altura_janela: Altura da janela em pixels
        """
        self.ambiente = ambiente
        self.largura_janela = largura_janela
        self.altura_janela = altura_janela
        
        # Calcular tamanho da célula
        self.celula_largura = largura_janela // ambiente.largura
        self.celula_altura = altura_janela // ambiente.altura
        
        # Inicializar Pygame
        pygame.init()
        self.tela = pygame.display.set_mode((largura_janela, altura_janela + 100))
        pygame.display.set_caption("Simulador SMA - Sistema Multi-Agente")
        self.relogio = pygame.time.Clock()
        self.fonte = pygame.font.Font(None, 24)
        self.fonte_pequena = pygame.font.Font(None, 18)
        
        # Estado
        self.pausado = False
        self.velocidade = 10  # FPS
        
    def desenhar_ambiente_farol(self):
        """Desenha ambiente do tipo Farol"""
        # Desenhar grid
        for x in range(self.ambiente.largura + 1):
            pygame.draw.line(
                self.tela, self.COR_GRID,
                (x * self.celula_largura, 0),
                (x * self.celula_largura, self.altura_janela)
            )
        for y in range(self.ambiente.altura + 1):
            pygame.draw.line(
                self.tela, self.COR_GRID,
                (0, y * self.celula_altura),
                (self.largura_janela, y * self.celula_altura)
            )
        
        # Desenhar obstáculos
        if hasattr(self.ambiente, 'obstaculos'):
            for obstaculo in self.ambiente.obstaculos:
                x = obstaculo.x * self.celula_largura
                y = obstaculo.y * self.celula_altura
                pygame.draw.rect(
                    self.tela, self.COR_OBSTACULO,
                    (x + 1, y + 1, self.celula_largura - 2, self.celula_altura - 2)
                )
        
        # Desenhar farol
        if hasattr(self.ambiente, 'pos_farol'):
            farol_x = self.ambiente.pos_farol.x * self.celula_largura + self.celula_largura // 2
            farol_y = self.ambiente.pos_farol.y * self.celula_altura + self.celula_altura // 2
            pygame.draw.circle(self.tela, self.COR_FAROL, (farol_x, farol_y), self.celula_largura // 3)
            # Desenhar raios
            for i in range(8):
                angulo = i * 45
                import math
                x1 = farol_x + math.cos(math.radians(angulo)) * (self.celula_largura // 3)
                y1 = farol_y + math.sin(math.radians(angulo)) * (self.celula_largura // 3)
                x2 = farol_x + math.cos(math.radians(angulo)) * (self.celula_largura // 2)
                y2 = farol_y + math.sin(math.radians(angulo)) * (self.celula_largura // 2)
                pygame.draw.line(self.tela, self.COR_FAROL, (x1, y1), (x2, y2), 2)
        
        # Desenhar agentes
        for agente_id, info in self.ambiente.agentes.items():
            pos = info['posicao']
            x = pos.x * self.celula_largura + self.celula_largura // 2
            y = pos.y * self.celula_altura + self.celula_altura // 2
            pygame.draw.circle(self.tela, self.COR_AGENTE, (x, y), self.celula_largura // 3)
            # Desenhar ID do agente
            texto = self.fonte_pequena.render(agente_id[:3], True, (255, 255, 255))
            texto_rect = texto.get_rect(center=(x, y))
            self.tela.blit(texto, texto_rect)
    
    def desenhar_ambiente_foraging(self):
        """Desenha ambiente do tipo Foraging"""
        # Desenhar grid
        for x in range(self.ambiente.largura + 1):
            pygame.draw.line(
                self.tela, self.COR_GRID,
                (x * self.celula_largura, 0),
                (x * self.celula_largura, self.altura_janela)
            )
        for y in range(self.ambiente.altura + 1):
            pygame.draw.line(
                self.tela, self.COR_GRID,
                (0, y * self.celula_altura),
                (self.largura_janela, y * self.celula_altura)
            )
        
        # Desenhar obstáculos
        if hasattr(self.ambiente, 'obstaculos'):
            for obstaculo in self.ambiente.obstaculos:
                x = obstaculo.x * self.celula_largura
                y = obstaculo.y * self.celula_altura
                pygame.draw.rect(
                    self.tela, self.COR_OBSTACULO,
                    (x + 1, y + 1, self.celula_largura - 2, self.celula_altura - 2)
                )
        
        # Desenhar recursos
        if hasattr(self.ambiente, 'recursos'):
            for recurso_pos, valor in self.ambiente.recursos.items():
                x = recurso_pos.x * self.celula_largura + self.celula_largura // 2
                y = recurso_pos.y * self.celula_altura + self.celula_altura // 2
                tamanho = min(8, valor // 2 + 3)
                pygame.draw.circle(self.tela, self.COR_RECURSO, (x, y), tamanho)
                # Mostrar valor
                texto = self.fonte_pequena.render(str(valor), True, (0, 0, 0))
                texto_rect = texto.get_rect(center=(x, y))
                self.tela.blit(texto, texto_rect)
        
        # Desenhar ninhos
        if hasattr(self.ambiente, 'ninhos'):
            for ninho_pos in self.ambiente.ninhos:
                x = ninho_pos.x * self.celula_largura + self.celula_largura // 2
                y = ninho_pos.y * self.celula_altura + self.celula_altura // 2
                pygame.draw.rect(
                    self.tela, self.COR_NINHO,
                    (x - self.celula_largura // 3, y - self.celula_altura // 3,
                     self.celula_largura * 2 // 3, self.celula_altura * 2 // 3)
                )
        
        # Desenhar agentes
        for agente_id, info in self.ambiente.agentes.items():
            pos = info['posicao']
            x = pos.x * self.celula_largura + self.celula_largura // 2
            y = pos.y * self.celula_altura + self.celula_altura // 2
            
            # Cor diferente se agente tem recursos
            cor = (255, 100, 100) if info.get('recursos', 0) > 0 else self.COR_AGENTE
            pygame.draw.circle(self.tela, cor, (x, y), self.celula_largura // 3)
            
            # Mostrar recursos carregados
            if info.get('recursos', 0) > 0:
                texto = self.fonte_pequena.render(str(info['recursos']), True, (255, 255, 255))
                texto_rect = texto.get_rect(center=(x, y))
                self.tela.blit(texto, texto_rect)
    
    def desenhar_ambiente_labirinto(self):
        """Desenha ambiente do tipo Labirinto"""
        # Desenhar grid
        for x in range(self.ambiente.largura + 1):
            pygame.draw.line(
                self.tela, self.COR_GRID,
                (x * self.celula_largura, 0),
                (x * self.celula_largura, self.altura_janela)
            )
        for y in range(self.ambiente.altura + 1):
            pygame.draw.line(
                self.tela, self.COR_GRID,
                (0, y * self.celula_altura),
                (self.largura_janela, y * self.celula_altura)
            )
        
        # Desenhar paredes
        if hasattr(self.ambiente, 'paredes'):
            for parede in self.ambiente.paredes:
                x = parede.x * self.celula_largura
                y = parede.y * self.celula_altura
                pygame.draw.rect(
                    self.tela, self.COR_OBSTACULO,
                    (x + 1, y + 1, self.celula_largura - 2, self.celula_altura - 2)
                )
        
        # Desenhar ponto de partida
        if hasattr(self.ambiente, 'pos_inicio'):
            inicio_x = self.ambiente.pos_inicio.x * self.celula_largura + self.celula_largura // 2
            inicio_y = self.ambiente.pos_inicio.y * self.celula_altura + self.celula_altura // 2
            pygame.draw.circle(self.tela, self.COR_INICIO, (inicio_x, inicio_y), self.celula_largura // 3)
            texto = self.fonte_pequena.render("IN", True, (0, 0, 0))
            texto_rect = texto.get_rect(center=(inicio_x, inicio_y))
            self.tela.blit(texto, texto_rect)
        
        # Desenhar ponto de chegada
        if hasattr(self.ambiente, 'pos_fim'):
            fim_x = self.ambiente.pos_fim.x * self.celula_largura + self.celula_largura // 2
            fim_y = self.ambiente.pos_fim.y * self.celula_altura + self.celula_altura // 2
            pygame.draw.circle(self.tela, self.COR_FIM, (fim_x, fim_y), self.celula_largura // 3)
            texto = self.fonte_pequena.render("OUT", True, (255, 255, 255))
            texto_rect = texto.get_rect(center=(fim_x, fim_y))
            self.tela.blit(texto, texto_rect)
        
        # Desenhar agentes
        for agente_id, info in self.ambiente.agentes.items():
            pos = info['posicao']
            x = pos.x * self.celula_largura + self.celula_largura // 2
            y = pos.y * self.celula_altura + self.celula_altura // 2
            pygame.draw.circle(self.tela, self.COR_AGENTE, (x, y), self.celula_largura // 3)
            # Desenhar ID do agente
            texto = self.fonte_pequena.render(agente_id[:3], True, (255, 255, 255))
            texto_rect = texto.get_rect(center=(x, y))
            self.tela.blit(texto, texto_rect)
    
    def desenhar_info(self, passo: int, agentes: List[Agente] = None):
        """Desenha informações na parte inferior da tela"""
        y_offset = self.altura_janela
        
        # Fundo para informações
        pygame.draw.rect(
            self.tela, (220, 220, 220),
            (0, y_offset, self.largura_janela, 100)
        )
        
        # Informações gerais
        texto_passo = self.fonte.render(f"Passo: {passo}", True, self.COR_TEXTO)
        self.tela.blit(texto_passo, (10, y_offset + 10))
        
        status = "PAUSADO" if self.pausado else "EXECUTANDO"
        texto_status = self.fonte.render(f"Status: {status}", True, self.COR_TEXTO)
        self.tela.blit(texto_status, (10, y_offset + 35))
        
        # Informações dos agentes
        if agentes:
            x_offset = 200
            for i, agente in enumerate(agentes[:4]):  # Mostrar até 4 agentes
                stats = agente.obter_estatisticas()
                texto_agente = self.fonte_pequena.render(
                    f"{agente.agente_id}: R={stats['recompensa_acumulada']:.1f}",
                    True, self.COR_TEXTO
                )
                self.tela.blit(texto_agente, (x_offset, y_offset + 10 + i * 20))
        
        # Instruções
        texto_instrucoes = self.fonte_pequena.render(
            "Espaço: Pausar | Q: Sair",
            True, self.COR_TEXTO
        )
        self.tela.blit(texto_instrucoes, (self.largura_janela - 200, y_offset + 10))
    
    def atualizar(self, passo: int, agentes: List[Agente] = None):
        """
        Atualiza a visualização
        
        Args:
            passo: Passo atual da simulação
            agentes: Lista de agentes (opcional)
        """
        # Processar eventos
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_SPACE:
                    self.pausado = not self.pausado
                elif evento.key == pygame.K_q:
                    return False
        
        # Limpar tela
        self.tela.fill(self.COR_FUNDO)
        
        # Desenhar ambiente baseado no tipo
        if isinstance(self.ambiente, Ambiente):
            # Determinar tipo de ambiente
            if hasattr(self.ambiente, 'pos_farol'):
                self.desenhar_ambiente_farol()
            elif hasattr(self.ambiente, 'recursos') or hasattr(self.ambiente, 'ninhos'):
                self.desenhar_ambiente_foraging()
            elif hasattr(self.ambiente, 'pos_inicio') or hasattr(self.ambiente, 'pos_fim'):
                self.desenhar_ambiente_labirinto()
            else:
                # Ambiente genérico
                self.desenhar_ambiente_farol()
        
        # Desenhar informações
        self.desenhar_info(passo, agentes)
        
        # Atualizar display
        pygame.display.flip()
        self.relogio.tick(self.velocidade)
        
        return True
    
    def fechar(self):
        """Fecha a visualização"""
        pygame.quit()
    
    def aguardar_tecla(self):
        """Aguarda uma tecla ser pressionada"""
        aguardando = True
        while aguardando:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    return False
                elif evento.type == pygame.KEYDOWN:
                    return True
        return True

