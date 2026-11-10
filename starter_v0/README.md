# Research Desk — phần đã triển khai

Chạy các lệnh dưới đây trong `starter_v0/`, bằng PowerShell.

## Mở UI

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Mở http://localhost:8501. Link demo tạm thời hiện có trong `artifacts/REPORT.md`.
Tab **Công cụ offline** chạy ngay, không gọi Gemini.
Tab **Trò chuyện** cần quota model; UI tự lưu transcript thật vào `transcripts/`
và cho tải JSON. Các lỗi API vẫn được hiển thị và ghi lại, không được đổi thành
kết quả thành công. Một lần preflight gần nhất báo model đã hết quota ngày.

Để cho máy khác dùng thử sau khi UI hoạt động:

```powershell
cloudflared tunnel --url http://localhost:8501
```

Lệnh này cần cài `cloudflared` riêng. Dán URL thật trả về vào REPORT Phần A và
giữ UI/tunnel chạy trong buổi demo. Hiện chưa có deployment public.

## Kiểm tra không cần API

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

Tool mới: `deduplicate`, có implementation, TOOL.md, registry, schema và unit
test. `data/eval_group.json` có 10 case, gồm 5 single-turn + 5 multi-turn.

## Chạy eval khi quota hồi lại

Baseline đầy đủ đã chạy trên **`gemini-3.5-flash-lite`**: 13/20 case đạt
(65%), không có provider_error. Run:
`runs/v0_B_base_gemini_20261110T113128259559.json`.
Giữ cùng model này ở các vòng tiếp theo để so sánh hợp lệ; model mặc định
`gemini-3.5-flash` trước đó đã hết quota ngày.

**Artifacts mặc định hiện là bản v3 đã chuẩn bị.** Để chạy v0/v1/v2/v3 đúng
nội dung, dùng snapshot qua script dưới đây; không chỉ đổi nhãn `--version`
trong khi vẫn dùng cùng prompt/tools mặc định.

```powershell
.\.venv\Scripts\python.exe scripts/run_versions.py --versions v1 --model gemini-3.5-flash-lite
.\.venv\Scripts\python.exe scripts/run_versions.py --versions v2 --model gemini-3.5-flash-lite
.\.venv\Scripts\python.exe scripts/run_versions.py --versions v3 --include-group --model gemini-3.5-flash-lite
```

Mỗi version hiện là **giả thuyết chưa kiểm chứng**, không phải cải tiến đã đo
được. Sau mỗi lượt, xem run JSON và điều chỉnh snapshot tiếp theo nếu cần.
V0 gốc được giữ nguyên; v1 làm rõ scope/routing, v2 sửa hỏi lại/xác nhận, v3 sửa
convention args và carryover. Kế hoạch ở `artifacts/versions/plan.json`.

Script dừng nếu còn provider_error và chỉ ghi CSV từ các run thực. Có thể thêm
`--model <model>` nếu chủ động đổi model; nên lấy lại baseline cho model đó.
Không chạy nhiều process cùng dùng quota của một project/model.

Xem lệnh mà không gọi API:

```powershell
.\.venv\Scripts\python.exe scripts/run_versions.py --versions v0 v1 v2 v3 --include-group --dry-run
```

Tổng hợp lại log đã có, không tốn quota:

```powershell
.\.venv\Scripts\python.exe scripts/summarize_evidence.py
```

## Chat live và phần nộp còn thiếu

```powershell
.\.venv\Scripts\python.exe chat.py --provider gemini --version v3 --model gemini-3.5-flash-lite
```

Thực hiện tối thiểu 3 lượt bằng model thật; giữ transcript JSON. Khi có một
bản nháp Telegram đang chờ, CLI yêu cầu nhập `xác nhận`/`yes` để gửi đúng nội
dung đã xem, hoặc `hủy`/`no` để hủy. UI có nút xác nhận/hủy riêng. Telegram là
bonus; không có token/chat ID thì không thể gửi.

Các việc còn cần kết nối/API: đo v1–v3 trên cùng model của baseline, chạy group eval, chat
live, kiểm tra quyền Twitter API45 (log hiện có HTTP 403), tạo link public và
cập nhật REPORT bằng bằng chứng thực. Thông tin nhóm còn để người nộp điền.
Không nộp `.env` hoặc API key.
