# Tần Số Trắng (White Noise Frequency)

Game kinh dị 2D top-down viết bằng **Pygame**. Toàn bộ đồ họa vẽ bằng `pygame.draw`, toàn bộ âm thanh (nhiễu radio, tạch tạch, beep) tự sinh bằng `pygame.mixer` + module `array` — **không cần file PNG/MP3/WAV**.

## Chạy trên Thonny

1. Mở **Thonny**.
2. Cài Pygame (1 lần): **Tools → Manage packages…** → gõ `pygame` → **Install**.
3. Mở `game.py` → **Run** (`F5`).

Hoặc double-click `CHOI.bat`.

Cửa sổ: **800×600**, **60 FPS**.

## Chơi trên web (Railway)

https://tansotrang-production.up.railway.app

Bản trình duyệt dùng cùng `game.py` (đóng gói pygbag). Mở link, **bấm vào khung game** để bắt đầu (trình duyệt cần thao tác đó mới bật tiếng). Lần đầu có thể chờ 30–60 giây để tải Python WASM. Phím giống bản desktop.

## Phím

| Phím | Việc |
| --- | --- |
| **WASD** hoặc **mũi tên** | Di chuyển |
| **SHIFT** (giữ) | Chạy — nhanh, tốn **thể lực**, The Void nghe rất xa |
| **Q** (giữ) | Nín thở / rón rén — chậm, tốn thể lực, khó bị nghe |
| **SPACE** | Đổi tần số **FM** (thế giới thực, an toàn) ↔ **AM** (thế giới song song, có quái) |
| **E** | Mở Hộp An Toàn (màn 3) |
| **P** | Tạm dừng / tiếp tục (hoặc click nút góc phải HUD). Phòng nhiều người: chỉ chủ phòng |
| **T** | Tạo nick / đăng nhập |
| **N** | Nhiều người (cần nick) |
| **ENTER** | Bắt đầu / qua màn |
| **R** | Chơi lại khi Game Over |
| **ESC** | Về menu / thoát |

## Nick và nhiều người

Trên menu: **T** tạo nick (3–16 ký tự) và mật khẩu, **F2** đổi giữa tạo nick và đăng nhập. **N** vào sảnh: **F1** tạo phòng (mã 4 ký tự) hoặc gõ mã rồi **ENTER** để vào. Tối đa 4 người. Trong phòng mỗi người bấm **SẴN SÀNG** (hoặc phím **S**). Khi đủ người, chủ phòng bấm chữ **START** thì ván mới bắt đầu.

- Thấy đồng đội cùng tần số; người ở tần số kia hiện bóng mờ.
- Băng cassette, mật mã và hộp an toàn dùng chung. Pin và thể lực của từng người.
- Quái do chủ phòng điều khiển, nên cả phòng thấy cùng một The Void.
- Ai còn sống đứng lên Trạm phát thanh ở FM khi đủ 3 băng thì cả phòng qua màn.
- Chết thì xem đồng đội chơi tiếp. Cả nhóm chết thì Game Over — chủ phòng bấm **R**.

Bản web và bản Thonny vào cùng phòng trên https://tansotrang-production.up.railway.app. Nick lưu trên máy chủ.

## Cơ chế chung

- **Pin** tụt khi ở AM, kể cả lúc sự cố đài màn 3. Hết pin bị ép về FM và **làm chậm**. Nhặt viên **pin xanh** ở FM để hồi. Màn 3 rải nhiều pin hơn vì mê cung rộng.
- **Thể lực** (thanh TL): chạy và nín thở đều tốn. Hết thể lực thì **thở gấp** — The Void nghe thấy. Đứng yên để hồi; sợ hãi làm hồi chậm hơn.
- **Sợ hãi**: tăng khi ở AM, gần / bị The Void săn. Nhân vật run, mắt mở to, màn hình đập theo nhịp tim.
- Quái **mù**: chỉ đuổi nếu bạn **di chuyển mà không nín thở (Q)** khi đứng gần. Chạy thì bị nghe từ xa. Đứng yên hoặc nín thở thì chúng không nghe thấy (trừ khi hết hơi).
- Ô sàn có dấu **+** đi được **cả hai** thế giới — đứng đây rồi SPACE để nhảy số khi tường bên kia chặn.

## 3 màn

1. **Tín hiệu rời rạc** — Lưới 12×9 phòng học. 3 băng cassette **vô hình**. Ở FM, lại gần vị trí ẩn: màn hình nhấp nháy + tiếng tạch tạch nhanh dần. Nhảy AM để nhặt, về FM né quái, chạy vào **Trạm phát thanh**.
2. **Mê cung không gian kép** — Lưới 16×12. Tường đá ở FM thành lối ở AM (và ngược lại). Nhảy SPACE luồn địa hình, lấy 3 băng, thoát.
3. **Dịch mã & cưỡng chế AM** — Lưới 40×30. Nhặt 3 mảnh mật mã (số 2 chữ số, **đổi mỗi lần chơi**) trên tường **FM**, mở 3 hộp an toàn ở **AM** (phím E). Cứ khoảng 10 giây đài hỏng: **ép sang AM ~4.4 giây, khoá SPACE**. Phải **giữ Q và đứng yên**. Nhúc nhích 1 px là quái lao tới.

Mục tiêu mỗi màn: **3 băng cassette** + đứng lên Trạm phát thanh ở **FM**.
