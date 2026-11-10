# Đối chiếu đề bài và trạng thái local

Nguồn yêu cầu: README.md ở root, mục Scope, TODO Checklist, Step 2 và Submit. Scope yêu cầu **10 case (5 single + 5 multi)** dù phần Submit chỉ nói tối thiểu 5; dùng mức 10 để đáp ứng cả hai. Đánh giá này không thay việc giảng viên chấm bài.

## Đã có và kiểm tra được

- Provider thật đã có raw run và live transcript; xem REPORT B1/B4. Preflight mới nhất bị HTTP 402, không ghi là pass.
- 11 tool, registry và TOOL.md đầy đủ; tool mới `deduplicate_sources`, 12 test cases sau parameterization, có route case G04.
- Baseline v0 và các mốc v1/v2/v3 giữ nguyên. Version log có metric, hypothesis, hash và đường dẫn raw evidence; không đổi tên run cũ thành version mới.
- Base 20/20, group 10/10 ở **cấu hình active đã kiểm chứng**. Các probes/repeats cũng giữ nguyên, không coi là held-out. Snapshot `artifacts/current/` khớp active.
- Có 10 group cases đúng 5 single và 5 contextual multi-turn; chưa thay thế hội thoại thật.
- Có transcript live 5 lượt hỏi lại → đồng ý chuẩn bị → lấy nội dung → preview → hủy; không gọi send. Latest base R08/R14 có lời từ chối thật, đã đọc thủ công, không chỉ dựa no-tool grader.
- Đã chạy lại 151 offline tests: 0 failed, 0 skipped; 1 cảnh báo môi trường LibreSSL. HTTP delivery trong test dùng mock.
- REPORT có Phần A (khả năng/tool/câu hỏi mẫu) và Phần B (phiên bản/evidence/giới hạn). Không chứng nhận lịch sử nộp đúng 16:30 chỉ bằng nội dung file.
- Đã bổ sung `analysis/baseline_failure_review.csv`: đủ R08/R10/R11/R12/R13/R14, kỳ vọng, thực tế và cách khắc phục. Riêng R13 được dataset gắn `wrong_tool` nhưng routing đúng, lỗi quan sát là `wrong_arg_value`; giữ nguyên nhãn gốc và giải thích thay vì sửa benchmark.
- Streamlit khởi động được tại 127.0.0.1:8503; có UI integration tests. Kết quả smoke HTTP ghi trong `analysis/local_ui_smoke.json`.
- Có script kiểm tra hồ sơ offline; xem DEMO_GUIDE.md.

## Còn thiếu hoặc cần xác minh trước khi nói “đủ toàn bộ đề”

1. **Link UI dùng thử từ máy khác.** Chưa có public URL đã xác minh. `localhost` không đáp ứng mục link dùng thử. Có hướng dẫn tunnel trong DEMO_GUIDE; cần mở demo, thử từ máy khác rồi ghi URL/thời điểm vào report. Không tạo link giả.
2. **Description cho mọi tool.** Active `policy`, `paper_text` chưa nêu rõ when/when-not; `timeframe` còn chung chung. Lần thử sửa description bị HTTP 402 và measured_cases=0; proposal chưa áp dụng đã được bỏ khỏi hồ sơ gọn. Khi sửa lại phải có bằng chứng khớp hash mới; không áp điểm 100% cũ cho thay đổi mới.
3. **“Mỗi vòng một thay đổi/một giả thuyết”.** V3 scope có controlled comparison một đoạn prompt; hardening nhiều thay đổi được tách mô tả. Canonical v1 kế thừa từ nhóm gộp sửa prompt và clarify schema; bảng lịch sử có các bước trung gian nhưng không phải tất cả đều cùng provider. Nêu minh bạch và để nhóm/giảng viên xác nhận cách tính vòng; không tái tạo baseline giả hay sửa lịch sử để đủ tiêu chí.
4. **Provider hiện tại:** preflight và hai run đề xuất bị HTTP 402 (ngân sách/token mặc định), chưa phải model sai. Cần xử lý hạn mức hoặc bổ sung giới hạn output token có kiểm thử trước khi demo/chạy mới. Không tiếp tục retry hàng loạt khi lỗi này còn tồn tại.

## Bonus — không phải phần bắt buộc còn thiếu

- Ollama >=2 model <=8B và >=2 vòng tối ưu: chưa làm, không báo điểm local-model.
- UI + hơn 3 tool tự viết mới: hiện chỉ có 1 tool mới; không đủ bonus này.
- Poster HTML/SVG: tùy chọn, markdown Part A đã có.
- Gửi Telegram thật: chưa chứng minh delivery thực tế. Giữ luồng consent và tests, không gửi tin chỉ để có evidence nếu chưa được người dùng yêu cầu.

## Dọn dẹp và bảo toàn

Đã bỏ các run/transcript trung gian được thay thế, bảng parse trùng, samples, proposal chưa áp dụng và hồ sơ đóng gói phụ. Giữ 15 raw run, 3 transcript và bảng analysis/experiment_history.csv với toàn bộ metric/hash của các lần thử, kể cả fail. Giữ .env/.venv ở local và ignore trên Git. Dọn bằng commit thường trên phattran, không rewrite history hoặc thay main. Các file cũ đã commit có thể khôi phục từ lịch sử Git; có backup ngoài repo cho cả file chưa commit.

Đợt dọn tiếp: xóa toàn bộ raw trong runs/rejected, stability v1 thất bại, baseline OpenRouter trùng, các bước v1 trung gian và run/transcript local v2 đã được thay thế; giữ raw baseline v0, mốc v1 chung và đối chứng v2-control dù có case FAIL vì cần cho so sánh. Transcript từ chối tác vụ ngoài phạm vi hoặc xác nhận hủy đúng yêu cầu không được coi là thất bại.
