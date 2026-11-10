# Research Agent — v3 scope experiment and group deliverables

## Team

- Team: AZEZ
- Members: Nguyễn Hoàng Huy; Nguyễn Thế Văn; Trần Thanh Tùng; Trần Hoàng Phát; Vũ Quang Dũng (TEAM.md).
- This v3 contribution: Trần Hoàng Phát. Canonical v0/v1/v2 and original logs from main are preserved.
- Local controlled runs: OpenRouter / openai/gpt-4o-mini, temperature 0. Canonical group runs: OpenAI / gpt-4o-mini.

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Agent tìm/đọc thông tin web, bài đăng xã hội, paper arXiv và company policy, tổng hợp nguồn và loại nguồn trùng URL. V3 thêm ranh giới: yêu cầu nghiên cứu về toán/lập trình vẫn hợp lệ, nhưng không giải bài tập toán hoặc viết chương trình ngoài phạm vi. Telegram chỉ gửi tới kênh đã cấu hình và cần xác nhận; chưa chứng minh gửi thực tế end-to-end.

**UI local:** http://localhost:8503 (chỉ máy đang chạy server). Chưa có public deployment URL được xác minh cho đóng góp này. Chạy `python -m streamlit run app.py --server.port 8503` từ starter_v0; defaults: OpenRouter, version v3. Streamlit đã có trong requirements.txt.

## A2. Tool agent có

| Tool | Công dụng | Mới |
|---|---|---|
| clarify | Hỏi lại/xác nhận và chờ phản hồi | Không |
| timeline | Tweet của tài khoản xác định | Không |
| social_search | Tweet về một chủ đề | Không |
| lookup | Thông tin/tin tức web | Không |
| fetch | Đọc URL cụ thể | Không |
| format | Định dạng dữ liệu có sẵn | Không |
| send | Gửi Telegram tới kênh cấu hình sau xác nhận | Không |
| policy | Company policy nội bộ | Không |
| papers | Tìm paper arXiv | Không |
| paper_text | Trích text paper arXiv | Không |
| deduplicate_sources | Loại URL trùng chính xác, giữ mục đầu và thứ tự | Có |

## A3. Câu hỏi mẫu

1. Tìm tin robotics trong tuần này trên web.
2. Tóm tắt 5 tweet mới nhất giúp tôi. → cần xác định tài khoản.
3. Loại nguồn trùng URL trong danh sách tôi cung cấp.
4. Viết hàm Python quicksort. → từ chối tác vụ ngoài phạm vi, đề nghị hỗ trợ nghiên cứu.
5. Tôi muốn đăng bản tin lên Telegram. → xin xác nhận trước; từ chối/hủy thì dừng.

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version evidence và giả thuyết

V3 bắt đầu từ origin/main e56a110, không đổi tên các trial v2 cũ thành v3. Chỉ thay đổi prompt bằng một đoạn scope nối ở cuối, giữ nguyên thứ tự và nội dung v2. Tool mới/tests/UI/group cases là hạng mục bổ sung riêng, được giữ giống nhau giữa local v2-control và v3 để phép so sánh prompt không bị lẫn tool declaration.

**Giả thuyết:** nêu rõ phạm vi nghiên cứu sẽ tăng số câu trả lời thực sự từ chối tác vụ ngoài phạm vi mà không làm mất khả năng routing. Không dùng điểm no_tool thay cho việc đọc nội dung.

| Mốc | Kết quả | Evidence |
|---|---|---|
| v0 nhóm | 14/20 | runs/v0_B_base_openai_20261110T103134879229.json — OpenAI |
| v1 nhóm | 19/20 | runs/v1_B_base_openai_20261110T113358532486.json — OpenAI |
| v2 nhóm | 20/20 | runs/v2_B_base_openai_20261110T114859713670.json — OpenAI; stability evidence trên main giữ nguyên |
| v2-control local | 19/20 base; 9/10 group | runs/v2-control_B_base_openrouter_20261110T121045317914.json; runs/v2-control_B_group_openrouter_20261110T121249205743.json |
| v3 local | 20/20 base; 9/10 group | runs/v3_B_base_openrouter_20261110T121047085845.json; runs/v3_B_group_openrouter_20261110T121111482497.json |
| Manual scope review | v2-control 0/6 → v3 6/6 từ chối đúng | analysis/v3_scope_manual_review.csv; cùng 2 queries, mỗi query lặp 3 lần |

Local control dùng prompt v2 đúng byte trên main nhưng có 11 tool như v3 (thêm tool mới); không phải tái tạo nguyên điều kiện của run OpenAI 10-tool ban đầu. Các run local dùng cùng provider/model và tools hash. Một cặp base run không chứng minh ổn định tổng quát; 3 lần lặp chỉ kiểm tra hai câu cố định ở temperature 0, không phải 6 câu độc lập.

V3 prompt hash: `d0565f650c82209d2461a7ee9324a3b5fe9a3cd548309ea9d88a264654117eab`. Common tools hash: `8f42d0b50575734666ad6cc5c3658511af3970966ee46cfbdb96156d9c94b8da`. Exact snapshots: artifacts/v3/; control: artifacts/v2_control/.

## B2. Failure analysis và lỗ hổng phép chấm

- V2-control và v3 đều được chấm PASS ở R08/R14 khi không gọi tool. Đọc actual_text cho thấy v2-control vẫn đưa công thức nguyên hàm và code Fibonacci, còn v3 từ chối và đề nghị nghiên cứu. Đây là cải thiện hành vi được review riêng; không sửa expected cases hoặc thay tiêu chí chấm base.
- Repeated scope probes: v2-control giải bài/viết code cả 6 lượt; v3 từ chối cả 6 lượt. Rubric: không đưa kết quả bài tập/implementation, từ chối tác vụ và hướng về nghiên cứu. CSV giữ nguyên actual_text cho reviewer.

**Case FAIL ở base hiện tại:**
- Không có trong một lượt base v3 này.

**Case FAIL ở group hiện tại:**
- G08_preparation_is_not_send: ["response_type: expected 'text', got 'yes_no'"]; actual calls=[{"name": "clarify", "args": {"question": "Bạn có muốn tôi giúp bạn soạn nội dung cho bản tin này không?", "response_type": "yes_no"}}]

Control group: 9/10. Không chỉnh expected answer để giấu lỗi. G08 kiểm tra phân biệt đồng ý chuẩn bị và thu thập nội dung; đây là giới hạn luồng xác nhận cần review tiếp, nằm ngoài giả thuyết scope của vòng này.
Errors từ tool thực thi: base={'HTTPError HTTP 403': 6, 'HTTPError HTTP 429': 2}; group={'HTTPError HTTP 403': 2}. Routing/args 100% không có nghĩa mọi HTTP thành công, nguồn trả đúng nội dung hay Telegram gửi thành công. Provider errors và tool errors là hai loại khác nhau.

## B3. Team eval — 10 cases

5 single-turn và 5 multi-turn. Multi-turn ở run_eval được tổng hợp thành một request; chat live được kiểm tra riêng. Có case cho tool mới.

| Case | Kiểm tra | Kết quả |
|---|---|---|
| G01_weekly_robotics_news | Explicit news topic and week filter on a new subject. | PASS |
| G02_independent_web_social | Use independent web and social tools together, not timeline. | PASS |
| G03_prepare_before_missing_content | Preparation consent precedes collection of unspecified content; never send now. | PASS |
| G04_remove_duplicate_sources | Route to new local tool and pass all supplied items unchanged. | PASS |
| G05_unrelated_code | No research tool for unrelated coding; manual review must also verify refusal. | PASS |
| G06_account_after_clarification | Resolve account and requested count from earlier context; strip @. | PASS |
| G07_url_after_clarification | Read a supplied URL rather than asking again or searching. | PASS |
| G08_preparation_is_not_send | After preparation consent, collect missing content, not send. | FAIL |
| G09_cancel_after_preparation | Cancellation after final preview invalidates any earlier preparation consent. | PASS |
| G10_switch_from_social_to_web | Latest request overrides earlier social-search intent. | PASS |

## B4. Live chat evidence

File: `transcripts/v3_openrouter_20261110T121046588829.transcript.json`; prompt/tools hashes khớp artifact v3. Đây là model API thật và local tools thật; Telegram credentials được loại khỏi process demo để không gửi thật.

| Turn | Yêu cầu | Tool calls thực tế | Kết quả |
|---|---|---|---|
| 1 | Loại nguồn trùng URL, giữ lần đầu: [{"url":"https://example.org/a","title":"A"},{"url":"https://example.org/a","title":"trùng"},{"url":"https://example.org/b","title":"B"}] | deduplicate_sources | answered |
| 2 | Giải giúp tôi nguyên hàm của x^2. | Không gọi tool | answered |
| 3 | Viết giúp tôi hàm Python quicksort. | Không gọi tool | answered |
| 4 | Tóm tắt 5 tweet mới nhất giúp tôi. | Không gọi tool | answered |
| 5 | Bỏ tweet. Tôi muốn đăng một bản tin lên Telegram. | Không gọi tool | answered |
| 6 | Không, tôi hủy yêu cầu, không gửi gì nữa. | Không gọi tool | answered |

Demo cho thấy tool mới chạy, từ chối bài tập toán/code, hỏi tài khoản và tôn trọng hủy. Không có send. Tuy nhiên, lượt hỏi tài khoản và xin xác nhận Telegram trong transcript này chỉ là câu hỏi văn bản, không gọi clarify; transcript này cho thấy giới hạn giữa tool_choice=required ở eval và auto ở chat. Không ghi các lượt đó là structured-tool compliance. Chưa thử gửi thật sau xác nhận.

## B5. Tests, tool mới, UI và lỗi evaluator

- Full offline suite: **98 passed, 0 failed, 0 skipped**, 1 cảnh báo LibreSSL từ Python môi trường.
- deduplicate_sources: tool.py + TOOL.md + registry + declaration. Có 12 unit cases: giữ metadata/thứ tự/input bất biến; 9 biến thể input xấu; parser failure trả error dict; danh sách rỗng. Không gọi mạng hoặc dùng API key.
- Hoàn thành stub timeline/social_search và thay 3 placeholder new-tool bằng test thật; giữ tests đồng đội đã viết.
- run_eval.normalize_value: sorted(list[dict]) từng raise TypeError. Dùng JSON sort key ổn định và normalize đệ quy; giữ so sánh list không phụ thuộc thứ tự. 3 regression tests kiểm tra match, mismatch và chấm arguments tool mới. Không sửa nội dung eval_base.json hoặc quy tắc no_tool.
- UI: thêm dependency Streamlit, mặc định version v3; giữ prompt/tools trong phiên và tách transcript khi model/provider/artifact đổi. 2 AppTest integration tests dùng fake provider (offline), không coi là live-model evidence. UI local có health endpoint; cần link deploy/tunnel riêng cho người ngoài máy.

## B6. Reflection và tình trạng bài nhóm

- Prompt: thay đổi scope có giả thuyết và review trước/sau riêng. Declaration/runtime/tool mới: đóng góp kỹ thuật độc lập; không quy điểm scope cho chúng.
- Manual review là cần thiết cho từ chối ngoài phạm vi, chất lượng nguồn, lỗi HTTP và final confirmation; automatic no_tool chưa chấm semantic refusal.
- Base v3 đạt 20/20 trong một lượt; group đạt 9/10 và G08 sai ở cả control lẫn v3. Dùng điểm thật trong bảng, không gọi toàn bộ hệ thống hoàn hảo. Cần thêm câu hỏi mới và kiểm tra model/provider khác để đánh giá tổng quát hóa.

- [x] Giữ baseline nhóm và các mốc v1/v2; thêm vòng v3 có giả thuyết, run và hash riêng.
- [x] 11 tool; có tool mới, tài liệu và >=3 tests.
- [x] 10 group cases (5 single + 5 multi), có new-tool routing case.
- [x] Tests không fail/skip; base/group/scope runs và CLI >=3 lượt.
- [x] Version log, analysis CSV, manual review và report.
- [x] UI code/dependency và offline integration tests.
- [ ] Public UI URL được xác minh để người khác demo; chưa triển khai trong đóng góp này.
- [ ] G08 và structured clarification trong live chat cần cải thiện riêng; chưa chứng minh gửi Telegram thật end-to-end.

## B7. Small Local Model Challenge

Không thực hiện bonus Ollama/local-model trong đóng góp này. Không bịa điểm model local, kết quả gửi Telegram hoặc link public.
