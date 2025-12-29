import requests
import json
from bs4 import BeautifulSoup

def maxima_voip(usuario, senha):
    session = requests.Session()
    login_url = "http://cliente.maximavoip.net:8080/SipPulsePortal/pages/login/login.jsf"

    rep_login = session.get(login_url)

    soup = BeautifulSoup(rep_login.text, 'html.parser')
    print(rep_login.text[:1000])
    view_state = soup.find("input", {"name": "javax.faces.ViewState"})["value"]



    payload_login = {
        "frmLogin": "frmLogin",
        "frmLogin:username": usuario,
        "frmLogin:password": senha,
        "frmLogin:btnLogin": "Entrar",
        "javax.faces.ViewState": view_state
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response_login = session.post(login_url, data=payload_login, headers=headers)

    if "Bem-vindo" not in response_login.text:
        print("⚠️ Falha no login! Verifique usuário e senha.")
        return

    print("✅ Login realizado com sucesso!")

    # 3️⃣ Agora acessa o relatório
    url_relatorio = "http://cliente.maximavoip.net:8080/SipPulsePortal/pages/reports/asrsubscriber.jsf"
    response = session.post(url_relatorio)

    print("Status:", response.status_code)
    print("Content-Type:", response.headers.get("content-type"))
    print(response.text[:500])  # só pra conferir o que veio

usuario = '80323@sip.maximavoip.net'
senha = 'EqHVcTJpzCKGnl6v'
maxima_voip(usuario, senha)