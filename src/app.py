import json
import pandas as pd
import requests
import streamlit as st

# =================== CONFIGURAÇÃO =============
# Tente ambas as URLs se uma não funcionar
OLLAMA_URL_GENERATE = "http://localhost:11434/api/generate"
OLLAMA_URL_CHAT = "http://localhost:11434/api/chat"
MODELO = "gpt-oss"

# =========== CARREGA DADOS ===================
try:
    perfil = json.load(open('./data/perfil_investidor.json'))
    transacoes = pd.read_csv('./data/transacoes.csv')
    historico = pd.read_csv('./data/historico_atendimento.csv')
    produtos = json.load(open('./data/produtos_financeiros.json'))
except FileNotFoundError as e:
    st.error(f"Arquivo não encontrado: {e}")
    st.stop()

# ================= MONTAR CONTEXTO ===============
contexto = f"""
CLIENTE: {perfil['nome']}, {perfil['idade']} anos, perfil {perfil['perfil_investidor']}
OBJETIVO: {perfil['objetivo_principal']}
PATRIMONIO: R$ {perfil['patrimonio_total']} | RESERVA: R$ {perfil['reserva_emergencia_atual']}

TRANSAÇÕES RECENTES:
{transacoes.to_string(index=False)}

ATENDIMENTOS ANTERIORES:
{historico.to_string(index=False)}

PRODUTOS DISPONIVEIS:
{json.dumps(produtos, indent=2, ensure_ascii=False)}
"""

SYSTEM_PROMPT = """Você é o Edu, um educador financeiro amigável e didático. Responda de forma sucinta e direta com no máximo 3 parágrafos."""

# ============= CHAMAR OLLAMA ===========
def perguntar(msg):
    prompt = f"{SYSTEM_PROMPT}\n\nCONTEXTO:\n{contexto}\n\nPERGUNTA: {msg}\n\nRESPOSTA EDU:"
    
    # Tenta primeiro com /api/generate
    try:
        response = requests.post(
            OLLAMA_URL_GENERATE,
            json={"model": MODELO, "prompt": prompt, "stream": False},
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json().get('response', 'Sem resposta')
        else:
            # Se falhar, tenta com /api/chat
            response = requests.post(
                OLLAMA_URL_CHAT,
                json={
                    "model": MODELO,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json().get('message', {}).get('content', 'Sem resposta')
            else:
                return f"❌ Erro {response.status_code}: Ollama não está respondendo. Verifique se está rodando `ollama serve`"
                
    except requests.exceptions.ConnectionError:
        return "❌ Ollama não está rodando! Abra um terminal e execute: ollama serve"
    except Exception as erro:
        return f"❌ Erro: {str(erro)}"

# ======= INTERFACE =============
st.title("Edu, o Educador Financeiro")

if pergunta := st.chat_input("Sua dúvida sobre finanças..."):
    st.chat_message("user").write(pergunta)
    with st.spinner("Edu está pensando..."):
        resposta = perguntar(pergunta)
        st.chat_message("assistant").write(resposta)
