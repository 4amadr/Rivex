"""
Script para mapear dinamicamente todas as filas/clientes do Vonix.
Extrai as filas diretamente do HTML da página principal após login.
"""
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

URL_BASE = os.getenv('LINK_VONIX6', 'http://contech6.vonixcc.com.br')
LOGIN = os.getenv('LOGIN_VONIX')
PASSWORD = os.getenv('PASSWORD_VONIX')

# ============================================================
# 1. LOGIN
# ============================================================
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
})

url_login = f"{URL_BASE}/login/signin"
resp = session.get(url_login)
soup = BeautifulSoup(resp.text, 'html.parser')
token = soup.find('input', {'name': 'authenticity_token'})['value']

session.post(url_login, data={
    'authenticity_token': token,
    'return_to': '',
    'username': LOGIN,
    'password': PASSWORD,
    'commit': 'Entrar'
}, headers={
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': url_login,
    'Origin': URL_BASE,
}, allow_redirects=True)

print("[LOGIN] OK\n")

# ============================================================
# 2. GET na página principal para ver a estrutura do seletor de filas
# ============================================================
resp_home = session.get(f"{URL_BASE}/", allow_redirects=True)
soup_home = BeautifulSoup(resp_home.text, 'html.parser')

# Salvar o HTML para análise
with open('tests/html_pagina_principal.html', 'w', encoding='utf-8') as f:
    f.write(resp_home.text)
print("[SALVO] HTML da página principal em tests/html_pagina_principal.html\n")

# ============================================================
# 3. ENCONTRAR TODAS AS FORMAS DE LISTAR FILAS
# ============================================================

# Método 1: Inputs com name="queue_id[]"
print("=" * 70)
print("MÉTODO 1: Inputs queue_id[]")
print("=" * 70)
queue_inputs = soup_home.find_all('input', {'name': 'queue_id[]'})
print(f"Total encontrado: {len(queue_inputs)}")
for qi in queue_inputs[:5]:
    print(f"  Tag completa: {qi}")
    # Buscar label ou texto próximo
    parent = qi.parent
    print(f"  Parent tag: {parent.name if parent else 'N/A'}")
    print(f"  Parent text: {parent.get_text(strip=True)[:100] if parent else 'N/A'}")
    print()

# Método 2: Options em selects
print("=" * 70)
print("MÉTODO 2: Select/Options")
print("=" * 70)
selects = soup_home.find_all('select')
for sel in selects:
    name = sel.get('name', 'sem-nome')
    options = sel.find_all('option')
    print(f"Select name='{name}' ({len(options)} options)")
    for opt in options[:5]:
        print(f"  value='{opt.get('value', '')}' | text='{opt.get_text(strip=True)}'")
    if len(options) > 5:
        print(f"  ... mais {len(options) - 5} options")
    print()

# Método 3: Labels com checkbox
print("=" * 70)
print("MÉTODO 3: Checkboxes com labels")
print("=" * 70)
checkboxes = soup_home.find_all('input', {'type': 'checkbox'})
print(f"Total checkboxes: {len(checkboxes)}")
for cb in checkboxes[:10]:
    name = cb.get('name', '')
    value = cb.get('value', '')
    # Buscar label associada
    label = None
    cb_id = cb.get('id', '')
    if cb_id:
        label = soup_home.find('label', {'for': cb_id})
    if not label:
        label = cb.find_next_sibling('label')
    if not label:
        parent = cb.parent
        label_text = parent.get_text(strip=True) if parent else ''
    else:
        label_text = label.get_text(strip=True)
    
    print(f"  name='{name}' value='{value}' label='{label_text}'")
print()

# Método 4: Lista <li> com filas
print("=" * 70)
print("MÉTODO 4: Lista <li> com informações de filas")
print("=" * 70)
# Procurar dentro de formulários de seleção de fila
form_queue = soup_home.find('form', action=lambda x: x and 'set_show_queue' in x)
if form_queue:
    print(f"Form encontrado: action='{form_queue.get('action')}'")
    lis = form_queue.find_all('li')
    print(f"Total de <li>: {len(lis)}")
    for li in lis[:10]:
        checkbox = li.find('input', {'type': 'checkbox'})
        label = li.find('label')
        if checkbox and label:
            print(f"  value='{checkbox.get('value', '')}' | nome='{label.get_text(strip=True)}'")
    if len(lis) > 10:
        print(f"  ... mais {len(lis) - 10} itens")
else:
    print("Form de set_show_queue NÃO encontrado. Buscando alternativas...")
    all_forms = soup_home.find_all('form')
    for form in all_forms:
        print(f"  Form: action='{form.get('action', 'N/A')}' method='{form.get('method', 'N/A')}'")

# Método 5: Buscar qualquer estrutura que contenha nomes de fila conhecidos
print("\n" + "=" * 70)
print("MÉTODO 5: Busca por nomes conhecidos no HTML")
print("=" * 70)
known_queues = ['tcrepresentacao', 'assismollerke', 'realpromotora', 'ASSIS', 'REAL PROMOTORA', 'TC']
for kq in known_queues:
    occurrences = resp_home.text.count(kq)
    print(f"  '{kq}' aparece {occurrences} vezes no HTML")

# Método 6: Extrair direto do cookie (contém user_queues)
print("\n" + "=" * 70)
print("MÉTODO 6: Filas no cookie de sessão")
print("=" * 70)
import base64
cookie_value = session.cookies.get('_rails235_session', '')
# O cookie Rails usa Base64 com Marshal do Ruby - não é JSON
# Mas podemos extrair as strings das filas
try:
    decoded = base64.b64decode(cookie_value.split('--')[0])
    # Extrair strings legíveis
    import re
    queue_names = re.findall(r'"([a-z0-9_]+)"', decoded.decode('latin-1'))
    # Filtrar apenas nomes de filas (excluir tokens do Rails)
    ignore = {'BAh7', 'allow_listen', 'admin_agents', 'admin_dial_permissions', 
              'admin_users', 'admin_routes', 'admin_queues', 'admin_trunkings',
              'admin_dialer', 'admin_extensions', 'is_play', 'has_admin', 'user',
              '_csrf_token', 'start_time', 'directions', 'flash', 'queue',
              'is_auto', 'is_out', 'audio_only', 'session_id', 'is_in',
              'user_queues', 'admin_permissions'}
    filas_cookie = [q for q in queue_names if q not in ignore and len(q) > 2]
    print(f"Filas extraídas do cookie: {len(filas_cookie)}")
    for f in filas_cookie:
        print(f"  {f}")
except Exception as e:
    print(f"Erro ao decodificar cookie: {e}")
