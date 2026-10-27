"""
Diagnostico isolado de timeout/concorrencia do Vonix (somente GET de leitura).

- Credenciais vem do .env (URL_BASE_VONIX6, LOGIN_VONIX, SENHA_VONIX); nunca sao impressas.
- Fase 1: sequencial, timeouts decrescentes a partir de 35 s.
- Fase 2: concorrencia gradual (conservadora) com o menor timeout confiavel.
- Para sozinho em 429/5xx, taxa de erro alta, degradacao de latencia, Ctrl-C
  ou ao atingir --max-requests.
- Saidas (gitignored): output/vonix_diag/raw_*.jsonl e relatorio_*.md

Uso:
    python tests/diag_vonix_timeout.py --reps 3 --max-requests 300
    python tests/diag_vonix_timeout.py --concurrency 1,2,3 --queue-id 123
"""
import argparse
import json
import os
import re
import statistics
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output" / "vonix_diag"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36")
STOP = threading.Event()


class Budget:
    """Limite global e thread-safe de requisicoes."""
    def __init__(self, maximo):
        self.maximo, self.usado, self.lock = maximo, 0, threading.Lock()

    def take(self):
        with self.lock:
            if self.usado >= self.maximo or STOP.is_set():
                return False
            self.usado += 1
            return True


def payloads(dia: date):
    d = dia.strftime("%d/%m/%Y")
    d7 = (dia - timedelta(days=6)).strftime("%d/%m/%Y")

    def calls(status="", **extra):
        p = {
            "interval[select]": "custom", "interval[start_date]": d,
            "interval[start_time]": "00:00:00", "interval[end_date]": d,
            "interval[end_time]": "23:59:59", "terminal": "", "agent": "",
            "queue[direction]": "ALL", "sort": "", "to_excel": "0", "to_csv": "0",
            "x": "10", "y": "10", "locality": "", "call_type_id": "",
            "carrier_id": "", "trunking_id": "", "directions[]": "AUTO",
            "waits": "Igual", "call_waiting": "", "duration": "Igual",
            "duration_call": "", "status[select]": status, "substatus[select]": "",
        }
        p.update(extra)
        return p

    return {
        "/calls": {
            "calls_total": calls(),
            "calls_completed": calls("completed"),
            "calls_abandon": calls("abandon"),
            "calls_discard": calls("discard"),
            "calls_total_7d": calls(**{"interval[start_date]": d7}),
        },
        "/agents/calls_overview": {
            "agents_1d": {"interval[select]": "custom",
                          "interval[start_date]": d, "interval[end_date]": d},
            "agents_7d": {"interval[select]": "custom",
                          "interval[start_date]": d7, "interval[end_date]": d},
        },
    }


def login(base, user, pwd):
    s = requests.Session()
    s.headers["User-Agent"] = UA
    r = s.get(f"{base}/login/signin", timeout=35)
    tok = BeautifulSoup(r.text, "html.parser").find("input", {"name": "authenticity_token"})
    if tok is None:
        raise RuntimeError("authenticity_token nao encontrado")
    s.post(f"{base}/login/signin", timeout=35, data={
        "authenticity_token": tok["value"], "return_to": "", "username": user,
        "password": pwd, "commit": "Entrar"})
    home = s.get(base + "/", timeout=35)
    if BeautifulSoup(home.text, "html.parser").find("input", {"name": "authenticity_token", "type": "hidden"}) \
            and "login/signin" in home.url:
        raise RuntimeError("login falhou (retornou formulario de login)")
    return s, home.text


def pick_queue(html, forced):
    if forced:
        return forced
    soup = BeautifulSoup(html, "html.parser")
    for el in soup.find_all(["input", "option"]):
        if (el.get("name") == "queue_id[]" or el.name == "option") and el.get("value", "").isdigit():
            return el["value"]
    return None


def set_queue(s, base, queue_id):
    r = s.get(base + "/", timeout=35)
    tok = BeautifulSoup(r.text, "html.parser").find("input", {"name": "authenticity_token"})
    if tok is None or not queue_id:
        return False
    s.post(f"{base}/login/set_show_queue", timeout=35, data={
        "authenticity_token": tok["value"], "return_to": "/overview", "queue_id[]": queue_id})
    return True


def classify(exc):
    """Separa as categorias de falha; nao presume que sao o mesmo problema."""
    msg = str(exc).lower()
    if isinstance(exc, requests.exceptions.ConnectTimeout):
        return "timeout_conexao"
    if isinstance(exc, requests.exceptions.ReadTimeout):
        return "timeout_leitura"
    if "pool" in msg and ("full" in msg or "exhaust" in msg):
        return "pool_connection"
    if isinstance(exc, requests.exceptions.ConnectionError):
        return "falha_conexao"
    return "erro_outro"


def one(s, base, ep, name, params, timeout, fase, conc, budget, fh, lock):
    if not budget.take():
        return None
    t0 = time.perf_counter()
    rec = {"ts": datetime.now().isoformat(timespec="seconds"), "fase": fase, "endpoint": ep,
           "payload": name, "timeout": timeout, "concorrencia": conc,
           "status": None, "erro": None, "bytes": 0, "sessao_valida": None}
    try:
        r = s.get(base + ep, params=params, timeout=timeout)
        rec["status"], rec["bytes"] = r.status_code, len(r.content)
        rec["sessao_valida"] = not ("login/signin" in r.url
                                    or "name=\"authenticity_token\"" in r.text[:20000]
                                    and "password" in r.text[:20000].lower())
        if r.status_code == 429:
            rec["erro"] = "http_429"
        elif r.status_code >= 500:
            rec["erro"] = f"http_{r.status_code}"
        elif r.status_code != 200:
            rec["erro"] = f"http_{r.status_code}"
        elif not rec["sessao_valida"]:
            rec["erro"] = "sessao_perdida"
    except Exception as e:  # noqa: BLE001
        rec["erro"] = classify(e)
    rec["tempo_s"] = round(time.perf_counter() - t0, 3)
    with lock:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        fh.flush()
    return rec


def stats(recs):
    ok = [r for r in recs if not r["erro"]]
    lat = sorted(r["tempo_s"] for r in ok)
    errs = {}
    for r in recs:
        if r["erro"]:
            errs[r["erro"]] = errs.get(r["erro"], 0) + 1
    p95 = lat[min(len(lat) - 1, int(round(0.95 * (len(lat) - 1))))] if lat else None
    return {"n": len(recs), "sucesso": len(ok) / len(recs) if recs else 0,
            "media": statistics.mean(lat) if lat else None,
            "mediana": statistics.median(lat) if lat else None,
            "p95": p95, "max": lat[-1] if lat else None, "erros": errs}


def fmt(x):
    return "-" if x is None else f"{x:.2f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeouts", default="35,30,25,20,15,10,8,6,5,4,3,2")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--concurrency", default="1,2,3,4")
    ap.add_argument("--conc-requests", type=int, default=12, help="requisicoes por nivel/endpoint")
    ap.add_argument("--max-requests", type=int, default=300)
    ap.add_argument("--pause", type=float, default=1.0, help="pausa entre requisicoes sequenciais")
    ap.add_argument("--date-offset", type=int, default=4, help="dias atras (padrao do Rivex = 4)")
    ap.add_argument("--queue-id", default=None)
    ap.add_argument("--max-error-rate", type=float, default=0.10)
    a = ap.parse_args()

    load_dotenv(ROOT / ".env")
    base = (os.getenv("URL_BASE_VONIX6") or "").rstrip("/")
    user, pwd = os.getenv("LOGIN_VONIX"), os.getenv("SENHA_VONIX")
    if not (base and user and pwd):
        sys.exit("Variaveis URL_BASE_VONIX6/LOGIN_VONIX/SENHA_VONIX ausentes no .env")
    if not base.startswith("http"):
        base = "http://" + base

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_path, rep_path = OUT_DIR / f"raw_{stamp}.jsonl", OUT_DIR / f"relatorio_{stamp}.md"
    timeouts = [int(x) for x in a.timeouts.split(",")]
    levels = [int(x) for x in a.concurrency.split(",")]
    budget, lock = Budget(a.max_requests), threading.Lock()
    pl = payloads(date.today() - timedelta(days=a.date_offset))
    notes, seq, conc_res, reliable = [], {}, {}, {}

    s, home = login(base, user, pwd)
    qid = pick_queue(home, a.queue_id)
    if set_queue(s, base, qid):
        notes.append("Fila selecionada via set_show_queue (estado de sessao; id omitido).")
    else:
        notes.append("Nenhuma fila identificada; consultas sem filtro de fila (dados podem ser vazios).")
    adapter = HTTPAdapter(pool_connections=4, pool_maxsize=max(levels), pool_block=False)
    s.mount("http://", adapter)
    s.mount("https://", adapter)

    try:
        with open(raw_path, "w", encoding="utf-8") as fh:
            # ---------- Fase 1: sequencial ----------
            for ep, items in pl.items():
                for name, params in items.items():
                    for t in timeouts:
                        recs = []
                        for _ in range(a.reps):
                            r = one(s, base, ep, name, params, t, "sequencial", 1, budget, fh, lock)
                            if r is None:
                                break
                            recs.append(r)
                            time.sleep(a.pause)
                        if not recs:
                            STOP.set()
                            break
                        st = stats(recs)
                        seq[(ep, name, t)] = st
                        if any(k in ("http_429",) or k.startswith("http_5") for k in st["erros"]):
                            notes.append(f"Parada: {ep}/{name} t={t}s retornou 429/5xx {st['erros']}")
                            STOP.set()
                            break
                        if st["sucesso"] < 1.0:  # primeira falha: nao desce mais para este payload
                            break
                    if STOP.is_set():
                        break
                if STOP.is_set():
                    break

            # menor timeout confiavel: 100% sucesso e p95 < 80% do timeout,
            # considerando margem: o menor timeout cujo sucesso foi 100% e todos os maiores tambem
            for ep in pl:
                cands = []
                for name in pl[ep]:
                    oks = [t for t in timeouts if (ep, name, t) in seq]
                    good = [t for t in oks if seq[(ep, name, t)]["sucesso"] == 1.0
                            and (seq[(ep, name, t)]["p95"] or 0) <= 0.8 * t]
                    if good:
                        cands.append(min(good))
                if cands:
                    reliable[ep] = max(cands)  # o pior payload define o endpoint

            # ---------- Fase 2: concorrencia gradual ----------
            base_p95 = {}
            for ep in pl:
                if STOP.is_set() or ep not in reliable:
                    continue
                t = reliable[ep]
                names = list(pl[ep])
                for lv in levels:
                    if STOP.is_set():
                        break
                    jobs = [names[i % len(names)] for i in range(a.conc_requests)]
                    with ThreadPoolExecutor(max_workers=lv) as ex:
                        futs = [ex.submit(one, s, base, ep, n, pl[ep][n], t, "concorrente",
                                          lv, budget, fh, lock) for n in jobs]
                        recs = [f.result() for f in futs if f.result() is not None]
                    if not recs:
                        STOP.set()
                        break
                    st = stats(recs)
                    conc_res[(ep, lv)] = st
                    if lv == levels[0]:
                        base_p95[ep] = st["p95"]
                    bad = (1 - st["sucesso"]) > a.max_error_rate
                    sat = any(k == "http_429" or k.startswith("http_5") or k == "pool_connection"
                              for k in st["erros"])
                    degr = bool(base_p95.get(ep) and st["p95"] and st["p95"] > 2 * base_p95[ep])
                    if bad or sat or degr:
                        notes.append(f"Parada concorrencia {ep} nivel {lv}: "
                                     f"{'erros ' if bad else ''}{'saturacao ' if sat else ''}"
                                     f"{'degradacao p95>2x ' if degr else ''}{st['erros']}")
                        break
                    time.sleep(2)
    except KeyboardInterrupt:
        STOP.set()
        notes.append("Interrompido pelo usuario (Ctrl-C); resultados parciais.")
    finally:
        s.close()

    # ---------- Relatorio (sem credenciais) ----------
    L = ["# Relatorio de diagnostico Vonix (gerado automaticamente)", "",
         f"- Data da execucao: {datetime.now():%Y-%m-%d %H:%M}",
         f"- Requisicoes usadas: {budget.usado}/{a.max_requests}",
         f"- Data consultada: hoje - {a.date_offset} dias; reps/timeout: {a.reps}; pausa: {a.pause}s",
         f"- Concorrencia testada: {levels}; requisicoes/nivel: {a.conc_requests}", "",
         "## Observacoes", *[f"- {n}" for n in notes], "",
         "## Fase sequencial", "",
         "| Endpoint | Payload | Timeout | N | Sucesso | Media | Mediana | P95 | Max | Erros |",
         "|---|---|---:|---:|---:|---:|---:|---:|---:|---|"]
    for (ep, name, t), st in seq.items():
        L.append(f"| {ep} | {name} | {t} | {st['n']} | {st['sucesso']:.0%} | {fmt(st['media'])} | "
                 f"{fmt(st['mediana'])} | {fmt(st['p95'])} | {fmt(st['max'])} | {st['erros'] or '-'} |")
    L += ["", "## Fase de concorrencia", "",
          "| Endpoint | Nivel | N | Sucesso | Media | Mediana | P95 | Erros |",
          "|---|---:|---:|---:|---:|---:|---:|---|"]
    for (ep, lv), st in conc_res.items():
        L.append(f"| {ep} | {lv} | {st['n']} | {st['sucesso']:.0%} | {fmt(st['media'])} | "
                 f"{fmt(st['mediana'])} | {fmt(st['p95'])} | {st['erros'] or '-'} |")
    L += ["", "## Menor timeout confiavel (criterio: 100% sucesso e P95 <= 80% do timeout)", ""]
    L += [f"- `{ep}`: **{t}s**" for ep, t in reliable.items()] or ["- Inconclusivo."]
    L += ["", "> Resultado valido apenas para a janela, fila e carga testadas. "
          "Timeout de aplicacao (timeout_leitura/conexao), falha de conexao, pool e "
          "erros HTTP sao contabilizados separadamente."]
    rep_path.write_text("\n".join(L), encoding="utf-8")
    print(f"Relatorio: {rep_path}\nBruto: {raw_path}")


if __name__ == "__main__":
    main()
