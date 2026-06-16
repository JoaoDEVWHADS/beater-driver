import os
import wave
import array

def aplicar_filtro_abafamento(caminho_entrada, caminho_saida, cutoff=600):
    try:
        if not os.path.exists(caminho_entrada):
            print(f"Aviso: {caminho_entrada} nao existe.")
            return False
            
        print(f"Abafando som: {caminho_entrada} -> {caminho_saida}")
        with wave.open(caminho_entrada, 'rb') as w_in:
            params = w_in.getparams()
            nchannels, sampwidth, framerate, nframes = params[:4]
            raw_data = w_in.readframes(nframes)
            
        # Converte para array de inteiros de 16 bits nativo do Python (tipo 'h')
        if sampwidth == 2:
            data = array.array('h')
            data.frombytes(raw_data)
        else:
            # Caso não seja 16-bit, copia diretamente
            with open(caminho_saida, 'wb') as f:
                f.write(raw_data)
            return True

        # Tamanho da janela de suavização
        window_size = int(framerate / cutoff)
        if window_size < 1:
            window_size = 1

        # Média móvel em Python puro
        dados_filtrados = array.array('h', [0] * len(data))
        current_sum = sum(data[:window_size])
        
        # Filtro de suavização
        for i in range(len(data)):
            # Atualiza a janela deslizante
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(data), i + window_size // 2)
            window_len = end_idx - start_idx
            
            # Média dos elementos na janela
            val_media = sum(data[start_idx:end_idx]) // window_len
            
            # Reduz volume ligeiramente (multiplica por 0.75)
            dados_filtrados[i] = int(val_media * 0.75)
            
        # Grava o resultado abafado
        with wave.open(caminho_saida, 'wb') as w_out:
            w_out.setparams(params)
            w_out.writeframes(dados_filtrados.tobytes())
            
        print("Som abafado com sucesso!")
        return True
    except Exception as e:
        print(f"Erro ao filtrar {caminho_entrada}: {e}")
        return False

# Garante que os arquivos base de pista existem em audio/pista_ambiente/
import shutil

pista_ambiente = "audio/pista_ambiente"
if not os.path.exists(f"{pista_ambiente}/rua_loop.wav") and os.path.exists(f"{pista_ambiente}/asfalto_loop.wav"):
    print("Criando rua_loop.wav a partir de asfalto_loop.wav...")
    shutil.copyfile(f"{pista_ambiente}/asfalto_loop.wav", f"{pista_ambiente}/rua_loop.wav")

if not os.path.exists(f"{pista_ambiente}/estrada_loop.wav") and os.path.exists(f"{pista_ambiente}/terra_loop.wav"):
    print("Criando estrada_loop.wav a partir de terra_loop.wav...")
    shutil.copyfile(f"{pista_ambiente}/terra_loop.wav", f"{pista_ambiente}/estrada_loop.wav")

if not os.path.exists(f"{pista_ambiente}/lama_loop.wav") and os.path.exists(f"{pista_ambiente}/terra_loop.wav"):
    print("Criando lama_loop.wav a partir de terra_loop.wav...")
    shutil.copyfile(f"{pista_ambiente}/terra_loop.wav", f"{pista_ambiente}/lama_loop.wav")

# Aplica nos sons de motor internos da cabine (dentro/)
pasta_corolla = "audio/carros/corolla"
aplicar_filtro_abafamento(f"{pasta_corolla}/fora/idle.wav", f"{pasta_corolla}/dentro/idle.wav", cutoff=400)
aplicar_filtro_abafamento(f"{pasta_corolla}/fora/low.wav", f"{pasta_corolla}/dentro/low.wav", cutoff=450)
aplicar_filtro_abafamento(f"{pasta_corolla}/fora/mid.wav", f"{pasta_corolla}/dentro/mid.wav", cutoff=500)
aplicar_filtro_abafamento(f"{pasta_corolla}/fora/high.wav", f"{pasta_corolla}/dentro/high.wav", cutoff=550)
aplicar_filtro_abafamento(f"{pasta_corolla}/fora/pipoco.wav", f"{pasta_corolla}/dentro/pipoco.wav", cutoff=300)

# Aplica nas ações mecânicas internas da cabine (dentro/)
# (ligar, marcha, freio fora vs dentro)
aplicar_filtro_abafamento(f"{pasta_corolla}/ligar.wav", f"{pasta_corolla}/fora/ligar.wav", cutoff=2000) # Fora é quase original
aplicar_filtro_abafamento(f"{pasta_corolla}/ligar.wav", f"{pasta_corolla}/dentro/ligar.wav", cutoff=500) # Dentro é bem abafado

aplicar_filtro_abafamento(f"{pasta_corolla}/marcha.wav", f"{pasta_corolla}/fora/marcha.wav", cutoff=2000)
aplicar_filtro_abafamento(f"{pasta_corolla}/marcha.wav", f"{pasta_corolla}/dentro/marcha.wav", cutoff=500)

aplicar_filtro_abafamento(f"{pasta_corolla}/freio.wav", f"{pasta_corolla}/fora/freio.wav", cutoff=1800)
aplicar_filtro_abafamento(f"{pasta_corolla}/freio.wav", f"{pasta_corolla}/dentro/freio.wav", cutoff=400)

# Copia os loops de pista/solo padrão de fora e cria versões filtradas para dentro
# (Simula som de rua/piso de forma abafada)
aplicar_filtro_abafamento("audio/pista_ambiente/asfalto_loop.wav", f"{pasta_corolla}/fora/asfalto_loop.wav", cutoff=2000)
aplicar_filtro_abafamento("audio/pista_ambiente/asfalto_loop.wav", f"{pasta_corolla}/dentro/asfalto_loop.wav", cutoff=350)

aplicar_filtro_abafamento("audio/pista_ambiente/terra_loop.wav", f"{pasta_corolla}/fora/terra_loop.wav", cutoff=2000)
aplicar_filtro_abafamento("audio/pista_ambiente/terra_loop.wav", f"{pasta_corolla}/dentro/terra_loop.wav", cutoff=350)

aplicar_filtro_abafamento("audio/pista_ambiente/lama_loop.wav", f"{pasta_corolla}/fora/lama_loop.wav", cutoff=2000)
aplicar_filtro_abafamento("audio/pista_ambiente/lama_loop.wav", f"{pasta_corolla}/dentro/lama_loop.wav", cutoff=300)

aplicar_filtro_abafamento("audio/pista_ambiente/estrada_loop.wav", f"{pasta_corolla}/fora/estrada_loop.wav", cutoff=2000)
aplicar_filtro_abafamento("audio/pista_ambiente/estrada_loop.wav", f"{pasta_corolla}/dentro/estrada_loop.wav", cutoff=350)

aplicar_filtro_abafamento("audio/pista_ambiente/rua_loop.wav", f"{pasta_corolla}/fora/rua_loop.wav", cutoff=2000)
aplicar_filtro_abafamento("audio/pista_ambiente/rua_loop.wav", f"{pasta_corolla}/dentro/rua_loop.wav", cutoff=350)

print("Ajuste acústico finalizado!")
