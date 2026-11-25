from bs4 import BeautifulSoup

def get_token_login_vonix(login):
    sopa = BeautifulSoup(login, "html.parser")
    token_input = sopa.find("input", {"name": "authenticity_token"})
    if token_input is None or not token_input.get("value"):
        raise ValueError("token do vonix não encontrado")

    return str(token_input["value"])
