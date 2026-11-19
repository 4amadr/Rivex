from bs4 import BeautifulSoup

with open('tests/html_pagina_principal.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

form = soup.find('form', action='/login/set_show_queue')
checkboxes = form.find_all('input', {'name': 'queue_id[]'})

print(f"TOTAL DE FILAS: {len(checkboxes)}\n")
print(f"{'ID':<35} | {'NOME DA FILA'}")
print("-" * 80)
for cb in checkboxes:
    queue_id = cb.get('value', '')
    nome = cb.parent.get_text(strip=True)
    print(f"{queue_id:<35} | {nome}")
