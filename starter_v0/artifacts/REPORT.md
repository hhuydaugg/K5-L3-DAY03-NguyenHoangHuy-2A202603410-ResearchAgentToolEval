# Research Agent — báo cáo hiện tại trên nhánh phattran

## Team

- Team: AZEZ
- Members: Nguyễn Hoàng Huy; Nguyễn Thế Văn; Trần Thanh Tùng; Trần Hoàng Phát; Vũ Quang Dũng.
- Contribution owner: Trần Hoàng Phát. One active personal branch: phattran. Separate phattran-v3 branch deleted after all commits were merged and pushed; PR #2 closed without merging main.
- Version evidence remains v0/v1/v2/v3 as required. Raw JSON labels are unchanged. Superseded trial files were removed from this branch during submission cleanup; all run metrics/hashes remain in analysis/experiment_history.csv and originals are recoverable from Git history or the external pre-cleanup backup. Current follow-up is a v3 hardening revision with a new artifact hash.

# PHẦN A — Giới thiệu agent

## A1. Agent làm được gì

Agent nghiên cứu web, mạng xã hội, paper arXiv và company policies; đọc nguồn, tổng hợp digest và loại nguồn trùng URL. Nghiên cứu VỀ toán/lập trình vẫn được phép; agent từ chối giải bài tập hoặc viết chương trình ngoài phạm vi.

Telegram có các bước riêng: đồng ý chuẩn bị → lấy nội dung → preview đầy đủ và kênh đã cấu hình → xác nhận cuối ở lượt sau → gửi đúng bản đã xác nhận. Chưa gửi, thay đổi, từ chối, hủy hoặc đổi đích sẽ không giữ quyền gửi cũ. Chỉ hỗ trợ kênh cấu hình trên server.

**UI local:** http://localhost:8503 — chạy `python -m streamlit run app.py --server.port 8503` từ starter_v0. Chưa có public deployment URL được xác minh; link local không phải link cho máy khác.

## A2. Tools

| Tool | Công dụng | Mới |
|---|---|---|
| clarify | Hỏi thông tin/consent có stage, tạo preview chuẩn | Không |
| timeline | Bài đăng của tài khoản xác định | Không |
| social_search | Thảo luận về chủ đề | Không |
| lookup | Tra cứu web với query/topic/timeframe | Không |
| fetch | Đọc URL thực sự đã cung cấp/tìm thấy | Không |
| format | Định dạng dữ liệu đã có | Không |
| send | Gửi Telegram sau kiểm tra quyền ở live runtime | Không |
| policy | Tra cứu policy nội bộ | Không |
| papers | Tìm paper arXiv | Không |
| paper_text | Trích text paper arXiv | Không |
| deduplicate_sources | Loại URL trùng, giữ mục đầu và thứ tự | Có |

Live-only adapter có thêm finish_response để kết thúc lượt bằng answer/refusal/cancelled. Nó không phải research/action tool, không nằm trong base evaluation declarations; live_tools_hash và raw rounds công khai khác biệt này.

## A3. Câu hỏi mẫu

1. Tóm tắt 5 tweet mới nhất giúp tôi. → hỏi tài khoản qua clarify.
2. Tôi muốn chuẩn bị đăng bản tin lên Telegram. → xin đồng ý chuẩn bị, chưa gửi.
3. Đồng ý chuẩn bị, tôi chưa có nội dung. → hỏi nội dung bằng text.
4. Nội dung chính xác: Đây là bản tin nhóm. Chưa gửi. → preview không lẫn chỉ dẫn chưa gửi.
5. Tìm tài liệu nghiên cứu trên web về lập trình bất đồng bộ. → vẫn nghiên cứu bình thường.

# PHẦN B — Chi tiết / Bằng chứng

## B1. Versions, hypotheses và kết quả thật

Các mốc nhóm giữ nguyên: v0 OpenAI 14/20; v1 OpenAI 19/20; v2 OpenAI 20/20 (giữ các run mốc chính và v2 stability thành công; toàn bộ raw run nhóm trước PR #3 được bảo toàn, gồm stability/rejected trials). Đã xác minh hash baseline v0 nhóm khác starter do CRLF so với LF: chuyển hai file starter từ commit 73bf0f556ed8 sang CRLF khớp cả prompt_hash và tools_hash gốc; nội dung không khác. V3 scope ban đầu có controlled comparison dùng cùng OpenRouter/11-tool configuration: control 19/20, v3 20/20; manual refusal 0/6 → 6/6 trên hai câu cố định lặp ba lần. Xem analysis/v3_scope_manual_review.csv. Không so OpenAI và OpenRouter như cùng điều kiện.

Hardening hiện tại có các giả thuyết/bản sửa riêng: stage rõ giúp phân biệt chuẩn bị và gửi; schema clarify chặt tránh nhầm response_type/stage và thiếu question; quy tắc nguồn hiện tại/carry-over tránh gọi dư; runtime kiểm tra quyền gửi và xử lý lỗi độc lập với model. Đây là nhiều bản sửa, không quy toàn bộ thay đổi điểm cho một dòng prompt.

| Bộ kiểm tra | Kết quả hiện tại | JSON gốc |
|---|---|---|
| Base | 20/20; measured=20; provider_errors=0 | runs/v3_B_base_openrouter_20261110T140413243846.json |
| Group | 10/10; measured=10; provider_errors=0 | runs/v3_B_group_openrouter_20261110T130027992623.json |
| 16 probes bổ sung | 16/16; measured=16; provider_errors=0 | runs/v3_B_cross_openrouter_20261110T140411362763.json |

**Offline:** 151 passed, 0 failed, 0 skipped; 1 cảnh báo LibreSSL từ môi trường. Không thay đổi nội dung eval_base.json.

Hồ sơ giữ 21 raw run và 4 transcript: bảo toàn nguyên 11 run/3 transcript của nhóm trước PR #3; phần cá nhân giữ 10 run và 1 transcript phục vụ replay, v3 cuối, robustness và đối chứng. Các trial cá nhân trung gian được bỏ khỏi working tree theo yêu cầu dọn repo; toàn bộ metric và SHA-256 vẫn có trong analysis/experiment_history.csv, kể cả các lần 85%, 90%, group 9/10 và robustness 13/16 hoặc 15/16. Bản raw cũ có thể khôi phục từ Git trước commit dọn dẹp; file chưa commit có bản backup ngoài repo. Không dùng tập file đã rút gọn để tuyên bố ổn định hoặc chỉ có kết quả tốt. Hai lượt bị PermissionError lúc lưu và một request bị ngắt không có JSON hoàn chỉnh, không được ghi nhận điểm. Runner nay kiểm tra quyền lưu bằng file tạm trước khi gọi API. OpenAI-compatible client có timeout mặc định 60 giây, không retry ẩn và luôn đóng client; có thể cấu hình MODEL_TIMEOUT_SECONDS dương.

Các probes bổ sung là bộ phát triển do nhóm tự tạo, đã được dùng trong vòng sửa; không gọi là held-out benchmark. Repeats là cùng câu hỏi ở temperature 0, không phải nhiều câu độc lập. Chưa chứng minh tổng quát hóa hoặc end-to-end hoàn hảo.

## B2. Những lỗi đã xử lý và cách đo

**Đối chiếu baseline v0:** `analysis/baseline_failure_review.csv` liệt kê đủ 6 case FAIL gốc cùng kỳ vọng/call thực tế và bản sửa. R08/R14: out_of_scope nhưng gọi send; R10: thiếu tài khoản nhưng tự chọn sama; R11: thiếu URL nhưng tạo example.com/article; R12: gửi khi chưa xác nhận; R13: chọn đúng hai tool nhưng sai query và thiếu topic=news. R13 mang nhãn dataset `wrong_tool`, trong khi observed mismatch là `wrong_arg_value`; không sửa nhãn gốc. Đã đọc actual_text của R08/R14 trong latest base và xác nhận có lời từ chối, không chỉ căn cứ PASS no-tool.

- G08: đồng ý chuẩn bị nhưng thiếu nội dung → clarify text/collect_send_text, không lặp lại consent yes_no. Nếu đã có nội dung, chuyển thẳng sang confirm_send.
- Live structured questions: CLI/UI yêu cầu tool calls, dùng clarify cho câu hỏi và finish_response cho lời kết. Plain text hoặc batch trộn clarify/finish/send bị từ chối; có sửa có giới hạn, không âm thầm giả làm tool call. Raw attempts vẫn được giữ.
- Runtime consent: phải có prepare consent và preview; chỉ một yes rõ ràng ở lượt SAU preview cho phép gửi đúng text và đúng destination hash. Cancel/edit/uncertain answer/destination change hủy quyền; gửi xong hoặc lỗi thì tiêu thụ quyền. Không gửi lại tự động.
- Preview: tool tạo câu hỏi hiển thị toàn văn và đích cấu hình. Với nội dung người dùng gắn nhãn rõ, runtime giữ nguyên text đã cho, tách chỉ dẫn điều khiển như câu chưa gửi ở cuối; nội dung được quote thì giữ nguyên. Mismatch bị trả lại để model sửa, không sửa ngầm arguments trong log.
- Đọc nguồn: query rỗng hoặc URL tự tạo bị chặn ở live runtime. Nguồn HTTP lỗi/timeout, metadata HTTP lỗi hoặc nội dung rỗng không được coi là thành công. Không có nguồn dùng được thì trả lỗi/no_results cố định; có nguồn tốt lẫn lỗi thì luôn kèm thông báo lỗi. Gọi lặp cùng arguments không thực hiện network lần nữa trong lượt đó.
- Provider lỗi sau khi đọc nguồn: giữ kết quả công cụ trước đó và lỗi trong transcript, không làm mất trace hoặc giả là đã hoàn tất.
- Low-level send: yêu cầu boolean true thật và text không rỗng; Telegram ok=false không báo sent. Lỗi URL có bot token được che trước khi log. One-shot evaluator không thực hiện gửi; model-proposed calls vẫn được chấm như cũ.
- Source/author routing: một yêu cầu bài của tác giả không tự thêm social_search; nguồn đã bị bỏ không quay lại khi chỉ nhắc lại chủ đề. Tài khoản đã biết dùng handle đã xác minh, không ghép họ tên để đoán (account_alias_sources.md).

**Lỗi thực thi tool còn quan sát được trong run hiện tại:**
- Base: {'HTTPError HTTP 403': 7, 'SourceHTTPError HTTP 404': 2, 'HTTPError HTTP 429': 1}.
- Group: {'HTTPError HTTP 403': 1, 'HTTPError HTTP 429': 1, 'SourceHTTPError HTTP 404': 1}.
- Robustness: {'HTTPError HTTP 403': 2, 'HTTPError HTTP 429': 1}.

403/429 do quyền/hạn mức dịch vụ, hoặc sự cố mạng ngoài ứng dụng, chưa được coi là đã sửa ở phía nhà cung cấp. Ứng dụng đã xử lý và báo đúng trạng thái. Phát hiện 404 dựa HTTP/metadata có sẵn; nội dung soft-404 không có metadata và chất lượng/relevance của nguồn vẫn cần review.

## B3. Group và robustness cases

Group giữ 10 case (5 single-turn, 5 contextual multi-turn), không đổi expected answers để tăng điểm. Raw multi-turn eval là context tổng hợp trong một request; không thay thế chat thật.

| Case | Kiểm tra | Kết quả |
|---|---|---|
| G01_weekly_robotics_news | Explicit news topic and week filter on a new subject. | PASS |
| G02_independent_web_social | Use independent web and social tools together, not timeline. | PASS |
| G03_prepare_before_missing_content | Preparation consent precedes collection of unspecified content; never send now. | PASS |
| G04_remove_duplicate_sources | Route to new local tool and pass all supplied items unchanged. | PASS |
| G05_unrelated_code | No research tool for unrelated coding; manual review must also verify refusal. | PASS |
| G06_account_after_clarification | Resolve account and requested count from earlier context; strip @. | PASS |
| G07_url_after_clarification | Read a supplied URL rather than asking again or searching. | PASS |
| G08_preparation_is_not_send | After preparation consent, collect missing content, not send. | PASS |
| G09_cancel_after_preparation | Cancellation after final preview invalidates any earlier preparation consent. | PASS |
| G10_switch_from_social_to_web | Latest request overrides earlier social-search intent. | PASS |

Bộ bổ sung gồm 16 case về từ chối mới, nghiên cứu hợp lệ về toán/lập trình/skin classification, nguồn đã đổi, xác nhận cuối, hủy và bài đăng theo tác giả. Cases/expected answers được giữ trong data/eval_robustness.json. Xem analysis/current_runs.csv để đọc toàn bộ kết quả hiện tại.

## B4. Live chat và runtime evidence

File: `transcripts/v3_openrouter_20261110T140357969604.transcript.json`. Artifact và runtime hashes khớp code hiện tại. Model API thật, clarify thật; không giả lập model. Telegram credentials được bỏ khỏi riêng process demo và không có send call. Gửi thành công/thất bại, đổi đích, thay text và chống dùng lại consent được kiểm tra bằng mock HTTP/offline, không gửi Telegram thật.

| Turn | Trạng thái | Registered tools | Nội dung quan sát |
|---|---|---|---|
| 1 | waiting_for_user | clarify | Bạn muốn tóm tắt tweet của tài khoản nào? |
| 2 | waiting_for_user | clarify | Bạn có muốn chuẩn bị một bản tin để đăng lên Telegram không? |
| 3 | waiting_for_user | clarify | Bạn có thể cung cấp nội dung cho bản tin mà bạn muốn đăng lên Telegram không? |
| 4 | waiting_for_user | clarify,clarify | Nội dung: / Đây là bản tin kiểm tra của nhóm. /  / Đích gửi: kênh Telegram đã cấu hình. / Bạn xác nhận gửi đúng nội dung này đến kênh đã cấu hình không? |
| 5 | answered | Không | Yêu cầu đã bị hủy. Không có gì được gửi đi. |

Raw base/group dùng model tool calls trực tiếp (11 registered tools); CLI/UI dùng required-tools-v1 với thêm finish_response (12 declarations). Base không được nâng điểm nhờ runtime guards. Live metadata: runtime_hash `9baa3a45e17ba988f7cf7b61bc858e7e74e870d859d804481b8dafd983ee5d74`, live_tools_hash `144e7233998f772959e1932be9cd2f4c03cc1fbb6141170953017401dbede0d8`. Raw model attempts, tool results, protocol errors và terminal kind đều ở rounds. Không coi cấu hình live và raw eval là phép đo giống nhau.

## B5. Code tests và UI

- 151 offline tests: includes 12 new-tool cases, grader list-of-object regression, protocol/permission/state/source-error behavior, provider error retention, client deadline/close, fail-before-API write-access check và 2 UI integration tests. Mocks không chứng minh external service uptime.
- Một API smoke riêng đã xác minh clarify strict schema gửi đủ question, response_type, options, stage và draft_text. Cấu hình strict theo hướng dẫn chính thức: https://developers.openai.com/api/docs/guides/function-calling . Không giả định provider khác đều hỗ trợ giống OpenRouter đã kiểm tra.
- UI lưu consent state theo session và reset khi provider/model/artifact/runtime đổi; transcript không trộn các cấu hình. AppTest dùng fake provider và được ghi rõ offline. Chưa có public deployment URL được xác minh.

## B6. Assessment checklist và giới hạn

- [x] Có baseline và evidence v1/v2/v3 thật; version_log giữ nguyên mốc nhóm và bổ sung trial/revision đúng hash.
- [x] Có >=5 tool, tool mới + TOOL.md + registry + declaration + >=3 tests.
- [x] Có 10 group cases, 5 single + 5 multi, có new-tool route.
- [x] Có base/group JSON, development probes, CLI >=3 lượt và report; các repeats bổ sung không bắt buộc được rút gọn, metric lịch sử vẫn được giữ.
- [x] Offline tests không fail/skip; UI code chạy được và metadata/consent session có test.
- [x] Giữ benchmark của nhóm: eval_base.json không đổi; không sửa dữ liệu điểm hoặc đổi nhãn run cũ.
- [ ] Public UI URL cho người ngoài máy: chưa triển khai trong thay đổi này.
- [ ] Telegram thực tế và toàn bộ provider/UI combinations chưa được xác minh end-to-end.

Không tuyên bố mọi đầu vào đều đúng chỉ từ các bộ nhỏ này. Source relevance, semantic factuality, unknown handles và soft error pages vẫn cần giám sát; model output không được coi là quyền thực hiện hành động.

## B7. Bonus local model

Không thực hiện bonus Ollama trong phần này; không có kết quả local-model được báo cáo.

## B8. Hồ sơ tối giản và kiểm tra trước nộp

Chỉ giữ code chạy agent/UI, tests, data, report, version log và bằng chứng cần đối chiếu. Đã bỏ hướng dẫn/checklist phụ, script audit phụ, snapshot active trùng file gốc, snapshot local v2 đã thay thế và báo cáo cá nhân lịch sử trùng. Các file đã có trước PR #3 được giữ lại, gồm cả poster lịch sử, samples và bảng phân tích nhóm; chúng không đại diện cấu hình active hiện tại. Các snapshot v0/v1/v2 lấy từ lịch sử main dùng cho replay; v2_control/v3 phục vụ đối chứng scope.

Còn phải hoàn thiện public UI URL, descriptions policy/paper_text và timeframe, provider frontmatter của tool mới, và trình bày giới hạn thí nghiệm nhiều thay đổi. Không coi điểm routing 100% là xác nhận dịch vụ nguồn hoặc gửi Telegram end-to-end.

## B9. Chạy lại v0–v1–v2 tại local từ lịch sử main

Các snapshot artifacts/v0, artifacts/v1, artifacts/v2 lấy nguyên từ các commit main tương ứng 73bf0f556ed8, 1fd06e6c0bd8, e56a110f8b6b. Không ghi đè prompt/tools v3 đang dùng ở artifacts root. Cùng provider OpenRouter, model openai/gpt-4o-mini, temperature=0, output cap=512; chạy tuần tự v0 rồi v1 rồi v2, dùng one-shot runtime/grader hiện tại và không thực thi send. Giới hạn output được thêm vào SDK request chỉ trong process replay, không sửa provider/runtime code của bản nộp. Raw JSON có replay_metadata ghi nguồn commit, cấu hình và giới hạn token.

- v0: 13/20 (65%); measured=20, provider_errors=0; `runs/v0_B_base_openrouter_20261110T155117759410.json`.
- v1: 19/20 (95%); measured=20, provider_errors=0; `runs/v1_B_base_openrouter_20261110T155220687009.json`.
- v2: 20/20 (100%); measured=20, provider_errors=0; `runs/v2_B_base_openrouter_20261110T155320532977.json`.

V3 hiện có: 20/20 tại runs/v3_B_base_openrouter_20261110T140413243846.json; không chạy lại v3 trong đợt này. Run v3 đó không áp output cap 512 của replay, nên chưa gọi cả v0–v3 là so sánh đồng nhất hoàn toàn. Các mốc OpenAI 14/20, 19/20, 20/20 là bằng chứng nhóm cũ, không thay bằng điểm OpenRouter mới. Chất lượng thực thi nguồn vẫn phải đọc tool_results; không suy ra end-to-end thành công từ routing score.

Truy xuất v0: source LF prompt SHA f0c107a9d7a14032c948d642d7c36f2a85cb6d69a099530093a874c94d472446 và tools SHA 8db0ba629f52ad1ec171bae4e4e84472c12f950fa1a6db5e1d27bad6e749b740. Chỉ chuyển LF sang CRLF sẽ khớp prompt SHA eb1c8179815bd79d34de7d326420bb99b3072e6e8ae96464c02d4411f905fc68 và tools SHA 5b22a2476d41b989d5dc1e54f24ce7890e781909deb2f7afafb856ab53a6d7c0 của baseline nhóm. Vì vậy đã xác minh khác biệt byte do xuống dòng, không phải thay nội dung.

## B10. Bộ bằng chứng được chọn cho bài nộp

Giữ nguyên từng byte 11 run và 3 transcript tồn tại trước PR #3 để không xóa bằng chứng nhóm. Đây là lịch sử cần được phân biệt với phần cá nhân; việc một run có FAIL không có nghĩa được loại khỏi bài so sánh.

Phần cá nhân giữ 10 run: 3 replay v0/v1/v2; v3 active base/group/robustness; 2 run base v2-control/v3 scope và 2 run scope repeats đối chứng. Giữ 1 live transcript v3 active 5 lượt. Các cặp đối chứng có config khác active và chỉ dùng cho kết luận scope tương ứng, không gộp thành điểm active.

Bỏ 2 run scope group cũ (v2-control 9/10 và v3 scope 9/10), 2 run lặp hardening/account bổ sung và transcript scope cũ. Chúng không còn cần để chứng minh kết quả bản nộp. Không thay score JSON còn giữ; điểm của run đã bỏ vẫn ở analysis/experiment_history.csv. Bản raw cũ có thể khôi phục từ Git history. Run mới thấp điểm vẫn giữ vì là baseline/so sánh, không chỉ chọn JSON đạt 100%.

Quy tắc bảo toàn sau rà soát: không xóa file có trước PR #3. Các run/transcript nhóm, bảng phân tích nhóm, version_changes.html và samples được khôi phục từ đúng bản trước merge, không chỉnh nội dung để phù hợp điểm mới. Chỉ rút gọn phần cá nhân thêm trong PR #3 hoặc sau đó. Không tự động đồng bộ việc dọn local vào main. Bộ file chọn để nộp dùng các đường dẫn trong report/version log; giữ nguyên cấu trúc nhóm để không gây xáo trộn.
