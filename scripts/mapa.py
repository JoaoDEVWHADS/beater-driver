# scripts/mapa.py

class Rua:
    def __init__(self, nome, x_min, x_max, y_min, y_max, tipo_piso="asfalto"):
        self.nome = nome
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.tipo_piso = tipo_piso  # "asfalto" ou "terra"

    def contem_posicao(self, x, y):
        return self.x_min <= x <= self.x_max and self.y_min <= y <= self.y_max


class MapaCidade:
    def __init__(self):
        self.ruas = []
        self.configurar_mapa_padrao()
        self.gerar_cidade_gigante()

    def configurar_mapa_padrao(self):
        # Suas ruas originais preservadas no centro do mapa
        self.ruas.append(Rua("Avenida Central", -500, 500, -20, 20, "asfalto"))
        self.ruas.append(Rua("Rua dos Buracos", -30, 30, -500, 500, "terra"))
        self.ruas.append(Rua("Beco do Chevette", 100, 300, 100, 130, "terra"))

    def gerar_cidade_gigante(self):
        """Gerador automático de malha urbana com mais de 60 ruas interligadas"""
        
        # 1. GRANDES AVENIDAS HORIZONTAIS (Leste-Oeste) - Cortam o mapa de ponta a ponta
        # Largura de 40 metros cada (Y_min a Y_max) estendendo-se por 6000 metros de comprimento
        avenidas_h = [
            ("Avenida Marginal Norte", -2500),
            ("Avenida dos Autores", -1800),
            ("Avenida Dragon", -1200),
            ("Avenida Industrial", -600),
            ("Avenida dos Jacarandás", 600),
            ("Avenida Carrelo", 1200),
            ("Avenida dos Esportes", 1800),
            ("Avenida Marginal Sul", 2500)
        ]
        for nome, y_centro in avenidas_h:
            self.ruas.append(Rua(nome, -3000, 3000, y_centro - 20, y_centro + 20, "asfalto"))

        # 2. GRANDES AVENIDAS VERTICAIS (Norte-Sul) - Cruzam as horizontais perfeitamente
        # Largura de 40 metros cada (X_min a X_max) estendendo-se por 6000 metros de altura
        avenidas_v = [
            ("Avenida Leste Suprema", 2500),
            ("Avenida Panorâmica", 1800),
            ("Avenida do Comércio", 1200),
            ("Avenida das Nações", 600),
            ("Avenida Oeste Divisória", -600),
            ("Avenida Tecnológica", -1200),
            ("Avenida da Saudade", -1800),
            ("Avenida Velha Oeste", -2500)
        ]
        for nome, x_centro in avenidas_v:
            self.ruas.append(Rua(nome, x_centro - 20, x_centro + 20, -3000, 3000, "asfalto"))

        # 3. RUAS SECUNDÁRIAS DE BAIRRO (Asfalto - Interligando as Avenidas)
        # Vamos criar blocos residenciais e comerciais numerados em posições calculadas
        nomes_ruas_h = [
            "Rua dos Pinheiros", "Rua das Palmeiras", "Rua dos Girassóis", "Rua Santa Maria", 
            "Rua São Jorge", "Rua da Paz", "Rua Bela Vista", "Rua Tiradentes", 
            "Rua Quinze de Novembro", "Rua Sete de Setembro", "Rua Amazonas", "Rua Bahia",
            "Rua Paraná", "Rua Rio de Janeiro", "Rua Minas Gerais", "Rua São Paulo"
        ]
        
        # Gerando 16 ruas horizontais menores em diferentes quadrantes
        for i, nome in enumerate(nomes_ruas_h):
            y_pos = -2200 + (i * 300)
            if y_pos == 0 or abs(y_pos) in [600, 1200, 1800, 2500]: 
                y_pos += 70 # Desvia para não encavalar com as grandes avenidas
            self.ruas.append(Rua(nome, -2000, 2000, y_pos - 12, y_pos + 12, "asfalto"))

        nomes_ruas_v = [
            "Rua Rui Barbosa", "Rua Castro Alves", "Rua Machado de Assis", "Rua Carlos Drummond",
            "Rua Clarice Lispector", "Rua Cecília Meireles", "Rua Guimarães Rosa", "Rua Jorge Amado",
            "Rua Anita Garibaldi", "Rua Princesa Isabel", "Rua Duque de Caxias", "Rua Marechal Deodoro",
            "Rua Benjamin Constant", "Rua de Trás", "Rua da Frente", "Rua do Meio"
        ]
        
        # Gerando 16 ruas verticais menores em diferentes quadrantes
        for i, nome in enumerate(nomes_ruas_v):
            x_pos = -2200 + (i * 300)
            if x_pos == 0 or abs(x_pos) in [600, 1200, 1800, 2500]:
                x_pos += 70 # Desvia para não encavalar
            self.ruas.append(Rua(nome, x_pos - 12, x_pos + 12, -2000, 2000, "asfalto"))

        # 4. BAIRRO PERIFÉRICO / RURAL (Estradas de Terra Distantes e Perigosas)
        # Perfeito para testar a suspensão do Chevette e cobrar mais caro no Uber!
        estradas_terra = [
            # Estradas horizontais distantes
            ("Estrada do Capão Redondo", -3500, 3500, -2900, -2850),
            ("Estrada da Cachoeira", -3500, 3500, 2850, 2900),
            ("Caminho Velho do Sítio", -2800, -500, 1500, 1540),
            ("Linha Rural do Norte", 500, 2800, -1540, -1500),
            # Estradas verticais distantes
            ("Estrada da Olaria", -2900, -2850, -3500, 3500),
            ("Estrada da Mineração", 2850, 2900, -3500, 3500),
            ("Ramal dos Eucaliptos", -1540, -1500, -2800, -500),
            ("Travessa da Fazenda", 1500, 1540, 500, 2800)
        ]
        for nome, x1, x2, y1, y2 in estradas_terra:
            self.ruas.append(Rua(nome, x1, x2, y1, y2, "terra"))

        # 5. PEQUENOS BECOS E TRAVESSAS (Caminhos curtos e apertados para manobrar)
        # Adiciona variedade extra totalizando mais de 65 ruas
        becos = [
            ("Beco da Lama", -200, -100, -400, -380, "terra"),
            ("Travessa do Perigo", 400, 430, -800, -400, "asfalto"),
            ("Viela Escura", -800, -400, 800, 830, "terra"),
            ("Beco do Corsa", 1300, 1600, 1300, 1330, "asfalto"),
            ("Travessa do Gol", -1600, -1300, -1330, -1300, "asfalto")
        ]
        for nome, x1, x2, y1, y2, piso in becos:
            self.ruas.append(Rua(nome, x1, x2, y1, y2, piso))

    def obter_piso_e_rua(self, x, y):
        # Varre de trás para frente para dar prioridade para becos e ruas menores sobre as grandes avenidas
        for rua in reversed(self.ruas):
            if rua.contem_posicao(x, y):
                return rua.tipo_piso, rua.nome
        # Se sair das ruas, vira terreno baldio de terra
        return "terra", "Terreno Baldio"