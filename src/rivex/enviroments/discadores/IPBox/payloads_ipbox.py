def payload_produtividade_agentes(data): # relatórios de PA1
    payload = f'de={data}000000&ate={data}235959'

    return payload

def headers_produtividade_agentes(token):
    headers = {
    'Authorization': f'{{token}}',
    'Content-Type': 'application/x-www-form-urlencoded'
}
    
    return headers

def payload_desempenho_telefonia(data): # relatórios de TA1
    payload=f'de={data}000000&ate={data}235959&operacao=Opera%C3%A7%C3%A3o%201'
    return payload

def headers_desempenho_telefonia(token):
    headers = {
  'Authorization': f'{{token}}',
  'Content-Type': 'application/x-www-form-urlencoded'
}
    return headers

def payload_chamadas_abandonadas(data):
    payload='de={{de}}&ate={{ate}}&fila={{fila}}&status={{status}}&rna={{rna}}&desligada={{desligada}}&durde={{durde}}&durate={{durate}}&filade={{filade}}&filaate={{filaate}}'
    return payload

def headers_chamadas_abandonadas(token):
    headers = {
  'Authorization': f'{{token}}',
  'Content-Type': 'application/json'
}
    
    return headers