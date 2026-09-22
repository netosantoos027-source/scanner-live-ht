import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime
import pytz
import sys

# ---------------------------------------------------------------------
# PROJETO: ROBÔ OVER 0.5 HT (PRODUÇÃO EM INFRAESTRUTURA API-FOOTBALL)
# ---------------------------------------------------------------------
TELEGRAM_TOKEN = "8977957095:AAFGcSuzjKxb2uX0lQzWwaozFdrreZ9myjc"
TELEGRAM_CHAT_ID = "@robo_over_05_ht"

# Sua chave de acesso verificada e ativa
API_FOOTBALL_KEY = "64c94cc7flc652eaf9c39ad0b3b3773f"

API_URL = "https://api-sports.io"
fuso_br = pytz.timezone('America/Sao_Paulo')
jogos_sinalizados = {}

def calcular_estrelas(stats):
    """ Filtro quantitativo estrito baseado nas regras de chutes do Neto """
    chutes = stats['chutes_totais']
    no_alvo = stats['chutes_no_gol']
    escanteios = stats['escanteios']
    ataques = stats['ataques_perigosos']
    
    if ataques < 7: return 1

    # 🚨 REGRA PROJETO: 4 ESTRELAS (Perfil Eficiente)
    if chutes >= 3 and no_alvo >= 1 and ataques >= 9:
        if chutes >= 5 and escanteios >= 2 and ataques >= 13: return 5
        return 4

    # 🚨 REGRA PROJETO: 3 ESTRELAS (Perfil Abafamento Geral)
    if chutes >= 5 and no_alvo >= 1 and escanteios >= 1: return 3

    if chutes >= 2 or escanteios >= 1: return 2
    return 1

def enviar_telegram(texto):
    """ Função centralizada para disparo de alertas """
    site_base = "https://" + "api.telegram.org"
    pasta_bot = "/bot" + TELEGRAM_TOKEN
    acao_envio = "/sendMessage"
    url_final = site_base + pasta_bot + acao_envio
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": texto, "parse_mode": "Markdown"}
    try: requests.post(url_final, json=payload, timeout=5)
    except: print("❌ Falha ao enviar notificação para o Telegram.", flush=True)

print("📡 [SISTEMA PROFISSIONAL] Robô Over 0.5 HT conectado à infraestrutura API-Football...", flush=True)

# Loop calibrado para efetuar 5 varreduras completas e proteger a cota diária
for loop in range(5):
    data_agora = datetime.now(fuso_br).strftime('%d-%m-%Y %H:%M:%S')
    print(f"🔄 Varrendo partidas ao vivo... {data_agora}", flush=True)
    
    try:
        headers = {
            "x-rapidapi-key": API_FOOTBALL_KEY,
            "x-rapidapi-host": "v3.football.api-sports.io"
        }
        response = requests.get(API_URL, headers=headers, timeout=5)
        
        if response.status_code != 200:
            print(f"⚠️ Servidor ocupado. Status: {response.status_code}", flush=True)
            time.sleep(60)
            continue
            
        partidas = response.json().get('response', [])
        if not partidas:
            print("  ℹ️ Nenhuma partida em andamento monitorada neste minuto.", flush=True)
            time.sleep(60)
            continue
            
        print(f"  📊 Analisando {len(partidas)} jogos em andamento no mundo agora...", flush=True)
        
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
                
                # Monitoramento de Green Real
                if jogo_id in jogos_sinalizados and 7 <= minuto <= 17:
                    if placar_total > 0 and jogos_sinalizados[jogo_id]['gols_iniciais'] == 0:
                        msg_green = f"✅ *GREEENNN!!!* ✅\n"
                        msg_green += f"🏃‍♂️ *Partida Atualizada:* {time_casa} {gols_casa} x {gols_fora} {time_fora}\n"
                        msg_green += f"⏱️ *Minuto do Gol:* {minuto}'"
                        enviar_telegram(msg_green)
                        del jogos_sinalizados[jogo_id]
                        continue

                # Monitoramento de Alerta de Entrada Real
                if 7 <= minuto <= 17:
                    if jogo_id in jogos_sinalizados: continue
                    if placar_total > 0: continue
                        
                    stats_lista = partida.get('statistics', [])
                    stats_jogo = {"chutes_totais": 0, "chutes_no_gol": 0, "ataques_perigosos": 0, "escanteios": 0, "fator_historico": 80}
                    
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
                        
                        jogos_sinalizados[jogo_id] = {
                            "gols_iniciais": placar_total,
                            "time_casa": time_casa,
                            "time_fora": time_fora
                        }
            except:
                continue
    except Exception as e:
        print(f"❌ Falha de processamento: {e}", flush=True)
        
    time.sleep(60)
