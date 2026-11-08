from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import random
import string
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote

app = FastAPI(title="Roblox Username Checker")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

VALIDATE = "https://auth.roblox.com/v1/usernames/validate"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

def check_one(username: str) -> dict:
    username = username.strip()
    if not username:
        return {"username": username, "available": False, "error": "empty"}
    if len(username) < 3:
        return {"username": username, "available": False, "error": "too_short", "code": 3}
    if len(username) > 20:
        return {"username": username, "available": False, "error": "too_long", "code": 3}
    try:
        url = f"{VALIDATE}?username={quote(username, safe='')}&birthday=2000-01-01T00:00:00.000Z&context=Signup"
        r = SESSION.get(url, timeout=8)
        if r.status_code != 200:
            if r.status_code in (429, 500, 502, 503):
                time.sleep(0.4)
                r = SESSION.get(url, timeout=8)
            if r.status_code != 200:
                return {"username": username, "available": None, "status": r.status_code, "error": "http"}
        data = r.json()
        code = data.get("code")
        msg = data.get("message", "")
        bypass = not username.isascii()
        if code == 0:
            return {"username": username, "available": True, "status": 200, "code": 0, "message": msg, "bypass": bypass}
        if code == 1:
            return {"username": username, "available": False, "status": 200, "code": 1, "message": msg, "bypass": bypass}
        return {"username": username, "available": False, "status": 200, "code": code, "message": msg, "error": "invalid", "bypass": bypass}
    except Exception as e:
        return {"username": username, "available": None, "error": str(e)}

def check_many(names, workers=12):
    results = [None] * len(names)
    with ThreadPoolExecutor(max_workers=max(1, min(workers, 34))) as ex:
        future_map = {ex.submit(check_one, n): i for i, n in enumerate(names)}
        for fut in as_completed(future_map):
            idx = future_map[fut]
            try:
                results[idx] = fut.result()
            except Exception as e:
                results[idx] = {"username": names[idx], "available": None, "error": str(e)}
    return results

def generate_candidates(length, count, mode="mixed", font_bypass=False):
    letters = string.ascii_lowercase
    digits = string.digits
    alnum = letters + digits
    out = set()
    def valid(name):
        if not name or len(name) < 3 or len(name) > 20:
            return False
        if name[0] == "_" or name[-1] == "_" or name.count("_") > 1:
            return False
        return all(c == "_" or c.isalnum() or ord(c) > 127 for c in name)
    def add(name, force_len=True):
        name = name.strip()
        if force_len and length and length >= 3 and len(name) != length:
            return
        if valid(name):
            out.add(name.lower() if name.isascii() else name)
    guard = 0
    while len(out) < count and guard < count * 50:
        guard += 1
        ln = length if length >= 3 else random.randint(4, 8)
        if mode == "clean" or (mode == "mixed" and random.random() < 0.55):
            add("".join(random.choices(alnum, k=ln)))
        else:
            w = random.choice(["x", "z", "q", "v", "k", "w", "y"]) + "".join(random.choices(alnum, k=ln - 1))
            add(w)
    return list(out)[:count]

@app.get("/")
def home():
    for p in ("public/index.html", "index.html"):
        if os.path.exists(p):
            return FileResponse(p, media_type="text/html")
    return HTMLResponse("<h1>missing ui</h1>")

@app.get("/api/check")
def api_check(username: str = Query(..., min_length=1)):
    return JSONResponse(check_one(username))

@app.get("/api/check/batch")
def api_check_batch(usernames: str = Query(...), workers: int = Query(12, ge=1, le=34)):
    names = [u.strip() for u in usernames.split(",") if u.strip()]
    if len(names) > 50:
        raise HTTPException(400, "Max 50 usernames per batch")
    return JSONResponse({"results": check_many(names, workers=min(workers, 34)), "count": len(names)})

@app.get("/api/candidates")
def api_candidates(
    length: int = Query(0, ge=0, le=20),
    limit: int = Query(100, ge=1, le=5000),
    mode: str = Query("mixed", pattern="^(mixed|clean|sus)$"),
    font_bypass: bool = Query(False),
):
    names = generate_candidates(length if length >= 3 else 0, limit, mode=mode, font_bypass=font_bypass)
    return JSONResponse({"length": length, "mode": mode, "font_bypass": font_bypass, "count": len(names), "candidates": names})

@app.get("/api/scan")
def api_scan(
    length: int = Query(6, ge=3, le=12),
    limit: int = Query(100, ge=1, le=5000),
    workers: int = Query(12, ge=1, le=34),
    mode: str = Query("mixed", pattern="^(mixed|clean|sus)$"),
    font_bypass: bool = Query(False),
):
    candidates = generate_candidates(length, limit, mode=mode, font_bypass=font_bypass)
    results = check_many(candidates, workers=workers)
    available = [r for r in results if r.get("available") is True]
    return JSONResponse({
        "length": length,
        "mode": mode,
        "checked": len(results),
        "available_count": len(available),
        "available": available,
        "all": results,
    })
