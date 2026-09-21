import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime
import pytz
import sys

# ---------------------------------------------------------------------
# PROJETO: ROBÔ OVER 0.5 HT (MATRIZ AJUSTADA: 3 E 4 ESTRELAS PERSONALIZADAS)
# ---------------------------------------------------------------------
TELEGRAM_TOKEN = "8977957095:AAFGcSuzjKxb2uX0lQzWwaozFdrreZ9myjc"
TELEGRAM_CHAT_ID = "@robo_over_05_ht"

# Rota pública descentralizada estável e gratuita de dados
p1 = "https://" + "raw."
p2 = "githubusercontent.com"
p3 = "/stats-sports/live-foot/main/fixtures.json"
API_URL = p1 + p2 + p3

fuso_br = pytz.timezone('America/Sao_Paulo')
jogos_sinalizados = {}

def calcular_estrelas(stats):
    """ Calcula a nota em estrelas baseada estritamente nos novos critérios do Neto """
    chutes = stats['chutes_totais']
    no_alvo = stats['chutes_no_gol']
    escanteios = stats['escanteios']
    ataques = stats['ataques_perigosos']
    
    # Base inicial de pontos pelos ataques perigosos flexibilizados (mínimo 7)
    if ataques < 7:
        return 1

    # 🚨 REGRA PROJETO: 4 ESTRELAS (Perfil Eficiente)
    # Exige: 3 ou mais finalizações totais E pelo menos 1 no alvo
    if chutes >= 3 and no_alvo >= 1 and ataques >= 9:
        # Bônus para 5 Estrelas se o jogo for um massacre completo com escanteio e 13+ ataques
        if chutes >= 5 and escanteios >= 2 and ataques >= 13:
            return 5
        return 4

    # 🚨 REGRA PROJETO: 3 ESTRELAS (Perfil Abafamento Geral)
    # Exige: 5 ou mais finalizações totais E pelo menos 1 no alvo E pelo menos 1 escanteio
    if chutes >= 5 and no_alvo >= 1 and escanteios >= 1:
        return 3

    # Caso o jogo tenha ataques mas não cumpra os combos de 3 ou 4 estrelas acima
    if chutes >= 2 or escanteios >= 1:
        return 2
        
    return 1

def enviar_telegram(texto):
    """ Função centralizada para disparo de alertas rápidos """
    site_base = "https://" + "api.telegram.org"
    pasta_bot = "/bot" + TELEGRAM_TOKEN
    acao_envio = "/sendMessage"
    url_final = site_base + pasta_bot + acao_envio
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": texto, "parse_mode": "Markdown"}
    try:
        requests.post(url_final, json=payload, timeout=5)
    except Exception as e:
        print(f"❌ Erro de rede no Telegram: {e}", flush=True)

print("📡 [SISTEMA REAL] Robô Over 0.5 HT monitorando nova matriz de chutes...", flush=True)

# Loop contínuo de alta frequência
for loop in range(100):
    data_agora = datetime.now(fuso_br).strftime('%d-%m-%Y %H:%M:%S')
    print(f"🔄 Varrendo partidas... {data_agora}", flush=True)
    
    try:
        url_dinamica = f"{API_URL}?t={int(time.time())}"
        response = requests.get(url_dinamica, timeout=5)
        
        if response.status_code != 200:
            time.sleep(30)
            continue
            
        try:
            dados_brutos = response.json()
        except:
            time.sleep(30)
            continue
            
        jogos = dados_brutos.get('data', [])
        if not jogos:
            time.sleep(30)
            continue
        
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
                    
                    # O robô aceita e envia alertas no seu canal a partir de 3 estrelas
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
                
    except:
        time.sleep(30)
        
    time.sleep(30)
