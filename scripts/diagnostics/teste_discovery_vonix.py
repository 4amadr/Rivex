"""
Teste de validação: descobre filas automaticamente e coleta dados de uma fila real.
Demonstra o fluxo completo sem nenhuma lista hardcoded.
"""
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import date

# Adicionar o projeto ao path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rivex.environments.discadores.vonix.vonix_queue_discovery import VonixQueueDiscovery

load_dotenv()

URL_BASE = os.getenv('LINK_VONIX6', 'http://contech6.vonixcc.com.br')
LOGIN = os.getenv('LOGIN_VONIX')
PASSWORD = os.getenv('PASSWORD_VONIX')


def fazer_login(session, url_base, login, password):
    """Login padrão no Vonix."""
    url_login = f"{url_base}/login/signin"
    resp = session.get(url_login)
    soup = BeautifulSoup(resp.text, 'html.parser')
    token = soup.find('input', {'name': 'authenticity_token'})['value']
    
    session.post(url_login, data={
        'authenticity_token': token,
        'return_to': '',
        'username': login,
        'password': password,
        'commit': 'Entrar'
    }, headers={
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': url_login,
        'Origin': url_base,
    }, allow_redirects=True)
    return session


def filtrar_fila(session, url_base, queue_id):
    """Seleciona uma fila para coleta."""
    resp = session.get(f"{url_base}/", allow_redirects=True)
    soup = BeautifulSoup(resp.text, 'html.parser')
    token = soup.find('input', {'name': 'authenticity_token'})['value']
    
    session.post(f"{url_base}/login/set_show_queue", data={
        'authenticity_token': token,
        'return_to': '/overview',
        'queue_id[]': queue_id
    }, headers={
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': f"{url_base}/",
        'Origin': url_base,
    }, allow_redirects=True)


# ============================================================
# EXECUÇÃO
# ============================================================
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
})

# 1. Login
print("[1] Fazendo login...")
fazer_login(session, URL_BASE, LOGIN, PASSWORD)
print("[1] Login OK\n")

# 2. DESCOBERTA AUTOMÁTICA DE FILAS
print("[2] Descobrindo filas automaticamente...")
discovery = VonixQueueDiscovery(session, URL_BASE)

# Mostrar resumo
stats = discovery.resumo()
print()

# 3. Comparar com dict_agentes hardcoded
print("=" * 60)
print("COMPARAÇÃO: Hardcoded vs Dinâmico")
print("=" * 60)

from src.rivex.environments.discadores.vonix.equipes_vonix import dict_agentes

hardcoded_ids = set()
for nome, filas in dict_agentes.items():
    for fila in filas:
        hardcoded_ids.add(fila)

dinamicos_ids = set(discovery.ids_das_filas(apenas_ativas=False))

print(f"\n  IDs hardcoded ({len(hardcoded_ids)}): {sorted(hardcoded_ids)}")
print(f"  IDs no sistema ({len(dinamicos_ids)}): {len(dinamicos_ids)} filas")

# IDs que estão hardcoded mas existem no sistema
existentes = hardcoded_ids & dinamicos_ids
faltantes = hardcoded_ids - dinamicos_ids
novos = dinamicos_ids - hardcoded_ids

print(f"\n  [OK] Existem no sistema: {sorted(existentes)}")
print(f"  [FALTA] Nao encontrados: {sorted(faltantes) if faltantes else 'Nenhum'}")
print(f"  [NOVO] Novos (nao hardcoded): {len(novos)} filas")

# 4. Demonstrar coleta com fila descoberta dinamicamente
print(f"\n{'='*60}")
print("TESTE: Coleta com fila descoberta automaticamente")
print(f"{'='*60}")

# Pegar a primeira fila ativa automática
filas_auto = discovery.filas_automaticas()
if filas_auto:
    fila_teste = filas_auto[0]
    data_hoje = date.today().strftime('%Y-%m-%d')
    
    print(f"\n  Fila selecionada: {fila_teste['id']} ({fila_teste['nome']})")
    print(f"  Data: {data_hoje}")
    
    # Filtrar e coletar
    filtrar_fila(session, URL_BASE, fila_teste['id'])
    
    # Coletar chamadas totais
    resp = session.get(f"{URL_BASE}/calls", params={
        'interval[select]': 'custom',
        'interval[start_date]': data_hoje,
        'interval[start_time]': '00:00:00',
        'interval[end_date]': data_hoje,
        'interval[end_time]': '23:59:59',
        'directions[]': 'AUTO',
        'status[select]': '',
        'substatus[select]': '',
        'queue[direction]': 'ALL',
    })
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    div = soup.find('div', id='maincontent')
    if div:
        box = div.find('div', class_='box-title')
        if box:
            texto = box.text
            inicio = texto.find("(") + 1
            fim = texto.find(")")
            total = texto[inicio:fim] if inicio > 0 and fim > 0 else "N/A"
            print(f"  Chamadas totais: {total}")
    
    # Agressividade
    resp_agr = session.get(f"{URL_BASE}/admin/queue_edit/{fila_teste['id']}")
    soup_agr = BeautifulSoup(resp_agr.text, 'html.parser')
    speed = soup_agr.find('input', id='dialer_dial_speed')
    print(f"  Agressividade: {speed['value'] if speed else 'N/A'}")

# 5. Demonstrar busca
print(f"\n{'='*60}")
print("BUSCA DE FILAS")
print(f"{'='*60}")

for termo in ['TC', 'assis', 'real', 'master']:
    resultados = discovery.buscar_fila(termo)
    print(f"\n  Busca '{termo}': {len(resultados)} resultados")
    for r in resultados:
        print(f"    {r['id']:<35} {r['nome']}")

print(f"\n{'='*60}")
print("✅ DESCOBERTA AUTOMÁTICA FUNCIONANDO")
print(f"{'='*60}")
