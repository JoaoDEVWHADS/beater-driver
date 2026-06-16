import pygame
import sys
import numpy as np
import math
from scripts.audio_engine import AudioEngine
from scripts.carro import Carro
from scripts.interface import MenuPrincipal 
from scripts.jogador import Jogador
from scripts.mapa import MapaCidade
from scripts.uber_system import UberSystem # Importando o novo sistema exportado!
from scripts.config import obter_caminho_recurso

pygame.init()
tela = pygame.display.set_mode((400, 420)) 
pygame.display.set_caption("Ride Share: Brazil")
relogio = pygame.time.Clock()

audio = AudioEngine()
carro = Carro(audio)
jogador = Jogador(audio)
mapa = MapaCidade()
menu = MenuPrincipal(audio)

# Instanciando o sistema Uber passando a carteira do menu
uber = UberSystem(audio, menu)

# --- SISTEMA DE ÁUDIO DO PISO ---
rua_atual_nome = ""
canal_asfalto = pygame.mixer.Channel(10)
canal_terra = pygame.mixer.Channel(11)

try:
    som_loop_asfalto = pygame.mixer.Sound(obter_caminho_recurso("audio/pista_ambiente/asfalto_loop.wav"))
    som_loop_terra = pygame.mixer.Sound(obter_caminho_recurso("audio/pista_ambiente/terra_loop.wav"))
    canal_asfalto.play(som_loop_asfalto, loops=-1)
    canal_asfalto.set_volume(0.0)
    canal_terra.play(som_loop_terra, loops=-1)
    canal_terra.set_volume(0.0)
except Exception as e:
    print(f"Aviso: Não foi possível carregar os loops de ambiente: {e}")

def gerar_bipe_codigo(frequencia, duracao, vol_esq=1.0, vol_dir=1.0):
    amostragem = 44100
    num_amostras = int(duracao * (amostragem / 1000.0))
    t = np.linspace(0, duracao / 1000.0, num_amostras, False)
    onda = np.sin(frequencia * t * 2 * np.pi)
    onda_int = (onda * 16384).astype(np.int16)
    estereo = np.column_stack((onda_int, onda_int))
    estereo[:, 0] = (estereo[:, 0] * vol_esq).astype(np.int16)
    estereo[:, 1] = (estereo[:, 1] * vol_dir).astype(np.int16)
    return pygame.sndarray.make_sound(estereo)

estado_jogo = "MENU" 

rodando_geral = True
while rodando_geral:
    
    tempo_atual = pygame.time.get_ticks()
    teclas = pygame.key.get_pressed()

    if estado_jogo == "MENU":
        opcao_escolhida = menu.iniciar(tela, relogio)
        if opcao_escolhida == "Sair":
            rodando_geral = False
            break
        elif opcao_escolhida == "Carreira":
            carro_escolhido = menu.abrir_selecao_carro(tela, relogio)
            if carro_escolhido is None:
                continue
            carro.definir_modelo(carro_escolhido)
            carro.no_carro = False
            
            # Recarrega os sons de pista e pneus de acordo com as especificidades do novo carro
            try:
                canal_asfalto.stop()
            except:
                pass
            try:
                canal_terra.stop()
            except:
                pass
                
            try:
                som_loop_asfalto = pygame.mixer.Sound(obter_caminho_recurso(carro.som_asfalto))
                canal_asfalto.play(som_loop_asfalto, loops=-1)
                canal_asfalto.set_volume(0.0)
            except Exception as e:
                print(f"Aviso: Não foi possível carregar asfalto loop: {e}")
                
            try:
                som_loop_terra = pygame.mixer.Sound(obter_caminho_recurso(carro.som_terra))
                canal_terra.play(som_loop_terra, loops=-1)
                canal_terra.set_volume(0.0)
            except Exception as e:
                print(f"Aviso: Não foi possível carregar terra loop: {e}")
                
            estado_jogo = "MODOLIVRE"
            uber.estado_app = "MODOLIVRE"
            audio.falar(f"Modo Carreira iniciado. Seu {carro.nome} está estacionado. Segure a tecla L para entrar e ligar o motor, ou aperte P para abrir o celular.")
            continue

    tecla_partida_segurada = False
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando_geral = False
            sys.exit()
            
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                carro.motor_ligado = False
                carro.tentando_partida = False
                audio.motor_stop()
                estado_jogo = "MENU"
                pygame.time.wait(200)

            # SE ESTIVER EDITANDO O NOME NO CADASTRO, ENCAMINHA PARA A DIGITAÇÃO DE TEXTO LIVRE
            if uber.estado_app == "CELULAR_CADASTRO" and uber.etapa_cadastro == 1:
                uber.tratar_entrada_texto(evento)
            else:
                # Trata as etapas numéricas do cadastro (Etapa 2 e 3)
                if uber.estado_app == "CELULAR_CADASTRO":
                    uber.tratar_teclado_cadastro(evento.key)

                # Ignição (Tecla L)
                if evento.key == pygame.K_l:
                    if carro.motor_ligado:
                        carro.ligar_desligar_motor(desligar_forcado=True)
                    else:
                        carro.ligar_desligar_motor()

                # Controle do Celular via UberSystem (Tecla P)
                if evento.key == pygame.K_p:
                    uber.abrir_celular()

                # Confirmações no Aplicativo (CORREÇÃO DO FECHAMENTO DO JOGO: Passando o argumento 'mapa')
                if evento.key == pygame.K_SPACE:
                    uber.confirmar_acao_espaco(tempo_atual, carro, mapa)

                # Câmbio Automático (Setas)
                if evento.key == pygame.K_UP: carro.subir_marcha()
                if evento.key == pygame.K_DOWN: carro.reduzir_marcha()
                    
                # Painel do Carro (1 a 5)
                if evento.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5]:
                    carro.ler_item_painel(evento.key)
                    
                # GPS por voz (Tecla F)
                if evento.key == pygame.K_f:
                    uber.falar_gps(carro)

    if teclas[pygame.K_l] and not carro.motor_ligado:
        tecla_partida_segurada = True

    # Movimentação física do veículo independente do app
    carro.atualizar(teclas, tecla_partida_segurada)
    
    # Executa a lógica delegada do Uber
    uber.atualizar_logica(tempo_atual, carro, gerar_bipe_codigo)

    # Monitoramento do Asfalto e Sons de Pneus
    if estado_jogo != "MENU":
        piso_detectado, nome_da_rua = mapa.obter_piso_e_rua(carro.x, carro.y)

        if nome_da_rua != rua_atual_nome:
            rua_atual_nome = nome_da_rua
            audio.falar(f"Entrou na {rua_atual_nome}")

        if carro.motor_ligado and carro.velocidade > 0.5:
            volume_alvo = min(carro.velocidade / 60.0, 0.7)
            if piso_detectado == "asfalto":
                canal_asfalto.set_volume(volume_alvo)
                canal_terra.set_volume(0.0)
            else:
                canal_terra.set_volume(volume_alvo)
                canal_asfalto.set_volume(0.0)
        else:
            canal_asfalto.set_volume(0.0)
            canal_terra.set_volume(0.0)

    # Adicionado fundo visual simples para a caixa de texto renderizar profissionalmente
    tela.fill((10, 10, 15))
    if uber.estado_app == "CELULAR_CADASTRO" and uber.etapa_cadastro == 1:
        # Renderiza visualmente o texto digitado na tela do jogo para ficar profissional
        fonte_input = pygame.font.SysFont("Arial", 24)
        txt_label = fonte_input.render("Digite seu nome e aperte ENTER:", True, (255, 255, 255))
        txt_digitado = fonte_input.render(uber.cadastro_nome + "|", True, (0, 255, 0))
        tela.blit(txt_label, (20, 150))
        tela.blit(txt_digitado, (20, 190))

    pygame.display.flip()
    relogio.tick(60)