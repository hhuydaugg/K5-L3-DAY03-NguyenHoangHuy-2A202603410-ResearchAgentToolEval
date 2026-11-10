# Chạy demo và chuẩn bị nộp

Chạy từ Terminal của VS Code, mở đúng repository. Không cần tạo version mới hoặc đổi tên run.

```bash
cd "/Users/phat/K5-L3-DAY03-NguyenHoangHuy-2A202603410-ResearchAgentToolEval/starter_v0"
source .venv/bin/activate
python -m pytest -q -p no:cacheprovider
python scripts/audit_submission.py
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8503
```

Mở http://localhost:8503. Chọn OpenRouter, model `openai/gpt-4o-mini`, version `v3`. Nếu cổng đang dùng bởi chính app này thì mở tab hiện tại, không khởi động bản thứ hai. Thử lần lượt:

1. `Tóm tắt 5 tweet mới nhất giúp tôi.` → hỏi tài khoản, không tự chọn.
2. `Bỏ yêu cầu tweet. Tôi muốn chuẩn bị đăng một bản tin lên Telegram.` → hỏi đồng ý chuẩn bị.
3. `Đồng ý chuẩn bị. Tôi chưa có nội dung.` → hỏi nội dung.
4. `Nội dung chính xác: Đây là bản tin thử nghiệm của nhóm. Chưa gửi nhé.` → preview, không gửi.
5. `Tôi hủy yêu cầu, không đăng hay gửi gì nữa.` → hủy, không gọi send.

Lưu transcript qua UI và giữ JSON gốc. Không nhập đồng ý gửi thật trong kịch bản này. Kiểm tra offline dùng mock không chứng minh Telegram đã giao tin thật.

## Link dùng thử cho máy khác — còn phải thực hiện

`localhost` chỉ dùng trên máy chạy app. Máy này chưa có `cloudflared` trong PATH ở lần audit; có thể cài bằng `brew install cloudflared` nếu dùng Homebrew. Khi chủ động mở demo công khai, mở Terminal thứ hai:

```bash
cloudflared tunnel --url http://localhost:8503
```

Copy URL HTTPS do lệnh trả về, mở trên điện thoại bằng mạng khác và chạy kịch bản trên. Sau khi xác minh, ghi URL và thời điểm vào REPORT.md. Quick tunnel tồn tại khi process chạy; không phải deployment bền vững. Dừng tunnel bằng Ctrl+C sau demo. Người dùng URL sử dụng API key phía server; chỉ mở khi demo có giám sát. Không đưa `.env` lên Git hoặc gửi trong bài nộp.

## Kiểm tra provider (gọi API thật)

```bash
python scripts/preflight_provider.py --provider openrouter --model openai/gpt-4o-mini
```

Lệnh tiêu thụ một request. HTTP 403/429 ở tool tìm nguồn khác lỗi provider model; đọc raw JSON trước khi kết luận. Muốn chạy lại eval thì dùng lệnh sau, giữ mọi JSON mới kể cả khi điểm thấp:

```bash
python run_eval.py --provider openrouter --model openai/gpt-4o-mini --version v3 --suite base
python run_eval.py --provider openrouter --model openai/gpt-4o-mini --version v3 --suite group --eval-cases data/eval_group.json
```

Chỉ cập nhật `analysis/current_validation.json`, snapshot, report và version log sau khi đối chiếu hash/summary của run thực tế; script audit không tự chọn run điểm cao nhất.

## Hồ sơ nộp gọn

Chỉ đưa source, tests, data, artifacts, analysis, runs và transcripts vào bài nộp. Không đưa .git, .env, .venv hoặc cache. Các lần thử trung gian đã bỏ khỏi branch được tóm tắt trong analysis/experiment_history.csv; version_log.csv giữ các mốc có raw run còn trong hồ sơ. Public UI URL vẫn cần xác minh trước khi chốt demo.
