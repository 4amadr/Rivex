from bs4 import BeautifulSoup

def get_html(html):
    return BeautifulSoup(html, "html.parser")

def get_token(html_token):
    token = html_token.find("input", attrs={"name": "authenticity_token"})["value"]
    return token