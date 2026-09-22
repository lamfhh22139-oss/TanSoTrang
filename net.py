# -*- coding: utf-8 -*-
"""Kết nối máy chủ: nick + phòng. Desktop dùng HTTP; trình duyệt dùng fetch."""
import json
import os
import sys
import threading
import time

_THU_MUC = os.path.dirname(os.path.abspath(__file__))
_PHIEN = os.path.join(_THU_MUC, "phien.json")
MAY_CHU_MAC_DINH = "https://tansotrang-production.up.railway.app"

_JS = r"""
if (!window.TST) {
  window.TST = { xong: 0, kq: "" };
  window.TST.gui = function(id) {
    var url = window.TST.url;
    var body = window.TST.body;
    fetch(url, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: body
    }).then(function(r) { return r.text(); })
      .then(function(t) {
        try { window.localStorage.setItem("tanso_kq", t); } catch (e) {}
        try { window.localStorage.setItem("tanso_xong", String(id)); } catch (e) {}
        window.TST.kq = t;
        window.TST.xong = id;
      })
      .catch(function() {
        var t = "{\"ok\":false,\"loi\":\"mat mang\"}";
        try { window.localStorage.setItem("tanso_kq", t); } catch (e) {}
        try { window.localStorage.setItem("tanso_xong", String(id)); } catch (e) {}
        window.TST.kq = t;
        window.TST.xong = id;
      });
  };
  window.TST.ban = function() {
    fetch(window.TST.urlBan, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: window.TST.bodyBan
    }).catch(function() {});
  };
}
"""


def _trinh_duyet():
    return sys.platform == "emscripten"


class KetNoi:
    """Một yêu cầu chính tại một thời điểm, cộng lệnh gửi-không-chờ (rời phòng)."""

    def __init__(self):
        self.token = ""
        self.nick = ""
        self.goc = MAY_CHU_MAC_DINH
        self._id = 0
        self._seq = 1
        self._kq = None
        self._tra = None
        self._khoa = threading.Lock()
        self._luc = 0.0
        self._js = False
        self._san = False

    def chuan_bi(self):
        if self._san:
            return
        self._san = True
        if _trinh_duyet():
            self.goc = ""
            self._cai_js()
        else:
            self.goc = os.environ.get("TANSO_MAY_CHU", MAY_CHU_MAC_DINH).rstrip("/")
        self.tai_phien()

    def _cai_js(self):
        if self._js:
            return
        import platform
        platform.window.eval(_JS)
        self._js = True

    def tai_phien(self):
        raw = ""
        try:
            if _trinh_duyet():
                import platform
                raw = platform.window.localStorage.getItem("tanso_phien") or ""
            elif os.path.isfile(_PHIEN):
                with open(_PHIEN, "r", encoding="utf-8") as f:
                    raw = f.read()
        except Exception:
            raw = ""
        try:
            data = json.loads(str(raw) or "{}")
        except Exception:
            data = {}
        self.nick = str(data.get("nick") or "")
        self.token = str(data.get("token") or "")

    def dat_phien(self, nick, token):
        self.nick = nick
        self.token = token
        raw = json.dumps({"nick": nick, "token": token}, ensure_ascii=False)
        try:
            if _trinh_duyet():
                import platform
                platform.window.localStorage.setItem("tanso_phien", raw)
            else:
                with open(_PHIEN, "w", encoding="utf-8") as f:
                    f.write(raw)
        except Exception:
            pass

    def xoa_phien(self):
        self.nick = ""
        self.token = ""
        try:
            if _trinh_duyet():
                import platform
                platform.window.localStorage.removeItem("tanso_phien")
            elif os.path.isfile(_PHIEN):
                os.remove(_PHIEN)
        except Exception:
            pass

    def ranh(self):
        if self._id and time.time() - self._luc > 12.0:
            self._id = 0
        return self._id == 0

    def gui(self, path, body):
        """Gửi và chờ kết quả ở bom()/lay(). Trả False nếu đang bận."""
        if not self.ranh():
            return False
        self._seq += 1
        self._id = self._seq
        self._kq = None
        self._luc = time.time()
        self._bat(path, body, self._id, cho=True)
        return True

    def ban(self, path, body):
        """Gửi không chiếm hàng chờ (rời phòng, đăng xuất)."""
        self._bat(path, body, 0, cho=False)

    def _bat(self, path, body, so_id, cho):
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        url = self.goc + path
        if _trinh_duyet():
            import platform
            self._cai_js()
            if cho:
                platform.window.TST.url = url
                platform.window.TST.body = raw.decode("utf-8")
                platform.window.TST.gui(so_id)
            else:
                platform.window.TST.urlBan = url
                platform.window.TST.bodyBan = raw.decode("utf-8")
                platform.window.TST.ban()
            return

        def _chay():
            txt = '{"ok":false,"loi":"mat mang"}'
            try:
                import urllib.request
                req = urllib.request.Request(
                    url, data=raw, headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=8) as r:
                    txt = r.read().decode("utf-8")
            except Exception:
                pass
            if cho:
                with self._khoa:
                    self._tra = (so_id, txt)

        threading.Thread(target=_chay, daemon=True).start()

    def bom(self):
        if not self._id:
            return
        txt = None
        if _trinh_duyet():
            try:
                import platform
                xong = platform.window.localStorage.getItem("tanso_xong")
                if str(xong) != str(self._id):
                    xong2 = platform.window.TST.xong
                    if str(xong2) != str(self._id):
                        return
                    txt = str(platform.window.TST.kq)
                else:
                    txt = str(platform.window.localStorage.getItem("tanso_kq") or "")
            except Exception:
                return
        else:
            with self._khoa:
                if self._tra and self._tra[0] == self._id:
                    txt = self._tra[1]
                    self._tra = None
            if txt is None:
                return
        self._id = 0
        try:
            self._kq = json.loads(txt or "{}")
        except Exception:
            self._kq = {"ok": False, "loi": "loi du lieu"}
        if not isinstance(self._kq, dict):
            self._kq = {"ok": False, "loi": "loi du lieu"}

    def lay(self):
        k = self._kq
        self._kq = None
        return k
