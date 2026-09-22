import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime
import pytz
import sys

# ---------------------------------------------------------------------
# PROJETO: ROBÔ OVER 0.5 HT (OTIMIZADO PARA 5 MINUTOS / JANELA 14H ÀS 22H)
# ---------------------------------------------------------------------
TELEGRAM_TOKEN = "8977957095:AAFGcSuzjKxb2uX0lQzWwaozFdrreZ9myjc"
TELEGRAM_CHAT_ID = "@robo_over_05_ht"

API_FOOTBALL_KEY = "64c94cc7flc652eaf9c39ad0b3b3773f"
API_URL = "https://api-sports.io"

fuso_br = pytz.timezone('America/Sao_Paulo')
hora_atual_br = datetime.now(fuso_br).hour

# 🚨 TRAVA DE SEGURANÇA DIÁRIA: Só consome a API se estiver entre 14:00h e 22:00h BR
if not (14 <= hora_atual_br < 22):
    print(f"💤 Fora do horário operacional (14h às 22h). Varre-se cancelada para poupar créditos.", flush=True)
    sys.exit(0)

def calcular_estrelas(stats):
    chutes = stats['chutes_totais']
    no_alvo = stats['chutes_no_gol']
    escanteios = stats['escanteios']
    ataques = stats['ataques_perigosos']
    
    if ataques < 7: return 1
    if chutes >= 3 and no_alvo >= 1 and ataques >= 9:
        if chutes >= 5 and escanteios >= 2 and ataques >= 13: return 5
        return 4
    if chutes >= 5 and no_alvo >= 1 and escanteios >= 1: return 3
    if chutes >= 2 or escanteios >= 1: return 2
    return 1

def enviar_telegram(texto):
    site_base = "https://" + "api.telegram.org"
    pasta_bot = "/bot" + TELEGRAM_TOKEN
    acao_envio = "/sendMessage"
    url_final = site_base + pasta_bot + acao_envio
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": texto, "parse_mode": "Markdown"}
    try: requests.post(url_final, json=payload, timeout=5)
    except: print("❌ Falha ao enviar notificação para o Telegram.", flush=True)

data_agora = datetime.now(fuso_br).strftime('%d-%m-%Y %H:%M:%S')
print(f"📡 [SISTEMA CRONOMETRADO] Varredura estratégica iniciada... {data_agora}", flush=True)

try:
    headers = {
        "x-rapidapi-key": API_FOOTBALL_KEY,
        "x-rapidapi-host": "v3.football.api-sports.io"
    }
    
    # Consome exatamente 1 requisição controlada
    response = requests.get(API_URL, headers=headers, timeout=6)
    
    if response.status_code == 403:
        print("⚠️ Status 403: Chave bloqueada. Lembre-se de ativar a assinatura gratuita do plano de 100 reqs no painel da API-Football.", flush=True)
        sys.exit(0)
        
    if response.status_code != 200:
        print(f"⚠️ Servidor com instabilidade momentânea. Status: {response.status_code}", flush=True)
        sys.exit(0)
        
    partidas = response.json().get('response', [])
    if not partidas:
        print("  ℹ️ Nenhuma partida em andamento no mundo neste minuto.", flush=True)
        sys.exit(0)
        
    print(f"  📊 Analisando {len(partidas)} jogos ao vivo...", flush=True)
    
    for partida in partidas:
        try:
            jogo_id = str(partida['fixture']['id'])
            minuto = int(partida['fixture']['status']['elapsed'])
            gols_casa = partida['goals']['home']
            gols_fora = partida['goals']['away']
            
            gols_casa = int(gols_casa) if gols_casa is not None else 0
            gols_fora = int(gols_fora) if gols_fora is not None else 0
            placar_total = gols_casa + gols_fora
            
            time_casa = partida['teams']['home']['name']
            time_fora = partida['teams']['away']['name']

            # Filtro operacional rígido (7 aos 17 minutos com placar 0x0)
            if 7 <= minuto <= 17 and placar_total == 0:
                stats_lista = partida.get('statistics', [])
                stats_jogo = {"chutes_totais": 0, "chutes_no_gol": 0, "ataques_perigosos": 0, "escanteios": 0}
                
                for s in stats_lista:
                    for item in s.get('statistics', []):
                        tipo = item['type']
                        val = int(item['value']) if item['value'] is not None else 0
                        if 'Total Shots' in tipo: stats_jogo['chutes_totais'] += val
                        if 'Shots on Goal' in tipo: stats_jogo['chutes_no_gol'] += val
                        if 'Dangerous Attacks' in tipo: stats_jogo['ataques_perigosos'] += val
                        if 'Corner Kicks' in tipo: stats_jogo['escanteios'] += val
                
                nota_estrelas = calcular_estrelas(stats_jogo)
                
                if nota_estrelas >= 3:
                    liga = partida['league']['name']
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
        except:
            continue
except Exception as e:
    print(f"❌ Falha de processamento técnico: {e}", flush=True)

print("✅ Análise instantânea concluída!", flush=True)
