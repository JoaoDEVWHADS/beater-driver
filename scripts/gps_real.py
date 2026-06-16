import os
import math
import hashlib
import threading
import requests
import pygame
from gtts import gTTS
from scripts.config import obter_caminho_recurso

# Centro de São Paulo (Metrô Jabaquara)
LAT_CENTRO = -23.6465
LON_CENTRO = -46.6412

# Fatores de conversão de metros para coordenadas
# 1 grau de latitude ~ 111.120 metros
# 1 grau de longitude ~ 111.120 metros * cos(lat)
METRO_POR_GRAU_LAT = 111120.0
COS_LAT_CENTRO = math.cos(math.radians(LAT_CENTRO))
METRO_POR_GRAU_LON = METRO_POR_GRAU_LAT * COS_LAT_CENTRO

def local_para_real(x, y):
    """Converte coordenadas locais (x, y) do jogo para latitude e longitude reais."""
    # X aumenta para Leste, Y aumenta para Sul (ou seja, -Y vai para o Norte)
    lat = LAT_CENTRO - (y / METRO_POR_GRAU_LAT)
    lon = LON_CENTRO + (x / METRO_POR_GRAU_LON)
    return lat, lon

def real_para_local(lat, lon):
    """Converte latitude e longitude reais para coordenadas locais (x, y) do jogo."""
    y = -(lat - LAT_CENTRO) * METRO_POR_GRAU_LAT
    x = (lon - LON_CENTRO) * METRO_POR_GRAU_LON
    return x, y

class GPSReal:
    def __init__(self, audio):
        self.audio = audio
        self.offline = False
        
        # Canal dedicado de áudio para o GPS (canal 9)
        self.canal_gps = pygame.mixer.Channel(9)
        
        # Pasta de cache para as falas do gTTS
        self.cache_dir = obter_caminho_recurso("audio/gps_cache")
        if not os.path.exists(self.cache_dir):
            try:
                os.makedirs(self.cache_dir, exist_ok=True)
            except Exception as e:
                print(f"Erro ao criar pasta de cache do GPS: {e}")

        # Estado da navegação
        self.destino_ativo = False
        self.modo_passeio = True  # Começa no modo passeio livre por SP
        
        self.destino_lat = None
        self.destino_lon = None
        self.destino_x = 0.0
        self.destino_y = 0.0
        self.destino_nome = ""

        # Rota atual calculada pelo OSRM
        self.rota_pontos = []      # Lista de (x, y) locais
        self.rota_passos = []      # Passos da rota curva-a-curva
        self.distancia_total = 0.0 # Em metros
        self.tempo_total = 0.0      # Em segundos
        
        # Monitoramento de trajetos
        self.ultimo_passo_anunciado = -1
        self.ultima_rua_anunciada = ""
        self.proximo_aviso_curva_dist = -1
        
        # Variáveis de controle para o Modo Passeio Livre
        self.ultimo_x_passeio = -9999.0
        self.ultimo_y_passeio = -9999.0
        self.tempo_ultimo_reverse = 0
        self.thread_reverse_ativa = False
        
        # Estado de busca (para interface do app)
        self.buscando = False
        self.erro_busca = ""
        self.sucesso_busca = False

    def falar(self, texto):
        """Gera e reproduz o texto com a voz do Google (gTTS) em background/cache."""
        if not texto:
            return
            
        print(f"GPS Voz: {texto}")
        
        # Se estiver offline de propósito ou sem gtts, fala via sistema padrão (leitor de tela)
        if self.offline:
            self.audio.falar(texto)
            return

        def _worker():
            try:
                # Cria nome do arquivo baseado no hash do texto para o cache
                md5_name = hashlib.md5(texto.encode("utf-8")).hexdigest() + ".mp3"
                caminho_file = os.path.join(self.cache_dir, md5_name)
                
                if not os.path.exists(caminho_file):
                    tts = gTTS(text=texto, lang="pt")
                    tts.save(caminho_file)
                
                # Toca o áudio gerado
                pygame.mixer.init()
                sound = pygame.mixer.Sound(caminho_file)
                self.canal_gps.play(sound)
            except Exception as e:
                print(f"Erro na geração de voz gTTS: {e}. Usando leitor padrão.")
                self.audio.falar(texto)

        threading.Thread(target=_worker, daemon=True).start()

    def limpar_destino(self):
        """Limpa o destino ativo e retorna para o modo rolê/passeio livre por SP."""
        self.destino_ativo = False
        self.modo_passeio = True
        self.destino_lat = None
        self.destino_lon = None
        self.destino_nome = ""
        self.rota_pontos = []
        self.rota_passos = []
        self.ultimo_passo_anunciado = -1
        self.ultima_rua_anunciada = ""
        self.falar("Destino cancelado. Iniciando passeio livre por São Paulo.")

    def buscar_por_cep(self, cep, numero, carro_x, carro_y):
        """Busca o destino assincronamente a partir de um CEP e número."""
        self.buscando = True
        self.erro_busca = ""
        self.sucesso_busca = False
        
        def _worker():
            try:
                # 1. Consulta ViaCEP
                cep_limpo = cep.replace("-", "").replace(" ", "").strip()
                res = requests.get(f"https://viacep.com.br/ws/{cep_limpo}/json/", timeout=5)
                if res.status_code != 200:
                    raise Exception("Erro ao acessar API do CEP.")
                
                dados_cep = res.json()
                if "erro" in dados_cep:
                    raise Exception("CEP não encontrado.")
                
                logradouro = dados_cep.get("logradouro", "")
                bairro = dados_cep.get("bairro", "")
                cidade = dados_cep.get("localidade", "São Paulo")
                
                if not logradouro:
                    raise Exception("CEP sem logradouro definido.")

                # 2. Geocodificação Nominatim
                endereco_busca = f"{logradouro}, {numero}, {bairro}, {cidade}, SP, Brasil"
                headers = {"User-Agent": "BeaterDriverGPS/1.0 (contact: admin@beaterdriver.com)"}
                url_geo = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(endereco_busca)}&format=json&limit=1"
                
                res_geo = requests.get(url_geo, headers=headers, timeout=5)
                if res_geo.status_code != 200 or not res_geo.json():
                    # Tenta sem o número se falhar
                    endereco_busca_sem_num = f"{logradouro}, {bairro}, {cidade}, SP, Brasil"
                    url_geo = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(endereco_busca_sem_num)}&format=json&limit=1"
                    res_geo = requests.get(url_geo, headers=headers, timeout=5)
                    
                dados_geo = res_geo.json()
                if not dados_geo:
                    raise Exception("Endereço não localizado no mapa.")
                
                lat = float(dados_geo[0]["lat"])
                lon = float(dados_geo[0]["lon"])
                
                # 3. Calcula Rota (OSRM)
                self.calcular_rota(carro_x, carro_y, lat, lon, f"{logradouro}, {numero}")
                
            except Exception as e:
                print(f"Erro no worker de busca: {e}")
                self.erro_busca = str(e)
                self.buscando = False
                self.falar(f"Falha ao obter rota: {self.erro_busca}")

        threading.Thread(target=_worker, daemon=True).start()

    def calcular_rota(self, start_x, start_y, end_lat, end_lon, nome_destino):
        """Calcula a rota curva-a-curva via OSRM."""
        start_lat, start_lon = local_para_real(start_x, start_y)
        
        try:
            url_osrm = (
                f"http://router.project-osrm.org/route/v1/driving/"
                f"{start_lon},{start_lat};{end_lon},{end_lat}"
                f"?overview=full&geometries=geojson&steps=true&language=pt"
            )
            res = requests.get(url_osrm, timeout=5)
            if res.status_code != 200:
                raise Exception("Servidor de rotas offline.")
                
            dados = res.json()
            if "routes" not in dados or not dados["routes"]:
                raise Exception("Rota não encontrada.")
                
            rota = dados["routes"][0]
            self.distancia_total = float(rota["distance"])
            self.tempo_total = float(rota["duration"])
            
            # Extrai pontos da geometria
            coords = rota["geometry"]["coordinates"]
            self.rota_pontos = [real_para_local(c[1], c[0]) for c in coords]
            
            # Extrai passos
            self.rota_passos = []
            legs = rota.get("legs", [])
            for leg in legs:
                steps = leg.get("steps", [])
                for step in steps:
                    step_coords = step["geometry"]["coordinates"][0] # primeiro ponto
                    step_x, step_y = real_para_local(step_coords[1], step_coords[0])
                    self.rota_passos.append({
                        "x": step_x,
                        "y": step_y,
                        "distancia": step.get("distance", 0.0),
                        "rua": step.get("name", "via"),
                        "instrucao": step.get("maneuver", {}).get("instruction", "Siga em frente"),
                        "anunciado": False
                    })
            
            self.destino_lat = end_lat
            self.destino_lon = end_lon
            self.destino_x, self.destino_y = real_para_local(end_lat, end_lon)
            self.destino_nome = nome_destino
            
            self.destino_ativo = True
            self.modo_passeio = False
            self.ultimo_passo_anunciado = -1
            self.buscando = False
            self.sucesso_busca = True
            
            minutos = int(self.tempo_total / 60)
            dist_km = round(self.distancia_total / 1000, 1)
            self.falar(f"Rota calculada para {self.destino_nome}. Distância de {dist_km} quilômetros. Tempo estimado de {minutos} minutos.")
            
        except Exception as e:
            print(f"Erro no cálculo de rota: {e}")
            self.offline_fallback(start_x, start_y, end_lat, end_lon, nome_destino)

    def offline_fallback(self, start_x, start_y, end_lat, end_lon, nome_destino):
        """Fallback simples local caso o GPS esteja offline."""
        self.destino_lat = end_lat
        self.destino_lon = end_lon
        self.destino_x, self.destino_y = real_para_local(end_lat, end_lon)
        self.destino_nome = nome_destino
        
        # Cria uma linha reta simples como rota
        self.rota_pontos = [(start_x, start_y), (self.destino_x, self.destino_y)]
        self.rota_passos = [{
            "x": self.destino_x,
            "y": self.destino_y,
            "distancia": math.sqrt((self.destino_x - start_x)**2 + (self.destino_y - start_y)**2),
            "rua": nome_destino,
            "instrucao": f"Siga em frente até {nome_destino}",
            "anunciado": False
        }]
        self.distancia_total = self.rota_passos[0]["distancia"]
        self.tempo_total = self.distancia_total / 12.0 # média de 43 km/h
        
        self.destino_ativo = True
        self.modo_passeio = False
        self.ultimo_passo_anunciado = -1
        self.buscando = False
        self.sucesso_busca = True
        
        dist_km = round(self.distancia_total / 1000, 1)
        self.falar(f"GPS Offline: Rota em linha reta calculada para {self.destino_nome}. Distância aproximada de {dist_km} quilômetros.")

    def atualizar(self, carro_x, carro_y, tempo_atual):
        """Atualiza a lógica do GPS a cada quadro (tick)."""
        if self.modo_passeio:
            # Passeio Livre por SP: anuncia rua/bairro de passagem a cada 100 metros
            dist_movida = math.sqrt((carro_x - self.ultimo_x_passeio)**2 + (carro_y - self.ultimo_y_passeio)**2)
            if dist_movida >= 100.0:
                if tempo_atual - self.tempo_ultimo_reverse > 10000 and not self.thread_reverse_ativa:
                    self.ultimo_x_passeio = carro_x
                    self.ultimo_y_passeio = carro_y
                    self.tempo_ultimo_reverse = tempo_atual
                    self.reverso_geocode_async(carro_x, carro_y)
        
        elif self.destino_ativo and self.rota_passos:
            # Navegação guiada dinâmica (suporta marcha à ré e re-anúncios)
            # Reseta o anúncio se o carro se afastar mais de 150m do último passo anunciado
            if self.ultimo_passo_anunciado != -1:
                last_passo = self.rota_passos[self.ultimo_passo_anunciado]
                dx = last_passo["x"] - carro_x
                dy = last_passo["y"] - carro_y
                dist_last = math.sqrt(dx**2 + dy**2)
                if dist_last > 150.0:
                    self.ultimo_passo_anunciado = -1

            # Acha o passo mais próximo à frente ou atrás
            passo_mais_proximo_idx = -1
            menor_dist = 999999.0
            
            for i, passo in enumerate(self.rota_passos):
                dx = passo["x"] - carro_x
                dy = passo["y"] - carro_y
                dist_passo = math.sqrt(dx**2 + dy**2)
                if dist_passo < menor_dist:
                    menor_dist = dist_passo
                    passo_mais_proximo_idx = i
            
            if passo_mais_proximo_idx != -1 and menor_dist <= 120.0:
                passo = self.rota_passos[passo_mais_proximo_idx]
                # Só anuncia se não for o último passo anunciado
                if self.ultimo_passo_anunciado != passo_mais_proximo_idx:
                    self.ultimo_passo_anunciado = passo_mais_proximo_idx
                    # Prepara a mensagem amigável com a distância em metros
                    inst_limpa = passo['instrucao'].replace("Vire", "vire").replace("Siga", "siga")
                    self.falar(f"Em {int(menor_dist)} metros, {inst_limpa}")
            
            # Chegou ao destino?
            dx_dest = self.destino_x - carro_x
            dy_dest = self.destino_y - carro_y
            dist_restante = math.sqrt(dx_dest**2 + dy_dest**2)
            if dist_restante <= 25.0:
                self.falar("Você chegou ao seu destino.")
                self.destino_ativo = False

    def reverso_geocode_async(self, x, y):
        """Chama a API do Nominatim em background para descobrir o endereço atual no passeio livre."""
        self.thread_reverse_ativa = True
        lat, lon = local_para_real(x, y)
        
        def _worker():
            try:
                headers = {"User-Agent": "BeaterDriverGPS/1.0 (contact: admin@beaterdriver.com)"}
                url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&zoom=18"
                res = requests.get(url, headers=headers, timeout=5)
                if res.status_code == 200:
                    dados = res.json()
                    address = dados.get("address", {})
                    road = address.get("road", address.get("suburb", "via de São Paulo"))
                    suburb = address.get("suburb", "")
                    
                    if road != self.ultima_rua_anunciada:
                        self.ultima_rua_anunciada = road
                        msg = f"Você está na {road}"
                        if suburb:
                            msg += f", bairro {suburb}"
                        self.falar(msg)
            except Exception as e:
                print(f"Erro no geocode reverso: {e}")
            finally:
                self.thread_reverse_ativa = False

        threading.Thread(target=_worker, daemon=True).start()

    def falar_status_viagem(self, carro_x, carro_y):
        """Informa a distância e o tempo estimado restante da rota."""
        if not self.destino_ativo:
            self.falar("Passeio livre por São Paulo. Sem rota ativa.")
            return

        dx = self.destino_x - carro_x
        dy = self.destino_y - carro_y
        dist = math.sqrt(dx**2 + dy**2)
        dist_km = round(dist / 1000.0, 1)
        
        # Estimativa de tempo baseado na distância restante proporcional
        tempo_estimado_min = int((dist / max(1.0, self.distancia_total)) * self.tempo_total / 60.0)
        tempo_estimado_min = max(1, tempo_estimado_min)
        
        self.falar(f"Faltam {dist_km} quilômetros para o destino. Tempo restante estimado: {tempo_estimado_min} minutos.")
