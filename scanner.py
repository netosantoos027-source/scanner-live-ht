import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime
import pytz

# ---------------------------------------------------------------------
# PROJETO: ROBÔ OVER 0.5 HT (LAYOUT AJUSTADO + SISTEMA DE GREEN)
# ---------------------------------------------------------------------
TELEGRAM_TOKEN = "8977957095:AAFGcSuzjKxb2uX0lQzWwaozFdrreZ9myjc"
TELEGRAM_CHAT_ID = "@robo_over_05_ht"

# Servidor público de dados esportivos em tempo real
API_URL = "https://b3score.com" 

fuso_br = pytz.timezone('America/Sao_Paulo')

# Dicionário na memória do robô para rastrear quais jogos receberam sinal de entrada
# Isso evita que o robô envie o mesmo alerta repetidas vezes e monitora o Green
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
    """ Função centralizada e blindada para disparo de alertas """
    site_base = "https://" + "api.telegram.org"
    pasta_bot = "/bot" + TELEGRAM_TOKEN
    acao_envio = "/sendMessage"
    url_final = site_base + pasta_bot + acao_envio
    
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": texto, "parse_mode": "Markdown"}
    try:
        requests.post(url_final, json=payload, timeout=10)
    except Exception as e:
        print(f"Erro de rede no envio: {e}")

print("📡 [SISTEMA EM PRODUÇÃO] Robô Over 0.5 HT monitorando o mercado ao vivo...")

# Loop de escaneamento contínuo de alta frequência (Aproximadamente 50 minutos por ciclo)
for loop in range(100):
    data_agora = datetime.now(fuso_br).strftime('%d-%m-%Y %H:%M:%S')
    print(f"🔄 [Robô Over 0.5 HT] Varrendo partidas em andamento... {data_agora}")
    
    try:
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
                # Se o jogo já recebeu um Alerta antes e ainda está dentro da janela do tempo
                if jogo_id in jogos_sinalizados and 7 <= minuto <= 17:
                    # Se o placar mudou (saiu gol) em relação ao momento da entrada (que era 0x0)
                    if placar_total > 0 and jogos_sinalizados[jogo_id]['gols_iniciais'] == 0:
                        msg_green = f"✅ *GREEENNN!!!* ✅\n"
                        msg_green += f"⚽ Gol confirmado no primeiro tempo!\n"
                        msg_green += f"📌 *Partida:* {time_casa} vs {time_fora}\n"
                        msg_green += f"⏱️ *Momento do Gol:* Minuto {minuto}"
                        
                        enviar_telegram(msg_green)
                        # Remove da lista para não enviar o Green duas vezes no mesmo jogo
                        del jogos_sinalizados[jogo_id]
                        continue

                # ---------------------------------------------------------------------
                # 🚨 SISTEMA DE CAPTURA DE ALERTA DE ENTRADA
                # ---------------------------------------------------------------------
                # Filtra estritamente a janela operacional entre os minutos 7 e 17
                if 7 <= minuto <= 17:
                    
                    # Se o jogo já foi alertado nesta rodada, ignoramos para não inundar o canal
                    if jogo_id in jogos_sinalizados:
                        continue
                        
                    # Se já saiu gol antes da análise, o jogo é descartado
                    if placar_total > 0:
                        continue
                        
                    stats_jogo = {
                        "chutes_totais": int(jogo.get('shots_total', 0)),
                        "chutes_no_gol": int(jogo.get('shots_on_target', 0)),
                        "ataques_perigosos": int(jogo.get('dangerous_attacks', 0)),
                        "escanteios": int(jogo.get('corners', 0)),
                        "fator_historico": int(jogo.get('history_score', 80))
                    }
                    
                    nota_estrelas = calcular_estrelas(stats_jogo)
                    
                    # Regra de filtro estrito: Só emite o sinal se bater 4 ou 5 estrelas
                    if nota_estrelas >= 4:
                        liga = jogo.get('league_name', 'Liga Principal')
                        icones_estrelas = "*" * nota_estrelas
                        
                        # 📝 NOVO PADRÃO AJUSTADO CONFORME SOLICITADO
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
                        
                        # Dispara o Alerta de Entrada
                        enviar_telegram(msg_entrada)
                        
                        # Registra o jogo na memória para monitorar o Green nas próximas varreduras
                        jogos_sinalizados[jogo_id] = {
                            "gols_iniciais": placar_total,
                            "time_casa": time_casa,
                            "time_fora": time_fora
                        }
                        
            except:
                continue
                
    except Exception as e:
        print(f"Erro temporário de conexão com os dados: {e}")
        
    # Espera 30 segundos para efetuar a próxima varredura em tempo real
    time.sleep(30)
