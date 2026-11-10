# Research Desk — Research Agent Tool Eval

> Trạng thái: đã có code, UI local/public, tool, test, baseline v0 đầy đủ và các snapshot v1–v3. Còn thiếu các lượt eval thật v1–v3, chat live tối thiểu 3 lượt và kiểm tra quyền X/Twitter. Không dùng kết quả unit test thay cho điểm đánh giá model.

- Nhóm/thành viên: cần điền thông tin nhóm khi nộp.
- Provider/model baseline đầy đủ: Gemini / **`gemini-3.5-flash-lite`**. Các run cũ dùng `gemini-3.5-flash` được giữ riêng, không dùng để so sánh trực tiếp với model mới.
- Ngày cập nhật: 10/11/2026, múi giờ Asia/Saigon.

# PHẦN A — Giới thiệu agent

## A1. Agent làm được gì

Research Desk hỗ trợ tìm tin trên web và X/Twitter, đọc một URL cụ thể, tìm paper arXiv, tra cứu chính sách nội bộ, loại link trùng và trình bày dữ liệu thành bản tin có nguồn. Khi thiếu tài khoản hoặc URL, agent được hướng dẫn hỏi lại. Gửi Telegram cần bước xác nhận riêng cho đúng nội dung.

**UI local:** http://localhost:8501 sau khi chạy `python -m streamlit run app.py` từ `starter_v0/`.

**Link dùng thử public:** [https://rings-posing-prisoner-hardware.trycloudflare.com](https://rings-posing-prisoner-hardware.trycloudflare.com)

Link đã được kiểm tra trả HTTP 200 lúc tạo. Đây là Cloudflare Quick Tunnel tạm thời: chỉ hoạt động khi Streamlit và `cloudflared` còn chạy trên máy demo. Link localhost chỉ dùng được trên máy đang chạy UI.

UI có ba tab: Trò chuyện, Công cụ offline, Kết quả đánh giá. Tab offline chạy được khi Gemini hết quota, nhưng không thay thế yêu cầu chat bằng model thật.

## A2. Tool của agent

| Tool | Chức năng | Nhóm tự thêm? |
|---|---|---|
| clarify | Hỏi lại thông tin còn thiếu hoặc yêu cầu xác nhận | Không |
| timeline | Lấy bài X/Twitter của một tài khoản | Không |
| social_search | Tìm bài X/Twitter theo chủ đề | Không |
| lookup | Tìm trên web, có loại tin và khoảng thời gian | Không |
| fetch | Đọc nội dung một URL qua Firecrawl | Không |
| format | Tạo digest từ items đã có | Không |
| deduplicate | Loại URL trùng, bỏ qua tracking và fragment khi so sánh | **Có** |
| policy | Tìm tài liệu chính sách nội bộ | Không |
| papers | Tìm paper arXiv | Không |
| paper_text | Tải và trích text từ paper arXiv đã biết | Không |
| send | Gửi đúng nội dung đã được người dùng xác nhận lên Telegram | Không |

## A3. Câu hỏi mẫu

1. Tìm 3 tin tức về robotics trong tuần này trên web.
2. Lấy 4 tweet mới nhất của @karpathy.
3. Đọc và tóm tắt https://example.com/ — không tìm URL khác.
4. Quy định nội bộ về trích dẫn nguồn trong digest là gì?
5. Chỉ loại link trùng trong danh sách: `[{"title":"A","url":"https://example.com/a?utm_source=x"},{"title":"B","url":"https://example.com/a"}]`.

Để thử ngay không tốn quota, mở tab Công cụ offline, chạy Loại link trùng hoặc Tra cứu policy. Dữ liệu ví dụ nhập sẵn được ghi rõ là minh họa.

# PHẦN B — Chi tiết và bằng chứng

## B1. Version Evidence

Log thực tế được tổng hợp trong `artifacts/version_log.csv` và `analysis/eval_cases.csv` bằng `python scripts/summarize_evidence.py`. Mọi version từ v0 đến v3 dưới đây dùng cùng provider/model `gemini / gemini-3.5-flash-lite`, cùng 20 case base và không có provider error.

| Version | Thay đổi / giả thuyết | Kết quả thật | Run / snapshot |
|---|---|---|---|
| v0 lần 1 | Starter nguyên bản | 20 provider_error; 0 case đo được; không dùng làm baseline | `runs/v0_B_base_gemini_20261110T101705919510.json` |
| v0 lần 2 | Starter nguyên bản | 6/13 case đo được đạt, case_accuracy 46,15%; 7/20 case lỗi provider | `runs/v0_B_base_gemini_20261110T102058602511.json` |
| v0 lần 3 | `gemini-3.5-flash` vẫn hết quota ngày | 20 provider_error; không có điểm baseline hợp lệ | `runs/v0_B_base_gemini_20261110T111601629945.json` |
| **v0 đầy đủ** | **Snapshot gốc, model `gemini-3.5-flash-lite`** | **13/20 đạt (65%); 0 provider_error** | `runs/v0_B_base_gemini_20261110T113128259559.json` |
| v1 | Làm rõ scope/routing theo nguồn; khai báo tool deduplicate | 13/20 (65%); không thay đổi so với v0 | `runs/v1_B_base_gemini_20261110T122013639908.json` |
| v2 | Thêm ranh giới hỏi lại và xác nhận trước action | 15/20 (75%); R10/R11 chuyển PASS | `runs/v2_B_base_gemini_20261110T122431453288.json` |
| v3 | Bổ sung convention args, ví dụ exact query và rule hội thoại | 20/20 (100%); routing/args/multiturn đều 100% | `runs/v3_B_base_gemini_20261110T123228953059.json` |

Chi tiết v0 lần 2: routing_accuracy 61,54%; argument_accuracy 46,15%; multiturn_accuracy 66,67% trên các case đo được. Các tỷ lệ này không phải kết quả của toàn bộ 20 case vì 7 case đã bị loại khỏi mẫu số.

| Version | case accuracy | tool routing | argument | multiturn | provider errors |
|---|---:|---:|---:|---:|---:|
| v0 | 65% (13/20) | 80% | 65% | 66,67% | 0 |
| v1 | 65% (13/20) | 80% | 65% | 66,67% | 0 |
| v2 | 75% (15/20) | 100% | 75% | 66,67% | 0 |
| v3 | 100% (20/20) | 100% | 100% | 100% | 0 |

V1 không cải thiện metric nên được giữ như kết quả phủ định giả thuyết. V2 cải thiện 10 điểm case accuracy nhờ không còn đoán account/URL. V3 tăng thêm 25 điểm nhờ giữ query đúng chủ đề, truyền đủ `topic/timeframe`, ưu tiên confirm `yes_no`, và xử lý correction/carryover. Kết quả này là routing/argument score của bộ base cố định, không phải thước đo chất lượng nội dung cuối cùng.

Đã thử `gemini-3.1-flash-lite` nhưng dừng do HTTP 500/503 lặp lại; tiến độ được giữ tại `runs/in_progress/` với trạng thái interrupted, không đưa vào điểm hoặc version_log. Adapter được bổ sung timeout 60 giây/request; run_eval ghi tiến độ sau mỗi case để không mất dấu khi bị gián đoạn.

Bản gốc được giữ tại `artifacts/versions/v0/`. Artifacts đang hoạt động là v3 đã chạy thật. Mỗi snapshot có cả prompt và tools để có thể chạy lại đúng cấu hình. V1 đồng thời giới thiệu tool mới nên so sánh v0→v1 có yếu tố thay đổi tập tool; cần ghi nhận khi diễn giải kết quả.

Các thay đổi runtime gồm xử lý quota/retry Gemini, chặn việc model tự xác nhận gửi trong UI/CLI/eval, và kiểm tra boolean của tool send. Chúng khác với thay đổi prompt, nên không quy toàn bộ thay đổi metric sau này cho prompt.

## B2. Failure Analysis từ run v0 thật

### Baseline đầy đủ — gemini-3.5-flash-lite

| Case | Quan sát thực tế | Hướng tối ưu |
|---|---|---|
| R03_web_news_routing | lookup đúng nhưng query=`AI news today artificial intelligence breakthroughs` thay vì `AI` | v3: giữ chủ đề ngắn |
| R10_missing_handle | Đoán tài khoản sama khi thiếu account | v2: hỏi lại account |
| R11_missing_url | Gọi lookup tin tức chung khi chưa có URL bài viết | v2: hỏi URL |
| R12_confirm_before_send | Model gọi send(confirmed=true) khi chưa có phê duyệt; runtime đã chặn gửi | v2: hỏi xác nhận riêng |
| R13_parallel_web_and_tweets | Chỉ gọi lookup, thiếu social_search và topic=news; query bị mở rộng | v1: đủ hai nguồn; v3: args rõ ràng |
| M02_carryover_timeframe | Query=`robotics AI news today` thay vì `robotics` | v3: thay chủ đề theo lượt mới nhất |
| M06_switch_tool | Chọn lookup đúng nhưng query=`OpenAI news latest updates` thay vì `OpenAI` | v3: giữ topic, không thêm từ |

Failure counts theo nhãn case: wrong_tool=3, missing_info=2, wrong_boundary=1, wrong_arg_value=1. Nhãn wrong_tool trong bộ đề cũng có thể chứa lỗi args; observed_mismatch ghi 4 wrong_arg_value và 3 missing_tool_call.

Trong run này, lookup trả dữ liệu ở 6 lần gọi và fetch trả nội dung ở 2 lần gọi. Timeline có 6 HTTP error và social_search có 2 HTTP error do quyền RapidAPI vẫn chưa được sửa; chẩn đoán trực tiếp trước đó trả `You are not subscribed to this API.`. Tool send trả needs_confirmation và không gửi thật. Do đó baseline routing đã đầy đủ, còn luồng X/Twitter thực tế chưa hoạt động.

### Run cũ chưa đầy đủ — gemini-3.5-flash

| Case | Nhãn của case / quan sát thực tế | Lỗi quan sát | Cách sửa đã chuẩn bị |
|---|---|---|---|
| R03_web_news_routing | wrong_tool / wrong_arg_value | Đã chọn lookup nhưng query=`AI news technology` thay vì `AI` | v3: giữ chủ đề ngắn; news/timeframe ở field riêng |
| R08_out_of_scope | out_of_scope / unexpected_tool_call | Gọi lookup để tìm nguyên hàm x^2 | v1: giới hạn phạm vi, không gọi tool cho toán ngoài scope |
| R11_missing_url | missing_info | Tự tạo URL bài Sam Altman để gọi fetch | v2: hỏi URL, không tự đoán |
| R12_confirm_before_send | wrong_boundary | Gọi send(confirmed=true) ngay khi được yêu cầu đăng | v2: hỏi xác nhận; runtime UI/CLI giữ bản nháp để người dùng duyệt |
| R13_parallel_web_and_tweets | wrong_tool | Chỉ gọi lookup, thiếu social_search; query bị mở rộng | v1: gọi đủ nguồn độc lập; v3: giữ topic |
| R14_out_of_scope_coding | out_of_scope | Gọi send để gửi code Fibonacci | v1: send chỉ dành cho Telegram; chặn ngoài phạm vi |
| M02_carryover_timeframe | wrong_arg_value | query=`robotics news` thay vì `robotics` | v3: giữ topic chính xác và carry timeframe=day |

7 lỗi provider: 4 HTTP 503 do model quá tải và 3 HTTP 429 do giới hạn request/phút, lấy từ `results[*].result.failures`. Một lần preflight sau đó báo hết quota ngày 20 request; thông tin này là chẩn đoán kết nối, không phải điểm eval mới.

Trong tool_results của run v0, timeline/social_search trả HTTP 403, fetch cũng có HTTP error. Eval hiện chấm tool routing/arguments, không xác nhận tool đã trả nội dung hữu ích. Vì vậy PASS của eval không đồng nghĩa luồng research chạy thành công từ đầu đến cuối. Cần xử lý quyền/gói RapidAPI và thử các tool thật sau khi quota cho phép.

## B3. Team Eval Cases

Đã viết **10 case: 5 single-turn + 5 multi-turn** trong `data/eval_group.json`, không sửa `eval_base.json`. Run v3 group đạt **10/10**, routing/arguments/multiturn đều 100%, không có provider error: `runs/v3_B_group_gemini_20261110T123423722288.json`.

| Case | Kiểm tra | Expected |
|---|---|---|
| G01_explicit_handle | Bỏ @, limit=4 | timeline(screenname=karpathy, limit=4) |
| G02_news_month | Query và news/month/count | lookup(robotics, news, month, 3) |
| G03_deduplicate_existing_items | Route tới tool mới trên items có sẵn | deduplicate |
| G04_missing_article_url | Không bịa URL | clarify(response_type=text) |
| G05_company_citation_policy | Chính sách nội bộ | policy(policy_area=source_citation) |
| G06_correct_social_order | Latest→Top, giữ topic và count | social_search(PyTorch, Top, 2) |
| G07_correct_article_url | Bỏ URL cũ, chỉ đọc URL sửa | fetch(https://example.com/new) |
| G08_change_topic_keep_constraints | Đổi AMD→NVIDIA, giữ tuần và count | lookup(NVIDIA, news, week, 3) |
| G09_cancel_publication | Hủy gửi ở lượt mới nhất | Không gọi tool |
| G10_deduplicate_after_supplied_results | Dùng lại items từ hội thoại | deduplicate |

G03/G10 đều PASS, chứng minh model route tới `deduplicate` khi items đã có trong request/hội thoại. Tính chính xác của kết quả chuẩn hóa URL được kiểm tra bằng unit test riêng.

## B4. Live Chat Evidence

Transcript provider thật: `transcripts/v3_gemini_20261110T123937847917.transcript.json`, provider `gemini`, model `gemini-3.5-flash-lite`, artifact `v3+pb8bfbc906b1c+t368438afec59`.

| Lượt | User request | Tool call | Kết quả |
|---|---|---|---|
| 1 | What does the internal source citation policy say? | `policy(query="source citation policy")` | Trả về source tiers, citation URL, lưu ý arXiv và Tier 3 |
| 2 | Please summarize this article for me. | `clarify(response_type="text")` | Dừng để yêu cầu URL, không tự tạo link |
| 3 | https://openai.com/research/ | `fetch(url="https://openai.com/research/")` | Đọc URL và trả tóm tắt có link nguồn |

Đây là chat live thực, không dùng transcript mẫu hoặc fake provider. CLI được sửa cấu hình UTF-8 để transcript không lỗi ký tự tiếng Việt trên PowerShell.

## B5. Tool mới, unit test và UI

Tool mới: `tools/deduplicate/tool.py`, có `TOOL.md`, registry và schema đồng bộ. Tool giữ item xuất hiện đầu tiên cho mỗi URL, bỏ `utm_*`, `fbclid`, `gclid` và fragment khi so sánh; vẫn giữ path phân biệt hoa/thường và các tham số có ý nghĩa. URL gốc trong item không bị thay đổi. Item không có URL được giữ riêng, không gộp chỉ vì trùng tiêu đề.

Unit test bao gồm happy path, input sai/thiếu, nhánh lỗi, không sửa input, URL có tracking, và item thiếu URL. Các test TODO của starter đã được thay bằng test thực cho clarify/format/send/lookup/fetch/timeline/social_search/policy. Lệnh kiểm tra offline:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

Bug tìm thấy: send dùng `if not confirmed`, khiến các giá trị truthy sai kiểu như chuỗi `"false"` hoặc số `1` được coi là xác nhận. Đã đổi sang `confirmed is True` và giữ regression test chứng minh không có HTTP request với các giá trị sai kiểu. Eval routing không phát hiện được lỗi này vì nó không thay model bằng các input sai kiểu trực tiếp.

UI: `app.py`, cấu hình tại `.streamlit/config.toml`. Có chat nhiều vòng, xem tool results, lưu/tải transcript, dùng trực tiếp tool local, và xem run đã lưu. Nút xác nhận gửi Telegram nằm ngoài model; model không được tự dùng confirmed=true để gửi từ UI/CLI. Eval one-shot vẫn lưu raw tool call để chấm, nhưng không thực hiện gửi thật.

Bằng chứng tại `analysis/verification.txt`: **123 passed, 0 failed, 0 skipped** trước khi thêm regression test UTF-8; test full mới nhất đạt **124 passed, 0 failed, 0 skipped**. UI được kiểm tra bằng Streamlit AppTest với provider giả lập, và server local/public trả HTTP 200 cho trang chính lẫn `/_stcore/health`. Đây là kiểm thử offline/UI; eval và chat live ở các phần trên dùng Gemini thật. Chưa có bằng chứng Telegram gửi thật vì chưa cấu hình/chạy bonus này.

## B6. Reflection và phần còn lại

- `system_prompt.md` xử lý scope, routing tổng quát, khi nào hỏi lại, thứ tự phụ thuộc, carryover và sửa thông tin qua nhiều lượt.
- `tools.yaml` mô tả chức năng, khi dùng/không dùng và convention của từng tham số.
- Cần manual review cho chất lượng nội dung, nguồn/citation, quyền thực hiện action, và các tool HTTP error. Automatic routing score không đo các phần này.
- V1 không thay đổi metric; v2 giảm 2 lỗi missing_info; v3 giải quyết những failure còn lại của base. Đây là kết quả lặp trên một model/suite cố định, nên cần thêm holdout eval nếu dùng để kết luận tổng quát hơn.
- Không bỏ các khoảng chờ quota hoặc thay model âm thầm để tăng điểm. Nếu dùng model khác, ghi model rõ ràng và lấy baseline của model đó.

Lệnh chạy lại khi cần tái lập hoặc khi thay model:

```powershell
.\.venv\Scripts\python.exe scripts/run_versions.py --versions v1 --model gemini-3.5-flash-lite
.\.venv\Scripts\python.exe scripts/run_versions.py --versions v2 --model gemini-3.5-flash-lite
.\.venv\Scripts\python.exe scripts/run_versions.py --versions v3 --include-group --model gemini-3.5-flash-lite
```

Script dừng khi còn lỗi provider và tự cập nhật version_log/analysis từ run JSON thật. Nếu thay model, phải lấy baseline mới; không so trực tiếp với bảng trên. Model cũ từng báo quota 20 request/ngày; không mặc định model mới có cùng quota hoặc tất cả version chạy được trong một ngày free tier.

Phần còn lại: sửa quyền RapidAPI để X/Twitter trả dữ liệu thật, điền tên nhóm/thành viên và giữ tunnel chạy khi demo. Không nộp `.env`/API key.

## B7. Small Local Model Challenge

Chưa thực hiện bonus Ollama/local model. Không có điểm hoặc run local để báo cáo.
