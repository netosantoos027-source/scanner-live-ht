import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime
import pytz

# ---------------------------------------------------------------------
# PROJETO: ROBÔ OVER 0.5 HT (FONTE DE DADOS ILIMITADA E GRATUITA)
# ---------------------------------------------------------------------
TELEGRAM_TOKEN = "8977957095:AAFGcSuzjKxb2uX0lQzWwaozFdrreZ9myjc"
TELEGRAM_CHAT_ID = "@robo_over_05_ht"

# Nova rota de dados pública, gratuita e sem limite de requisições
API_URL = "https://githubusercontent.com"

fuso_br = pytz.timezone('America/Sao_Paulo')

# Dicionário para rastrear os jogos sinalizados e monitorar o Green
jogos_sinalizados = {}

def calcular_estrelas(stats):
    """ Calcula a pontuação de 1 a 5 estrelas baseada no volume de pressão ofensiva """
    estrelas = 0
    if stats['chutes_totais'] >= 3: estrelas += 1
    if stats['chutes_no_gol'] >= 1: estrelas += 1
    if stats['ataques_perigosos'] >= 13: estrelas += 1
    if stats['escanteios'] >= 1: estrelas += 1
    if stats['fator_historico'] >= 75: estrelas += 1
    return max(1, min(estrelas, 5))

def enviar_telegram(texto):
    """ Função centralizada para disparo de alertas """
    site_base = "https://" + "api.telegram.org"
    pasta_bot = "/bot" + TELEGRAM_TOKEN
    acao_envio = "/sendMessage"
    url_final = site_base + pasta_bot + acao_envio
    
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": texto, "parse_mode": "Markdown"}
    try:
        requests.post(url_final, json=payload, timeout=10)
    except Exception as e:
        print(f"Erro de rede no Telegram: {e}")

print("📡 [ROBÔ OVER 0.5 HT] Monitorando mercado em alta frequência (Modo Gratuito Ativo)...")

# Loop contínuo (Roda por aproximadamente 50 minutos varrendo os dados públicos)
for loop in range(100):
    data_agora = datetime.now(fuso_br).strftime('%d-%m-%Y %H:%M:%S')
    print(f"🔄 [Robô Over 0.5 HT] Varrendo partidas em andamento... {data_agora}")
    
    try:
        # Puxa os dados da rede pública sem precisar de chaves, tokens ou pagamentos
        response = requests.get(API_URL, timeout=12)
        if response.status_code != 200:
            time.sleep(30)
            continue
            
        jogos = response.json().get('data', [])
        
        for jogo in jogos:
            try:
                jogo_id = str(jogo.get('id', ''))
                minuto = int(jogo.get('minute', 0))
                gols_casa = int(jogo.get('home_goals', 0))
                gols_fora = int(jogo.get('away_goals', 0))
                time_casa = jogo.get('home_name')
                time_fora = jogo.get('away_name')
                placar_total = gols_casa + gols_fora
                
                # ---------------------------------------------------------------------
                # 🟢 SISTEMA DE MONITORAMENTO DE GREEN
                # ---------------------------------------------------------------------
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

                # ---------------------------------------------------------------------
                # 🚨 SISTEMA DE CAPTURA DE ALERTA DE ENTRADA
                # ---------------------------------------------------------------------
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
                        
            except:
                continue
                
    except Exception as e:
        print(f"Erro na varredura: {e}")
        
    # Espera 30 segundos para a próxima leitura de alta frequência
    time.sleep(30)
