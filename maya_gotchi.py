"""
Maya-Gotchi 🐟🧶
================
Um tamagotchi em Pygame que se alimenta de sardinhas e relaxa fazendo crochê.

Conceitos demonstrados (portfólio):
- POO (classes Stat, Pet, Button, Game)
- Game loop com delta time
- Pixel art procedural (sprites definidos como grades de caracteres)
- Máquina de estados simples (idle / eating / crocheting / sleeping)
- Persistência em JSON com decaimento offline (o pet "vive" com o jogo fechado)

Como rodar:
    pip install pygame
    python maya_gotchi.py
"""

#Importando as bibliotecas necessarias
#Json para salvar e carregar o status
import json
#Para as animacoes
import math
#Montar caminhos de arquivos portateis
import os
#Medir em tempo real
import time

try:
#para dar vida ao jogo
    import pygame
#Captura de forma especifica o erro
except ImportError:
    raise SystemExit(
        "   Instale com:  pip install pygame\n"

    )

#Configuracao em geral
#Altura e largura da tela
LARGURA, ALTURA = 650, 650
#Frames per second
FPS = 100
#Tamanho do pixel dos nonecos
PIXEL = 14  

try:
# Plano A: descobrir a pasta onde o arquivo .py está
    _PASTA = os.path.dirname(os.path.abspath(__file__))
except NameError:
 # Plano B: se __file__ não existe (notebook), usa a pasta de trabalho atual
    _PASTA = os.getcwd()
SAVE_PATH = os.path.join(_PASTA, "save.json")

# Paleta (chave usada nas grades de sprite, cor RGB)
PALETA = {
    "P": (74, 50, 38),      # cabelo castanho escuro (contorno)
    "C": (121, 85, 61),     # cabelo castanho
    "c": (156, 116, 84),    # cabelo castanho claro (brilho)
    "S": (236, 198, 170),   # pele
    "s": (219, 178, 148),   # pele sombra
    "R": (226, 141, 122),   # bochecha
    "O": (48, 38, 42),      # olhos / boca
    "B": (255, 255, 255),   # brilho do olho
    "A": (72, 120, 196),    # blusa azul
    "a": (54, 95, 163),     # blusa azul sombra
    "G": (245, 195, 68),    # blusa amarela
    "g": (214, 160, 44),    # blusa amarela sombra
    "F": (120, 144, 156),   # sardinha - corpo
    "f": (84, 110, 122),    # sardinha - sombra
    "L": (198, 40, 40),     # lata vermelha
    "l": (255, 205, 100),   # detalhe dourado da lata
    "Y": (240, 98, 146),    # novelo de la rosa
    "y": (194, 53, 147),    # sombra do novelo
    "H": (176, 190, 197),   # agulha de croche
    "Z": (144, 164, 174),   # Zzz
}

#Cor da blusa
COR_BLUSA = "azul"

#Cor do cenario
FUNDO_DIA = (250, 243, 224)
FUNDO_NOITE = (38, 50, 66)
COR_PAINEL = (255, 255, 255)
COR_TEXTO = (60, 50, 45)

#Transforma a arte em dados
def grade_para_surface(grade: list[str], escala: int = PIXEL) -> pygame.Surface:
    #Converte uma grade de caracteres em uma Surface de pixel art.
    altura = len(grade)
    largura = max(len(linha) for linha in grade)
    surf = pygame.Surface((largura * escala, altura * escala), pygame.SRCALPHA)
    for y, linha in enumerate(grade):
        for x, ch in enumerate(linha):
            cor = PALETA.get(ch)
            if cor:
                pygame.draw.rect(surf, cor, (x * escala, y * escala, escala, escala))
    return surf


#Sprintes - Cria o avatar
def sprite_maya(expressao: str = "feliz", frame: int = 0) -> list[str]:
   #Avatar: cabelo longo castanho, blusa azul
    # Olhos e boca por expressao
    if expressao == "feliz":
        olhos = "PCS.OB..OB.SCP"
        bochecha = "PCSR......RSCP"
        boca = "PCS..O..O..SCP", "PCS...OO...SCP"
    elif expressao == "neutra":
        olhos = "PCS.OB..OB.SCP"
        bochecha = "PCS........SCP"
        boca = "PCS........SCP", "PCS...OO...SCP"
    elif expressao == "triste":
        olhos = "PCS.O....O.SCP"
        bochecha = "PCS........SCP"
        boca = "PCS...OO...SCP", "PCS..O..O..SCP"
    else:  # dormindo / piscar
        olhos = "PCS.OO..OO.SCP"
        bochecha = "PCSR......RSCP" if expressao == "piscar" else "PCS........SCP"
        boca = "PCS........SCP", "PCS...OO...SCP" if expressao == "piscar" else "PCS....O...SCP"

    # Mechas laterais balancam com o frame
    lado = ("C", "c") if frame % 2 == 0 else ("c", "C")

    grade = [
        "....PPPPPP....",
        "..PPCCCCCCPP..",
        ".PCCcCCCCcCCP.",
        ".PCCCCCCCCCCP.",
        "PCCCCCCCCCCCCP",
        "PCCSSSSSSSSCCP",
        "PCSSSSSSSSSSCP",
        olhos,
        bochecha,
        boca[0],
        boca[1],
        "PCsSSSSSSSSsCP",
        f"P{lado[0]}C.SSSSSS.C{lado[1]}P",
        f"P{lado[0]}C..SSSS..C{lado[1]}P",
    ]

    # Blusa azul 
    X, x = ("A", "a") if COR_BLUSA == "azul" else ("G", "g")
    grade += [
        f"P{lado[0]}C{X}{X}{X}{X}{X}{X}{X}{X}C{lado[1]}P",
        f"PC{x}{X}{X}{X}{X}{X}{X}{X}{X}{x}CP",
        f".C.{X}{X}{X}{X}{X}{X}{X}{X}.C.",
        f".c.{X}{X}{x}{X}{X}{x}{X}{X}.c.",
        f"...{X}{X}{X}{X}{X}{X}{X}{X}...",
        f"..S{x}{X}{X}{X}{X}{X}{X}{x}S..",
        f"...{X}{X}{X}{X}{X}{X}{X}{X}...",
        "....S....S....",
        "....S....S....",
    ]
    return grade


SPRITE_SARDINHA = [
    "..FFFF....",
    ".FFFFFFf..",
    "FBFFFFFff.",
    ".FFFFFFf..",
    "..FFFF..f.",
]

SPRITE_LATA = [
    "LLLLLLLLLL",
    "LllllllllL",
    "LlFFFFFFlL",
    "LllllllllL",
    "LLLLLLLLLL",
]

SPRITE_NOVELO = [
    "..YYYY..",
    ".YYyYYY.",
    "YYYYyYYY",
    "YYyYYYYY",
    ".YYYYyY.",
    "..YYYY.H",
    ".......H",
]


#Modelo do Avatar
class Stat:
  #Um atributo do pet (0-100) que decai com o tempo.
  #Uma classe encapsula o comportamento comum: valor entre 0 e 100 que decai proporcionalmente ao tempo

    def __init__(self, nome: str, valor: float = 80.0, decaimento_por_min: float = 2.0):
        self.nome = nome
        self.valor = valor
        self.decaimento_por_min = decaimento_por_min

    def atualizar(self, dt_segundos: float):
        self.valor -= self.decaimento_por_min * (dt_segundos / 60.0)
        self.valor = max(0.0, min(100.0, self.valor))

    def alterar(self, delta: float):
        self.valor = max(0.0, min(100.0, self.valor + delta))


class Pet:
   #Estado e regras do tamagotchi. 
   #O pet está sempre em exatamente um de quatro estados, e as transições são controladas.

    def __init__(self):
        #Se cai, precisa comer
        self.fome = Stat("Fome", 80, decaimento_por_min=3.0)       
        self.energia = Stat("Energia", 80, decaimento_por_min=1.5)
        self.diversao = Stat("Diversão", 80, decaimento_por_min=2.0)
        #Comer, Crochete e Dormir -  impede comer e dormir ao mesmo tempo
        self.estado = "idle" 
        #Faz a ação durar um tempo e voltar sozinha para idle         
        self.timer_estado = 0.0
        self.nascimento = time.time()

    #Acoes 
    def alimentar(self):
        if self.estado == "idle":
            self.estado = "eating"
            self.timer_estado = 2.5
            self.fome.alterar(+30)
            self.energia.alterar(+5)

    def fazer_croche(self):
        #Uma regra de negócio: exausta, ela recusa
        if self.estado == "idle" and self.energia.valor > 15:
            self.estado = "crocheting"
            self.timer_estado = 4.0
            self.diversao.alterar(+30)
            self.energia.alterar(-10)

    def dormir(self):
        if self.estado == "idle":
            self.estado = "sleeping"
            self.timer_estado = 6.0

    #Simulação
    def atualizar(self, dt: float):
        if self.estado == "sleeping":
            #Recupera dormindo
            self.energia.alterar(8 * dt) 
            self.fome.atualizar(dt)
        else:
            for stat in (self.fome, self.energia, self.diversao):
                stat.atualizar(dt)

        if self.estado != "idle":
            self.timer_estado -= dt
            if self.timer_estado <= 0:
                self.estado = "idle"

    #Regula o humor
    @property
    def humor(self) -> str:
        media = (self.fome.valor + self.energia.valor + self.diversao.valor) / 3
        if self.estado == "sleeping":
            return "dormindo"
        if media > 65:
            return "feliz"
        if media > 35:
            return "neutra"
        return "triste"

    # Se trata da persistência 
    def to_dict(self) -> dict:
        return {
            "fome": self.fome.valor,
            "energia": self.energia.valor,
            "diversao": self.diversao.valor,
            "nascimento": self.nascimento,
            "salvo_em": time.time(),
        }

    #Permite construir o objeto pela classe 
    @classmethod
    def from_dict(cls, dados: dict) -> "Pet":
        pet = cls()
        pet.fome.valor = dados.get("fome", 80)
        pet.energia.valor = dados.get("energia", 80)
        pet.diversao.valor = dados.get("diversao", 80)
        pet.nascimento = dados.get("nascimento", time.time())

        # Decaimento offline: o tempo passou enquanto o jogo estava fechado
        offline = max(0.0, time.time() - dados.get("salvo_em", time.time()))
        offline = min(offline, 8 * 3600)  # limite de 8h para não "matar" o pet
        for stat in (pet.fome, pet.energia, pet.diversao):
            stat.atualizar(offline)
        return pet


def salvar(pet: Pet):
    with open(SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(pet.to_dict(), f, indent=2)


def carregar() -> Pet:
    if os.path.exists(SAVE_PATH):
        try:
            with open(SAVE_PATH, encoding="utf-8") as f:
                return Pet.from_dict(json.load(f))
        except (json.JSONDecodeError, OSError):
            pass
    return Pet()


# Interface do jogo
# Cria o botão e guarda suas informações
class Button:
    def __init__(self, rect: pygame.Rect, texto: str, cor: tuple, acao):
        self.rect = rect
        self.texto = texto
        self.cor = cor
        self.acao = acao
        
     # Desenha o botão na tela
    def desenhar(self, tela, fonte, mouse_pos):
        hover = self.rect.collidepoint(mouse_pos)
        cor = tuple(min(255, c + 25) for c in self.cor) if hover else self.cor
        pygame.draw.rect(tela, cor, self.rect, border_radius=12)
        label = fonte.render(self.texto, True, (255, 255, 255))
        tela.blit(label, label.get_rect(center=self.rect.center))
        
    # Serve para executar a ação guardada (alimentar, crochê ou dormir)
    def clicar(self, pos):
        if self.rect.collidepoint(pos):
            self.acao()

# Prepara tudo antes do jogo começar
class Game:
    # Serve para criar a janela, carregar o pet e montar os botões (roda 1 vez só)
    def __init__(self):
        pygame.init()
        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption("Maya-Gotchi 🐟🧶")
        self.clock = pygame.time.Clock()
        self.fonte = pygame.font.SysFont("arial", 20, bold=True)
        self.fonte_peq = pygame.font.SysFont("arial", 15)
        self.pet = carregar()
        self.tempo_anim = 0.0
        self.rodando = True

        y = ALTURA - 90
        # Serve para ligar cada botão a uma ação do pet 
        self.botoes = [
            Button(pygame.Rect(40, y, 165, 52), "Sardinha 🐟", (198, 40, 40), self.pet.alimentar),
            Button(pygame.Rect(237, y, 165, 52), "Crochê 🧶", (240, 98, 146), self.pet.fazer_croche),
            Button(pygame.Rect(434, y, 165, 52), "Dormir 💤", (69, 90, 120), self.pet.dormir),
        ]

    # Desenha uma barra de status 
    def desenhar_barra(self, x, y, largura, valor, cor, nome):
        pygame.draw.rect(self.tela, (225, 218, 205), (x, y, largura, 18), border_radius=9)
        w = int(largura * valor / 100)
        if w > 8:
            pygame.draw.rect(self.tela, cor, (x, y, w, 18), border_radius=9)
        label = self.fonte_peq.render(f"{nome}: {int(valor)}", True, COR_TEXTO)
        self.tela.blit(label, (x + 6, y - 20))

    # Desenha a personagem e os acessórios
    def desenhar_pet(self):
        frame = int(self.tempo_anim * 2) % 2
        expressao = self.pet.humor
        # piscar de vez em quando
        if expressao != "dormindo" and int(self.tempo_anim * 10) % 40 == 0:
            expressao = "piscar"
            
        # Gera a imagem do avatar deste quadro
        sprite = grade_para_surface(sprite_maya(expressao, frame))
        # flutuação suave (respiração)
        bob = math.sin(self.tempo_anim * 2.5) * 6
        x = LARGURA // 2 - sprite.get_width() // 2
        y = 210 + int(bob)
        self.tela.blit(sprite, (x, y))

        # acessórios de acordo com o estado
        if self.pet.estado == "eating":
            lata = grade_para_surface(SPRITE_LATA, 8)
            sard = grade_para_surface(SPRITE_SARDINHA, 8)
            self.tela.blit(lata, (x - 100, y + 140))
            mordida = math.sin(self.tempo_anim * 10) * 10
            self.tela.blit(sard, (x + sprite.get_width() - 30 + mordida, y + 80))
        elif self.pet.estado == "crocheting":
            novelo = grade_para_surface(SPRITE_NOVELO, 8)
            gira = math.sin(self.tempo_anim * 6) * 8
            self.tela.blit(novelo, (x + sprite.get_width() + 10, y + 120 + gira))
        elif self.pet.estado == "sleeping":
            for i in range(3):
                t = (self.tempo_anim * 1.5 + i * 0.6) % 2
                z = self.fonte.render("Z", True, PALETA["Z"])
                self.tela.blit(z, (x + sprite.get_width() + 10 + i * 18, y - 20 - t * 30))

    # Serve para montar cada quadro do jogo
    def desenhar(self):
        dormindo = self.pet.estado == "sleeping"
        self.tela.fill(FUNDO_NOITE if dormindo else FUNDO_DIA)

        titulo = self.fonte.render("Maya-Gotchi", True,
                                   (240, 240, 240) if dormindo else COR_TEXTO)
        self.tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 24))

        # Subtítulo com idade e humor
        idade_h = (time.time() - self.pet.nascimento) / 3600
        sub = self.fonte_peq.render(
            f"idade: {idade_h:.1f}h  •  humor: {self.pet.humor}", True,
            (200, 205, 215) if dormindo else (140, 130, 120))
        self.tela.blit(sub, (LARGURA // 2 - sub.get_width() // 2, 52))

        # painel de stats
        painel = pygame.Rect(40, 90, LARGURA - 80, 90)
        pygame.draw.rect(self.tela, COR_PAINEL, painel, border_radius=16)
        self.desenhar_barra(60, 130, 150, self.pet.fome.valor, (198, 40, 40), "Fome")
        self.desenhar_barra(245, 130, 150, self.pet.energia.valor, (42, 157, 143), "Energia")
        self.desenhar_barra(430, 130, 150, self.pet.diversao.valor, (240, 98, 146), "Diversão")

        # Desenha o avatar por cima do fundo
        self.desenhar_pet()

        # Desenha os botões
        mouse = pygame.mouse.get_pos()
        for b in self.botoes:
            b.desenhar(self.tela, self.fonte, mouse)

         #Mostra o quadro pronto na tela
        pygame.display.flip()

    # Serve para repetir eventos -> atualizar -> desenhar até a janela fechar
    def executar(self):
        ultimo_save = time.time()
        while self.rodando:
            dt = self.clock.tick(FPS) / 1000.0
            self.tempo_anim += dt

            #Executar
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    self.rodando = False
                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    for b in self.botoes:
                        b.clicar(evento.pos)

            #Atualizar
            self.pet.atualizar(dt)

            #Salvar
            if time.time() - ultimo_save > 10:   # autosave a cada 10s
                salvar(self.pet)
                ultimo_save = time.time()

            #Desenhar
            self.desenhar()

        # Save final ao fechar 
        salvar(self.pet)
        pygame.quit()

# Serve para permitir importar as classes em outro arquivo sem abrir o jogo
if __name__ == "__main__":
    Game().executar()
