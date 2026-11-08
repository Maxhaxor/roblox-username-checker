from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import random
import string
import itertools
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

# Roblox username rules (signup validate):
# length 3-20, letters/digits/underscore, at most one _, cannot start/end with _

HOMO = {
    "a": ["а", "ɑ", "α", "ａ"], "b": ["Ƅ", "ƅ", "ｂ"], "c": ["с", "ϲ", "ｃ"],
    "d": ["ԁ", "ⅾ", "ｄ"], "e": ["е", "ҽ", "ｅ"], "f": ["ƒ", "ｆ"],
    "g": ["ɡ", "ｇ"], "h": ["һ", "հ", "ｈ"], "i": ["і", "ɩ", "ｉ", "ɪ"],
    "j": ["ј", "ｊ"], "k": ["κ", "ｋ"], "l": ["ⅼ", "ｌ", "ʟ"], "m": ["ｍ"],
    "n": ["ո", "ｎ"], "o": ["о", "ο", "ｏ", "օ"], "p": ["р", "ｐ"],
    "q": ["ԛ", "ｑ"], "r": ["ɾ", "ｒ"], "s": ["ѕ", "ｓ"], "t": ["τ", "ｔ"],
    "u": ["υ", "ս", "ｕ"], "v": ["ν", "ｖ"], "w": ["ԝ", "ｗ"],
    "x": ["х", "ⅹ", "ｘ"], "y": ["у", "ｙ", "ʏ"], "z": ["ᴢ", "ｚ"],
    "0": ["𝟎", "𝟘", "０"], "1": ["𝟏", "𝟙", "１"], "2": ["𝟐", "𝟚", "２"],
    "3": ["𝟑", "𝟛", "３"], "4": ["𝟒", "𝟜", "４"], "5": ["𝟓", "𝟝", "５"],
    "6": ["𝟔", "𝟞", "６"], "7": ["𝟕", "𝟟", "７"], "8": ["𝟖", "𝟠", "８"],
    "9": ["𝟗", "𝟡", "９"],
}

BASE = [
    "kill", "dead", "dark", "void", "hate", "rage", "pain", "blood", "gore", "sick",
    "toxic", "venom", "acid", "nuke", "bomb", "gun", "blade", "knife", "slash", "stab",
    "cult", "hex", "curse", "doom", "hell", "demon", "devil", "satan", "lucifer", "beast",
    "psycho", "maniac", "crazy", "insane", "mad", "wild", "feral", "savage", "brutal",
    "thug", "gang", "cartel", "mafia", "outlaw", "bandit", "rogue", "rebel", "anarch",
    "drug", "weed", "coke", "meth", "trip", "high", "drunk", "wasted", "blitzed",
    "sex", "sexy", "slut", "whore", "hoe", "thot", "milf", "dilf", "nsfw", "lewd",
    "dick", "cock", "pussy", "ass", "boob", "tit", "cum", "jizz", "sperm", "anal",
    "fag", "gay", "bi", "trans", "queer", "homo", "lesbo", "dyke",
    "nazi", "kkk", "racist", "bigot", "fascist", "hitler", "stalin",
    "rape", "rapist", "pedo", "terror", "jihad", "isis",
    "suicide", "killme", "die", "murder", "shoot", "hang", "cut", "bleed",
    "scam", "fraud", "phish", "hack", "crack", "leak", "dox", "swat",
    "god", "jesus", "allah", "buddha", "trump", "biden", "obama", "putin", "musk",
    "nigger", "nigga", "chink", "spic", "kike", "wetback", "retard",
    "groom", "loli", "shota", "cp", "jailbait",
    "cumslut", "cumdump", "fucktoy", "fleshlight",
    "necrophile", "zoophile", "bestial", "incest", "twincest",
]
SUFFIX = ["x", "xx", "z", "zz", "69", "420", "666", "13", "88", "14", "1488", "911", "777", "xxx"]
PREFIX = ["x", "xx", "its", "im", "real", "not", "pro", "og", "the", "da", "ya", "ur"]
LEET = str.maketrans({"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7", "b": "8", "g": "9"})

def leet(s: str) -> str:
    return s.translate(LEET)

def apply_homoglyphs(text: str, intensity: float = 0.55) -> str:
    out = []
    for ch in text:
        low = ch.lower()
        if low in HOMO and random.random() < intensity:
            out.append(random.choice(HOMO[low]))
        else:
            out.append(ch)
    return "".join(out)

def valid_roblox_shape(name: str) -> bool:
    if not name or len(name) < 3 or len(name) > 20:
        return False
    if name[0] == "_" or name[-1] == "_":
        return False
    if name.count("_") > 1:
        return False
    for c in name:
        if c == "_" or c.isalnum() or ord(c) > 127:
            continue
        return False
    return True

def generate_candidates(length: int, count: int, mode: str = "mixed", font_bypass: bool = False) -> list[str]:
    letters = string.ascii_lowercase
    digits = string.digits
    alnum = letters + digits
    out = set()

    def add(name: str, force_len: bool = True):
        name = name.strip()
        if force_len and length and length >= 3 and len(name) != length:
            return
        if not valid_roblox_shape(name):
            return
        if font_bypass:
            for intens in (0.35, 0.55, 0.75, 0.9):
                v = apply_homoglyphs(name, intens)
                if valid_roblox_shape(v):
                    out.add(v)
            out.add(name)
        else:
            out.add(name.lower() if name.isascii() else name)

    def gen_sus():
        guard = 0
        while len(out) < count and guard < count * 40:
            guard += 1
            word = random.choice(BASE)
            style = random.randint(0, 11)
            if style == 0:
                add(word, force_len=bool(length >= 3))
            elif style == 1:
                add(word + random.choice(SUFFIX), force_len=bool(length >= 3))
            elif style == 2:
                add(random.choice(PREFIX) + word, force_len=bool(length >= 3))
            elif style == 3:
                add(leet(word), force_len=bool(length >= 3))
            elif style == 4:
                add(leet(word) + random.choice(["69", "420", "666", "xxx", "88"]), force_len=bool(length >= 3))
            elif style == 5:
                core = word if not length else word[: max(1, length - 2)]
                add(core + "".join(random.choices(digits, k=2)), force_len=bool(length >= 3))
            elif style == 6:
                combo = word + random.choice(BASE)
                add(combo[:length] if length >= 3 else combo, force_len=bool(length >= 3))
            elif style == 7:
                add(word + "_" + random.choice(["x", "z", "69", "xxx"]), force_len=False)
            elif style == 8:
                add("i" + word, force_len=bool(length >= 3))
            elif style == 9:
                add(word + "er", force_len=bool(length >= 3))
            elif style == 10:
                add(random.choice(["xx", "x"]) + word[: max(1, (length or 8) - 2)], force_len=bool(length >= 3))
            else:
                add(word[::-1], force_len=bool(length >= 3))
            if length >= 3 and len(out) < count:
                add("".join(random.choices(letters + "xkqzywv" + digits, k=length)))

    def gen_clean():
        ln = length if length >= 3 else 4
        if length == 3:
            pool = ["".join(p) for p in itertools.product(letters, repeat=3)]
            random.shuffle(pool)
            for p in pool:
                add(p)
                if len(out) >= count:
                    return
            while len(out) < count:
                add("".join(random.choices(alnum, k=3)))
            return
        patterns = [
            lambda: "".join(random.choices(letters, k=ln)),
            lambda: "".join(random.sample(letters, min(ln, len(letters)))),
            lambda: random.choice(letters) + "".join(random.choices(digits, k=ln - 1)),
            lambda: "".join(random.choices(letters, k=max(1, ln - 2))) + "".join(random.choices(digits, k=min(2, ln))),
            lambda: random.choice("xzqykwv") + "".join(random.choices(alnum, k=ln - 1)),
            lambda: random.choice("aeiou") + "".join(random.choices(letters, k=ln - 1)),
        ]
        while len(out) < count:
            add(random.choice(patterns)())

    if mode == "sus":
        gen_sus()
    elif mode == "clean":
        gen_clean()
    else:
        gen_sus()
        gen_clean()
    result = list(out)
    random.shuffle(result)
    return result[:count]


def check_one(username: str) -> dict:
    username = username.strip()
    if not username:
        return {"username": username, "available": False, "error": "empty"}
    if len(username) < 3:
        return {"username": username, "available": False, "error": "too_short", "code": 3}
    if len(username) > 20:
        return {"username": username, "available": False, "error": "too_long", "code": 3}

    try:
        url = (
            f"{VALIDATE}?username={quote(username, safe='')}"
            f"&birthday=2000-01-01T00:00:00.000Z&context=Signup"
        )
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
        # 2+ invalid / moderated / shape errors
        return {
            "username": username,
            "available": False,
            "status": 200,
            "code": code,
            "message": msg,
            "error": "invalid",
            "bypass": bypass,
        }
    except Exception as e:
        return {"username": username, "available": None, "error": str(e)}


def check_many(names: list[str], workers: int = 15) -> list[dict]:
    results = [None] * len(names)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        future_map = {ex.submit(check_one, n): i for i, n in enumerate(names)}
        for fut in as_completed(future_map):
            idx = future_map[fut]
            try:
                results[idx] = fut.result()
            except Exception as e:
                results[idx] = {"username": names[idx], "available": None, "error": str(e)}
    return results


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
def api_check_batch(usernames: str = Query(...), workers: int = Query(15, ge=1, le=25)):
    names = [u.strip() for u in usernames.split(",") if u.strip()]
    if len(names) > 100:
        raise HTTPException(400, "Max 100 usernames per batch")
    return JSONResponse({"results": check_many(names, workers=min(workers, 25)), "count": len(names)})


@app.get("/api/candidates")
def api_candidates(
    length: int = Query(0, ge=0, le=20),
    limit: int = Query(500, ge=1, le=5000),
    mode: str = Query("mixed", pattern="^(mixed|clean|sus)$"),
    font_bypass: bool = Query(False),
):
    names = generate_candidates(length if length >= 3 else 0, limit, mode=mode, font_bypass=font_bypass)
    return JSONResponse({"length": length, "mode": mode, "font_bypass": font_bypass, "count": len(names), "candidates": names})


@app.get("/api/scan")
def api_scan(
    length: int = Query(4, ge=3, le=12),
    limit: int = Query(100, ge=1, le=400),
    workers: int = Query(15, ge=1, le=25),
    mode: str = Query("mixed", pattern="^(mixed|clean|sus)$"),
    font_bypass: bool = Query(False),
):
    candidates = generate_candidates(length, limit, mode=mode, font_bypass=font_bypass)
    results = check_many(candidates, workers=workers)
    available = [r for r in results if r.get("available") is True]
    return JSONResponse({
        "length": length,
        "mode": mode,
        "font_bypass": font_bypass,
        "checked": len(results),
        "available_count": len(available),
        "available": available,
        "all": results,
    })
