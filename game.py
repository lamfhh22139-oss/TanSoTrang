# -*- coding: utf-8 -*-
"""
TẦN SỐ TRẮNG  (White Noise Frequency)
Game kinh dị 2D top-down — Pygame — chạy trên Thonny.

Cách chạy:
    1. Thonny → Tools → Manage packages… → cài "pygame"
    2. Mở file game.py này → Run (F5)
    hoặc double-click CHOI.bat

Đồ họa: toàn bộ vẽ bằng pygame.draw (không dùng PNG).
Âm thanh: tự sinh nhiễu radio / tạch tạch bằng pygame.mixer + module array
         (không dùng file mp3/wav).

Phím:
    WASD / mũi tên   Di chuyển
    SHIFT            Chạy (tốn thể lực, quái nghe xa hơn)
    Q                Nín thở / rón rén (tốn thể lực, khó bị nghe)
    SPACE            Đổi tần số FM ↔ AM (chế độ dò: băng hiện mờ)
    P                Tạm dừng / tiếp tục
    ENTER            Menu → cốt truyện → vào game
    E                Mở Hộp An Toàn (màn 3)
    R                Chơi lại (khi thua)
    ESC              Về menu / thoát menu
"""

import array
import asyncio
import math
import os
import random
import sys

import pygame


# =============================================================================
# HẰNG SỐ CẤU HÌNH
# =============================================================================
RONG, CAO = 800, 600
FPS = 60
HUD_H = 52                          # Chiều cao thanh giao diện trên cùng
TILE = 40                           # Kích thước một ô lưới (pixel)

FM, AM = "FM", "AM"                 # Hai thế giới tần số

PIN_TOI_DA = 100.0
PIN_HAO_MOI_GIAY = 6.0              # Pin tụt khi chủ động ở AM (~17s một thanh)
PIN_NHAT = 42.0                     # Lượng pin hồi khi nhặt viên pin
PIN_TOI_THIEU_AM = 4.0              # Dưới mức này không tự bật AM được

TOC_DO = 150.0                      # Tốc độ đi bình thường (px/s)
TOC_DO_CHAY = 238.0                 # SHIFT — nhanh hơn quái đuổi, nhưng ồn
TOC_DO_REN = 58.0                   # Q nín thở
TOC_DO_HET_PIN = 62.0               # Bị làm chậm khi hết pin
TOC_DO_QUAI_TUAN = 48.0
TOC_DO_QUAI_DUOI = 168.0            # Nhanh hơn đi bộ → phải chạy hoặc nhảy FM
TOC_DO_QUAI_LAO = 420.0             # Cưỡng chế AM: lao tới giết ngay

BAN_KINH_NGHE = 118.0               # Quái nghe thấy nếu đi bộ
BAN_KINH_CHAY = 178.0               # Chạy thì nghe rất xa
BAN_KINH_REN = 30.0                 # Khi đang nín thở (Q)
BAN_KINH_NHAT = 22.0                # Bán kính nhặt vật phẩm
BAN_KINH_TIN_HIEU = 280.0           # Màn 1: tầm dò băng cassette ẩn (map rộng)

THE_LUC_TOI_DA = 100.0
THE_LUC_HAO_CHAY = 34.0             # Hết sprint ~3s
THE_LUC_HAO_NIN = 15.5              # Nín được ~6s — đủ 4s cưỡng chế AM nếu đầy
THE_LUC_HOI = 26.0
SO_HAI_TOI_DA = 100.0

CUONG_CHE_MIN = 9.5                 # Màn 3: chu kỳ sự cố đài (giây)
CUONG_CHE_MAX = 12.5
CUONG_CHE_KEO_DAI = 4.4             # Thời gian bị nhốt trong AM
CUONG_CHE_AN_HAN = 0.40             # Chừa một nhịp để kịp giữ Q

# Màu sắc — FM (thế giới thực, đèn huỳnh quang vàng-xám)
MAU_NEN_FM = (18, 18, 16)
MAU_SAN_FM = (46, 48, 42)
MAU_TUONG_FM = (78, 74, 62)
MAU_BAN_HOC = (92, 64, 38)
# AM (thế giới song song, đỏ-đen)
MAU_NEN_AM = (8, 2, 4)
MAU_SAN_AM = (28, 10, 14)
MAU_TUONG_AM = (72, 18, 24)

# Máy trạng thái màn hình
MENU, COT_TRUYEN, CHOI, TAM_DUNG, JUMPSCARE, THANG, THUA, CHIEN_THANG = (
    "menu", "cot_truyen", "choi", "tam_dung", "jumpscare", "thang", "thua", "chien_thang"
)

# Cốt truyện mở đầu — từng trang, ENTER lật trang / ESC bỏ qua
TRANG_TRUYEN = (
    (
        "03:17  —  TRẠM PHÁT THANH 540",
        "Bạn là bảo vệ ca đêm cuối cùng còn nhận máy.\n"
        "FM 88.8 im tiếng đã ba tuần. Lịch trực bị xóa sạch.\n"
        "Trên bàn: tách cà phê nguội của người ca trước\n"
        "và một mẩu giấy:  «Đừng trả lời tần số trắng.»",
    ),
    (
        "BĂNG GHI ÂM",
        "Trong ngăn kéo có ba cuộn cassette không nhãn.\n"
        "Bấm play — không phải nhạc. Là hơi thở. Bước chân.\n"
        "Rồi một giọng, như từ trong loa bước ra:\n"
        "«Chúng không nhìn thấy anh. Chúng nghe.»",
    ),
    (
        "AM  540 kHz",
        "AM không phải kênh dự phòng.\n"
        "Đó là một thế giới đè lên thế giới này.\n"
        "Tường trở thành lối. Lối trở thành tường.\n"
        "The Void đi trong nhiễu — không mặt, chỉ lỗ. Mù, đói tiếng.",
    ),
    (
        "QUY TẮC SỐNG SÓT",
        "SPACE  —  nhảy FM (an toàn) / AM (chế độ dò).\n"
        "Ở AM, băng cassette hiện bóng mờ. Đứng lên là nhặt.\n"
        "Q  nín thở.  SHIFT  chạy (ồn, tốn thể lực).  P  tạm dừng.\n"
        "Nhặt đủ 3 băng, về Trạm phát thanh, rồi TẮT ĐÀI.",
    ),
)


# =============================================================================
# TIỆN ÍCH
# =============================================================================
def khoang_cach(ax, ay, bx, by):
    """Khoảng cách Euclid giữa hai điểm."""
    return math.hypot(ax - bx, ay - by)


def chuan_hoa(dx, dy):
    """Đưa vector về độ dài 1 (tránh chia cho 0)."""
    d = math.hypot(dx, dy)
    if d <= 1e-6:
        return 0.0, 0.0
    return dx / d, dy / d


def cham_4_goc(x, y, w, h, kiem_tuong):
    """True nếu bất kỳ góc nào của hình chữ nhật đụng tường."""
    diem = (
        (x, y),
        (x + w - 1, y),
        (x, y + h - 1),
        (x + w - 1, y + h - 1),
    )
    for px, py in diem:
        tx = int(px // TILE)
        ty = int(py // TILE)
        if kiem_tuong(tx, ty):
            return True
    return False


_THU_MUC = os.path.dirname(os.path.abspath(__file__))
_FONT_THUONG = os.path.join(_THU_MUC, "fonts", "NotoSans-Regular.ttf")
_FONT_DAM = os.path.join(_THU_MUC, "fonts", "NotoSans-Bold.ttf")


def tao_font(co, dam=False):
    """Font có dấu tiếng Việt (file TTF cho web, SysFont trên Thonny)."""
    for path in ((_FONT_DAM if dam else _FONT_THUONG), _FONT_THUONG):
        if path and os.path.isfile(path):
            try:
                return pygame.font.Font(path, co)
            except Exception:
                pass
    for ten in ("Tahoma", "Segoe UI", "Arial", "Verdana"):
        try:
            return pygame.font.SysFont(ten, co, bold=dam)
        except Exception:
            continue
    return pygame.font.Font(None, co)


def blit_tam(man, surface, cx, cy):
    """Vẽ surface với tâm tại (cx, cy)."""
    r = surface.get_rect(center=(int(cx), int(cy)))
    man.blit(surface, r)


def _poly(diem, ox=0, oy=0):
    """Đổi list (x,y) float → list điểm nguyên, cộng offset."""
    return [(int(x + ox), int(y + oy)) for x, y in diem]


def ve_quai_am(man, cx, cy, scale, t, trang_thai, huong_x=1, bien_the=0, nhieu=True):
    """
    Thực thể The Void: thân đen thượt như lỗ thủng không gian, đầu là
    nhật thực tần số (vành sáng, lỗ đen). Không mắt, không miệng.
    Mù, hút tiếng động. pygame.draw, không dùng ảnh.
    scale≈2.0 trong game; jumpscare dùng scale lớn.
    """
    s = float(scale)
    cx, cy = float(cx), float(cy)
    fx = 1 if huong_x >= 0 else -1
    chase = trang_thai in (Enemy.CHASE, Enemy.RUSH, "chase", "rush")
    rush = trang_thai in (Enemy.RUSH, "rush")
    chi_tiet = s >= 2.6
    nhip = t * (18.0 if rush else 11.0 if chase else 5.0)
    cx += math.sin(t * 27.0) * (1.6 if rush else 0.55) * s * 0.3 * fx
    lean = (3.6 if rush else 2.2 if chase else 0.8) * s * fx

    mau_than = (8, 4, 12) if not chase else (14, 2, 6)
    mau_vien = (32, 26, 40) if not chase else (58, 14, 22)
    nhip_lo = 0.82 + 0.18 * (0.5 + 0.5 * math.sin(t * (8.0 if chase else 2.8)))
    if chase:
        mau_vong = (int(255 * nhip_lo), int(62 * nhip_lo), int(48 * nhip_lo))
    else:
        mau_vong = (int(198 * nhip_lo), int(204 * nhip_lo), int(214 * nhip_lo))
    day_nhe = max(1, int(min(s, 2.4) * 1.35))

    # Đầu cao, thân thượt — chân vẫn quanh cy+21s để khớp hitbox
    hx = cx + lean * 0.7
    hy = cy - 30 * s
    dau_w = 7.4 * s
    dau_h = 8.6 * s

    def _i(v):
        return int(round(v))

    def ve_voi(x0, y0, goc, dai, pha, mau, day0):
        n = 5 if chi_tiet else 4
        px, py = x0, y0
        for i in range(1, n + 1):
            k = i / float(n)
            go = goc + math.sin(pha + k * 3.8) * (0.5 + 0.4 * k)
            nx = x0 + math.cos(go) * dai * k
            ny = y0 + math.sin(go) * dai * k
            pygame.draw.line(
                man, mau, (_i(px), _i(py)), (_i(nx), _i(ny)),
                max(1, int(day0 * (1.0 - k * 0.8))),
            )
            px, py = nx, ny

    def ve_siluet(ox, oy, mau, vien=None):
        bx, by = cx + ox, cy + oy
        buoc = math.sin(nhip) * (5.5 if chase else 3.2) * s
        hong_y = by + 6.0 * s
        for sign, kb, kd in ((-1, -0.3, 1.0), (1, 0.34, 0.97)):
            x_h = bx + sign * 1.7 * s
            gx = x_h + sign * 2.2 * s + buoc * kb
            gy = hong_y + 8.5 * s
            fx_ = gx + sign * 1.1 * s - buoc * kb * 0.35
            fy = by + 21.5 * s * kd
            day = max(2, day_nhe + 1)
            pygame.draw.line(man, mau, (_i(x_h), _i(hong_y)), (_i(gx), _i(gy)), day + 1)
            pygame.draw.line(man, mau, (_i(gx), _i(gy)), (_i(fx_), _i(fy)), day)
            pygame.draw.polygon(
                man, mau,
                [
                    (_i(fx_ - 1.0 * s), _i(fy)),
                    (_i(fx_ + 2.4 * s * sign), _i(fy + 0.5 * s)),
                    (_i(fx_), _i(fy - 1.4 * s)),
                ],
            )
        vai = 5.0 * s
        than = [
            (bx - vai + lean * 0.2, by - 15.5 * s),
            (bx + vai + lean * 0.2, by - 15.5 * s),
            (bx + 2.6 * s, by + 2.5 * s),
            (bx + 1.8 * s, by + 7.0 * s),
            (bx - 1.8 * s, by + 7.0 * s),
            (bx - 2.6 * s, by + 2.5 * s),
        ]
        pygame.draw.polygon(man, mau, _poly(than))
        if vien is not None:
            pygame.draw.polygon(man, vien, _poly(than), 1)
        pygame.draw.line(
            man, mau,
            (_i(bx + lean * 0.35), _i(by - 15.5 * s)),
            (_i(hx + ox), _i(hy + dau_h * 0.88)),
            max(2, day_nhe),
        )
        pygame.draw.ellipse(
            man, mau,
            (_i(hx + ox - dau_w), _i(hy + oy - dau_h), _i(dau_w * 2), _i(dau_h * 2)),
        )
        vai_y = by - 14.5 * s
        dai_tay = 16.0 * s if chase else 15.0 * s
        for sign in (-1, 1):
            swing = math.sin(nhip + (0.0 if sign < 0 else 3.1)) * (4.4 if chase else 2.8) * s
            toi = (2.4 * s if chase else 1.2 * s) * fx
            x0 = bx + 4.6 * s * sign + lean * 0.3
            y0 = vai_y
            x1 = x0 + sign * 3.2 * s + toi * 0.35
            y1 = y0 + 7.2 * s + swing * 0.28
            x2 = x1 + sign * 1.6 * s + toi * 0.7
            y2 = y0 + dai_tay * 0.72 + swing
            day = max(2, day_nhe)
            pygame.draw.line(man, mau, (_i(x0), _i(y0)), (_i(x1), _i(y1)), day + 1)
            pygame.draw.line(man, mau, (_i(x1), _i(y1)), (_i(x2), _i(y2)), day)
            pygame.draw.circle(man, mau, (_i(x2), _i(y2)), max(2, int(1.5 * s)))

    # Bóng + khói chân
    pygame.draw.ellipse(
        man, (0, 0, 0),
        (_i(cx - 11 * s), _i(cy + 17 * s), _i(22 * s), _i(7 * s)),
    )
    for i in range(3):
        pygame.draw.ellipse(
            man, (7, 4, 10),
            (
                _i(cx - 9 * s + i * 3.6 * s + math.sin(t * 2.1 + i) * 1.6 * s),
                _i(cy + 15.5 * s),
                _i((8 - i) * s),
                _i(4.2 * s),
            ),
        )
    # Tua rò từ vai — ngắn, không thành cần câu
    n_voi = 3 if (chi_tiet or bien_the == 2 or chase) else 2
    for i in range(n_voi):
        goc = -2.35 + i * 0.95
        dai = min((8 + (i % 2) * 2.5) * s, 16 + 3.2 * s)
        ve_voi(
            hx - 1.5 * s * fx, hy + 4 * s, goc, dai,
            t * 2.8 + i,
            (14, 8, 18) if not chase else (32, 4, 10),
            max(1, day_nhe),
        )

    ve_siluet(0, 0, mau_than, mau_vien)

    # Sườn nứt (chỉ khi đuổi / jumpscare)
    if chase or chi_tiet:
        for i in range(3):
            yy = cy - 11 * s + i * 3.4 * s
            mo = (2.6 - i * 0.3) * s
            pygame.draw.line(
                man, (70, 16, 24) if chase else (28, 20, 36),
                (_i(cx - mo + lean * 0.15), _i(yy)),
                (_i(cx + mo * 0.35), _i(yy + 0.5 * s)),
                1,
            )

    # Ngón tua
    vai_y = cy - 14.5 * s
    dai_tay = 16.0 * s if chase else 15.0 * s
    for sign in (-1, 1):
        swing = math.sin(nhip + (0.0 if sign < 0 else 3.1)) * (4.4 if chase else 2.8) * s
        toi = (2.4 * s if chase else 1.2 * s) * fx
        x0 = cx + 4.6 * s * sign + lean * 0.3
        y0 = vai_y
        x1 = x0 + sign * 3.2 * s + toi * 0.35
        y1 = y0 + 7.2 * s + swing * 0.28
        x2 = x1 + sign * 1.6 * s + toi * 0.7
        y2 = y0 + dai_tay * 0.72 + swing
        co_so = math.atan2(y2 - y1, x2 - x1)
        for k in range(4):
            ve_voi(
                x2, y2, co_so + (k - 1.5) * 0.38,
                min((5.0 if chase else 3.8) * s, 10 + 2.2 * s),
                t * 3.2 + sign + k,
                mau_vien if not chase else (110, 22, 30),
                max(1, int(min(s, 2.2))),
            )

    # ----- Lỗ The Void: nhật thực trên đầu đen, không mặt nạ trắng -----
    # Vành thịt xám tối quanh vết thương (không phải mặt cười)
    pygame.draw.ellipse(
        man, (54, 50, 58) if not chase else (62, 28, 32),
        (
            _i(hx - dau_w * 0.72),
            _i(hy - dau_h * 0.72),
            _i(dau_w * 1.44),
            _i(dau_h * 1.44),
        ),
    )

    lo_rx = (3.8 if not chase else 4.6 if not rush else 5.2) * s
    lo_ry = (4.2 if not chase else 6.4 if not rush else 7.8) * s
    if bien_the == 1:
        lo_ry *= 1.12
    vong = max(1, int(min(s, 2.2) * 0.9))
    if nhieu:
        pygame.draw.ellipse(
            man, (110, 16, 22),
            (_i(hx - lo_rx - 0.7 * s), _i(hy - lo_ry),
             _i(lo_rx * 2), _i(lo_ry * 2)),
            vong,
        )
        pygame.draw.ellipse(
            man, (20, 40, 90),
            (_i(hx - lo_rx + 0.7 * s), _i(hy - lo_ry),
             _i(lo_rx * 2), _i(lo_ry * 2)),
            vong,
        )
    pygame.draw.ellipse(
        man, (0, 0, 0),
        (_i(hx - lo_rx), _i(hy - lo_ry), _i(lo_rx * 2), _i(lo_ry * 2)),
    )
    pygame.draw.ellipse(
        man, mau_vong,
        (_i(hx - lo_rx), _i(hy - lo_ry), _i(lo_rx * 2), _i(lo_ry * 2)),
        max(1, vong + 1),
    )
    if chase:
        pygame.draw.ellipse(
            man, (80, 6, 10),
            (
                _i(hx - lo_rx - 1.2 * s), _i(hy - lo_ry - 1.2 * s),
                _i((lo_rx + 1.2 * s) * 2), _i((lo_ry + 1.2 * s) * 2),
            ),
            max(1, vong),
        )
    for k in (0.58, 0.28):
        pygame.draw.ellipse(
            man, (30, 10, 14) if chase else (22, 22, 28),
            (
                _i(hx - lo_rx * k), _i(hy - lo_ry * k),
                _i(lo_rx * k * 2), _i(lo_ry * k * 2),
            ),
            1,
        )
    # Điểm sáng xa trong lỗ
    pygame.draw.circle(
        man, mau_vong,
        (_i(hx + 0.4 * s * fx), _i(hy + 0.2 * s)),
        max(1, int(0.55 * s)),
    )

    n_soc = 4 if s < 2.2 else (6 if chi_tiet else 5)
    for i in range(n_soc):
        yy = hy - lo_ry * 0.72 + i * (lo_ry * 1.4 / n_soc) + math.sin(t * 11 + i) * 0.5 * s
        ny = (yy - hy) / max(1e-3, lo_ry)
        if abs(ny) >= 0.88:
            continue
        half = lo_rx * math.sqrt(max(0.0, 1.0 - ny * ny)) * 0.82
        col = (36, 6, 8) if chase else (30, 30, 36)
        if int(t * 13 + i) % 4 == 0:
            col = (140, 140, 148) if not chase else (160, 32, 36)
        pygame.draw.line(man, col, (_i(hx - half), _i(yy)), (_i(hx + half), _i(yy)), 1)

    if bien_the == 2:
        for ox, oy, r in ((-4.4 * s, -5.0 * s, 1.4 * s), (4.6 * s, -3.6 * s, 1.2 * s)):
            pygame.draw.circle(man, (0, 0, 0), (_i(hx + ox), _i(hy + oy)), max(2, int(r)))
            pygame.draw.circle(man, mau_vong, (_i(hx + ox), _i(hy + oy)), max(2, int(r)), 1)

    if bien_the == 1:
        pygame.draw.line(
            man, (10, 4, 8),
            (_i(hx + 0.3 * s), _i(hy + lo_ry)),
            (_i(hx + 0.8 * s * fx), _i(hy + dau_h * 0.88)),
            max(1, vong),
        )

    if nhieu:
        rng = random.Random(int(t * 9) ^ 0x3D)
        for _ in range(4 if chi_tiet else 2):
            ang = rng.random() * 6.28
            rr = (dau_w + 1.4 * s) * (0.8 + 0.35 * rng.random())
            pygame.draw.rect(
                man, (180, 180, 186) if rng.random() > 0.45 else (48, 8, 12),
                (_i(hx + math.cos(ang) * rr), _i(hy + math.sin(ang) * rr * 0.8),
                 max(1, int(0.7 * s)), max(1, int(0.7 * s))),
            )


# =============================================================================
# ÂM THANH TỰ SINH (module array + pygame.mixer — không file ngoài)
# =============================================================================
SAMPLE_RATE = 22050


def _sound_tu_mang(mang):
    """
    Đóng gói array.array('h') (số nguyên 16-bit) thành pygame.Sound.
    Mixer được khởi tạo mono, signed 16-bit, 22050 Hz.
    """
    try:
        return pygame.mixer.Sound(buffer=mang.tobytes())
    except Exception:
        try:
            return pygame.mixer.Sound(buffer=bytes(mang))
        except Exception:
            return None


def tao_nhieu_trang(thoi_ms, am_luong=0.18, hat=None):
    """Nhiễu trắng (white noise) — tiếng tĩnh của sóng radio AM."""
    n = max(1, int(SAMPLE_RATE * thoi_ms / 1000.0))
    amp = int(32767 * max(0.0, min(1.0, am_luong)))
    rng = hat if hat is not None else random
    buf = array.array("h")
    for _ in range(n):
        buf.append(rng.randint(-amp, amp))
    return _sound_tu_mang(buf)


def tao_tieng_tach(thoi_ms=38, am_luong=0.45):
    """
    Tiếng 'tạch' ngắn: nhiễu có envelope tụt nhanh.
    Dùng cho tín hiệu dò băng cassette ở màn 1.
    """
    n = max(1, int(SAMPLE_RATE * thoi_ms / 1000.0))
    amp = int(32767 * am_luong)
    buf = array.array("h")
    for i in range(n):
        fade = 1.0 - (i / float(n))
        fade *= fade
        buf.append(int(random.randint(-amp, amp) * fade))
    return _sound_tu_mang(buf)


def tao_beep(tan_so, thoi_ms, am_luong=0.28, quet=0.0):
    """
    Beep hình sine, có fade in/out để khỏi nổ loa.
    quet > 0: tần số tăng (FM), quet < 0: tần số giảm (AM).
    """
    n = max(1, int(SAMPLE_RATE * thoi_ms / 1000.0))
    amp = int(32767 * am_luong)
    buf = array.array("h")
    for i in range(n):
        t = i / float(SAMPLE_RATE)
        k = i / float(n)
        f = tan_so * (1.0 + quet * k)
        # Envelope: 8% đầu lên, 25% cuối xuống
        if k < 0.08:
            env = k / 0.08
        elif k > 0.75:
            env = (1.0 - k) / 0.25
        else:
            env = 1.0
        v = int(amp * env * math.sin(2.0 * math.pi * f * t))
        if v > 32767:
            v = 32767
        elif v < -32767:
            v = -32767
        buf.append(v)
    return _sound_tu_mang(buf)


def tao_hu(thoi_ms=700, am_luong=0.32):
    """Tiếng hú trầm khi game over / jumpscare."""
    n = max(1, int(SAMPLE_RATE * thoi_ms / 1000.0))
    amp = int(32767 * am_luong)
    buf = array.array("h")
    for i in range(n):
        t = i / float(SAMPLE_RATE)
        k = i / float(n)
        f = 180.0 - 90.0 * k
        env = (1.0 - k) * (0.6 + 0.4 * random.random())
        sine = math.sin(2.0 * math.pi * f * t)
        noise = (random.random() * 2.0 - 1.0) * 0.35
        v = int(amp * env * (sine * 0.7 + noise))
        if v > 32767:
            v = 32767
        elif v < -32767:
            v = -32767
        buf.append(v)
    return _sound_tu_mang(buf)


class Audio:
    """Quản lý toàn bộ tiếng tự sinh: tĩnh AM, tạch tạch, beep đổi sóng."""

    def __init__(self):
        self.ok = False
        self.kenh_tinh = None
        self.kenh_sfx = None
        self.kenh_canh = None
        self.nhieu = None
        self.tach = []
        self.beep_am = None
        self.beep_fm = None
        self.nhat = None
        self.bao_dong = None
        self.hu = None
        self.mo_hop = None
        self._am_dang_am = False
        try:
            pygame.mixer.set_num_channels(16)
            self.kenh_tinh = pygame.mixer.Channel(0)
            self.kenh_sfx = pygame.mixer.Channel(1)
            self.kenh_canh = pygame.mixer.Channel(2)
            self.nhieu = tao_nhieu_trang(900, 0.16)
            self.tach = [tao_tieng_tach() for _ in range(4)]
            self.beep_am = tao_beep(920, 160, 0.26, quet=-0.55)
            self.beep_fm = tao_beep(420, 160, 0.26, quet=0.85)
            self.nhat = tao_beep(740, 90, 0.30)
            self.bao_dong = tao_beep(880, 220, 0.34)
            self.hu = tao_hu()
            self.mo_hop = tao_beep(520, 280, 0.28, quet=0.4)
            self.ok = self.nhieu is not None
        except Exception:
            self.ok = False

    def cap_nhat_the_gioi(self, tan_so):
        """Bật vòng lặp nhiễu tĩnh khi vào AM, tắt khi về FM."""
        if not self.ok or self.kenh_tinh is None:
            return
        if tan_so == AM:
            if not self._am_dang_am:
                if self.nhieu is not None:
                    self.kenh_tinh.play(self.nhieu, loops=-1)
                    self.kenh_tinh.set_volume(0.42)
                self._am_dang_am = True
        else:
            if self._am_dang_am:
                self.kenh_tinh.stop()
                self._am_dang_am = False

    def dat_am_luong_tinh(self, v):
        if self.ok and self.kenh_tinh is not None:
            self.kenh_tinh.set_volume(max(0.0, min(1.0, v)))

    def phat_tach(self):
        if self.ok and self.tach:
            s = random.choice(self.tach)
            if s is not None:
                s.set_volume(0.55 + random.random() * 0.3)
                s.play()

    def phat_doi_song(self, tan_so_moi):
        if not self.ok:
            return
        s = self.beep_am if tan_so_moi == AM else self.beep_fm
        if s is not None:
            s.play()

    def phat_nhat(self):
        if self.ok and self.nhat is not None:
            self.nhat.play()

    def phat_bao_dong(self):
        if self.ok and self.bao_dong is not None and self.kenh_canh is not None:
            if not self.kenh_canh.get_busy():
                self.kenh_canh.play(self.bao_dong)

    def dung_bao_dong(self):
        if self.kenh_canh is not None:
            self.kenh_canh.stop()

    def phat_hu(self):
        if self.ok and self.hu is not None:
            self.hu.play()

    def phat_mo_hop(self):
        if self.ok and self.mo_hop is not None:
            self.mo_hop.play()

    def tam_dung(self):
        try:
            pygame.mixer.pause()
        except Exception:
            pass

    def tiep_tuc(self):
        try:
            pygame.mixer.unpause()
        except Exception:
            pass

    def im_het(self):
        try:
            pygame.mixer.unpause()
        except Exception:
            pass
        try:
            pygame.mixer.stop()
        except Exception:
            pass
        self._am_dang_am = False


# =============================================================================
# CAMERA — bám theo người chơi, căn giữa nếu bản đồ nhỏ hơn màn hình
# =============================================================================
class Camera:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0

    def cap_nhat(self, tx, ty, map_w, map_h, rung=0.0):
        vw, vh = RONG, CAO - HUD_H
        self.x = tx - vw * 0.5
        self.y = ty - vh * 0.5
        if map_w <= vw:
            self.x = (map_w - vw) * 0.5
        else:
            self.x = max(0.0, min(self.x, map_w - vw))
        if map_h <= vh:
            self.y = (map_h - vh) * 0.5
        else:
            self.y = max(0.0, min(self.y, map_h - vh))
        if rung > 0.05:
            self.x += random.uniform(-rung, rung)
            self.y += random.uniform(-rung, rung)

    def apply(self, x, y):
        """Đổi toạ độ thế giới → toạ độ màn hình (đã trừ HUD)."""
        return int(x - self.x), int(y - self.y + HUD_H)

    def apply_rect(self, r):
        return pygame.Rect(
            int(r.x - self.x),
            int(r.y - self.y + HUD_H),
            r.w,
            r.h,
        )


# =============================================================================
# PLAYER — nhân vật điều khiển
# =============================================================================
class Player:
    """
    Bảo vệ ca đêm: WASD/mũi tên đi, SHIFT chạy, Q nín thở.
    Thể lực giới hạn; sợ hãi tăng khi The Void ở gần.
    """

    def __init__(self, x, y):
        self.w = 16
        self.h = 16
        self.dat_lai(x, y)

    def dat_lai(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.huong = (0, 1)          # Vector hướng (logic)
        self.huong_mat = 2           # 0 lên, 1 phải, 2 xuống, 3 trái — để vẽ
        self.ron_ren = False         # Nín thở (Q) — quái khó nghe
        self.nin_tho = False
        self.dang_chay = False
        self.dang_di = False
        self.bam_di_chuyen = False
        self.pin = PIN_TOI_DA
        self.the_luc = THE_LUC_TOI_DA
        self.so_hai = 0.0
        self.kiet_suc = False        # Hết pin → bị làm chậm cho đến khi nhặt pin
        self.met = False             # Thể lực cạn — không chạy/nín được
        self.tho_gat_t = 0.0         # Hết hơi: thở gấp, quái nghe thấy
        self.bang = 0
        self.ma_so = []
        self.nhap_nhay = 0.0
        self.buoc_t = 0.0
        self.tho = 0.0
        self.nhay_mat = 2.4
        self.rung_t = 0.0            # Timer rung người khi sợ

    @property
    def cx(self):
        return self.x + self.w * 0.5

    @property
    def cy(self):
        return self.y + self.h * 0.5

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def cap_nhat(self, dt, keys, level, tan_so):
        """Di chuyển + thể lực + va chạm tường theo tần số hiện tại."""
        bam_q = bool(keys[pygame.K_q])
        bam_chay = bool(keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])
        dx = (1 if keys[pygame.K_d] or keys[pygame.K_RIGHT] else 0) - (
            1 if keys[pygame.K_a] or keys[pygame.K_LEFT] else 0
        )
        dy = (1 if keys[pygame.K_s] or keys[pygame.K_DOWN] else 0) - (
            1 if keys[pygame.K_w] or keys[pygame.K_UP] else 0
        )
        self.bam_di_chuyen = dx != 0 or dy != 0

        if dx or dy:
            self.huong = (dx, dy)
            if abs(dx) >= abs(dy):
                self.huong_mat = 1 if dx > 0 else 3
            else:
                self.huong_mat = 2 if dy > 0 else 0

        if self.tho_gat_t > 0:
            self.tho_gat_t = max(0.0, self.tho_gat_t - dt)

        # Q ưu tiên hơn SHIFT — không vừa chạy vừa nín
        muon_nin = bam_q and self.the_luc > 1.5 and self.tho_gat_t <= 0
        muon_chay = (
            bam_chay and self.bam_di_chuyen and not muon_nin
            and self.the_luc > 5.0 and not self.kiet_suc
        )

        if muon_nin:
            self.nin_tho = True
            self.dang_chay = False
            self.the_luc -= THE_LUC_HAO_NIN * dt
        elif muon_chay:
            self.nin_tho = False
            self.dang_chay = True
            self.the_luc -= THE_LUC_HAO_CHAY * dt
        else:
            self.dang_chay = False
            self.nin_tho = False
            hoi = THE_LUC_HOI
            if self.bam_di_chuyen:
                hoi *= 0.42
            hoi *= 1.0 - 0.55 * (self.so_hai / SO_HAI_TOI_DA)
            self.the_luc += hoi * dt

        if self.the_luc <= 0.0:
            self.the_luc = 0.0
            if muon_nin or muon_chay:
                self.tho_gat_t = 0.65
            self.nin_tho = False
            self.dang_chay = False
            self.met = True
        else:
            self.the_luc = min(THE_LUC_TOI_DA, self.the_luc)
            if self.the_luc > 18.0:
                self.met = False

        # ron_ren: chỉ khi nín thở thành công (không phải lúc thở gấp)
        self.ron_ren = self.nin_tho and self.tho_gat_t <= 0.0

        if self.kiet_suc:
            spd = TOC_DO_HET_PIN
        elif self.ron_ren:
            spd = TOC_DO_REN
        elif self.dang_chay:
            spd = TOC_DO_CHAY
        else:
            spd = TOC_DO
        if self.met or self.the_luc < 16.0:
            spd *= 0.78
        if self.so_hai > 80.0:
            spd *= 0.88

        if dx and dy:
            inv = 1.0 / math.sqrt(2.0)
            dx *= inv
            dy *= inv

        self.vx = dx * spd
        self.vy = dy * spd

        def tuong(tx, ty):
            return level.la_tuong(tx, ty, tan_so)

        nx = self.x + self.vx * dt
        if not cham_4_goc(nx, self.y, self.w, self.h, tuong):
            self.x = nx
        ny = self.y + self.vy * dt
        if not cham_4_goc(self.x, ny, self.w, self.h, tuong):
            self.y = ny

        mw, mh = level.kich_thuoc_pixel()
        self.x = max(2.0, min(self.x, mw - self.w - 2.0))
        self.y = max(2.0, min(self.y, mh - self.h - 2.0))

        self.dang_di = abs(self.vx) + abs(self.vy) > 1.0 and self.bam_di_chuyen

        if self.dang_di:
            if self.ron_ren or self.kiet_suc or self.met:
                tan_buoc = 2.1
            elif self.dang_chay:
                tan_buoc = 7.2
            else:
                tan_buoc = 4.4
            self.buoc_t += dt * tan_buoc
        else:
            self.buoc_t = 0.0
        nhip_tho = 2.6 + 3.5 * (self.so_hai / SO_HAI_TOI_DA)
        if self.met or self.tho_gat_t > 0:
            nhip_tho += 3.0
        if self.nin_tho:
            nhip_tho = 0.4
        self.tho += dt * nhip_tho
        self.rung_t += dt
        self.nhay_mat -= dt * (1.0 + 1.4 * (self.so_hai / SO_HAI_TOI_DA))
        if self.nhay_mat < 0.0:
            self.nhay_mat = random.uniform(0.7, 2.8) if self.so_hai > 50 else random.uniform(2.2, 4.8)

        if self.nhap_nhay > 0:
            self.nhap_nhay -= dt

    def cap_nhat_so_hai(self, dt, tan_so, bi_san, d_min, cuong_che):
        """Sợ hãi: tăng ở AM / khi bị săn / gần The Void; hạ ở FM."""
        if tan_so == AM:
            self.so_hai += 9.0 * dt
            if d_min < 170.0:
                self.so_hai += (1.0 - d_min / 170.0) * 32.0 * dt
            if bi_san:
                self.so_hai += 24.0 * dt
            if cuong_che:
                self.so_hai += 16.0 * dt
        else:
            self.so_hai -= 15.0 * dt
        if self.kiet_suc:
            self.so_hai += 5.0 * dt
        if self.the_luc < 12.0:
            self.so_hai += 7.0 * dt
        if self.tho_gat_t > 0:
            self.so_hai += 10.0 * dt
        self.so_hai = max(0.0, min(SO_HAI_TOI_DA, self.so_hai))

    def hao_pin(self, dt, tan_so):
        """Pin chỉ tụt khi đang ở tần số AM."""
        if tan_so != AM:
            return False
        self.pin -= PIN_HAO_MOI_GIAY * dt
        if self.pin <= 0.0:
            self.pin = 0.0
            self.kiet_suc = True
            return True             # Báo Game: phải đẩy về FM
        return False

    def nap_pin(self, luong):
        self.pin = min(PIN_TOI_DA, self.pin + luong)
        if self.pin > 8.0:
            self.kiet_suc = False

    def ve(self, man, camera, tan_so):
        """Bảo vệ 4 hướng: mũ, huy hiệu, đai. Sợ / mệt hiện trên mặt và dáng."""
        sx, sy = camera.apply(self.x, self.y)
        so = self.so_hai / SO_HAI_TOI_DA
        met = self.met or self.the_luc < 22.0 or self.kiet_suc
        so_man = so > 0.45

        if tan_so == AM:
            ao, da = (78, 84, 98), (228, 226, 230)
        else:
            ao, da = (32, 44, 68), (222, 198, 168)
        if met:
            ao = (ao[0] + 18, ao[1] + 8, max(20, ao[2] - 10))
        if so > 0.35:
            k = min(1.0, (so - 0.35) / 0.65)
            da = (
                int(da[0] * (1 - k) + 210 * k),
                int(da[1] * (1 - k) + 214 * k),
                int(da[2] * (1 - k) + 222 * k),
            )
        quan, giay = (18, 22, 32), (12, 12, 14)
        mu, gach = (16, 22, 36), (212, 176, 58)
        radio = (36, 36, 40)
        chop = self.nhay_mat < 0.12

        if self.dang_di:
            amp = 5.2 if self.dang_chay else (2.2 if self.ron_ren else 3.6)
            swing = math.sin(self.buoc_t * 2.0 * math.pi)
            bob = abs(swing) * (2.4 if self.dang_chay else (0.7 if self.ron_ren else 1.6))
        else:
            swing = 0.0
            bob = math.sin(self.tho) * (1.15 if so > 0.5 or met else 0.55)
        sy = int(sy - bob)
        if self.ron_ren or met:
            sy += 3 if self.ron_ren else 2
        if so > 0.4:
            sx += int(math.sin(self.rung_t * (18 + 22 * so)) * (1 + 2 * so))

        pygame.draw.ellipse(man, (0, 0, 0), (sx - 1, sy + 15, 18, 6))
        cl = int(round(swing * (5 if self.dang_chay else 4)))
        cr = int(round(-swing * (5 if self.dang_chay else 4)))
        tl = int(round(-swing * 3))
        tr = int(round(swing * 3))
        mat = self.huong_mat

        def chan(x, y, len_them):
            pygame.draw.rect(man, quan, (x, y, 5, 6 + max(0, len_them)))
            pygame.draw.rect(man, giay, (x, y + 5 + max(0, len_them), 5, 3))

        def tay(x, y):
            pygame.draw.rect(man, da, (x, y, 3, 8))

        def ao_nguc(x, y, w, h):
            pygame.draw.rect(man, ao, (x, y, w, h))
            pygame.draw.rect(man, (14, 16, 22), (x, y, w, h), 1)
            pygame.draw.rect(man, gach, (x, y + h - 2, w, 2))  # đai

        def mu_bao(x, y, w):
            pygame.draw.rect(man, mu, (x - 1, y - 1, w + 2, 4))
            pygame.draw.rect(man, gach, (x - 1, y + 2, w + 2, 1))

        def mat_bao(fx, fy, doi=False):
            """Mặt: sợ = mắt trắng to; mệt = mí sụp; nín thở = má phồng."""
            if chop:
                pygame.draw.line(man, (20, 20, 30), (fx, fy + 1), (fx + 2, fy + 1), 1)
                if doi:
                    pygame.draw.line(man, (20, 20, 30), (fx + 4, fy + 1), (fx + 6, fy + 1), 1)
                return
            if met and not so_man:
                pygame.draw.line(man, (40, 32, 36), (fx, fy + 1), (fx + 2, fy + 1), 1)
                if doi:
                    pygame.draw.line(man, (40, 32, 36), (fx + 4, fy + 1), (fx + 6, fy + 1), 1)
            elif so_man:
                pygame.draw.rect(man, (240, 240, 246), (fx - 1, fy, 3, 3))
                pygame.draw.rect(man, (18, 10, 14), (fx, fy + 1, 2, 2))
                if doi:
                    pygame.draw.rect(man, (240, 240, 246), (fx + 3, fy, 3, 3))
                    pygame.draw.rect(man, (18, 10, 14), (fx + 4, fy + 1, 2, 2))
            else:
                pygame.draw.rect(man, (20, 20, 30), (fx, fy, 2, 2))
                if doi:
                    pygame.draw.rect(man, (20, 20, 30), (fx + 4, fy, 2, 2))
            if so_man:
                pygame.draw.line(man, (90, 40, 48), (fx + 1, fy + 4), (fx + 5, fy + 4), 1)
            if self.nin_tho:
                pygame.draw.circle(man, da, (fx + 3, fy + 4), 2)

        def mo_hoi(fx, fy):
            if so < 0.55 and not met:
                return
            pygame.draw.rect(man, (210, 220, 230), (fx, fy, 1, 2))
            pygame.draw.rect(man, (210, 220, 230), (fx + 3, fy - 1, 1, 2))

        if mat == 2:
            chan(sx + 2, sy + 12, cl)
            chan(sx + 9, sy + 12, cr)
            ao_nguc(sx + 3, sy + 5, 10, 10)
            pygame.draw.rect(man, gach, (sx + 5, sy + 8, 3, 2))  # huy hiệu
            tay(sx + 1, sy + 6 + tl)
            tay(sx + 12, sy + 6 + tr)
            pygame.draw.rect(man, radio, (sx + 13, sy + 9, 4, 5))
            pygame.draw.line(man, (200, 200, 190), (sx + 16, sy + 9), (sx + 16, sy + 4), 1)
            pygame.draw.rect(man, da, (sx + 4, sy + 0, 8, 7))
            mu_bao(sx + 4, sy + 0, 8)
            mat_bao(sx + 5, sy + 3, doi=True)
            mo_hoi(sx + 6, sy + 1)
        elif mat == 0:
            chan(sx + 2, sy + 12, cl)
            chan(sx + 9, sy + 12, cr)
            pygame.draw.rect(man, radio, (sx + 5, sy + 8, 6, 6))
            pygame.draw.line(man, (200, 200, 190), (sx + 8, sy + 8), (sx + 8, sy + 3), 1)
            pygame.draw.circle(man, (200, 70, 70) if tan_so == AM else (80, 180, 255), (sx + 8, sy + 3), 2)
            ao_nguc(sx + 3, sy + 5, 10, 10)
            tay(sx + 1, sy + 6 + tr)
            tay(sx + 12, sy + 6 + tl)
            pygame.draw.rect(man, mu, (sx + 3, sy - 1, 10, 8))
            pygame.draw.rect(man, gach, (sx + 3, sy + 2, 10, 1))
            pygame.draw.rect(man, da, (sx + 5, sy + 5, 6, 2))
        elif mat == 1:
            chan(sx + 4 + cr // 2, sy + 12, cr)
            chan(sx + 7 + cl // 2, sy + 12, cl)
            ao_nguc(sx + 4, sy + 5, 9, 10)
            pygame.draw.rect(man, gach, (sx + 9, sy + 8, 2, 2))
            tay(sx + 11, sy + 6 + tr)
            pygame.draw.rect(man, (210, 190, 70), (sx + 13, sy + 10 + tr, 3, 2))  # đèn pin
            pygame.draw.rect(man, radio, (sx + 2, sy + 9, 3, 5))
            pygame.draw.line(man, (200, 200, 190), (sx + 3, sy + 9), (sx + 3, sy + 5), 1)
            pygame.draw.rect(man, da, (sx + 6, sy + 0, 7, 7))
            mu_bao(sx + 6, sy + 0, 7)
            pygame.draw.rect(man, mu, (sx + 12, sy + 2, 2, 2))  # vành mũ
            mat_bao(sx + 10, sy + 3, doi=False)
            mo_hoi(sx + 8, sy + 1)
        else:
            chan(sx + 4 + cl // 2, sy + 12, cl)
            chan(sx + 7 + cr // 2, sy + 12, cr)
            ao_nguc(sx + 3, sy + 5, 9, 10)
            pygame.draw.rect(man, gach, (sx + 4, sy + 8, 2, 2))
            tay(sx + 2, sy + 6 + tl)
            pygame.draw.rect(man, (210, 190, 70), (sx, sy + 10 + tl, 3, 2))
            pygame.draw.rect(man, radio, (sx + 11, sy + 9, 3, 5))
            pygame.draw.line(man, (200, 200, 190), (sx + 13, sy + 9), (sx + 13, sy + 5), 1)
            pygame.draw.rect(man, da, (sx + 3, sy + 0, 7, 7))
            mu_bao(sx + 3, sy + 0, 7)
            pygame.draw.rect(man, mu, (sx + 2, sy + 2, 2, 2))
            mat_bao(sx + 4, sy + 3, doi=False)
            mo_hoi(sx + 6, sy + 1)

        if self.ron_ren:
            pygame.draw.circle(
                man, (160, 200, 230),
                (sx + self.w // 2, sy + self.h // 2 + 2), 12, 1
            )
        elif self.tho_gat_t > 0:
            pygame.draw.circle(
                man, (255, 90, 70),
                (sx + self.w // 2, sy + self.h // 2 + 2), 13, 1
            )


# =============================================================================
# ENEMY — quái vật mù, săn bằng TIẾNG ĐỘNG (chỉ tồn tại ở AM)
# =============================================================================
class Enemy:
    """
    Quái mù ở thế giới AM:
      - Đi tuần nếu không nghe thấy gì.
      - Nếu Player DI CHUYỂN mà KHÔNG nín thở (Q) trong bán kính nghe → đuổi.
      - Chạy (SHIFT) nghe rất xa. Nín thở thu nhỏ bán kính.
      - Hết hơi (thở gấp) thì bị nghe dù đứng yên.
      - Khi Cưỡng chế AM mà Player nhúc nhích / không giữ Q → lao diệt.
    """

    PATROL, CHASE, RUSH = "patrol", "chase", "rush"

    def __init__(self, x, y, he_so=1.0):
        self.w = 18
        self.h = 22
        self.x = float(x)
        self.y = float(y)
        self.trang_thai = Enemy.PATROL
        self.tieu_x = x
        self.tieu_y = y
        self.doi_chon = 0.0
        self.jitter = random.random() * 20.0   # lệch nhịp để không giật đồng loạt
        self.toc_do = TOC_DO_QUAI_TUAN
        self.he_so = he_so
        self.huong_x = 1
        self.bien_the = random.randint(0, 2)   # 0 lỗ giữa / 1 nứt mặt / 2 rỗ lỗ

    @property
    def cx(self):
        return self.x + self.w * 0.5

    @property
    def cy(self):
        return self.y + self.h * 0.5

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def _chon_diem_tuan(self, level):
        """Chọn ô AM đi được ngẫu nhiên trong vùng lân cận."""
        tx0 = int(self.cx // TILE)
        ty0 = int(self.cy // TILE)
        for _ in range(18):
            tx = tx0 + random.randint(-5, 5)
            ty = ty0 + random.randint(-5, 5)
            if level.o_di_duoc(tx, ty, AM):
                self.tieu_x = tx * TILE + TILE * 0.5 - self.w * 0.5
                self.tieu_y = ty * TILE + TILE * 0.5 - self.h * 0.5
                return
        self.tieu_x = self.x
        self.tieu_y = self.y

    def cap_nhat(self, dt, player, level, tan_so, cuong_che, vi_pham):
        # Quái chỉ sống ở AM — đứng im (ẩn) khi Player đang FM
        if tan_so != AM:
            if self.trang_thai != Enemy.RUSH:
                self.trang_thai = Enemy.PATROL
            return

        d = khoang_cach(self.cx, self.cy, player.cx, player.cy)

        # Cưỡng chế AM: vi phạm → mọi quái lao xuyên tường
        if cuong_che and vi_pham:
            self.trang_thai = Enemy.RUSH

        if self.trang_thai != Enemy.RUSH:
            r_nghe = BAN_KINH_CHAY if player.dang_chay else BAN_KINH_NGHE
            if player.tho_gat_t > 0.0 and d <= BAN_KINH_NGHE:
                self.trang_thai = Enemy.CHASE
            elif player.bam_di_chuyen and not player.ron_ren and d <= r_nghe:
                self.trang_thai = Enemy.CHASE
            elif player.bam_di_chuyen and player.ron_ren and d <= BAN_KINH_REN:
                self.trang_thai = Enemy.CHASE
            elif self.trang_thai == Enemy.CHASE and d > r_nghe * 1.55:
                self.trang_thai = Enemy.PATROL
                self.doi_chon = 0.0

        xuyen_tuong = False
        if self.trang_thai == Enemy.RUSH:
            self.toc_do = TOC_DO_QUAI_LAO * self.he_so
            self.tieu_x = player.x
            self.tieu_y = player.y
            xuyen_tuong = True
        elif self.trang_thai == Enemy.CHASE:
            self.toc_do = TOC_DO_QUAI_DUOI * self.he_so
            self.tieu_x = player.x
            self.tieu_y = player.y
        else:
            self.toc_do = TOC_DO_QUAI_TUAN * self.he_so
            self.doi_chon -= dt
            if self.doi_chon <= 0.0 or khoang_cach(self.cx, self.cy, self.tieu_x + self.w * 0.5, self.tieu_y + self.h * 0.5) < 8:
                self._chon_diem_tuan(level)
                self.doi_chon = random.uniform(1.2, 2.8)

        dx, dy = chuan_hoa(self.tieu_x - self.x, self.tieu_y - self.y)
        if abs(dx) > 0.15:
            self.huong_x = 1 if dx > 0 else -1
        buoc_x = dx * self.toc_do * dt
        buoc_y = dy * self.toc_do * dt

        def tuong(tx, ty):
            return level.la_tuong(tx, ty, AM)

        if xuyen_tuong:
            self.x += buoc_x
            self.y += buoc_y
        else:
            nx = self.x + buoc_x
            if not cham_4_goc(nx, self.y, self.w, self.h, tuong):
                self.x = nx
            elif self.trang_thai == Enemy.PATROL:
                self.doi_chon = 0.0
            ny = self.y + buoc_y
            if not cham_4_goc(self.x, ny, self.w, self.h, tuong):
                self.y = ny
            elif self.trang_thai == Enemy.PATROL:
                self.doi_chon = 0.0

        self.jitter += dt * 18.0

    def bat_duoc(self, player):
        r = self.rect().inflate(-4, -4)
        return r.colliderect(player.rect().inflate(-2, -2))

    def ve(self, man, camera, tan_so):
        if tan_so != AM:
            return
        # Vẽ lớn hơn hitbox: bóng trồi lên khỏi ô, chân trùng tâm va chạm
        sx, sy = camera.apply(self.cx, self.cy)
        ve_quai_am(
            man, sx, sy + 4, 2.0, self.jitter,
            self.trang_thai, self.huong_x, self.bien_the, nhieu=True,
        )


# =============================================================================
# ITEM — pin (FM), băng cassette (AM), mảnh mật mã (FM)
# =============================================================================
class Item:
    """
    loai:
        'battery'  — viên pin xanh, chỉ nhặt ở FM
        'cassette' — băng cassette, chỉ nhặt ở AM
                     an=True (màn 1): ẩn ở FM, hiện MỜ khi bật AM (chế độ dò)
        'code'     — mảnh giấy mật mã, chỉ nhặt ở FM (màn 3)
    """

    def __init__(self, loai, x, y, gia_tri=None, an=False):
        self.loai = loai
        self.x = float(x)
        self.y = float(y)
        self.w = 14
        self.h = 10
        self.gia_tri = gia_tri          # Con số mật mã (nếu là code)
        self.an = an
        self.da_nhat = False
        self.dao_dong = random.random() * 6.28

    @property
    def cx(self):
        return self.x + self.w * 0.5

    @property
    def cy(self):
        return self.y + self.h * 0.5

    def thu_nhat(self, player, tan_so):
        """Nhặt tự động khi đứng chồng lên và đúng thế giới."""
        if self.da_nhat:
            return False
        can_the = {
            "battery": FM,
            "cassette": AM,
            "code": FM,
        }.get(self.loai)
        if tan_so != can_the:
            return False
        if khoang_cach(self.cx, self.cy, player.cx, player.cy) > BAN_KINH_NHAT:
            return False
        self.da_nhat = True
        if self.loai == "battery":
            player.nap_pin(PIN_NHAT)
        elif self.loai == "cassette":
            player.bang += 1
        elif self.loai == "code":
            if self.gia_tri not in player.ma_so:
                player.ma_so.append(self.gia_tri)
        return True

    def _ve_bang(self, man, sx, sy, alpha):
        """Hộp cassette; alpha 0–255. Thấp = bóng mờ (chế độ dò)."""
        alpha = max(0, min(255, int(alpha)))
        spr = pygame.Surface((22, 16), pygame.SRCALPHA)
        pygame.draw.rect(spr, (90, 70, 40, alpha), (2, 3, 16, 10))
        pygame.draw.rect(spr, (40, 30, 16, alpha), (2, 3, 16, 10), 1)
        pygame.draw.circle(spr, (30, 24, 14, alpha), (7, 8), 2)
        pygame.draw.circle(spr, (30, 24, 14, alpha), (13, 8), 2)
        pygame.draw.rect(spr, (200, 180, 80, alpha), (5, 4, 10, 2))
        man.blit(spr, (sx - 3, sy - 2))

    def ve(self, man, camera, tan_so, dist_player=None):
        if self.da_nhat:
            return
        self.dao_dong += 0.08
        bob = math.sin(self.dao_dong) * 2
        sx, sy = camera.apply(self.x, self.y + bob)

        if self.loai == "cassette":
            # Chỉ hiện khi bật AM (chế độ có ma). FM = không vẽ băng.
            if tan_so != AM:
                return
            if self.an:
                nhip = 0.5 + 0.5 * math.sin(self.dao_dong * 1.4)
                alpha = 70 + int(80 * nhip)
                r = int(10 + 6 * nhip)
                pygame.draw.circle(man, (180, 160, 80), (sx + 7, sy + 5), r, 1)
            else:
                alpha = 255
            self._ve_bang(man, sx, sy, alpha)
            return

        if self.loai in ("battery", "code") and tan_so != FM:
            return
        if self.loai == "battery":
            pygame.draw.rect(man, (40, 180, 90), (sx, sy + 1, 12, 8))
            pygame.draw.rect(man, (20, 90, 45), (sx, sy + 1, 12, 8), 1)
            pygame.draw.rect(man, (200, 220, 210), (sx + 12, sy + 3, 3, 4))
            pygame.draw.line(man, (20, 60, 30), (sx + 3, sy + 5), (sx + 9, sy + 5), 1)
        elif self.loai == "code":
            pygame.draw.rect(man, (228, 214, 150), (sx, sy - 2, 12, 14))
            pygame.draw.rect(man, (90, 70, 30), (sx, sy - 2, 12, 14), 1)
            pygame.draw.line(man, (140, 40, 40), (sx + 2, sy + 2), (sx + 10, sy + 2), 1)
            pygame.draw.line(man, (140, 40, 40), (sx + 2, sy + 5), (sx + 8, sy + 5), 1)


# =============================================================================
# SAFE — hộp an toàn khóa băng cassette (màn 3, thế giới AM)
# =============================================================================
class Safe:
    """
    Hộp sắt ở AM. Cần đúng con số mật mã đã nhặt ở FM mới mở được (phím E).
    Mở xong nhả 1 băng cassette vào túi Player.
    """

    def __init__(self, x, y, ma):
        self.x = float(x)
        self.y = float(y)
        self.w = 28
        self.h = 28
        self.ma = ma
        self.da_mo = False

    @property
    def cx(self):
        return self.x + self.w * 0.5

    @property
    def cy(self):
        return self.y + self.h * 0.5

    def gan_player(self, player):
        return khoang_cach(self.cx, self.cy, player.cx, player.cy) < 28

    def thu_mo(self, player):
        if self.da_mo:
            return "da_mo"
        if not self.gan_player(player):
            return None
        if self.ma in player.ma_so:
            self.da_mo = True
            player.bang += 1
            return "mo"
        return "thieu_ma"

    def ve(self, man, camera, tan_so, font):
        if tan_so != AM:
            return
        sx, sy = camera.apply(self.x, self.y)
        mau = (50, 90, 55) if self.da_mo else (58, 58, 64)
        pygame.draw.rect(man, mau, (sx, sy, self.w, self.h))
        pygame.draw.rect(man, (18, 18, 20), (sx, sy, self.w, self.h), 2)
        pygame.draw.rect(man, (30, 30, 34), (sx + 6, sy + 8, 16, 14))
        # Núm xoay
        pygame.draw.circle(man, (160, 160, 150), (sx + 14, sy + 15), 5)
        pygame.draw.circle(man, (40, 40, 40), (sx + 14, sy + 15), 2)
        if not self.da_mo:
            chu = font.render(str(self.ma), True, (220, 200, 80))
            man.blit(chu, (sx + (self.w - chu.get_width()) // 2, sy - 14))
        else:
            pygame.draw.line(man, (80, 200, 90), (sx + 6, sy + 16), (sx + 12, sy + 22), 2)
            pygame.draw.line(man, (80, 200, 90), (sx + 12, sy + 22), (sx + 22, sy + 8), 2)


# =============================================================================
# LEVEL MANAGER — bản đồ, địa hình kép FM/AM, vật phẩm, lối thoát
# =============================================================================
class LevelManager:
    """
    Mỗi ô lưới:
        '#'  tường cả hai thế giới
        'D'  bàn học (tường cả hai, vẽ gỗ)
        '.'  sàn cả hai (điểm nhảy tần số an toàn)
        'F'  sàn FM / tường AM
        'A'  sàn AM / tường FM
    Mục tiêu mọi màn: 3 băng cassette + đứng lên Trạm phát thanh ở FM.
    """

    TEN = {
        1: "TÍN HIỆU RỜI RẠC",
        2: "MÊ CUNG KHÔNG GIAN KÉP",
        3: "DỊCH MÃ & CƯỠNG CHẾ AM",
    }
    MUC_TIEU = {
        1: "Dò sóng ở FM (tạch tạch), nhảy AM nhặt 3 băng ẩn, về Trạm phát thanh.",
        2: "Tường FM = lối AM. Nhảy SPACE luồn mê cung, lấy 3 băng, thoát.",
        3: "Nhặt mật mã (đổi mỗi lần chơi) ở FM, mở hộp ở AM (E). Đài hỏng: ĐỨNG YÊN + giữ Q.",
    }

    # Map màn 1 được sinh trong _tao_truong_hoc (trường ~32x22, nhiều phòng).

    def __init__(self):
        self.so = 1
        self.grid = []
        self.w = 0
        self.h = 0
        self.items = []
        self.safes = []
        self.enemies = []
        self.start = (TILE + 10, TILE + 10)
        self.exit_pos = (0, 0)          # Tâm ô thoát (pixel)
        self.ten = ""
        self.muc_tieu = ""

    def kich_thuoc_pixel(self):
        return self.w * TILE, self.h * TILE

    def o_hop_le(self, tx, ty):
        return 0 <= tx < self.w and 0 <= ty < self.h

    def o_di_duoc(self, tx, ty, tan_so):
        if not self.o_hop_le(tx, ty):
            return False
        t = self.grid[ty][tx]
        if t in ("#", "D"):
            return False
        if t == ".":
            return True
        if t == "F":
            return tan_so == FM
        if t == "A":
            return tan_so == AM
        return False

    def la_tuong(self, tx, ty, tan_so):
        return not self.o_di_duoc(tx, ty, tan_so)

    def di_duoc_ca_hai(self, tx, ty):
        return self.o_di_duoc(tx, ty, FM) and self.o_di_duoc(tx, ty, AM)

    def tam_o(self, tx, ty, w=16, h=16):
        """Đặt đối tượng vào giữa ô, trừ kích thước."""
        return tx * TILE + (TILE - w) * 0.5, ty * TILE + (TILE - h) * 0.5

    def tai_cap(self, so):
        """Sinh toàn bộ dữ liệu một màn chơi."""
        self.so = so
        self.ten = LevelManager.TEN[so]
        self.muc_tieu = LevelManager.MUC_TIEU[so]
        self.items = []
        self.safes = []
        self.enemies = []
        if so == 1:
            self._tai_man_1()
        elif so == 2:
            self._tai_man_kep(32, 24, seed=2026, so_quai=5, so_pin=5)
        else:
            # Mê cung + mật mã random mỗi lần vào màn 3
            self._tai_man_kep(
                40, 30, seed=random.randint(1, 2**31 - 1),
                so_quai=9, so_pin=8, man3=True,
            )

    def _gan_grid_tu_chuoi(self, hang):
        self.grid = [list(row) for row in hang]
        self.h = len(self.grid)
        self.w = len(self.grid[0])
        sx = sy = 1
        ex = self.w - 2
        ey = self.h - 2
        for y, row in enumerate(self.grid):
            for x, c in enumerate(row):
                if c == "S":
                    sx, sy = x, y
                    self.grid[y][x] = "."
                elif c == "X":
                    ex, ey = x, y
                    self.grid[y][x] = "."
        self.start = self.tam_o(sx, sy)
        self.exit_pos = (ex * TILE + TILE * 0.5, ey * TILE + TILE * 0.5)

    def _tao_truong_hoc(self, w=32, h=22):
        """
        Cánh trường rộng: 3 phòng trên + 2 phòng dưới + phòng đài,
        hành lang giữa. Camera sẽ cuộn theo người chơi.
        """
        g = [["#" for _ in range(w)] for _ in range(h)]
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                g[y][x] = "."

        def phong(x0, y0, pw, ph, cua_x, cua_y):
            for y in range(y0, y0 + ph):
                for x in range(x0, x0 + pw):
                    if y in (y0, y0 + ph - 1) or x in (x0, x0 + pw - 1):
                        g[y][x] = "#"
            g[cua_y][cua_x] = "."
            g[cua_y][min(w - 2, cua_x + 1)] = "."
            for dy in range(y0 + 2, y0 + ph - 2, 2):
                for dx in range(x0 + 2, x0 + pw - 3, 3):
                    if 0 < dy < h - 1 and 0 < dx < w - 2:
                        g[dy][dx] = "D"
                        g[dy][dx + 1] = "D"

        phong(1, 1, 9, 8, 4, 8)
        phong(12, 1, 9, 8, 16, 8)
        phong(23, 1, 8, 8, 26, 8)
        phong(1, 13, 9, 8, 4, 13)
        phong(12, 13, 9, 8, 16, 13)
        phong(23, 14, 8, 7, 26, 14)
        # Cột tủ locker trên hành lang
        for x in (10, 21):
            g[10][x] = "#"
            g[11][x] = "#"
        g[10][2] = "S"
        g[18][28] = "X"
        return g

    def _tai_man_1(self):
        """Trường 32x22 — băng ẩn, dò tín hiệu FM, hiện mờ khi bật AM."""
        self._gan_grid_tu_chuoi(["".join(row) for row in self._tao_truong_hoc()])
        vi_tri_bang = [(4, 4), (15, 16), (22, 10)]
        for tx, ty in vi_tri_bang:
            if self.o_di_duoc(tx, ty, FM):
                x, y = self.tam_o(tx, ty, 14, 10)
                self.items.append(Item("cassette", x, y, an=True))
        # Nếu ô bị bàn che, dời ra ô sàn gần nhất
        while sum(1 for i in self.items if i.loai == "cassette") < 3:
            for ty in range(2, self.h - 2):
                for tx in range(2, self.w - 2):
                    if self.grid[ty][tx] == "." and (tx, ty) not in ((2, 10), (28, 18)):
                        x, y = self.tam_o(tx, ty, 14, 10)
                        if all(khoang_cach(x, y, it.x, it.y) > 80 for it in self.items):
                            self.items.append(Item("cassette", x, y, an=True))
                            if sum(1 for i in self.items if i.loai == "cassette") >= 3:
                                break
                if sum(1 for i in self.items if i.loai == "cassette") >= 3:
                    break
        for tx, ty in ((8, 10), (16, 4), (25, 16), (3, 18), (28, 10)):
            if self.o_di_duoc(tx, ty, FM):
                x, y = self.tam_o(tx, ty, 14, 10)
                self.items.append(Item("battery", x, y))
        for tx, ty in ((18, 10), (5, 16), (27, 5), (14, 18)):
            if self.o_di_duoc(tx, ty, AM):
                x, y = self.tam_o(tx, ty, 18, 22)
                self.enemies.append(Enemy(x, y))

    def _tao_me_cung_kep(self, w, h, rng, ti_le_tuong=0.24):
        """
        Mê cung địa hình đối lập:
          - Lưới hành lang '.' mỗi 3 ô: đi được CẢ FM lẫn AM (chỗ nhảy số).
          - Ô trong phòng xen kẽ 'F' và 'A': tường bên này = lối bên kia.
        """
        g = [["#" for _ in range(w)] for _ in range(h)]
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                if x % 3 == 1 or y % 3 == 1:
                    g[y][x] = "."
                else:
                    phong = (x // 3) + (y // 3)
                    g[y][x] = "F" if (phong % 2 == 0) else "A"
        # Rải tường đặc trong phòng cho rối, không phá hành lang kép
        for y in range(2, h - 2):
            for x in range(2, w - 2):
                if g[y][x] in ("F", "A") and rng.random() < ti_le_tuong:
                    g[y][x] = "#"
        g[1][1] = "."
        g[h - 2][w - 2] = "."
        # Mở hành lang tới cửa thoát (đảm bảo dual-path)
        x, y = 1, 1
        tx, ty = w - 2, h - 2
        while x != tx:
            x += 1 if tx > x else -1
            g[1][x] = "."
        while y != ty:
            y += 1 if ty > y else -1
            g[y][tx] = "."
        return g

    def _bfs_trang_thai(self, sx, sy):
        """
        BFS trên (ô, tần số). Đứng trên ô đi được cả hai thì được nhảy số.
        Trả về tập (tx, ty, tan_so) tới được từ điểm spawn ở FM.
        """
        from collections import deque
        bat = (sx, sy, FM)
        q = deque([bat])
        seen = {bat}
        while q:
            x, y, f = q.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if self.o_di_duoc(nx, ny, f) and (nx, ny, f) not in seen:
                    seen.add((nx, ny, f))
                    q.append((nx, ny, f))
            nf = AM if f == FM else FM
            if self.o_di_duoc(x, y, nf) and (x, y, nf) not in seen:
                seen.add((x, y, nf))
                q.append((x, y, nf))
        return seen

    def _tai_man_kep(self, w, h, seed, so_quai, so_pin, man3=False):
        rng = random.Random(seed)
        self.grid = self._tao_me_cung_kep(
            w, h, rng, ti_le_tuong=0.32 if man3 else 0.24,
        )
        self.w, self.h = w, h
        self.start = self.tam_o(1, 1)
        self.exit_pos = ((w - 2) * TILE + TILE * 0.5, (h - 2) * TILE + TILE * 0.5)

        seen = self._bfs_trang_thai(1, 1)
        o_am = [(x, y) for (x, y, f) in seen if f == AM and (x, y) != (1, 1)]
        o_fm = [(x, y) for (x, y, f) in seen if f == FM and (x, y) != (1, 1)]
        o_a = [(x, y) for x, y in o_am if self.grid[y][x] == "A"]
        o_f = [(x, y) for x, y in o_fm if self.grid[y][x] == "F"]
        o_kep = [(x, y) for x, y in o_am if self.di_duoc_ca_hai(x, y)]
        if not o_a:
            o_a = o_am
        if not o_f:
            o_f = o_fm
        if not o_kep:
            o_kep = o_am

        def chon_xa(ds, n, cam):
            """Chọn n ô xa nhau và xa điểm cấm (spawn / exit)."""
            con = list(ds)
            rng.shuffle(con)
            chon = []
            while con and len(chon) < n:
                best = None
                best_d = -1
                for t in con:
                    dmin = 999
                    for c in cam + chon:
                        dmin = min(dmin, abs(t[0] - c[0]) + abs(t[1] - c[1]))
                    if dmin > best_d:
                        best_d = dmin
                        best = t
                if best is None:
                    break
                chon.append(best)
                con.remove(best)
            return chon

        cam = [(1, 1), (w - 2, h - 2)]
        da_dung = list(cam)
        if man3:
            ma_so = rng.sample(range(10, 100), 3)
            vt_ma = chon_xa(o_f, 3, da_dung)
            da_dung.extend(vt_ma)
            vt_hop = chon_xa(o_a, 3, da_dung)
            da_dung.extend(vt_hop)
            # Nếu thiếu ô, lấy thêm từ danh sách đầy đủ
            while len(vt_ma) < 3 and o_fm:
                t = o_fm[len(vt_ma) % len(o_fm)]
                if t not in vt_ma:
                    vt_ma.append(t)
                    da_dung.append(t)
                else:
                    break
            while len(vt_hop) < 3 and o_am:
                t = o_am[len(vt_hop) % len(o_am)]
                if t not in vt_hop:
                    vt_hop.append(t)
                    da_dung.append(t)
                else:
                    break
            if not vt_ma:
                vt_ma = [(1, 1)]
            if not vt_hop:
                vt_hop = [(w - 3, h - 2)]
            for i in range(3):
                tx, ty = vt_ma[i % len(vt_ma)]
                x, y = self.tam_o(tx, ty, 12, 14)
                self.items.append(Item("code", x, y, gia_tri=ma_so[i]))
                hx, hy = vt_hop[i % len(vt_hop)]
                sx, sy = self.tam_o(hx, hy, 28, 28)
                self.safes.append(Safe(sx, sy, ma_so[i]))
        else:
            for tx, ty in chon_xa(o_a, 3, da_dung):
                x, y = self.tam_o(tx, ty, 14, 10)
                self.items.append(Item("cassette", x, y, an=False))
                da_dung.append((tx, ty))

        for tx, ty in chon_xa(o_f, so_pin, da_dung):
            x, y = self.tam_o(tx, ty, 14, 10)
            self.items.append(Item("battery", x, y))
            da_dung.append((tx, ty))

        # Quái đứng trên hành lang kép, tránh spawn và vật phẩm
        vt_quai = chon_xa(o_kep, so_quai, da_dung)
        he_so = 1.12 if man3 else 1.0
        for tx, ty in vt_quai:
            x, y = self.tam_o(tx, ty, 18, 22)
            self.enemies.append(Enemy(x, y, he_so=he_so))

    def khoang_cach_bang_an(self, px, py):
        """Màn 1: khoảng cách tới băng cassette ẩn gần nhất (chưa nhặt)."""
        best = 1e9
        for it in self.items:
            if it.loai == "cassette" and not it.da_nhat:
                d = khoang_cach(px, py, it.cx, it.cy)
                if d < best:
                    best = d
        return best

    def dang_o_tram(self, player):
        """True khi đứng trên Trạm phát thanh."""
        return khoang_cach(player.cx, player.cy, self.exit_pos[0], self.exit_pos[1]) < 22

    def ve(self, man, camera, tan_so):
        """Vẽ mọi ô nằm trong khung nhìn."""
        map_w, map_h = self.kich_thuoc_pixel()
        vw, vh = RONG, CAO - HUD_H
        # Nền ngoài bản đồ
        man.fill(MAU_NEN_AM if tan_so == AM else MAU_NEN_FM)
        pygame.draw.rect(man, (10, 10, 12), (0, 0, RONG, HUD_H))

        tx0 = max(0, int(camera.x // TILE) - 1)
        ty0 = max(0, int(camera.y // TILE) - 1)
        tx1 = min(self.w, tx0 + vw // TILE + 3)
        ty1 = min(self.h, ty0 + vh // TILE + 3)

        for ty in range(ty0, ty1):
            for tx in range(tx0, tx1):
                t = self.grid[ty][tx]
                sx, sy = camera.apply(tx * TILE, ty * TILE)
                self._ve_o(man, sx, sy, t, tan_so, tx, ty)

        # Trạm phát thanh
        self._ve_tram(man, camera, tan_so)

    def _ve_o(self, man, sx, sy, t, tan_so, tx, ty):
        di_duoc = self.o_di_duoc(tx, ty, tan_so)
        if t == "D":
            pygame.draw.rect(man, MAU_BAN_HOC, (sx, sy, TILE, TILE))
            pygame.draw.rect(man, (60, 40, 22), (sx, sy, TILE, TILE), 1)
            pygame.draw.rect(man, (140, 110, 70), (sx + 6, sy + 8, 28, 18))
            pygame.draw.rect(man, (50, 80, 140), (sx + 10, sy + 12, 8, 6))
            pygame.draw.rect(man, (160, 40, 40), (sx + 22, sy + 12, 7, 9))
            return
        if not di_duoc:
            if tan_so == AM:
                pygame.draw.rect(man, MAU_TUONG_AM, (sx, sy, TILE, TILE))
                pygame.draw.rect(man, (40, 8, 12), (sx, sy, TILE, TILE), 1)
                pygame.draw.line(man, (90, 24, 30), (sx + 4, sy + 6), (sx + 36, sy + 34), 1)
            else:
                pygame.draw.rect(man, MAU_TUONG_FM, (sx, sy, TILE, TILE))
                pygame.draw.rect(man, (50, 48, 40), (sx, sy, TILE, TILE), 1)
                pygame.draw.rect(man, (90, 86, 72), (sx + 3, sy + 3, TILE - 6, 4))
            return
        # Sàn
        if tan_so == AM:
            pygame.draw.rect(man, MAU_SAN_AM, (sx, sy, TILE, TILE))
            pygame.draw.rect(man, (20, 6, 10), (sx, sy, TILE, TILE), 1)
        else:
            pygame.draw.rect(man, MAU_SAN_FM, (sx, sy, TILE, TILE))
            pygame.draw.rect(man, (36, 38, 32), (sx, sy, TILE, TILE), 1)
        # Ô kép: dấu + mờ — chỗ đứng để nhảy tần số
        if t == ".":
            cx, cy = sx + TILE // 2, sy + TILE // 2
            mau = (90, 40, 48) if tan_so == AM else (70, 78, 64)
            pygame.draw.line(man, mau, (cx - 4, cy), (cx + 4, cy), 1)
            pygame.draw.line(man, mau, (cx, cy - 4), (cx, cy + 4), 1)

    def _ve_tram(self, man, camera, tan_so):
        ex, ey = self.exit_pos
        sx, sy = camera.apply(ex - 16, ey - 18)
        than = (50, 90, 70) if tan_so == FM else (40, 20, 24)
        pygame.draw.rect(man, than, (sx, sy + 10, 32, 22))
        pygame.draw.rect(man, (20, 20, 22), (sx, sy + 10, 32, 22), 1)
        pygame.draw.rect(man, (30, 30, 32), (sx + 12, sy - 6, 8, 16))
        pygame.draw.line(man, (180, 180, 190), (sx + 16, sy - 6), (sx + 16, sy - 18), 2)
        pygame.draw.circle(man, (200, 200, 80) if tan_so == FM else (80, 20, 20),
                           (sx + 16, sy - 18), 4)
        # Sóng phát khi đang FM
        if tan_so == FM:
            for r in (8, 14, 20):
                pygame.draw.circle(man, (120, 200, 110), (sx + 16, sy - 18), r, 1)


# =============================================================================
# UI — menu, HUD, victory, game over
# =============================================================================
class UI:
    def __init__(self):
        self.f_nho = tao_font(15)
        self.f_vua = tao_font(18)
        self.f_dam = tao_font(20, dam=True)
        self.f_to = tao_font(36, dam=True)
        self.f_tieu = tao_font(48, dam=True)
        self.f_so = tao_font(16, dam=True)
        # Surface tái sử dụng cho nhiễu tĩnh (tránh tạo mới mỗi khung)
        self.surf_nhieu = pygame.Surface((RONG, CAO), pygame.SRCALPHA)
        self.vignette = self._tao_vignette()
        self.glitch = 0
        self.rect_nut_pause = pygame.Rect(RONG - 46, 8, 36, 36)

    def _tao_vignette(self):
        s = pygame.Surface((RONG, CAO), pygame.SRCALPHA)
        for i in range(36):
            a = int(i * 3.4)
            pygame.draw.rect(s, (0, 0, 0, a), (i * 3, i * 2, RONG - i * 6, CAO - i * 4), 4)
        return s

    def ve_nhieu_tinh(self, man, cuong_do, do_do=False):
        """Nhiễu sóng static: đường ngang + hạt. cuong_do 0..1."""
        if cuong_do <= 0.01:
            return
        self.surf_nhieu.fill((0, 0, 0, 0))
        n_line = int(18 + 55 * cuong_do)
        for _ in range(n_line):
            y = random.randint(HUD_H, CAO - 1)
            a = random.randint(18, int(70 + 80 * cuong_do))
            if do_do:
                col = (200, 40, 40, a)
            else:
                g = random.randint(180, 255)
                col = (g, g, g, a)
            pygame.draw.line(
                self.surf_nhieu, col,
                (0, y), (RONG, y), random.randint(1, 2)
            )
        n_hat = int(20 + 40 * cuong_do)
        for _ in range(n_hat):
            x = random.randint(0, RONG - 4)
            y = random.randint(HUD_H, CAO - 2)
            a = random.randint(40, 140)
            pygame.draw.rect(self.surf_nhieu, (255, 255, 255, a), (x, y, random.randint(2, 7), 1))
        man.blit(self.surf_nhieu, (0, 0))

    def ve_hud(self, man, tan_so, player, level, cuong_che, canh_bao, bi_san, tam_dung=False):
        """Thanh HUD: tần số, pin, mật mã, số băng, nút tạm dừng."""
        pygame.draw.rect(man, (12, 12, 14), (0, 0, RONG, HUD_H))
        pygame.draw.line(man, (70, 70, 80), (0, HUD_H - 1), (RONG, HUD_H - 1), 1)

        # Tần số
        if tan_so == FM:
            chu_ts = "FM  88.8 MHz"
            mau_ts = (80, 220, 120)
        else:
            chu_ts = "AM  540 kHz"
            mau_ts = (255, 70, 70) if not cuong_che else (255, 220, 40)
        s_ts = self.f_dam.render(chu_ts, True, mau_ts)
        man.blit(s_ts, (10, 6))
        if tan_so == AM:
            man.blit(self.f_nho.render("CHẾ ĐỘ DÒ", True, mau_ts), (14 + s_ts.get_width(), 10))
        man.blit(self.f_nho.render("Màn %d  %s" % (level.so, level.ten), True, (140, 140, 150)), (10, 28))

        def thanh(x, y, w, h, tle, mau, nhan):
            man.blit(self.f_nho.render(nhan, True, (185, 185, 190)), (x - 36, y - 2))
            pygame.draw.rect(man, (30, 30, 34), (x, y, w, h))
            pygame.draw.rect(man, mau, (x, y, int(w * max(0.0, min(1.0, tle))), h))
            pygame.draw.rect(man, (170, 170, 180), (x, y, w, h), 1)

        t_pin = player.pin / PIN_TOI_DA
        if t_pin > 0.45:
            mau_pin = (50, 200, 90)
        elif t_pin > 0.2:
            mau_pin = (220, 180, 40)
        else:
            mau_pin = (220, 50, 40)
        thanh(292, 8, 128, 12, t_pin, mau_pin, "PIN")

        t_tl = player.the_luc / THE_LUC_TOI_DA
        if player.nin_tho or player.dang_chay:
            mau_tl = (70, 180, 230) if player.nin_tho else (240, 160, 50)
        elif t_tl > 0.4:
            mau_tl = (90, 200, 170)
        elif t_tl > 0.18:
            mau_tl = (220, 180, 50)
        else:
            mau_tl = (220, 55, 50)
        thanh(292, 28, 128, 12, t_tl, mau_tl, "LỰC")

        # Băng cassette
        man.blit(self.f_nho.render("BĂNG", True, (200, 200, 190)), (450, 6))
        for i in range(3):
            rx = 450 + i * 28
            ry = 24
            if i < player.bang:
                pygame.draw.rect(man, (160, 120, 50), (rx, ry, 22, 14))
                pygame.draw.circle(man, (40, 30, 16), (rx + 7, ry + 7), 3)
                pygame.draw.circle(man, (40, 30, 16), (rx + 15, ry + 7), 3)
            else:
                pygame.draw.rect(man, (40, 40, 44), (rx, ry, 22, 14), 1)
        man.blit(self.f_so.render("%d/3" % player.bang, True, (230, 230, 220)), (538, 22))

        # Mật mã
        man.blit(self.f_nho.render("MẬT MÃ", True, (200, 200, 190)), (600, 6))
        if level.so == 3:
            ds = player.ma_so if player.ma_so else []
            txt = "  ".join(str(n) for n in ds) if ds else "—"
            man.blit(self.f_dam.render(txt, True, (240, 210, 80)), (600, 22))
        else:
            man.blit(self.f_nho.render("(chỉ màn 3)", True, (90, 90, 95)), (600, 24))

        # Nút tạm dừng — góc phải HUD, phím P
        r = self.rect_nut_pause
        hover = r.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(man, (55, 55, 64) if hover else (28, 28, 32), r)
        pygame.draw.rect(man, (200, 200, 210) if hover else (120, 120, 130), r, 1)
        if tam_dung:
            pygame.draw.polygon(
                man, (90, 230, 140),
                ((r.x + 12, r.y + 8), (r.x + 12, r.y + 28), (r.x + 28, r.y + 18)),
            )
        else:
            pygame.draw.rect(man, (230, 230, 225), (r.x + 11, r.y + 10, 5, 16))
            pygame.draw.rect(man, (230, 230, 225), (r.x + 20, r.y + 10, 5, 16))

        # Cảnh báo
        if cuong_che:
            msg = "CƯỠNG CHẾ AM  —  GIỮ Q + ĐỨNG YÊN"
            s = self.f_dam.render(msg, True, (255, 230, 60))
            man.blit(s, (RONG // 2 - s.get_width() // 2, HUD_H + 8))
        elif canh_bao:
            msg = "TÍN HIỆU MẤT  —  CHUẨN BỊ NÍN THỞ"
            s = self.f_dam.render(msg, True, (255, 140, 40))
            man.blit(s, (RONG // 2 - s.get_width() // 2, HUD_H + 8))
        elif bi_san:
            s = self.f_dam.render("ĐANG BỊ SĂN  —  NHẢY FM (SPACE) HOẶC NÍN THỞ", True, (255, 60, 50))
            man.blit(s, (RONG // 2 - s.get_width() // 2, HUD_H + 8))

    def ve_thong_bao(self, man, text):
        if not text:
            return
        s = self.f_vua.render(text, True, (240, 240, 230))
        bg = pygame.Surface((s.get_width() + 20, s.get_height() + 10), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 170))
        x = RONG // 2 - bg.get_width() // 2
        y = CAO - 70
        man.blit(bg, (x, y))
        man.blit(s, (x + 10, y + 5))

    def ve_goi_y(self, man, text):
        s = self.f_nho.render(text, True, (160, 160, 165))
        man.blit(s, (10, CAO - 22))

    def ve_menu(self, man, dt):
        man.fill((6, 6, 8))
        self.ve_nhieu_tinh(man, 0.55)
        self.glitch += dt
        # Title glitch RGB
        tieu = "TẦN SỐ TRẮNG"
        ox = int(math.sin(self.glitch * 17) * 3)
        s1 = self.f_tieu.render(tieu, True, (255, 40, 40))
        s2 = self.f_tieu.render(tieu, True, (40, 220, 255))
        s3 = self.f_tieu.render(tieu, True, (240, 240, 245))
        blit_tam(man, s1, RONG // 2 + ox, 118)
        blit_tam(man, s2, RONG // 2 - ox, 122)
        blit_tam(man, s3, RONG // 2, 120)
        phu = self.f_vua.render("WHITE NOISE FREQUENCY", True, (140, 140, 150))
        blit_tam(man, phu, RONG // 2, 168)

        bang = [
            "WASD / ↑↓←→   Di chuyển",
            "SHIFT         Chạy (tốn thể lực, The Void nghe xa)",
            "Q             Nín thở / rón rén  (tốn thể lực, khó bị nghe)",
            "SPACE         Đổi tần số  FM (an toàn)  ↔  AM (dò: quái + băng mờ)",
            "E             Mở Hộp An Toàn (màn 3, cần mật mã)",
            "P             Tạm dừng / tiếp tục",
            "",
            "Màn 1  Dò tạch tạch ở FM → SPACE sang AM, băng hiện mờ, đứng lên nhặt",
            "Màn 2  Tường bên này là lối bên kia — nhảy số luồn mê cung",
            "Màn 3  Mật mã (đổi mỗi lần) FM, hộp AM. Cứ ~10s đài hỏng: ĐỨNG YÊN + giữ Q",
            "Nhặt PIN XANH ở FM. Hết thể lực thì không chạy/nín được.",
        ]
        y = 204
        for dong in bang:
            s = self.f_nho.render(dong, True, (190, 190, 195))
            man.blit(s, (RONG // 2 - 300, y))
            y += 21

        nhap = self.f_dam.render("NHẤN  ENTER  —  CỐT TRUYỆN", True, (80, 255, 140))
        if int(self.glitch * 2) % 2 == 0:
            blit_tam(man, nhap, RONG // 2, 530)
        blit_tam(man, self.f_nho.render("ESC thoát", True, (110, 110, 115)), RONG // 2, 558)
        man.blit(self.vignette, (0, 0))

    def ve_cot_truyen(self, man, dt, so_trang, so_ky, n_trang):
        """Màn cốt truyện: đánh chữ từng ký tự, nhiễu radio nền."""
        man.fill((6, 5, 7))
        self.ve_nhieu_tinh(man, 0.28)
        self.glitch += dt
        tieu, than = TRANG_TRUYEN[so_trang]
        # Ăng-ten nhỏ góc trên
        pygame.draw.rect(man, (40, 40, 48), (RONG // 2 - 18, 36, 36, 22))
        pygame.draw.rect(man, (20, 20, 24), (RONG // 2 - 18, 36, 36, 22), 1)
        pygame.draw.line(man, (180, 180, 190), (RONG // 2, 36), (RONG // 2, 18), 2)
        pygame.draw.circle(man, (200, 60, 60), (RONG // 2, 16), 4)

        blit_tam(man, self.f_dam.render(tieu, True, (220, 80, 80)), RONG // 2, 88)

        hien = than[: max(0, int(so_ky))]
        y = 140
        for dong in hien.split("\n"):
            s = self.f_vua.render(dong, True, (210, 208, 200))
            man.blit(s, (RONG // 2 - 300, y))
            y += 32
        # Con trỏ nhấp
        if int(so_ky) < len(than) and int(self.glitch * 3) % 2 == 0:
            pygame.draw.rect(man, (200, 200, 190), (RONG // 2 - 300, y - 28, 10, 18))

        chan = "ENTER  tiếp  ·  ESC  bỏ qua cốt truyện     %d / %d" % (so_trang + 1, n_trang)
        blit_tam(man, self.f_nho.render(chan, True, (140, 140, 145)), RONG // 2, 548)
        man.blit(self.vignette, (0, 0))

    def ve_thang(self, man, level, da_xong_het):
        man.fill((4, 10, 8))
        self.ve_nhieu_tinh(man, 0.25)
        tieu = "TÍN HIỆU ỔN ĐỊNH"
        blit_tam(man, self.f_tieu.render(tieu, True, (80, 255, 140)), RONG // 2, 160)
        if da_xong_het:
            p = "Bạn đã tắt đài. Ba thế giới khép lại."
            n = "NHẤN ENTER — về menu"
        else:
            p = "Hoàn thành:  " + level.ten
            n = "NHẤN ENTER — vào màn tiếp theo"
        blit_tam(man, self.f_vua.render(p, True, (210, 210, 200)), RONG // 2, 230)
        if not da_xong_het and level.so < 3:
            nxt = LevelManager.TEN[level.so + 1]
            blit_tam(man, self.f_nho.render("Tiếp theo: " + nxt, True, (160, 160, 150)), RONG // 2, 270)
            blit_tam(man, self.f_nho.render(LevelManager.MUC_TIEU[level.so + 1], True, (140, 140, 130)), RONG // 2, 300)
        blit_tam(man, self.f_dam.render(n, True, (240, 240, 230)), RONG // 2, 400)

    def ve_chien_thang(self, man):
        man.fill((4, 8, 10))
        self.ve_nhieu_tinh(man, 0.2)
        blit_tam(man, self.f_tieu.render("BẠN ĐÃ THOÁT", True, (180, 255, 210)), RONG // 2, 150)
        blit_tam(man, self.f_to.render("TẦN SỐ TRẮNG", True, (80, 200, 160)), RONG // 2, 210)
        dong = [
            "Màn 1  Tín hiệu rời rạc",
            "Màn 2  Mê cung không gian kép",
            "Màn 3  Dịch mã & cưỡng chế AM",
            "",
            "Đài ngừng phát. Thế giới song song khép lại.",
        ]
        y = 280
        for d in dong:
            blit_tam(man, self.f_vua.render(d, True, (200, 200, 190)), RONG // 2, y)
            y += 28
        blit_tam(man, self.f_dam.render("ENTER — về menu     ESC — thoát", True, (230, 230, 220)), RONG // 2, 520)

    def ve_thua(self, man):
        man.fill((12, 0, 0))
        self.ve_nhieu_tinh(man, 0.7, do_do=True)
        blit_tam(man, self.f_tieu.render("TÍN HIỆU MẤT", True, (255, 40, 40)), RONG // 2, 180)
        blit_tam(man, self.f_to.render("GAME OVER", True, (220, 200, 200)), RONG // 2, 250)
        blit_tam(man, self.f_vua.render("Chúng nghe thấy bước chân của bạn.", True, (180, 140, 140)), RONG // 2, 320)
        blit_tam(man, self.f_dam.render("NHẤN  R  ĐỂ CHƠI LẠI     ESC — menu", True, (240, 240, 230)), RONG // 2, 420)

    def ve_tam_dung(self, man):
        """Overlay tạm dừng phủ lên khung hình đang đóng băng."""
        che = pygame.Surface((RONG, CAO), pygame.SRCALPHA)
        che.fill((0, 0, 0, 165))
        man.blit(che, (0, 0))
        self.ve_nhieu_tinh(man, 0.22)
        blit_tam(man, self.f_tieu.render("TẠM DỪNG", True, (240, 240, 230)), RONG // 2, 210)
        blit_tam(
            man,
            self.f_dam.render("P  /  ENTER  /  click  —  tiếp tục", True, (80, 255, 140)),
            RONG // 2, 290,
        )
        blit_tam(man, self.f_nho.render("ESC  —  về menu", True, (160, 160, 165)), RONG // 2, 332)

    def ve_jumpscare(self, man, t):
        """t: 0..1 — The Void lao vào mặt: chớp, lunge, lỗ nuốt màn."""
        t = max(0.0, min(1.0, t))
        if t < 0.10:
            man.fill((255, 255, 255) if int(t * 90) % 2 == 0 else (0, 0, 0))
            self.ve_nhieu_tinh(man, 1.0, do_do=True)
            return

        man.fill((0, 0, 0))
        self.ve_nhieu_tinh(man, 0.75 + 0.25 * t, do_do=True)

        # Nấn lại rồi SLAM
        if t < 0.28:
            k = 5.0 + (t - 0.10) * 18.0
        else:
            u = (t - 0.28) / 0.72
            slam = 1.0 - (1.0 - u) ** 3
            k = 8.2 + slam * 10.5

        sx = int(math.sin(t * 92.0) * (12 + 26 * t))
        sy = int(math.cos(t * 71.0) * (8 + 18 * t))
        cx = RONG // 2 + sx
        cy = int(CAO * 0.46 + 30.0 * k) + sy

        ve_quai_am(man, cx - 14, cy + 2, k * 0.97, t * 13.0, "rush", 1, 2, nhieu=False)
        ve_quai_am(man, cx + 12, cy - 2, k * 0.98, t * 13.0 + 1.1, "rush", 1, 1, nhieu=False)
        ve_quai_am(man, cx, cy, k, t * 13.0 + 0.4, "rush", 1, 1, nhieu=True)

        # Tua từ mép màn hình siết vào lỗ — đường gãy, không phải tia thẳng
        vong = (255, 36, 28)
        for i in range(6):
            goc = i * 1.05 + t * 2.4
            x0 = RONG // 2 + math.cos(goc) * (400 - t * 150)
            y0 = CAO // 2 + math.sin(goc) * (300 - t * 100)
            x1 = cx + math.cos(goc + 3.14) * 28
            y1 = int(CAO * 0.42) + math.sin(goc + 3.14) * 22
            px, py = x0, y0
            nseg = 5
            for s in range(1, nseg + 1):
                kk = s / float(nseg)
                nx = x0 + (x1 - x0) * kk + math.sin(t * 9 + s * 1.8 + i) * 22 * (1.0 - kk)
                ny = y0 + (y1 - y0) * kk + math.cos(t * 7 + s * 1.4 + i) * 16 * (1.0 - kk)
                pygame.draw.line(
                    man, vong, (int(px), int(py)), (int(nx), int(ny)),
                    2 if t > 0.35 else 1,
                )
                px, py = nx, ny

        # Lỗ nuốt màn hình
        if t > 0.42:
            u = (t - 0.42) / 0.58
            rw = int(70 + u * u * 520)
            rh = int(90 + u * u * 640)
            pygame.draw.ellipse(
                man, (0, 0, 0),
                (cx - rw // 2, CAO // 2 - rh // 2 + sy, rw, rh),
            )
            pygame.draw.ellipse(
                man, (220, 30, 24),
                (cx - rw // 2, CAO // 2 - rh // 2 + sy, rw, rh),
                max(2, int(4 - u * 2)),
            )
            if u > 0.35:
                pygame.draw.circle(
                    man, (180, 20, 20),
                    (cx, CAO // 2 + sy),
                    max(2, int(6 * (1.0 - u))),
                )

        if 0.16 < t < 0.22 or 0.46 < t < 0.52 or t > 0.92:
            f = pygame.Surface((RONG, CAO), pygame.SRCALPHA)
            f.fill((255, 240, 238, 140 if t < 0.9 else 200))
            man.blit(f, (0, 0))


# =============================================================================
# GAME — vòng lặp chính, đổi tần số, cưỡng chế AM, chuyển màn
# =============================================================================
class Game:
    def __init__(self):
        try:
            pygame.mixer.pre_init(SAMPLE_RATE, -16, 1, 512)
        except Exception:
            pass
        pygame.init()
        try:
            pygame.mixer.init(SAMPLE_RATE, -16, 1, 512)
        except Exception:
            pass
        self.man = pygame.display.set_mode((RONG, CAO))
        pygame.display.set_caption("Tần Số Trắng  —  White Noise Frequency")
        self.dong_ho = pygame.time.Clock()
        self.ui = UI()
        self.audio = Audio()
        self.camera = Camera()
        self.level = LevelManager()
        self.player = Player(TILE + 8, TILE + 8)

        self.trang_thai = MENU
        self.tan_so = FM
        self.chay = True

        # Cưỡng chế AM (màn 3)
        self.cuong_che = False
        self.cuong_che_t = 0.0
        self.cuong_che_cd = 0.0
        self.cuong_che_an_han = 0.0
        self.vi_pham_cuong_che = False

        self.thong_bao = ""
        self.thong_bao_t = 0.0
        self.gioi_thieu_t = 0.0
        self.jumpscare_t = 0.0
        self.flash_doi_song = 0.0
        self.tach_cd = 0.0
        self.thoi_gian_man = 0.0
        self.khoa_space = False          # Tránh giữ SPACE nhảy liên tục
        self.intro_trang = 0
        self.intro_ky = 0.0

    def bao(self, text, giay=2.4):
        self.thong_bao = text
        self.thong_bao_t = giay

    def bat_dau_man(self, so):
        self.level.tai_cap(so)
        px, py = self.level.start
        self.player.dat_lai(px, py)
        self.tan_so = FM
        self.cuong_che = False
        self.cuong_che_t = 0.0
        self.cuong_che_cd = random.uniform(CUONG_CHE_MIN, CUONG_CHE_MAX)
        self.cuong_che_an_han = 0.0
        self.vi_pham_cuong_che = False
        self.gioi_thieu_t = 5.0
        self.thoi_gian_man = 0.0
        self.flash_doi_song = 0.0
        self.audio.im_het()
        self.audio.cap_nhat_the_gioi(self.tan_so)
        self.bao(self.level.muc_tieu, 5.0)
        self.trang_thai = CHOI

    def tim_cho_dung(self, tan_so):
        """
        Nếu ô hiện tại là tường ở tần số mới, đẩy Player tới ô đi được gần nhất.
        Dùng khi hết pin / cưỡng chế AM bắt buộc phải nhảy thế giới.
        """
        p = self.player
        if not cham_4_goc(p.x, p.y, p.w, p.h, lambda tx, ty: self.level.la_tuong(tx, ty, tan_so)):
            return
        for ban_kinh in range(4, TILE * 4, 4):
            for goc in range(0, 360, 20):
                rad = math.radians(goc)
                nx = p.x + math.cos(rad) * ban_kinh
                ny = p.y + math.sin(rad) * ban_kinh
                mw, mh = self.level.kich_thuoc_pixel()
                if nx < 2 or ny < 2 or nx > mw - p.w - 2 or ny > mh - p.h - 2:
                    continue
                if not cham_4_goc(nx, ny, p.w, p.h, lambda tx, ty: self.level.la_tuong(tx, ty, tan_so)):
                    p.x, p.y = nx, ny
                    return

    def co_the_doi_song(self, tan_moi):
        """Nhảy số thủ công: chỉ được khi đứng trên ô đi được ở thế giới đích."""
        p = self.player
        return not cham_4_goc(
            p.x, p.y, p.w, p.h,
            lambda tx, ty: self.level.la_tuong(tx, ty, tan_moi),
        )

    def doi_tan_so(self, bat_buoc=False):
        """
        SPACE: FM ↔ AM.
        Không đổi được nếu thế giới kia là tường tại chỗ đứng (trừ khi bắt buộc).
        Hết pin / đang cưỡng chế thì khoá nhảy thủ công.
        """
        if self.cuong_che and not bat_buoc:
            self.bao("Đài hỏng — khoá SPACE", 1.2)
            return False
        moi = AM if self.tan_so == FM else FM
        if moi == AM and self.player.pin <= PIN_TOI_THIEU_AM and not bat_buoc:
            self.bao("Hết pin — không bật AM được. Nhặt pin xanh!", 2.0)
            return False
        if not bat_buoc and not self.co_the_doi_song(moi):
            self.bao("Tường thế giới kia — đứng ô hành lang (dấu +) rồi nhảy số", 2.2)
            return False
        self.tan_so = moi
        if bat_buoc:
            self.tim_cho_dung(moi)
        self.player.nhap_nhay = 0.18
        self.flash_doi_song = 0.16
        self.audio.phat_doi_song(moi)
        self.audio.cap_nhat_the_gioi(moi)
        if moi == AM and self.level.so == 1:
            self.bao("CHẾ ĐỘ DÒ — băng cassette hiện bóng mờ, đứng lên để nhặt", 2.8)
        return True

    def xu_ly_cuong_che(self, dt):
        """
        Màn 3: mỗi 9.5-12.5 giây đài hỏng, ép sang AM 4.4 giây, khoá SPACE.
        Phải GIỮ Q và không nhấn WASD/mũi tên. Vi phạm → quái lao tới.
        """
        if self.level.so != 3 or self.trang_thai != CHOI:
            self.cuong_che = False
            self.audio.dung_bao_dong()
            return

        if self.cuong_che:
            self.cuong_che_t -= dt
            self.cuong_che_an_han = max(0.0, self.cuong_che_an_han - dt)
            self.audio.phat_bao_dong()
            if self.cuong_che_an_han <= 0.0:
                if self.player.bam_di_chuyen or not self.player.ron_ren:
                    self.vi_pham_cuong_che = True
            if self.cuong_che_t <= 0.0:
                self.cuong_che = False
                self.vi_pham_cuong_che = False
                self.audio.dung_bao_dong()
                self.cuong_che_cd = random.uniform(CUONG_CHE_MIN, CUONG_CHE_MAX)
                # Sự cố kết thúc: đẩy về FM
                if self.tan_so != FM:
                    self.tan_so = FM
                    self.tim_cho_dung(FM)
                    self.audio.phat_doi_song(FM)
                    self.audio.cap_nhat_the_gioi(FM)
                self.bao("Đài ổn định trở lại — SPACE dùng được", 2.0)
        else:
            self.cuong_che_cd -= dt
            if self.cuong_che_cd <= 0.0:
                self.cuong_che = True
                self.cuong_che_t = CUONG_CHE_KEO_DAI
                self.cuong_che_an_han = CUONG_CHE_AN_HAN
                self.vi_pham_cuong_che = False
                if self.tan_so != AM:
                    self.tan_so = AM
                    self.tim_cho_dung(AM)
                    self.audio.phat_doi_song(AM)
                    self.audio.cap_nhat_the_gioi(AM)
                self.bao("CƯỠNG CHẾ AM — giữ Q, đứng yên!", 2.5)

    def tam_dung_choi(self):
        if self.trang_thai != CHOI:
            return
        self.trang_thai = TAM_DUNG
        self.audio.tam_dung()

    def tiep_tuc_choi(self):
        if self.trang_thai != TAM_DUNG:
            return
        self.trang_thai = CHOI
        self.audio.tiep_tuc()

    def chet(self):
        self.audio.im_het()
        self.audio.phat_hu()
        self.trang_thai = JUMPSCARE
        self.jumpscare_t = 0.0

    def cap_nhat_choi(self, dt, keys):
        self.thoi_gian_man += dt
        self.xu_ly_cuong_che(dt)

        self.player.cap_nhat(dt, keys, self.level, self.tan_so)

        # Pin chỉ tụt khi chủ động ở AM. Cưỡng chế màn 3 không hao — đã phạt bằng nín thở.
        if not self.cuong_che:
            het = self.player.hao_pin(dt, self.tan_so)
            if het:
                if self.tan_so != FM:
                    self.tan_so = FM
                    self.tim_cho_dung(FM)
                    self.audio.phat_doi_song(FM)
                    self.audio.cap_nhat_the_gioi(FM)
                self.bao("Hết pin! Bị đẩy về FM — tìm viên pin xanh", 2.5)

        # Nhặt vật phẩm
        for it in self.level.items:
            if it.thu_nhat(self.player, self.tan_so):
                self.audio.phat_nhat()
                if it.loai == "battery":
                    self.bao("Pin +%d%%" % int(PIN_NHAT), 1.6)
                elif it.loai == "cassette":
                    self.bao("Đã nhặt BĂNG CASSETTE  (%d/3)" % self.player.bang, 2.0)
                elif it.loai == "code":
                    self.bao("Mật mã:  %s" % "  ".join(str(n) for n in self.player.ma_so), 2.2)

        # Quái
        bi_san = False
        d_min = 9999.0
        for e in self.level.enemies:
            e.cap_nhat(
                dt, self.player, self.level, self.tan_so,
                self.cuong_che, self.vi_pham_cuong_che,
            )
            d_min = min(d_min, khoang_cach(e.cx, e.cy, self.player.cx, self.player.cy))
            if self.tan_so == AM and e.trang_thai in (Enemy.CHASE, Enemy.RUSH):
                bi_san = True
            if self.tan_so == AM and e.bat_duoc(self.player):
                self.chet()
                return
        self.player.cap_nhat_so_hai(
            dt, self.tan_so, bi_san, d_min, self.cuong_che,
        )
        if self.player.tho_gat_t > 0.58:
            self.bao("Hết hơi — The Void nghe thấy!", 1.3)

        # Thoát màn: đủ 3 băng + đứng trạm + đang FM
        if self.level.dang_o_tram(self.player):
            if self.tan_so != FM:
                self.bao("Trạm phát thanh chỉ hoạt động ở FM", 1.6)
            elif self.player.bang >= 3:
                self.audio.im_het()
                if self.level.so >= 3:
                    self.trang_thai = CHIEN_THANG
                else:
                    self.trang_thai = THANG
                return
            else:
                self.bao("Cần đủ 3 băng cassette rồi hãy phát sóng", 1.8)

        # Tín hiệu dò băng màn 1 (FM)
        if self.level.so == 1 and self.tan_so == FM:
            d = self.level.khoang_cach_bang_an(self.player.cx, self.player.cy)
            if d < BAN_KINH_TIN_HIEU:
                suc = 1.0 - d / BAN_KINH_TIN_HIEU
                khoang_tach = 0.85 - suc * 0.75          # 0.85s → 0.10s
                self.tach_cd -= dt
                if self.tach_cd <= 0.0:
                    self.audio.phat_tach()
                    self.tach_cd = max(0.08, khoang_tach)
                if suc > 0.72:
                    self.bao("Tín hiệu mạnh — SPACE sang AM để nhặt băng", 0.4)

        rung = 0.0
        if self.player.so_hai > 32.0:
            rung = (self.player.so_hai - 32.0) / 68.0 * 2.6
        if bi_san:
            rung += 1.4
        self.camera.cap_nhat(
            self.player.cx, self.player.cy,
            *self.level.kich_thuoc_pixel(),
            rung=rung,
        )
        if self.thong_bao_t > 0:
            self.thong_bao_t -= dt
        if self.gioi_thieu_t > 0:
            self.gioi_thieu_t -= dt
        if self.flash_doi_song > 0:
            self.flash_doi_song -= dt

        self._bi_san = bi_san

    def ve_choi(self):
        self.level.ve(self.man, self.camera, self.tan_so)
        for it in self.level.items:
            d = khoang_cach(it.cx, it.cy, self.player.cx, self.player.cy)
            it.ve(self.man, self.camera, self.tan_so, dist_player=d)
        for sf in self.level.safes:
            sf.ve(self.man, self.camera, self.tan_so, self.ui.f_so)
        for e in self.level.enemies:
            e.ve(self.man, self.camera, self.tan_so)
        self.player.ve(self.man, self.camera, self.tan_so)

        # Overlay AM / tín hiệu màn 1
        if self.tan_so == AM:
            do = 0.55 if not self.cuong_che else 0.85
            self.ui.ve_nhieu_tinh(self.man, do, do_do=self.cuong_che)
            # Vignette đỏ mỏng
            red = pygame.Surface((RONG, CAO), pygame.SRCALPHA)
            red.fill((80, 0, 0, 45 if not self.cuong_che else 80))
            self.man.blit(red, (0, 0))
        elif self.level.so == 1:
            d = self.level.khoang_cach_bang_an(self.player.cx, self.player.cy)
            if d < BAN_KINH_TIN_HIEU:
                suc = 1.0 - d / BAN_KINH_TIN_HIEU
                if random.random() < suc * 0.55:
                    flash = pygame.Surface((RONG, CAO), pygame.SRCALPHA)
                    flash.fill((255, 255, 255, int(25 + 90 * suc)))
                    self.man.blit(flash, (0, 0))
                self.ui.ve_nhieu_tinh(self.man, suc * 0.45)

        if self.flash_doi_song > 0:
            a = int(180 * (self.flash_doi_song / 0.16))
            f = pygame.Surface((RONG, CAO), pygame.SRCALPHA)
            f.fill((200, 200, 220, a) if self.tan_so == FM else (180, 40, 40, a))
            self.man.blit(f, (0, 0))

        # Overlay sợ hãi: vignette đập theo nhịp tim
        so = self.player.so_hai / SO_HAI_TOI_DA
        if so > 0.22:
            nhip = 0.55 + 0.45 * math.sin(self.player.tho * (1.6 + 1.8 * so))
            a = int((so - 0.18) * 110 * nhip)
            so_surf = pygame.Surface((RONG, CAO), pygame.SRCALPHA)
            so_surf.fill((40, 0, 0, min(110, a)))
            self.man.blit(so_surf, (0, 0))

        self.man.blit(self.ui.vignette, (0, 0))

        canh_bao = (
            self.level.so == 3
            and not self.cuong_che
            and 0 < self.cuong_che_cd <= 1.5
        )
        self.ui.ve_hud(
            self.man, self.tan_so, self.player, self.level,
            self.cuong_che, canh_bao, getattr(self, "_bi_san", False),
            tam_dung=(self.trang_thai == TAM_DUNG),
        )
        if self.thong_bao_t > 0:
            self.ui.ve_thong_bao(self.man, self.thong_bao)

        goi = "WASD/mũi tên đi  |  SHIFT chạy  |  Q nín thở  |  SPACE FM/AM  |  P tạm dừng"
        if self.level.so == 3:
            goi += "  |  E mở hộp"
        if self.tan_so == AM:
            goi += "   ·  Băng hiện mờ — đứng lên nhặt"
            if self.player.dang_chay:
                goi += "   ! CHẠY — The Void nghe rất xa"
            elif not self.player.ron_ren and self.player.bam_di_chuyen:
                goi += "   ! Đang bước — quái có thể nghe"
        self.ui.ve_goi_y(self.man, goi)

        # Gợi ý mở hộp khi đứng gần
        if self.tan_so == AM:
            for sf in self.level.safes:
                if not sf.da_mo and sf.gan_player(self.player):
                    self.ui.ve_thong_bao(self.man, "E — mở hộp (cần mật mã %d)" % sf.ma)

    def xu_ly_phim(self, su_kien):
        if su_kien.type == pygame.MOUSEBUTTONDOWN and su_kien.button == 1:
            if self.trang_thai == CHOI:
                if self.ui.rect_nut_pause.collidepoint(su_kien.pos):
                    self.tam_dung_choi()
            elif self.trang_thai == TAM_DUNG:
                self.tiep_tuc_choi()
            return
        if su_kien.type != pygame.KEYDOWN:
            return
        k = su_kien.key
        if self.trang_thai == MENU:
            if k in (pygame.K_RETURN, pygame.K_SPACE):
                self.intro_trang = 0
                self.intro_ky = 0.0
                self.trang_thai = COT_TRUYEN
                self.audio.phat_doi_song(AM)
            elif k == pygame.K_ESCAPE:
                self.chay = False
        elif self.trang_thai == COT_TRUYEN:
            than = TRANG_TRUYEN[self.intro_trang][1]
            if k == pygame.K_ESCAPE:
                self.bat_dau_man(1)
            elif k in (pygame.K_RETURN, pygame.K_SPACE):
                if self.intro_ky < len(than):
                    self.intro_ky = float(len(than))
                elif self.intro_trang + 1 < len(TRANG_TRUYEN):
                    self.intro_trang += 1
                    self.intro_ky = 0.0
                    self.audio.phat_tach()
                else:
                    self.bat_dau_man(1)
        elif self.trang_thai == CHOI:
            if k == pygame.K_p:
                self.tam_dung_choi()
            elif k == pygame.K_SPACE:
                self.doi_tan_so(bat_buoc=False)
            elif k == pygame.K_e:
                if self.tan_so == AM:
                    da_xu_ly = False
                    for sf in self.level.safes:
                        kq = sf.thu_mo(self.player)
                        if kq == "mo":
                            self.audio.phat_mo_hop()
                            self.bao("Hộp %d mở — nhặt được băng  (%d/3)" % (sf.ma, self.player.bang), 2.2)
                            da_xu_ly = True
                            break
                        if kq == "thieu_ma":
                            self.bao("Thiếu mật mã %d — tìm mảnh giấy ở FM" % sf.ma, 2.2)
                            da_xu_ly = True
                            break
                        if kq == "da_mo":
                            da_xu_ly = True
                            break
                    if not da_xu_ly and self.level.safes:
                        self.bao("Đứng sát hộp rồi nhấn E", 1.4)
            elif k == pygame.K_ESCAPE:
                self.audio.im_het()
                self.trang_thai = MENU
        elif self.trang_thai == TAM_DUNG:
            if k in (pygame.K_p, pygame.K_RETURN, pygame.K_SPACE):
                self.tiep_tuc_choi()
            elif k == pygame.K_ESCAPE:
                self.audio.im_het()
                self.trang_thai = MENU
        elif self.trang_thai == THANG:
            if k in (pygame.K_RETURN, pygame.K_SPACE):
                self.bat_dau_man(self.level.so + 1)
            elif k == pygame.K_ESCAPE:
                self.trang_thai = MENU
        elif self.trang_thai == CHIEN_THANG:
            if k in (pygame.K_RETURN, pygame.K_SPACE):
                self.trang_thai = MENU
            elif k == pygame.K_ESCAPE:
                self.chay = False
        elif self.trang_thai == THUA:
            if k == pygame.K_r:
                self.bat_dau_man(self.level.so)
            elif k == pygame.K_ESCAPE:
                self.trang_thai = MENU

    async def chay_game(self):
        print("Tần Số Trắng — đang chạy. Đóng cửa sổ hoặc ESC để thoát.")
        self._bi_san = False
        while self.chay:
            dt = self.dong_ho.tick(FPS) / 1000.0
            # Chống dt nhảy vọt khi cửa sổ bị kéo
            if dt > 0.08:
                dt = 0.08
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.chay = False
                else:
                    self.xu_ly_phim(ev)

            keys = pygame.key.get_pressed()

            if self.trang_thai == MENU:
                self.audio.cap_nhat_the_gioi(FM)
                self.ui.ve_menu(self.man, dt)
            elif self.trang_thai == COT_TRUYEN:
                self.audio.cap_nhat_the_gioi(AM)
                self.audio.dat_am_luong_tinh(0.22)
                than = TRANG_TRUYEN[self.intro_trang][1]
                self.intro_ky = min(float(len(than)), self.intro_ky + dt * 38.0)
                self.ui.ve_cot_truyen(
                    self.man, dt, self.intro_trang, self.intro_ky, len(TRANG_TRUYEN)
                )
            elif self.trang_thai == CHOI:
                self.cap_nhat_choi(dt, keys)
                if self.trang_thai == CHOI:
                    self.ve_choi()
            elif self.trang_thai == TAM_DUNG:
                self.ve_choi()
                self.ui.ve_tam_dung(self.man)
            elif self.trang_thai == JUMPSCARE:
                self.jumpscare_t += dt
                self.ui.ve_jumpscare(self.man, min(1.0, self.jumpscare_t / 1.12))
                if self.jumpscare_t >= 1.12:
                    self.trang_thai = THUA
            elif self.trang_thai == THANG:
                self.ui.ve_thang(self.man, self.level, da_xong_het=False)
            elif self.trang_thai == CHIEN_THANG:
                self.ui.ve_chien_thang(self.man)
            elif self.trang_thai == THUA:
                self.ui.ve_thua(self.man)

            pygame.display.flip()
            await asyncio.sleep(0)

        pygame.quit()


def main():
    asyncio.run(Game().chay_game())


if __name__ == "__main__":
    main()
