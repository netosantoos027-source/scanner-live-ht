import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime
import pytz
import sys

# ---------------------------------------------------------------------
# PROJETO: ROBÔ OVER 0.5 HT (PRODUÇÃO VIA SERVIDOR OPEN-SOURCE ESTÁVEL)
# ---------------------------------------------------------------------
TELEGRAM_TOKEN = "8977957095:AAFGcSuzjKxb2uX0lQzWwaozFdrreZ9myjc"
TELEGRAM_CHAT_ID = "@robo_over_05_ht"

# URL da API de dados de alta disponibilidade (Servidor Open-Source de Placares)
API_URL = "https://livescore.com"

fuso_br = pytz.timezone('America/Sao_Paulo')
jogos_sinalizados = {}

def calcular_estrelas(stats):
    """ Filtro quantitativo de 1 a 5 estrelas baseado no volume ofensivo """
    estrelas = 0
    if stats['chutes_totais'] >= 3: estrelas += 1
    if stats['chutes_no_gol'] >= 1: estrelas += 1
    if stats['ataques_perigosos'] >= 13: estrelas += 1
    if stats['escanteios'] >= 1: estrelas += 1
    if stats['fator_historico'] >= 75: estrelas += 1
    return max(1, min(estrelas, 5))

def enviar_telegram(texto):
    """ Função centralizada para disparo de alertas para o canal de futebol """
    site_base = "https://" + "api.telegram.org"
    pasta_bot = "/bot" + TELEGRAM_TOKEN
    acao_envio = "/sendMessage"
    url_final = site_base + pasta_bot + acao_envio
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": texto, "parse_mode": "Markdown"}
    try:
        requests.post(url_final, json=payload, timeout=5)
    except Exception as e:
        print(f"❌ Erro de rede no Telegram: {e}", flush=True)

print("📡 [SISTEMA REAL] Robô Over 0.5 HT monitorando o mercado ao vivo...", flush=True)

# Loop contínuo (Roda por aproximadamente 50 minutos por ciclo de agendamento)
for loop in range(100):
    data_agora = datetime.now(fuso_br).strftime('%d-%m-%Y %H:%M:%S')
    print(f"🔄 Varrendo partidas... {data_agora}", flush=True)
    
    try:
        # Requisição segura com cabeçalho padrão de navegador para evitar bloqueios
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(API_URL, headers=headers, timeout=5)
        
        if response.status_code != 200:
            print(f"⚠️ Servidor ocupado (Status {response.status_code}). Tentando em breve...", flush=True)
            time.sleep(30)
            continue
            
        try:
            dados_brutos = response.json()
        except ValueError:
            print("⚠️ Resposta vazia recebida do servidor. Aguardando próximo minuto...", flush=True)
            time.sleep(30)
            continue
            
        # Extração e mapeamento dos jogos ao vivo da API aberta
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
                        
                        # Formatação do Alerta conforme solicitado no padrão comercial
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
                        
            except Exception as e_jogo:
                continue
                
    except Exception as e_varredura:
        print(f"❌ Falha crítica de conexão: {e_varredura}", flush=True)
        time.sleep(30)
        
    time.sleep(30)
