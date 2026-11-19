"""
Script de diagnóstico para investigar o problema de sessão do Vonix.
Testa login, cookies, redirects e requisições subsequentes.
"""
import os
import sys
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

URL_BASE = os.getenv('LINK_VONIX6', 'http://contech6.vonixcc.com.br')
LOGIN = os.getenv('LOGIN_VONIX')
PASSWORD = os.getenv('PASSWORD_VONIX')

print(f"=== DIAGNÓSTICO VONIX ===")
print(f"URL Base: {URL_BASE}")
print(f"Login: {LOGIN}")
print(f"Password: {'*' * len(PASSWORD) if PASSWORD else 'VAZIO'}")
print()

# ============================================================
# ETAPA 1: GET na página de login para pegar token + cookies
# ============================================================
session = requests.Session()

# Configurar headers como navegador real
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
})

url_login = f"{URL_BASE}/login/signin"
print(f"[1] GET {url_login}")
resp_get = session.get(url_login, allow_redirects=True)
print(f"    Status: {resp_get.status_code}")
print(f"    URL final: {resp_get.url}")
print(f"    Cookies após GET: {dict(session.cookies)}")
print(f"    History (redirects): {[r.status_code for r in resp_get.history]}")
print()

# Extrair authenticity_token
soup = BeautifulSoup(resp_get.text, 'html.parser')
token_input = soup.find('input', {'name': 'authenticity_token'})
if token_input:
    token = token_input['value']
    print(f"    Token encontrado: {token[:40]}...")
else:
    print("    [ERRO] Nenhum authenticity_token encontrado!")
    # Mostrar campos do form
    form = soup.find('form')
    if form:
        inputs = form.find_all('input')
        print(f"    Inputs no form: {[(i.get('name'), i.get('type')) for i in inputs]}")
    sys.exit(1)

# ============================================================
# ETAPA 2: POST de login
# ============================================================
payload_login = {
    'authenticity_token': token,
    'return_to': '',
    'username': LOGIN,
    'password': PASSWORD,
    'commit': 'Entrar'
}

print(f"[2] POST {url_login}")
print(f"    Payload: {dict((k, v if k != 'authenticity_token' else v[:20]+'...') for k,v in payload_login.items())}")

resp_post = session.post(
    url_login,
    data=payload_login,
    headers={
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': url_login,
        'Origin': URL_BASE,
    },
    allow_redirects=True
)

print(f"    Status: {resp_post.status_code}")
print(f"    URL final: {resp_post.url}")
print(f"    Cookies após POST: {dict(session.cookies)}")
print(f"    History (redirects): {[(r.status_code, r.headers.get('Location', 'N/A')) for r in resp_post.history]}")
print(f"    Set-Cookie headers: {resp_post.headers.get('Set-Cookie', 'Nenhum')}")
print()

# Verificar se caiu na página de login novamente
soup_post = BeautifulSoup(resp_post.text, 'html.parser')
login_form = soup_post.find('input', {'name': 'authenticity_token'})
title = soup_post.find('title')
print(f"    Título da página: {title.text if title else 'N/A'}")
print(f"    Ainda tem form de login: {'SIM - LOGIN FALHOU' if login_form else 'NÃO - LOGIN OK'}")
print()

# Mostrar trecho do HTML para diagnóstico
body_text = soup_post.get_text()[:500]
print(f"    Texto do body (primeiros 500 chars):")
print(f"    {body_text}")
print()

# ============================================================
# ETAPA 3: Testar requisição subsequente (overview)
# ============================================================
url_overview = f"{URL_BASE}/overview"
print(f"[3] GET {url_overview}")
resp_overview = session.get(
    url_overview,
    headers={
        'Referer': resp_post.url,
    },
    allow_redirects=True
)
print(f"    Status: {resp_overview.status_code}")
print(f"    URL final: {resp_overview.url}")
print(f"    Cookies: {dict(session.cookies)}")
print(f"    History: {[(r.status_code, r.headers.get('Location', 'N/A')) for r in resp_overview.history]}")

soup_overview = BeautifulSoup(resp_overview.text, 'html.parser')
login_form_again = soup_overview.find('input', {'name': 'authenticity_token'})
title_ov = soup_overview.find('title')
print(f"    Título: {title_ov.text if title_ov else 'N/A'}")
print(f"    Retornou form de login: {'SIM - SESSÃO PERDIDA' if login_form_again else 'NÃO - SESSÃO ATIVA'}")
print()

# ============================================================
# ETAPA 4: Testar filtro (set_show_queue)
# ============================================================
url_filtro = f"{URL_BASE}/login/set_show_queue"
print(f"[4] GET {url_filtro} (para token do filtro)")
resp_filtro_get = session.get(url_filtro, allow_redirects=True)
print(f"    Status: {resp_filtro_get.status_code}")
print(f"    URL final: {resp_filtro_get.url}")
print()

# ============================================================
# ETAPA 5: Testar /calls
# ============================================================
url_calls = f"{URL_BASE}/calls"
print(f"[5] GET {url_calls}")
resp_calls = session.get(url_calls, allow_redirects=True)
print(f"    Status: {resp_calls.status_code}")
print(f"    URL final: {resp_calls.url}")
soup_calls = BeautifulSoup(resp_calls.text, 'html.parser')
title_calls = soup_calls.find('title')
login_form_calls = soup_calls.find('input', {'name': 'authenticity_token'})
print(f"    Título: {title_calls.text if title_calls else 'N/A'}")
print(f"    Retornou login: {'SIM' if login_form_calls else 'NÃO'}")
print()

# ============================================================
# ETAPA 6: Testar /agents/calls_overview
# ============================================================
url_agents = f"{URL_BASE}/agents/calls_overview"
print(f"[6] GET {url_agents}")
resp_agents = session.get(url_agents, allow_redirects=True)
print(f"    Status: {resp_agents.status_code}")
print(f"    URL final: {resp_agents.url}")
soup_agents = BeautifulSoup(resp_agents.text, 'html.parser')
title_agents = soup_agents.find('title')
print(f"    Título: {title_agents.text if title_agents else 'N/A'}")
print()

# ============================================================
# RESUMO
# ============================================================
print("=" * 60)
print("RESUMO DO DIAGNÓSTICO")
print("=" * 60)
all_cookies = dict(session.cookies)
print(f"Cookies finais da sessão: {all_cookies}")
print(f"Quantidade de cookies: {len(all_cookies)}")

# Verificar se há cookie de sessão
session_cookies = [k for k in all_cookies.keys() if 'session' in k.lower() or 'sid' in k.lower() or '_cc' in k.lower()]
print(f"Cookies de sessão encontrados: {session_cookies if session_cookies else 'NENHUM'}")
print()

# Dump de todos os response headers do login
print("Headers da resposta de login (POST):")
for k, v in resp_post.headers.items():
    print(f"    {k}: {v}")
