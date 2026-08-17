import time
import os
import requests
from dotenv import load_dotenv
from src.rivex.utils.environments_utils.discador.callix.payloads_callix import payload_callix, headers_callix

load_dotenv()

USUARIO = os.getenv("USUARIO_CALLIX_GERAL")
SENHA = os.getenv("SENHA_CALLIX_GERAL")


def login_callix(cliente):
    url_base = f"https://{cliente}.callix.com.br"
    url_login = f"{url_base}/api/v4/auth/session"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Origin": url_base,
        "Referer": url_base,
        "X-Api": "1, 1",
        "User-Agent": "Mozilla/5.0",
    }
    resp = requests.post(url_login, json={"username": USUARIO, "password": SENHA}, headers=headers)
    resp.raise_for_status()
    token_login = resp.json()["token"]
    print(f"  [LOGIN] OK")
    return token_login


def get_api_token(cliente, token_sessao):
    url_tokens = f"https://{cliente}.callix.com.br/api/v4/entities/api-tokens"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "cookie": f"token={token_sessao}",
        "x-api": "1",
        "x-timezone": "America/Sao_Paulo",
    }
    params = {"sort": "token", "page[limit]": "100"}
    resp = requests.get(url_tokens, headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json()["data"]
    if not data:
        raise RuntimeError("Nenhum token de API encontrado.")
    token_api = data[0]["attributes"]["token"]
    print(f"  [TOKEN API] OK - Bearer obtido")
    return token_api


def requisitar(cliente, bearer, data, extra_params=None):
    url = f"https://{cliente}.callix.com.br/api/v1/campaign_missed_calls"
    params = payload_callix("campaign_missed_calls", data)
    if extra_params:
        params.update(extra_params)
    h = headers_callix(bearer)
    inicio = time.perf_counter()
    resp = requests.get(url, headers=h, params=params)
    elapsed = time.perf_counter() - inicio
    print(f"  [REQ] status={resp.status_code}  tempo={elapsed:.3f}s  extra={extra_params}")
    return resp, elapsed


def inspecionar_failure_cause(dados):
    contagem = {}
    for item in dados:
        attrs = item.get("attributes", {})
        fc = attrs.get("failure_cause", attrs.get("failureCause", "SEM_CAMPO"))
        contagem[str(fc)] = contagem.get(str(fc), 0) + 1
    return contagem


def cabecalhos_rate_limit(resp):
    rl = {k: v for k, v in resp.headers.items()
          if any(x in k.lower() for x in ["ratelimit","retry","x-rate","x-limit","limit"])}
    if rl:
        print(f"  [HEADERS-RL] {rl}")
    else:
        print("  [HEADERS-RL] Nenhum header de rate-limit encontrado")
    return rl


def teste_1(cliente, bearer, data):
    print()
    print("=" * 70)
    print("TESTE 1 - Requisicao unica vs duas requisicoes filtradas")
    print("=" * 70)

    resp_sem, _ = requisitar(cliente, bearer, data)
    cabecalhos_rate_limit(resp_sem)

    if resp_sem.status_code != 200:
        print(f"  [FALHA] status={resp_sem.status_code}")
        return None

    js = resp_sem.json()
    dados = js.get("data", [])
    total = js.get("meta", {}).get("total", len(dados))
    print(f"  [SEM FILTRO] total={total}  pagina={len(dados)}")

    dist = inspecionar_failure_cause(dados)
    print(f"  [DISTRIBUICAO failure_cause] {dist}")

    abandonadas_local = [
        i for i in dados
        if str(i.get("attributes", {}).get("failure_cause",
               i.get("attributes", {}).get("failureCause", ""))) == "9"
    ]
    print(f"  [FILTRO LOCAL fc=9] {len(abandonadas_local)} registros")

    time.sleep(2)

    resp_com, _ = requisitar(cliente, bearer, data, {"filter[failure_cause]": "9"})
    cabecalhos_rate_limit(resp_com)

    if resp_com.status_code == 429:
        print("  [429] Aguardando 15s...")
        time.sleep(15)
        resp_com, _ = requisitar(cliente, bearer, data, {"filter[failure_cause]": "9"})

    if resp_com.status_code != 200:
        print(f"  [FALHA filtro] status={resp_com.status_code}")
        return None

    js2 = resp_com.json()
    dados_filt = js2.get("data", [])
    total2 = js2.get("meta", {}).get("total", len(dados_filt))
    print(f"  [COM FILTRO SERVIDOR] total={total2}  pagina={len(dados_filt)}")

    print()
    print("  [CONCLUSAO TESTE 1]")
    if len(abandonadas_local) == len(dados_filt) and len(dados_filt) > 0:
        print("  >>> RESULTADO: Filtro local EQUIVALE ao filtro servidor.")
        print("      -> SEGURO fazer UMA requisicao e separar localmente.")
        print("      -> Timer de 60s pode ser ELIMINADO.")
    elif len(dados_filt) > 0 and len(abandonadas_local) == 0:
        print("  >>> ATENCAO: failure_cause ausente nos dados sem filtro.")
        print("      -> Campo pode ser omitido quando sem filtro.")
    elif len(dados_filt) == 0 and len(abandonadas_local) == 0:
        print("  >>> INFO: Nenhum dado com failure_cause=9 na data selecionada.")
        print("      -> Testar com data diferente para conclusao definitiva.")
    else:
        diff = abs(len(abandonadas_local) - len(dados_filt))
        print(f"  >>> DIVERGENCIA: local={len(abandonadas_local)} vs servidor={len(dados_filt)} diff={diff}")

    return {
        "total_sem_filtro": total,
        "total_com_filtro": total2,
        "filtro_local_count": len(abandonadas_local),
        "distribuicao": dist,
    }


def teste_4(cliente, bearer, data):
    print()
    print("=" * 70)
    print("TESTE 4 - Inspecao de campos com e sem filtro")
    print("=" * 70)

    resp, _ = requisitar(cliente, bearer, data)
    if resp.status_code != 200:
        print(f"  [FALHA] {resp.status_code}")
        return None

    dados = resp.json().get("data", [])
    campos_sem = set()
    if dados:
        primeiro = dados[0]
        attrs = primeiro.get("attributes", {})
        campos_sem = set(attrs.keys())
        print(f"  [CAMPOS sem filtro] total_campos={len(campos_sem)}")
        print(f"  {sorted(campos_sem)}")
        fc = attrs.get("failure_cause", attrs.get("failureCause", "NAO_ENCONTRADO"))
        print(f"  [failure_cause no reg 0] valor={fc!r}")
        print()
        print("  [AMOSTRA attrs do primeiro registro]")
        for k, v in list(attrs.items()):
            print(f"    {k}: {v!r}")
    else:
        print("  [SEM DADOS] sem registros para a data (sem filtro)")

    time.sleep(5)

    resp2, _ = requisitar(cliente, bearer, data, {"filter[failure_cause]": "9"})
    if resp2.status_code != 200:
        print(f"  [FALHA filtrado] {resp2.status_code}")
        return None

    dados2 = resp2.json().get("data", [])
    campos_com = set()
    if dados2:
        primeiro2 = dados2[0]
        attrs2 = primeiro2.get("attributes", {})
        campos_com = set(attrs2.keys())
        print(f"  [CAMPOS com filtro fc=9] total_campos={len(campos_com)}")
        print(f"  {sorted(campos_com)}")
        fc2 = attrs2.get("failure_cause", attrs2.get("failureCause", "NAO_ENCONTRADO"))
        print(f"  [failure_cause no reg 0 filtrado] valor={fc2!r}")
    else:
        print("  [SEM DADOS] sem registros com failure_cause=9")

    print()
    print("  [CONCLUSAO TESTE 4]")
    if "failure_cause" in campos_sem or "failureCause" in campos_sem:
        print("  >>> OK - Campo failure_cause PRESENTE sem filtro.")
        print("      -> Filtro local VIAVEL.")
    else:
        print("  >>> NAO - Campo failure_cause AUSENTE sem filtro.")
        print("      -> API omite o campo quando nao filtrado.")

    return {"campos_sem_filtro": sorted(campos_sem), "campos_com_filtro": sorted(campos_com)}


def teste_3(cliente, bearer, data):
    print()
    print("=" * 70)
    print("TESTE 3 - Header Retry-After em respostas 429")
    print("=" * 70)

    print("  Disparando requisicoes consecutivas sem delay para induzir 429...")
    got_429 = False
    retry_after = None

    for i in range(6):
        resp, _ = requisitar(cliente, bearer, data)
        if resp.status_code == 429:
            got_429 = True
            all_h = dict(resp.headers)
            print(f"  [TODOS OS HEADERS 429] {all_h}")
            retry_after = (
                resp.headers.get("Retry-After")
                or resp.headers.get("X-RateLimit-Reset")
                or resp.headers.get("X-Rate-Limit-Reset")
            )
            print(f"  [Retry-After extraido] {retry_after!r}")
            break
        time.sleep(0.3)

    if not got_429:
        print("  INFO: nao foi possivel induzir 429 com 6 requisicoes rapidas.")

    print()
    print("  [CONCLUSAO TESTE 3]")
    if got_429 and retry_after:
        print(f"  >>> OK - API informa Retry-After={retry_after}.")
        print("      -> Implementar retry dinamico com esse valor.")
    elif got_429:
        print("  >>> ATENCAO - 429 sem Retry-After.")
        print("      -> Timer fixo ou exponential backoff necessarios.")
    else:
        print("  >>> INFO - 429 nao atingido. Rate-limit pode ser generoso.")

    return {"induziu_429": got_429, "retry_after": retry_after}


def teste_2(cliente, bearer, data):
    print()
    print("=" * 70)
    print("TESTE 2 - Intervalo minimo entre requisicoes para evitar 429")
    print("=" * 70)

    delays = [1, 2, 5, 10, 15]
    resultados = {}

    print("  Aguardando 30s para reset do rate-limit...")
    time.sleep(30)

    for delay in delays:
        print(f"  --- Testando delay={delay}s ---")
        resp1, _ = requisitar(cliente, bearer, data)
        if resp1.status_code == 429:
            print("  [429 na REQ1] Aguardando 30s...")
            time.sleep(30)
            resp1, _ = requisitar(cliente, bearer, data)

        print(f"  Aguardando {delay}s...")
        time.sleep(delay)

        resp2, _ = requisitar(cliente, bearer, data, {"filter[failure_cause]": "9"})
        sucesso = resp1.status_code == 200 and resp2.status_code == 200
        resultados[delay] = {
            "req1": resp1.status_code, "req2": resp2.status_code, "ok": sucesso
        }

        label = "SUCESSO" if sucesso else "FALHA"
        print(f"  [{label}] delay={delay}s req1={resp1.status_code} req2={resp2.status_code}")
        time.sleep(30)

    print()
    print("  [CONCLUSAO TESTE 2 - Resumo]")
    menor = None
    for delay, r in resultados.items():
        st = "OK" if r["ok"] else "XX"
        print(f"    {st}  delay={delay}s | req1={r['req1']} | req2={r['req2']}")
        if r["ok"] and menor is None:
            menor = delay

    if menor is not None:
        print(f"  >>> Intervalo minimo identificado: {menor}s  (atual: 60s)")
        print(f"  >>> Economia: {60 - menor}s por cliente por coleta")
    else:
        print("  >>> Nenhum delay testado foi suficiente. Usar req. unica (Teste 1).")

    return resultados


if __name__ == "__main__":
    print()
    print("#" * 70)
    print("# RIVEX - DIAGNOSTICO RATE LIMIT: campaign_missed_calls")
    print("#" * 70)

    CLIENTE = os.getenv("CALLIX_CLIENTE_TESTE", "").strip()
    DATA = os.getenv("CALLIX_DATA_TESTE", "2026-08-14").strip()

    if not CLIENTE:
        print()
        print("[ERRO] Defina CALLIX_CLIENTE_TESTE no .env (ex: contechsystem)")
        exit(1)
    if not USUARIO or not SENHA:
        print()
        print("[ERRO] USUARIO_CALLIX_GERAL e SENHA_CALLIX_GERAL devem estar no .env")
        exit(1)

    print(f"  Cliente: {CLIENTE}.callix.com.br")
    print(f"  Data: {DATA}")
    print()
    print("  Realizando login...")
    tok_sessao = login_callix(CLIENTE)
    bearer = get_api_token(CLIENTE, tok_sessao)

    r1 = teste_1(CLIENTE, bearer, DATA)
    time.sleep(10)
    r4 = teste_4(CLIENTE, bearer, DATA)
    time.sleep(15)
    r3 = teste_3(CLIENTE, bearer, DATA)
    time.sleep(30)
    r2 = teste_2(CLIENTE, bearer, DATA)

    print()
    print("#" * 70)
    print("# RESUMO FINAL")
    print("#" * 70)
    print(f"  T1 (req unica):   {r1}")
    print(f"  T4 (campos):      {r4}")
    print(f"  T3 (retry-after): {r3}")
    print(f"  T2 (min delay):   {r2}")
