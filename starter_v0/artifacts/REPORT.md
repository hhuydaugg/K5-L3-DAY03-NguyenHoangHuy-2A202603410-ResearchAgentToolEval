# Day 03 — Research Agent: v2 contribution and group evidence

## Team

- Team: AZEZ
- Members: Nguyễn Hoàng Huy; Nguyễn Thế Văn; Trần Thanh Tùng; Trần Hoàng Phát; Vũ Quang Dũng (see TEAM.md).
- This contribution: Trần Hoàng Phát, local v2; group v0/v1/v2 evidence is retained.
- Local provider/model: OpenRouter / openai/gpt-4o-mini. Group canonical runs use OpenAI / gpt-4o-mini.

# PHẦN A — Giới thiệu agent

## A1. Agent làm được gì

Agent tìm thông tin web, bài đăng xã hội, paper arXiv và company policy; đọc nguồn, tổng hợp digest và loại nguồn trùng URL. Telegram chỉ hỗ trợ kênh đã cấu hình trên server và cần xác nhận theo luồng trong prompt. API đọc nguồn có thể lỗi, nên agent chưa bảo đảm nghiên cứu end-to-end thành công.

**Link local đã kiểm tra:** http://localhost:8503 — chỉ dùng trên máy đang chạy UI. Chưa có public deployment URL được xác minh cho đóng góp này; cần triển khai/tunnel khi demo cho nhóm.

Run UI: `python -m streamlit run app.py --server.port 8503` from starter_v0. Provider mặc định OpenRouter; version v2. Đổi model/provider/artifact tạo phiên transcript mới để tránh lẫn bằng chứng.

## A2. Tools

| Tool | Công dụng | Mới trong đóng góp này |
|---|---|---|
| clarify | Hỏi thông tin thiếu hoặc xác nhận và chờ người dùng | Không |
| timeline | Bài đăng của một tài khoản xác định | Không |
| social_search | Tweet về một chủ đề | Không |
| lookup | Thông tin/tin tức web với topic và timeframe | Không |
| fetch | Đọc URL cụ thể | Không |
| format | Định dạng dữ liệu có sẵn | Không |
| send | Gửi nội dung đã xác nhận tới kênh Telegram cấu hình | Không |
| policy | Tìm company policy nội bộ | Không |
| papers | Tìm paper arXiv | Không |
| paper_text | Trích text paper arXiv | Không |
| deduplicate_sources | Loại URL HTTP(S) trùng chính xác, giữ mục đầu và thứ tự | Có |

## A3. Câu hỏi mẫu

1. Tìm tin robotics trong tuần này trên web.
2. Tóm tắt 5 tweet mới nhất giúp tôi. → agent cần hỏi tài khoản.
3. Tìm tin AI hôm nay trên web và tweet về AI.
4. Tôi muốn chuẩn bị đăng bản tin lên Telegram; chưa gửi.
5. Loại nguồn trùng URL trong danh sách nguồn tôi cung cấp.

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version evidence

Không đánh số lại JSON lịch sử. Các run v2 local mang nhãn v2 ngay lúc chạy; các lần thay đổi trong vòng này là thử nghiệm để hoàn thiện v2, không tự chuyển v3. Main cũng có v2 của Huy; không ghi đè hay xóa dòng log của nhóm.

| Mốc | Kết quả | Điều kiện / file |
|---|---|---|
| v0 nhóm | 14/20 | OpenAI; runs/v0_B_base_openai_20261110T103134879229.json |
| v1 nhóm | 19/20 | OpenAI; runs/v1_B_base_openai_20261110T113358532486.json |
| v2 nhóm trên main | 20/20 | OpenAI; runs/v2_B_base_openai_20261110T114859713670.json; stability evidence của nhóm được giữ nguyên |
| v2 Phát — base hiện tại | 19/20 (95% of measured cases) | runs/v2_B_base_openrouter_20261110T120531922498.json; OpenRouter |
| v2 Phát — group hiện tại | 10/10 (100% of measured cases) | runs/v2_B_group_openrouter_20261110T120457782521.json; measured=10, provider_errors=0 |
| v3 | Chưa thực hiện trong đóng góp này | Vẫn là yêu cầu của bài nhóm |

**Giả thuyết tổng thể của v2 local:** một contract thống nhất giữa prompt/declaration cho nguồn hiện tại, tham số tường minh và thứ tự xác nhận sẽ giảm tool dư/thiếu và arguments sai. Vòng này có nhiều thay đổi liên quan; không thể quy toàn bộ chênh lệch cho một dòng. New tool, unit tests, UI và sửa grader là các hạng mục kỹ thuật riêng, không được coi là nguyên nhân đã chứng minh của điểm base.

Các trial được giữ trong runs/ và version_log.csv: 65% do starter hashes, 85%, 85%, 90%, 95%, 95% và bản cuối theo file ở trên. Không chọn riêng một run đẹp để tuyên bố ổn định. Lần local 100% lúc 11:02 dùng tools hash khác; không dùng làm bằng chứng cho artifact hiện tại. Không coi OpenAI và OpenRouter là điều kiện giống nhau. Hash nhóm v0 khác starter commit vẫn chưa được giải thích.

Current prompt hash: `1781aa4e966c46bed185bc645473753facdec2cd5a2210d93a2c93faba821487`. Current tools hash: `cfaaf646e3c7eec195699c6dd6b4e718cc936814af8fa9390bee15ef38a6d993`. Exact snapshots: artifacts/v2/.

## B2. Failure analysis

- Trial 85%: R06/R13 thiếu topic=news; R12 dùng clarify(text) thay yes_no. Khôi phục contract tham số và ưu tiên xác nhận trong prompt/declaration.
- Trial 90%: R10 tìm tweet bằng query rỗng thay vì hỏi tài khoản; M06 gọi thêm social_search sau khi đổi sang web. Bổ sung quy tắc nguồn hiện tại và thông tin bắt buộc.
- Trial group đầu: G04 bị ghi provider_error do evaluator gọi sorted() trên list[dict]. Sửa normalize_value bằng JSON sort key ổn định và thêm 3 regression tests; không thay case/expected answer. Đây là lỗi chấm, không phải lỗi provider. Run cũ vẫn được giữ.

**Lỗi model còn lại ở base hiện tại:**
- M06_switch_tool: ['extra tool call social_search']; calls=[{"name": "lookup", "args": {"query": "OpenAI", "topic": "news", "timeframe": "week", "max_results": 5}}, {"name": "social_search", "args": {"query": "OpenAI", "search_type": "Latest", "limit": 5}}]

**Lỗi thực thi tool trong run hiện tại:** base={'HTTPError HTTP 403': 8, 'HTTPError HTTP 429': 1, 'ReadTimeout': 1, 'ConnectionError': 2}; group={'ReadTimeout': 2, 'HTTPError HTTP 403': 2}. Điểm routing/args không đo chất lượng nội dung hoặc thành công HTTP. Không thay đổi eval_base.json hoặc expected answers.

**Manual review ngoài phạm vi:**
- R08_out_of_scope: Xin lỗi, nhưng tôi không thể giải bài toán toán học hoặc viết mã. Tuy nhiên, tôi có thể hướng dẫn bạn cách tìm nguyên hàm của \( x^2 \).

Nguyên hàm của \( x^n \) (với \( n \neq -1 \)) được tính bằng công thức:

\[
\int x^n \, dx = \frac{x^{n+1}}{n+1} + C
\]

Trong trường hợp của \( x^2 \):

\[
\int x^2 \, dx = \frac{x^{2+1}}{2+1} + C = \frac{x^3}{3} + C
\]

Trong đó \( C \) là hằng số tích phân.
- R14_out_of_scope_coding: Xin lỗi, nhưng tôi không thể viết mã cho bạn. Tuy nhiên, tôi có thể hướng dẫn bạn cách viết hàm Fibonacci bằng đệ quy trong Python.

Hàm Fibonacci có thể được định nghĩa như sau:

1. Nếu n là 0, trả về 0.
2. Nếu n là 1, trả về 1.
3. Nếu n lớn hơn 1, trả về tổng của Fibonacci(n-1) và Fibonacci(n-2).

Dưới đây là cấu trúc cơ bản của hàm:

```python
def fibonacci(n):
    if n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)
```

Bạn có thể sử dụng hàm này bằng cách gọi `fibonacci(n)` với n là số bạn muốn tính.

## B3. Team eval cases

10 cases: 5 single-turn và 5 multi-turn context. Multi-turn trong run_eval là hội thoại tổng hợp thành một request, không thay thế chat live.

| Case | Kiểm tra | Kỳ vọng | Kết quả |
|---|---|---|---|
| G01_weekly_robotics_news | Explicit news topic and week filter on a new subject. | lookup | PASS |
| G02_independent_web_social | Use independent web and social tools together, not timeline. | lookup, social_search | PASS |
| G03_prepare_before_missing_content | Preparation consent precedes collection of unspecified content; never send now. | clarify | PASS |
| G04_remove_duplicate_sources | Route to new local tool and pass all supplied items unchanged. | deduplicate_sources | PASS |
| G05_unrelated_code | No research tool for unrelated coding; manual review must also verify refusal. | no_tool + manual review | PASS |
| G06_account_after_clarification | Resolve account and requested count from earlier context; strip @. | timeline | PASS |
| G07_url_after_clarification | Read a supplied URL rather than asking again or searching. | fetch | PASS |
| G08_preparation_is_not_send | After preparation consent, collect missing content, not send. | clarify | PASS |
| G09_cancel_after_preparation | Cancellation after final preview invalidates any earlier preparation consent. | no_tool + manual review | PASS |
| G10_switch_from_social_to_web | Latest request overrides earlier social-search intent. | lookup | PASS |

## B4. Live chat evidence

CLI transcript: `transcripts/v2_openrouter_20261110T120333645944.transcript.json`; hashes match current artifact. Model là API thật; clarify/deduplicate_sources là implementation thật. Telegram credentials bị loại khỏi riêng process demo để không gửi thông điệp ngoài ý muốn. Không mock kết quả model.

| Turn | Yêu cầu | Tool calls thực tế | Trạng thái |
|---|---|---|---|
| 1 | Tóm tắt 5 tweet mới nhất giúp tôi. | clarify | waiting_for_user |
| 2 | Bỏ yêu cầu tweet. Tôi muốn chuẩn bị đăng một bản tin lên Telegram. | clarify | waiting_for_user |
| 3 | Đồng ý chuẩn bị. Nội dung là: "Đây là bản tin thử nghiệm của nhóm". Chưa gửi nhé. | clarify | waiting_for_user |
| 4 | Tôi hủy yêu cầu, không đăng hay gửi gì nữa. | Không gọi tool | answered |
| 5 | Loại nguồn trùng URL, giữ lần đầu: [{"url":"https://example.org/a","title":"A"},{"url":"https://example.org/a","title":"trùng"},{"url":"https://example.org/b","title":"B"}] | deduplicate_sources | answered |

Không có send trong demo hủy. Ở transcript cuối, lượt 3 gọi đúng clarify(yes_no) nhưng câu hỏi không nhắc lại toàn văn nội dung; vì vậy chưa chứng minh yêu cầu final preview đầy đủ. Không gửi thật sau câu hỏi này. Chưa kiểm chứng gửi Telegram thực tế sau final consent. Kiểm tra cả tool_calls và assistant_text: hỏi xác nhận bằng văn bản thuần chưa thỏa yêu cầu gọi clarify. Các lượt đó vẫn là limitation nếu xuất hiện trong transcript cuối, không được ghi PASS chỉ vì câu chữ hợp lý. Nếu model tự lọc items trước deduplicate_sources thì số removed_count không còn phản ánh danh sách người dùng; unit test đúng không thay thế tính đúng của arguments do model gửi.

UI đã kiểm tra local bằng trình duyệt và health 200 trên một trial trước (hash trong UI transcript khác artifact cuối); tool deduplicate_sources thực sự chạy và hiển thị 2 nguồn A/B trong phiên UI. Transcript UI đang lưu trong transcripts/. Hai AppTest integration tests dùng fake provider có ghi rõ offline, kiểm tra lưu clarification/cancellation và tách phiên khi đổi config; không coi chúng là live-model evidence.

## B5. Tool tests và lỗi grader

- Full offline suite: 98 passed, 0 failed, 0 skipped; 1 LibreSSL warning từ môi trường Python. Không sửa môi trường SSL toàn hệ thống trong PR.
- Tool mới có 12 unit cases: happy path/metadata/order/input immutability; 9 bad-input variants; unexpected parser failure returns error dict; empty list. Không cần API key/network.
- Hoàn thành hai stub timeline/social_search còn lại và thay ba placeholder new-tool bằng tests thật; giữ các tests đồng đội đã viết.
- Grader regression: list-of-object arguments từng làm sorted() raise TypeError. 3 tests chứng minh match đúng, mismatch không crash và new-tool case được grade bình thường. Không sửa tiêu chí no_tool hay expected base cases.

## B6. Reflection và checklist

- Prompt chịu trách nhiệm phạm vi, lịch sử, thứ tự consent và dữ liệu nguồn không đáng tin. Declaration chịu trách nhiệm khi dùng/không dùng tool, topic/timeframe/Top/Latest và confirmed.
- No-tool PASS cần manual review nội dung từ chối. HTTP errors và kết quả rỗng cần manual review factual output. Live-model tool use còn cần đánh giá riêng vì base eval ép tool_choice=required cho nhiều case, chat dùng auto.
- Không đồng nhất điểm cao trên 20 case với end-to-end thành công hoặc khả năng tổng quát hóa. Các lượt group được viết trước khi chạy; đây vẫn là bộ nhỏ do nhóm tự tạo.

- [x] Provider preflight OpenRouter thành công.
- [x] Có 11 tool, descriptions và convention tham số rõ.
- [x] Base eval/run JSON với hash đúng; giữ các trial.
- [x] Version log và report có bằng chứng, không đánh số lại run.
- [x] Tool mới + TOOL.md + registry/declaration + >=3 tests.
- [x] 10 group cases, 5 single + 5 multi; có case route tool mới.
- [x] Unit tests không fail/skip; CLI live >=3 lượt; UI chạy local.
- [ ] v3: vẫn cần vòng giả thuyết/thay đổi/đánh giá riêng của nhóm.
- [ ] Public UI URL cho người khác dùng thử: chưa triển khai trong đóng góp này.
- [ ] Live-model clarity và source-switch behavior cần tiếp tục kiểm tra; không tuyên bố hoàn hảo.

## B7. Small Local Model Challenge

Không thực hiện bonus Ollama/local-model trong đóng góp v2 này. Không có kết quả local-model hoặc gửi Telegram thực tế được báo cáo.
