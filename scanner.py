import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime
import pytz
import sys

# ---------------------------------------------------------------------
# PROJETO: ROBÔ OVER 0.5 HT (SIMULADOR DO NOVO PADRÃO DE SENSIBILIDADE)
# ---------------------------------------------------------------------
TELEGRAM_TOKEN = "8977957095:AAFGcSuzjKxb2uX0lQzWwaozFdrreZ9myjc"
TELEGRAM_CHAT_ID = "@robo_over_05_ht"

fuso_br = pytz.timezone('America/Sao_Paulo')
jogos_sinalizados = {}

def calcular_estrelas(stats):
    """ Filtro quantitativo com a NOVA flexibilização de parâmetros """
    estrelas = 0
    if stats['chutes_totais'] >= 2: estrelas += 1  # Flexibilizado de 3 para 2
    if stats['chutes_no_gol'] >= 1: estrelas += 1
    if stats['ataques_perigosos'] >= 9: estrelas += 1  # Flexibilizado de 13 para 9
    if stats['escanteios'] >= 1: estrelas += 1
    if stats['fator_historico'] >= 75: estrelas += 1
    return max(1, min(estrelas, 5))

def enviar_telegram(texto):
    site_base = "https://" + "api.telegram.org"
    pasta_bot = "/bot" + TELEGRAM_TOKEN
    acao_envio = "/sendMessage"
    url_final = site_base + pasta_bot + acao_envio
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": texto, "parse_mode": "Markdown"}
    try:
        requests.post(url_final, json=payload, timeout=5)
    except Exception as e:
        print(f"❌ Erro de rede no Telegram: {e}", flush=True)

print("📡 [MODO SIMULADOR] Iniciando simulação da nova calibragem flexível...", flush=True)

# Loop de simulação rápida passo a passo
for loop in range(1, 4):
    data_agora = datetime.now(fuso_br).strftime('%d-%m-%Y %H:%M:%S')
    
    # 📌 PASSO 1: Injeta um jogo que antes seria rejeitado, mas que agora bate 4 Estrelas (Dispara Alerta)
    if loop == 1:
        print(f"🔄 Passo 1: Injetando partida com parâmetros flexibilizados... {data_agora}", flush=True)
        jogos = [{
            "id": "7777", "minute": 11, "home_goals": 0, "away_goals": 0,
            "shots_total": 2, "shots_on_target": 1, "dangerous_attacks": 10,
            "corners": 1, "history_score": 80, "home_name": "Arsenal",
            "away_name": "Chelsea", "league_name": "Premier League", "last_scorer": "Sem gols"
        }]
        
    # 📌 PASSO 2: Injeta a mudança de placar para validar a comemoração do Green detalhado
    elif loop == 2:
        print(f"🔄 Passo 2: Simulando gol da partida sinalizada... {data_agora}", flush=True)
        jogos = [{
            "id": "7777", "minute": 14, "home_goals": 1, "away_goals": 0,
            "shots_total": 3, "shots_on_target": 2, "dangerous_attacks": 13,
            "corners": 1, "history_score": 80, "home_name": "Arsenal",
            "away_name": "Chelsea", "league_name": "Premier League", "last_scorer": "Bukayo Saka"
        }]
    else:
        break

    for jogo in jogos:
        try:
            jogo_id = str(jogo.get('id', ''))
            minuto = int(jogo.get('minute', 0))
            gols_casa = int(jogo.get('home_goals', 0))
            gols_fora = int(jogo.get('away_goals', 0))
            time_casa = jogo.get('home_name')
            time_fora = jogo.get('away_name')
            placar_total = gols_casa + gols_fora
            
            # Executa o teste do Green Automatizado
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

            # Executa o teste do Alerta de Entrada
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
                
                if nota_estrelas >= 4:
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
                    
        except Exception as e:
            print(f"Erro no loop do simulador: {e}", flush=True)
            
    # Aguarda 15 segundos entre o Alerta e o Green para o teste ser rápido no celular
    time.sleep(15)

print("✅ Fim do teste de simulação rápida concluído com sucesso!", flush=True)
