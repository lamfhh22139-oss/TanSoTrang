# -*- coding: utf-8 -*-
"""Phục vụ bản web (pygbag) và API nick / phòng hợp tác. Cần COOP/COEP cho WASM."""
import hashlib
import json
import os
import secrets
import sqlite3
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build", "web")
PORT = int(os.environ.get("PORT", "8080"))
SO_NGUOI = 4
HET_MANG = 10.0

_KHOA = threading.Lock()
_DB = None
_PHONG = {}


def thu_muc_du_lieu():
    env = os.environ.get("DATA_DIR")
    if env:
        os.makedirs(env, exist_ok=True)
        return env
    for p in ("/data", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")):
        try:
            os.makedirs(p, exist_ok=True)
            thu = os.path.join(p, ".viet")
            with open(thu, "w", encoding="utf-8") as f:
                f.write("1")
            os.remove(thu)
            return p
        except Exception:
            continue
    return os.path.dirname(os.path.abspath(__file__))


def khoi_tao(thu_muc=None):
    """Mở sqlite nick. Gọi lại được (test)."""
    global _DB
    if thu_muc is None:
        thu_muc = thu_muc_du_lieu()
    os.makedirs(thu_muc, exist_ok=True)
    duong = os.path.join(thu_muc, "tanso.db")
    db = sqlite3.connect(duong, check_same_thread=False)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute(
        """CREATE TABLE IF NOT EXISTS nick (
            nick TEXT PRIMARY KEY COLLATE NOCASE,
            salt BLOB NOT NULL,
            bam BLOB NOT NULL,
            tao INTEGER NOT NULL
        )"""
    )
    db.execute(
        """CREATE TABLE IF NOT EXISTS phien (
            token TEXT PRIMARY KEY,
            nick TEXT NOT NULL,
            tao INTEGER NOT NULL
        )"""
    )
    db.commit()
    _DB = db
    return duong


def _db():
    if _DB is None:
        khoi_tao()
    return _DB


def _hop_nick(s):
    if not isinstance(s, str):
        return None
    s = s.strip()
    if not 3 <= len(s) <= 16:
        return None
    for ch in s:
        if not (ch.isalnum() or ch in "_-"):
            return None
    return s


def _hop_mk(s):
    if not isinstance(s, str):
        return None
    if not 4 <= len(s) <= 32:
        return None
    return s


def _bam(mk, salt):
    return hashlib.pbkdf2_hmac("sha256", mk.encode("utf-8"), salt, 100_000)


def _nick_tu_token(token):
    if not isinstance(token, str) or len(token) < 16:
        return None
    row = _db().execute("SELECT nick FROM phien WHERE token = ?", (token,)).fetchone()
    return row[0] if row else None


def _loi(text):
    return {"ok": False, "loi": text}


def _so(v, mac=0.0):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return mac
    if x != x or abs(x) > 1e6:
        return mac
    return x


def _don(now):
    mat_phong = []
    for ma, room in list(_PHONG.items()):
        mat = [n for n, p in room["nguoi"].items() if now - p["thay"] > HET_MANG]
        for n in mat:
            room["nguoi"].pop(n, None)
            if n in room["thu_tu"]:
                room["thu_tu"].remove(n)
        if not room["nguoi"]:
            mat_phong.append(ma)
            continue
        if room["host"] not in room["nguoi"]:
            if room["phase"] == "cho":
                room["host"] = room["thu_tu"][0]
            else:
                room["phase"] = "hu"
    for ma in mat_phong:
        _PHONG.pop(ma, None)


def _bo_nick(nick):
    for room in _PHONG.values():
        if nick in room["nguoi"]:
            room["nguoi"].pop(nick, None)
            if nick in room["thu_tu"]:
                room["thu_tu"].remove(nick)


def _tim_phong(nick):
    for room in _PHONG.values():
        if nick in room["nguoi"]:
            return room
    return None


def _ma_moi():
    bang = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    for _ in range(20):
        ma = "".join(secrets.choice(bang) for _ in range(4))
        if ma not in _PHONG:
            return ma
    return secrets.token_hex(2).upper()


def _nguoi_moi(nick):
    return {
        "nick": nick,
        "thay": time.time(),
        "song": True,
        "x": 0.0,
        "y": 0.0,
        "ts": "FM",
        "hm": 2,
        "chay": False,
        "ren": False,
        "di": False,
        "pin": 100.0,
        "tl": 100.0,
        "so": 0.0,
        "tho": 0.0,
        "vp": False,
        "san": False,
    }


def _reset_van(room, man, seed, doi_seed):
    room["van"] += 1
    room["man"] = man
    room["seed"] = seed if not doi_seed else secrets.randbelow(2_000_000_000) + 1
    room["phase"] = "choi"
    room["vat"] = {}
    room["hop"] = {}
    room["ma_chung"] = []
    room["bang"] = 0
    room["quai"] = []
    room["cc"] = False
    room["cd"] = 0.0
    room["dung"] = False
    for p in room["nguoi"].values():
        p["song"] = True
        p["vp"] = False
        p["ts"] = "FM"


def _trang(room, nick):
    thu = room["thu_tu"]
    ds = []
    for i, ten in enumerate(list(thu)):
        p = room["nguoi"].get(ten)
        if not p:
            continue
        ds.append({
            "nick": ten,
            "mau": i % 4,
            "song": bool(p["song"]),
            "la_chu": ten == room["host"],
            "x": round(p["x"], 1),
            "y": round(p["y"], 1),
            "ts": p["ts"],
            "hm": int(p["hm"]),
            "chay": bool(p["chay"]),
            "ren": bool(p["ren"]),
            "di": bool(p["di"]),
            "pin": round(p["pin"], 1),
            "tl": round(p["tl"], 1),
            "so": round(p["so"], 1),
            "tho": round(p["tho"], 2),
            "vp": bool(p["vp"]),
            "san": bool(p.get("san")),
        })
    try:
        thu_tu = thu.index(nick)
    except ValueError:
        thu_tu = 0
    return {
        "ok": True,
        "ma_phong": room["ma"],
        "phase": room["phase"],
        "van": room["van"],
        "man": room["man"],
        "seed": room["seed"],
        "la_chu": nick == room["host"],
        "thu_tu": thu_tu,
        "bang": room["bang"],
        "ma": list(room["ma_chung"]),
        "vat": dict(room["vat"]),
        "hop": dict(room["hop"]),
        "quai": room["quai"],
        "cc": bool(room["cc"]),
        "cd": round(float(room.get("cd") or 0), 2),
        "dung": bool(room["dung"]),
        "nguoi": ds,
    }


def _cap_nhat_nguoi(p, body):
    p["thay"] = time.time()
    p["x"] = _so(body.get("x"), p["x"])
    p["y"] = _so(body.get("y"), p["y"])
    ts = body.get("ts")
    if ts in ("FM", "AM"):
        p["ts"] = ts
    try:
        hm = int(body.get("hm", p["hm"]))
    except (TypeError, ValueError):
        hm = p["hm"]
    p["hm"] = hm if hm in (0, 1, 2, 3) else 2
    p["chay"] = bool(body.get("chay"))
    p["ren"] = bool(body.get("ren"))
    p["di"] = bool(body.get("di"))
    p["pin"] = _so(body.get("pin"), p["pin"])
    p["tl"] = _so(body.get("tl"), p["tl"])
    p["so"] = _so(body.get("so"), p["so"])
    p["tho"] = _so(body.get("tho"), p["tho"])
    p["vp"] = bool(body.get("vp"))


def _nhat(room, nick, body):
    if not room["nguoi"][nick]["song"] or room["phase"] != "choi":
        return
    for muc in body.get("nhat") or []:
        if not isinstance(muc, dict):
            continue
        try:
            i = int(muc.get("i"))
        except (TypeError, ValueError):
            continue
        if not 0 <= i < 500:
            continue
        loai = muc.get("loai")
        if loai not in ("battery", "cassette", "code"):
            continue
        key = str(i)
        if key in room["vat"]:
            continue
        room["vat"][key] = nick
        if loai == "cassette":
            room["bang"] = min(3, room["bang"] + 1)
        elif loai == "code":
            try:
                gia = int(muc.get("gia"))
            except (TypeError, ValueError):
                continue
            if gia not in room["ma_chung"]:
                room["ma_chung"].append(gia)
    for muc in body.get("mo") or []:
        if not isinstance(muc, dict):
            continue
        try:
            i = int(muc.get("i"))
            ma = int(muc.get("ma"))
        except (TypeError, ValueError):
            continue
        if not 0 <= i < 20:
            continue
        key = str(i)
        if key in room["hop"]:
            continue
        if ma not in room["ma_chung"]:
            continue
        room["hop"][key] = nick
        room["bang"] = min(3, room["bang"] + 1)


def _chu_cap_nhat(room, body):
    quai = body.get("quai")
    if isinstance(quai, list):
        sach = []
        for q in quai[:24]:
            if not isinstance(q, dict):
                continue
            tt = q.get("tt")
            if tt not in ("patrol", "chase", "rush"):
                tt = "patrol"
            hx = 1 if int(_so(q.get("hx"), 1)) >= 0 else -1
            sach.append({
                "x": round(_so(q.get("x")), 1),
                "y": round(_so(q.get("y")), 1),
                "tt": tt,
                "hx": hx,
            })
        room["quai"] = sach
    room["cc"] = bool(body.get("cc"))
    room["cd"] = _so(body.get("cd"), room.get("cd") or 0)
    room["dung"] = bool(body.get("dung"))
    for ten in body.get("bat") or []:
        if isinstance(ten, str) and ten in room["nguoi"]:
            room["nguoi"][ten]["song"] = False
    if room["phase"] == "choi" and room["nguoi"]:
        if all(not p["song"] for p in room["nguoi"].values()):
            room["phase"] = "thua"
    song = room["nguoi"]
    # Thắng khi người còn sống đứng trạm và đủ băng — ai cũng được báo, không chỉ chủ
    if room["phase"] == "choi" and room["bang"] >= 3:
        for ten, p in song.items():
            if p["song"] and ten == body.get("_ai") and body.get("tram"):
                room["phase"] = "thang" if room["man"] < 3 else "xong"
                break


def api(path, body):
    if not isinstance(body, dict):
        body = {}
    with _KHOA:
        _don(time.time())
        if path == "/api/dang-ky":
            return _dang_ky(body)
        if path == "/api/dang-nhap":
            return _dang_nhap(body)
        nick = _nick_tu_token(body.get("token"))
        if path == "/api/toi":
            if not nick:
                return _loi("het phien")
            return {"ok": True, "nick": nick}
        if path == "/api/dang-xuat":
            if nick:
                _db().execute("DELETE FROM phien WHERE token = ?", (body.get("token"),))
                _db().commit()
                _bo_nick(nick)
            return {"ok": True}
        if not nick:
            return _loi("het phien")
        if path == "/api/phong/tao":
            return _tao(nick)
        if path == "/api/phong/vao":
            return _vao(nick, body)
        if path == "/api/phong/roi":
            return _roi(nick)
        if path == "/api/phong/san":
            return _san(nick)
        if path == "/api/phong/san-sang":
            return _san_sang(nick)
        if path == "/api/phong/bat-dau":
            return _bat_dau(nick)
        if path == "/api/phong/tiep":
            return _tiep(nick)
        if path == "/api/dong-bo":
            return _dong_bo(nick, body)
        return _loi("khong co")


def _dang_ky(body):
    nick = _hop_nick(body.get("nick"))
    mk = _hop_mk(body.get("mat_khau"))
    if not nick:
        return _loi("Nick 3–16 ký tự, chữ hoặc số")
    if not mk:
        return _loi("Mật khẩu 4–32 ký tự")
    co = _db().execute(
        "SELECT 1 FROM nick WHERE nick = ? COLLATE NOCASE", (nick,)
    ).fetchone()
    if co:
        return _loi("Nick đã có người dùng")
    salt = secrets.token_bytes(16)
    _db().execute(
        "INSERT INTO nick (nick, salt, bam, tao) VALUES (?, ?, ?, ?)",
        (nick, salt, _bam(mk, salt), int(time.time())),
    )
    _db().commit()
    return _mo_phien(nick)


def _dang_nhap(body):
    nick = _hop_nick(body.get("nick"))
    mk = body.get("mat_khau") if isinstance(body.get("mat_khau"), str) else ""
    if not nick or not mk:
        return _loi("Nhập nick và mật khẩu")
    row = _db().execute(
        "SELECT nick, salt, bam FROM nick WHERE nick = ? COLLATE NOCASE", (nick,)
    ).fetchone()
    if not row or not secrets.compare_digest(_bam(mk, row[1]), row[2]):
        return _loi("Sai nick hoặc mật khẩu")
    return _mo_phien(row[0])


def _mo_phien(nick):
    token = secrets.token_hex(16)
    _db().execute(
        "INSERT INTO phien (token, nick, tao) VALUES (?, ?, ?)",
        (token, nick, int(time.time())),
    )
    _db().commit()
    return {"ok": True, "nick": nick, "token": token}


def _tao(nick):
    _roi(nick)
    ma = _ma_moi()
    room = {
        "ma": ma,
        "host": nick,
        "phase": "cho",
        "van": 0,
        "man": 1,
        "seed": 0,
        "nguoi": {nick: _nguoi_moi(nick)},
        "thu_tu": [nick],
        "vat": {},
        "hop": {},
        "ma_chung": [],
        "bang": 0,
        "quai": [],
        "cc": False,
        "cd": 0.0,
        "dung": False,
    }
    _PHONG[ma] = room
    return _trang(room, nick)


def _vao(nick, body):
    ma = body.get("ma")
    if not isinstance(ma, str):
        return _loi("Nhập mã phòng")
    ma = ma.strip().upper()
    room = _PHONG.get(ma)
    if not room or room["phase"] == "hu":
        return _loi("Không thấy phòng")
    if nick not in room["nguoi"] and len(room["nguoi"]) >= SO_NGUOI:
        return _loi("Phòng đầy (4 người)")
    if room["phase"] != "cho" and nick not in room["nguoi"]:
        return _loi("Phòng đã bắt đầu")
    if nick in room["nguoi"]:
        room["nguoi"][nick]["thay"] = time.time()
        return _trang(room, nick)
    _roi(nick)
    room = _PHONG.get(ma)
    if not room or room["phase"] == "hu":
        return _loi("Không thấy phòng")
    if len(room["nguoi"]) >= SO_NGUOI:
        return _loi("Phòng đầy (4 người)")
    room["nguoi"][nick] = _nguoi_moi(nick)
    room["thu_tu"].append(nick)
    return _trang(room, nick)


def _roi(nick):
    room = _tim_phong(nick)
    if not room:
        return {"ok": True, "phase": "ngoai"}
    _bo_nick(nick)
    if not room["nguoi"]:
        _PHONG.pop(room["ma"], None)
    elif room["host"] not in room["nguoi"]:
        if room["phase"] == "cho" and room["thu_tu"]:
            room["host"] = room["thu_tu"][0]
        elif room["phase"] != "cho":
            room["phase"] = "hu"
    return {"ok": True, "phase": "ngoai"}


def _san(nick):
    room = _tim_phong(nick)
    if not room:
        return _loi("chua vao phong")
    room["nguoi"][nick]["thay"] = time.time()
    return _trang(room, nick)


def _san_sang(nick):
    room = _tim_phong(nick)
    if not room:
        return _loi("chua vao phong")
    if room["phase"] != "cho":
        return _loi("Phòng đã bắt đầu")
    p = room["nguoi"][nick]
    p["san"] = not bool(p.get("san"))
    p["thay"] = time.time()
    return _trang(room, nick)


def _bat_dau(nick):
    room = _tim_phong(nick)
    if not room:
        return _loi("chua vao phong")
    if room["host"] != nick:
        return _loi("Chỉ chủ phòng bắt đầu được")
    if room["phase"] != "cho":
        return _loi("Phòng không ở sảnh")
    if len(room["nguoi"]) < 1:
        return _loi("Phòng trống")
    if not all(p.get("san") for p in room["nguoi"].values()):
        return _loi("Chưa sẵn sàng hết")
    seed = secrets.randbelow(2_000_000_000) + 1
    _reset_van(room, 1, seed, doi_seed=False)
    room["seed"] = seed
    return _trang(room, nick)


def _tiep(nick):
    room = _tim_phong(nick)
    if not room:
        return _loi("chua vao phong")
    if room["host"] != nick:
        return _loi("Chỉ chủ phòng bấm được")
    if room["phase"] == "thang" and room["man"] < 3:
        _reset_van(room, room["man"] + 1, 0, doi_seed=True)
    elif room["phase"] == "thua":
        _reset_van(room, room["man"], room["seed"], doi_seed=False)
    elif room["phase"] in ("xong", "thang"):
        room["phase"] = "cho"
        room["quai"] = []
        room["cc"] = False
        room["cd"] = 0.0
        room["dung"] = False
        for p in room["nguoi"].values():
            p["san"] = False
    else:
        return _loi("Chưa xong màn")
    return _trang(room, nick)


def _dong_bo(nick, body):
    room = _tim_phong(nick)
    if not room:
        return _loi("chua vao phong")
    p = room["nguoi"][nick]
    _cap_nhat_nguoi(p, body)
    if room["phase"] == "choi":
        body = dict(body)
        body["_ai"] = nick
        _nhat(room, nick, body)
        if p["song"] and body.get("tram") and room["bang"] >= 3:
            room["phase"] = "thang" if room["man"] < 3 else "xong"
        if nick == room["host"]:
            _chu_cap_nhat(room, body)
    return _trang(room, nick)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def end_headers(self):
        # credentialless: SharedArrayBuffer vẫn bật, CDN pygame-web không bị COEP chặn
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "credentialless")
        self.send_header("Cross-Origin-Resource-Policy", "cross-origin")
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def _json(self, code, obj):
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/health", "/healthz"):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"ok")
            return
        return super().do_GET()

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        try:
            n = int(self.headers.get("Content-Length", "0") or 0)
        except ValueError:
            n = 0
        if n < 0 or n > 65536:
            self._json(200, _loi("qua lon"))
            return
        raw = self.rfile.read(n) if n else b"{}"
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            body = {}
        if not path.startswith("/api/"):
            self._json(200, _loi("khong co"))
            return
        try:
            kq = api(path, body if isinstance(body, dict) else {})
        except Exception as exc:
            print("API lỗi %s: %s" % (path, exc), flush=True)
            kq = _loi("may chu loi")
        self._json(200, kq)

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args), flush=True)


if __name__ == "__main__":
    khoi_tao()
    if not os.path.isdir(ROOT):
        raise SystemExit("Thiếu thư mục %s — chạy pygbag --build trước." % ROOT)
    httpd = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print("Tần Số Trắng web — 0.0.0.0:%d  (root=%s)" % (PORT, ROOT), flush=True)
    httpd.serve_forever()
