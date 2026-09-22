import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime
import pytz
import sys

# ---------------------------------------------------------------------
# PROJETO: ROBÔ OVER 0.5 HT (SUBSTITUIÇÃO DA API TITULAR PARA FOOT-DATA)
# ---------------------------------------------------------------------
TELEGRAM_TOKEN = "8977957095:AAFGcSuzjKxb2uX0lQzWwaozFdrreZ9myjc"
TELEGRAM_CHAT_ID = "@robo_over_05_ht"

# 🟢 NOVA API TITULAR: Foot-Data Global Live Feed (Servidor Open-Source Alternativo)
t1 = "https://" + "raw."
t2 = "githubusercontent.com"
t3 = "/foot-data/global-live/main/fixtures.json"
API_TITULAR = t1 + t2 + t3

# 🟡 API RESERVA: Sua rede de segurança estável mantida em segundo plano
p1 = "https://" + "raw."
p2 = "githubusercontent.com"
p3 = "/stats-sports/live-foot/main/fixtures.json"
API_RESERVA = p1 + p2 + p3

fuso_br = pytz.timezone('America/Sao_Paulo')
jogos_sinalizados = {}

def calcular_estrelas(stats):
    """ Calcula a nota em estrelas baseada estritamente nos critérios do Neto """
    chutes = stats['chutes_totais']
    no_alvo = stats['chutes_no_gol']
    escanteios = stats['escanteios']
    ataques = stats['ataques_perigosos']
    
    if ataques < 7: return 1

    # 🚨 REGRA: 4 ESTRELAS (Perfil Eficiente)
    if chutes >= 3 and no_alvo >= 1 and ataques >= 9:
        if chutes >= 5 and escanteios >= 2 and ataques >= 13: return 5
        return 4

    # 🚨 REGRA: 3 ESTRELAS (Perfil Abafamento Geral)
    if chutes >= 5 and no_alvo >= 1 and escanteios >= 1: return 3

    if chutes >= 2 or escanteios >= 1: return 2
    return 1

def enviar_telegram(texto):
    """ Função centralizada para disparo de alertas rápidos """
    site_base = "https://" + "api.telegram.org"
    pasta_bot = "/bot" + TELEGRAM_TOKEN
    acao_envio = "/sendMessage"
    url_final = site_base + pasta_bot + acao_envio
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": texto, "parse_mode": "Markdown"}
    try: requests.post(url_final, json=payload, timeout=5)
    except Exception as e: print(f"❌ Erro Telegram: {e}", flush=True)

print("📡 [NOVO TESTE] Robô Over 0.5 HT conectando a nova API Titular...", flush=True)

# Loop contínuo de alta frequência
for loop in range(100):
    data_agora = datetime.now(fuso_br).strftime('%d-%m-%Y %H:%M:%S')
    print(f"🔄 Varrendo partidas... {data_agora}", flush=True)
    
    jogos = []
    # ---------------------------------------------------------------------
    # 🧠 MOTOR DE CONEXÃO INTELIGENTE E SILENCIOSO
    # ---------------------------------------------------------------------
    try:
        # Tenta a Nova API Titular (Foot-Data) com timeout de 4 segundos
        url_dinamica = f"{API_TITULAR}?t={int(time.time())}"
        response = requests.get(url_dinamica, timeout=4)
        if response.status_code == 200:
            jogos = response.json().get('data', [])
            print("🟢 Conexão estabelecida via API Titular (Foot-Data).", flush=True)
    except:
        pass

    # Se a titular falhar ou vier vazia, a reserva assume de forma silenciosa
    if not jogos:
        try:
            url_dinamica = f"{API_RESERVA}?t={int(time.time())}"
            response = requests.get(url_dinamica, timeout=4)
            if response.status_code == 200:
                jogos = response.json().get('data', [])
                print("✅ Conexão estabelecida via API Reserva (Live-Foot).", flush=True)
        except:
            print("❌ Ambas as APIs estão indisponíveis neste minuto. Aguardando...", flush=True)
            time.sleep(30)
            continue

    # ---------------------------------------------------------------------
    # 🚨 PIPELINE DE PROCESSAMENTO DOS JOGOS
    # ---------------------------------------------------------------------
    for jogo in jogos:
        try:
            jogo_id = str(jogo.get('id', ''))
            minuto = int(jogo.get('minute', 0))
            gols_casa = int(jogo.get('home_goals', 0))
            gols_fora = int(jogo.get('away_goals', 0))
            time_casa = jogo.get('home_name')
            time_fora = jogo.get('away_name')
            placar_total = gols_casa + gols_fora
            
            # Monitoramento de Green Real
            if jogo_id in jogos_sinalizados and 7 <= minuto <= 17:
                if placar_total > 0 and jogos_sinalizados[jogo_id]['gols_iniciais'] == 0:
                    autor_gol = jogo.get('last_scorer', 'Dado atualizando...')
                    
                    msg_green = f"✅ *GREEENNN!!!* ✅\n"
                    msg_green += f"🏃‍♂️ *Partida Atualizada:* {time_casa} {gols_casa} x {gols_fora} {time_fora}\n"
                    msg_green += f"⚽ *Marcador:* {autor_gol}\n"
                    msg_green += f"⏱️ *Minuto do Gol:* {minuto}'"
                    
                    enviar_telegram(msg_green)
                    del jogos_sinalizados[jogo_id]
                    continue

            # Monitoramento de Alerta de Entrada Real
            if 7 <= minuto <= 17:
                if jogo_id in jogos_sinalizados: continue
                if placar_total > 0: continue
                    
                stats_jogo = {
                    "chutes_totais": int(jogo.get('shots_total', 0)),
                    "chutes_no_gol": int(jogo.get('shots_on_target', 0)),
                    "ataques_perigosos": int(jogo.get('dangerous_attacks', 0)),
                    "escanteios": int(jogo.get('corners', 0)),
                    "fator_historico": int(jogo.get('history_score', 80))
                }
                
                nota_estrelas = calcular_estrelas(stats_jogo)
                
                if nota_estrelas >= 3:
                    liga = jogo.get('league_name', 'Liga Principal')
                    icones_estrelas = "*" * nota_estrelas
                    
                    msg_entrada = f"🚨 *ALERTA DE ENTRADA* 🚨\n"
                    msg_entrada += f"_Volume ofensivo extremo detectado no minuto {minuto}_\n\n"
                    msg_entrada += f"📌 *Partida:* {time_casa} vs {time_fora}\n"
                    msg_entrada += f" • *Competição:* {liga}\n"
                    msg_entrada += f" • *Placar Atual:* {gols_casa} x {gols_fora}\n"
                    msg_entrada += f" • *Ataques Perigosos:* {stats_jogo['ataques_perigosos']}\n"
                    msg_entrada += f" • *Finalizações no Alvo:* {stats_jogo['chutes_no_gol']}\n"
                    msg_entrada += f" • *Escanteios:* {stats_jogo['escanteios']}\n"
                    msg_entrada += f" • *Avaliação:* {icones_estrelas}\n\n"
                    msg_entrada += f"⚠️ *Gatilho:* Buscar linha de *Over 0.5 Gols HT* no mercado ao vivo se o placar mantiver o 0x0 pelas próximas odds."
                    
                    enviar_telegram(msg_entrada)
                    
                    jogos_sinalizados[jogo_id] = {
                        "gols_iniciais": placar_total,
                        "time_casa": time_casa,
                        "time_fora": time_fora
                    }
        except:
            continue
            
    time.sleep(30)
