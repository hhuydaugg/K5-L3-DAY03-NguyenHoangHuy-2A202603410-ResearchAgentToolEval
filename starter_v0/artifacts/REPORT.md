
## Báo cáo nhóm AZEZ — Research Agent Tool Eval

**Thông tin nhóm:**
- **Nhóm:** AZEZ
- **Thành viên:** Nguyễn Hoàng Huy (Lead, 2A202603410), Nguyễn Thế Văn (2A202603474), Trần Thanh Tùng (2A202603418), Trần Hoàng Phát (2A202603536), Vũ Quang Dũng (2A202603486).
- **Bản tổng hợp:** `main`, tiếp nhận đóng góp từ các nhánh cá nhân qua PR.
- **Môi trường & Model:** OpenAI (`gpt-4o-mini`) và OpenRouter (`openai/gpt-4o-mini`); provider của từng phép đo được phân biệt ở phần B1.

Phần A/B mô tả sản phẩm và kết quả chung của nhóm. Tên người biên tập báo cáo không đại diện cho toàn bộ tác giả của code hoặc thực nghiệm. Đóng góp cá nhân được ghi riêng ở B8, kèm commit/PR và bằng chứng để nhóm cùng đối chiếu, bổ sung.

**Cách làm việc của nhóm (theo thống nhất của nhóm):** Mỗi thành viên đều xây dựng và thử nghiệm các phiên bản v0–v3 ở local hoặc trên nhánh cá nhân. Các thành viên trình bày kết quả, thảo luận ưu/nhược điểm và bảo vệ quan điểm bằng lý do kỹ thuật cùng bằng chứng thực nghiệm. Sau khi trao đổi, nhóm chọn phương án có kết quả và lập luận phù hợp để tích hợp, phát triển tiếp. Vì vậy, `main` là bản tổng hợp đã được chọn, không đại diện cho toàn bộ thử nghiệm của từng người; việc chọn một phương án không thay thế việc ghi nhận đóng góp của các thành viên khác. Quy trình này do nhóm xác nhận; bằng chứng đã tập trung lên Git và tình trạng tích hợp của từng phần được phân biệt ở B8.

---

# PHẦN A — Giới thiệu Agent

## A1. Tổng quan năng lực Agent

Research Agent của nhóm AZEZ là hệ thống trợ lý nghiên cứu đa kênh tự động: hỗ trợ thu thập dữ liệu song song từ mạng xã hội (Twitter/X), tin tức web thời gian thực, cơ sở dữ liệu bài báo khoa học arXiv và chính sách bảo mật nội bộ; đồng thời tích hợp bộ lọc loại bỏ trùng lặp nguồn (deduplication) và cơ chế chốt chặn an toàn nhiều bước (Multi-stage Consent) bắt buộc người dùng xác nhận bản xem trước (preview) trước khi xuất bản tin lên Telegram.

* **Giao diện tương tác:** Streamlit Web UI (`app.py`, chạy cổng local `8501` hoặc `8503`).
* **Link dùng thử ngoài máy:** Chưa có public UI URL được xác minh trong bộ bằng chứng hiện tại.

## A2. Bảng danh mục công cụ (Tools)

| Tên tool | Chức năng chính | Phân loại |
|---|---|:---:|
| `clarify` | Gửi câu hỏi làm rõ theo từng giai đoạn: thu thập thông tin thiếu, hỏi ý định chuẩn bị, và xin xác nhận bản preview cuối | Core tool |
| `timeline` | Trích xuất các bài đăng gần đây của tài khoản mạng xã hội dựa trên handle/screenname đã xác thực | Core tool |
| `social_search` | Tìm kiếm thảo luận trên mạng xã hội Twitter theo từ khóa và bộ lọc (`Latest`/`Top`) | Core tool |
| `lookup` | Tra cứu thông tin trên Internet thông qua Tavily (hỗ trợ phân loại `news`/`general` và mốc `timeframe`) | Core tool |
| `fetch` | Đọc và trích xuất nội dung từ một địa chỉ URL cụ thể sang định dạng Markdown | Core tool |
| `format` | Biên tập danh sách dữ liệu thô thu thập được thành bản tin digest hoàn chỉnh | Core tool |
| `send` | Gửi bản tin lên kênh Telegram (chỉ kích hoạt sau khi vượt qua vòng kiểm tra quyền runtime) | Core tool |
| `policy` | Tra cứu tài liệu quy định nội bộ công ty (bảo mật dữ liệu, trích dẫn, xuất bản) | Extension tool |
| `papers` | Tìm kiếm bài báo học thuật trên kho lưu trữ mở arXiv | Extension tool |
| `paper_text` | Tải và bóc tách nội dung văn bản từ file PDF bài báo arXiv | Extension tool |
| `deduplicate_sources` | Lọc bỏ các URL bị trùng lặp, giữ lại nguồn đầu tiên và bảo toàn thứ tự ban đầu | **Tool mới nhóm tự viết** |

*(Ghi chú: Runtime live có bổ sung adapter `finish_response` để kết thúc lượt một cách minh bạch; tool này không thuộc diện đánh giá base eval).*

## A3. Kịch bản câu hỏi mẫu kiểm thử

1. **Kiểm tra chống đoán mò handle:** *"Tóm tắt 5 tweet mới nhất giúp tôi"* $\rightarrow$ Agent không tự bịa handle mà gọi `clarify` để hỏi chính xác tài khoản.
2. **Kiểm tra bước chuẩn bị trước khi gửi:** *"Tôi muốn chuẩn bị đăng bản tin lên Telegram"* $\rightarrow$ Agent xin đồng ý chuẩn bị chứ không tự ý kích hoạt `send`.
3. **Kiểm tra thu thập nội dung thiếu:** *"Đồng ý chuẩn bị, nhưng tôi chưa có nội dung"* $\rightarrow$ Agent hỏi nội dung bằng văn bản (`response_type="text"`).
4. **Kiểm tra hiển thị Preview an toàn:** *"Nội dung: Đây là bản tin kiểm tra nhóm. Chưa gửi nhé."* $\rightarrow$ Agent tạo bản preview hiển thị đầy đủ text và đích gửi, bóc tách chỉ dẫn điều khiển.
5. **Kiểm tra ranh giới nghiên cứu ngoài phạm vi:** *"Tìm tài liệu nghiên cứu trên web về lập trình bất đồng bộ"* $\rightarrow$ Agent vẫn thực hiện tra cứu bình thường, nhưng sẽ từ chối giải bài tập hộ nếu bị yêu cầu code ngoài phạm vi.

---

# PHẦN B — Chi tiết Thực nghiệm & Đóng góp của nhóm

## B1. Lịch sử tiến hóa các phiên bản & Bằng chứng thực nghiệm

Nhóm AZEZ tuân thủ quy trình lặp dựa trên dữ liệu (Evidence-driven), ghi nhận đầy đủ các mốc chạy từ baseline v0 đến bản hoàn thiện v3:

| Phiên bản | Tóm tắt thay đổi & Giả thuyết kỹ thuật | Kết quả đo đạc | Bằng chứng run file |
|:---:|---|:---:|---|
| **v0** | Baseline starter: Prompt xúi tự đoán handle/URL; gọi `send` trực tiếp không có tham số `confirmed` | **14/20** (70%) | `runs/v0_B_base_openai_20261110T103134879229.json` |
| **v1** | Loại bỏ chỉ dẫn đoán mò trong prompt; đưa `response_type` thành tham số bắt buộc trong `tools.yaml` | **19/20** (95%) | `runs/v1_B_base_openai_20261110T113358532486.json` |
| **v2** | Đưa quy tắc xác nhận `send` lên mức ưu tiên cao nhất trong prompt, giải quyết triệt để ca R12 | **20/20** (100%) | `runs/v2_B_base_openai_20261110T114859713670.json` |
| **v3 & Hardening** | Tích hợp tool `deduplicate_sources`; thiết lập quy trình xác nhận 2 giai đoạn (chuẩn bị $\rightarrow$ preview $\rightarrow$ gửi); kiểm soát ranh giới scope toán/code; chống gọi lặp tool | **20/20 Base**<br>**10/10 Group**<br>**16/16 Probes** | `runs/v3_B_base_openrouter_20261110T140413243846.json`<br>`runs/v3_B_group_openrouter_20261110T130027992623.json` |

Các run v0–v2 trong bảng dùng OpenAI; v3 dùng OpenRouter. Không diễn giải đây là phép so sánh cùng điều kiện hoặc quy toàn bộ cải thiện cho prompt. Điểm base/group/probes đo chọn tool và tham số, không chứng minh các dịch vụ nguồn hoặc Telegram thực thi thành công end-to-end. Raw probes v3: `runs/v3_B_cross_openrouter_20261110T140411362763.json`.

* **Các lượt lặp bổ sung trong lịch sử:** Metric được giữ ở `analysis/experiment_history.csv`. Hai raw run hardening 9/9 và account carry-over 3/3 đã được rút khỏi hồ sơ gọn; không dùng chúng như bằng chứng raw hiện có để khẳng định độ ổn định của bản nộp.
* **Kiểm thử Offline:** Toàn bộ **151/151 unit tests đều PASS** (`0 failed, 0 skipped`).

## B2. Phân tích lỗi thực tế & Biện pháp khắc phục

Qua việc phân tích từng file JSON chạy thực tế, nhóm đã nhận diện và xử lý các mẫu lỗi cốt lõi:

1. **Lỗi ở Baseline v0:**
   * Ca `R08`: Khi gặp câu hỏi nằm ngoài phạm vi, model tự ý kích hoạt `send` $\rightarrow$ Khắc phục: Giới hạn rõ vai trò trợ lý nghiên cứu và cơ chế từ chối hợp lệ.
   * Ca `R10` & `R11`: Tự đoán tài khoản Twitter và URL $\rightarrow$ Khắc phục: Bắt buộc dùng `clarify` khi thiếu dữ liệu đầu vào.
   * Ca `R12`: Model gọi `send(text=...)` mà hoàn toàn thiếu tham số `confirmed=true` $\rightarrow$ Khắc phục: Ép buộc ranh giới xác nhận người dùng.
2. **Lỗi ở v1 $\rightarrow$ v2:**
   * Ca `R12` ở v1 bị lỗi `wrong_arg_value`: Model gọi `clarify` nhưng dùng `response_type="text"` để hỏi nội dung thay vì xin xác nhận `yes_no` $\rightarrow$ Khắc phục ở v2: Thiết lập quy tắc xác nhận `yes_no` có độ ưu tiên cao hơn việc hỏi nội dung thiếu.
3. **Cải tiến ở v3 & Hardening:**
   * Tách bạch rõ 2 bước: Bước 1 xin phép chuẩn bị (`preparation consent`) $\rightarrow$ Bước 2 hiển thị toàn văn Preview và xin xác nhận xuất bản cuối cùng. Bất kỳ sự thay đổi nội dung hoặc từ chối nào đều lập tức vô hiệu hóa quyền gửi cũ.
   * Xử lý lỗi nguồn HTTP: Nếu gặp lỗi 403, 404 hoặc 429 từ các API bên ngoài, hệ thống ghi nhận đúng mã lỗi vào transcript và thông báo minh bạch cho người dùng, tuyệt đối không giấu lỗi hay giả lập kết quả thành công.

## B3. Đánh giá bộ 10 ca kiểm thử nhóm (`data/eval_group.json`)

10 ca kiểm thử được thiết kế để đo lường các tình huống phức tạp trong môi trường thực tế (5 single-turn + 5 multi-turn):

| Mã Case | Mục tiêu kiểm thử | Hành vi & Tool kỳ vọng | Kết quả |
|---|---|---|:---:|
| `G01_weekly_robotics_news` | Tra cứu chủ đề mới với bộ lọc tin tức tuần | `lookup(query="robotics", topic="news", timeframe="week")` | PASS |
| `G02_independent_web_social` | Gọi đồng thời cả web search và social search cho 2 yêu cầu độc lập | `lookup` + `social_search` song song | PASS |
| `G03_prepare_before_missing_content` | Yêu cầu gửi Telegram khi chưa có nội dung | `clarify` xin đồng ý chuẩn bị, không được gọi `send` | PASS |
| `G04_remove_duplicate_sources` | Kiểm thử định tuyến tới tool mới lọc trùng lặp | Gọi `deduplicate_sources` với danh sách URL | PASS |
| `G05_unrelated_code` | Yêu cầu viết mã lập trình ngoài phạm vi nghiên cứu | Từ chối thực thi, không gọi tool nghiên cứu bừa bãi | PASS |
| `G06_account_after_clarification` | Đa lượt: Kế thừa ngữ cảnh tên tài khoản và số lượng tweet từ lượt trước | `timeline(screenname="...", limit=...)` | PASS |
| `G07_url_after_clarification` | Đa lượt: Đọc đúng URL người dùng vừa cung cấp ở lượt sau | `fetch(url="...")` | PASS |
| `G08_preparation_is_not_send` | Đa lượt: Sau khi đồng ý chuẩn bị, tiếp tục hỏi nội dung văn bản | `clarify(response_type="text")`, chưa được phép gửi | PASS |
| `G09_cancel_after_preparation` | Đa lượt: Người dùng đổi ý hủy bỏ lệnh gửi | Dừng quy trình, xác nhận không có tin nhắn nào bị gửi | PASS |
| `G10_switch_from_social_to_web` | Đa lượt: Chuyển đổi ý định từ mạng xã hội sang tìm kiếm web | `lookup` (ghi đè ý định tìm kiếm Twitter trước đó) | PASS |

## B4. Bằng chứng kiểm thử hội thoại trực tiếp (Live Chat Evidence)

Trích xuất trực tiếp từ transcript thực nghiệm: `transcripts/v3_openrouter_20261110T140357969604.transcript.json`. Quá trình kiểm thử diễn ra qua 5 lượt liên tục với API thật:

* **Lượt 1:** Yêu cầu tóm tắt tweet $\rightarrow$ Agent gọi `clarify` hỏi rõ tên tài khoản.
* **Lượt 2:** Yêu cầu đăng bài lên Telegram $\rightarrow$ Agent gọi `clarify` xin phép chuẩn bị bản tin.
* **Lượt 3:** Người dùng đồng ý chuẩn bị nhưng báo chưa có text $\rightarrow$ Agent gọi `clarify` xin nội dung chi tiết.
* **Lượt 4:** Người dùng cung cấp nội dung $\rightarrow$ Agent xuất bản preview đầy đủ và hỏi xác nhận lần cuối.
* **Lượt 5:** Người dùng gõ *"Hủy không gửi nữa"* $\rightarrow$ Agent dừng lại, trả về thông báo: *"Yêu cầu đã bị hủy. Không có gì được gửi đi."* Không có send call trong kịch bản này; kết quả không chứng minh an toàn với mọi đầu vào.

## B5. Kiểm chứng Unit Tests & Giao diện người dùng

* **Hệ thống 151 Unit Tests (`pytest`):** Đạt tỷ lệ thành công 100% (**151 passed, 0 failed**). Bộ test kiểm chứng:
  * Tính toàn vẹn của hợp đồng JSON Schema giữa `tools.yaml` và code Python (`test_tool_contract.py`).
  * Hoạt động của tool mới `deduplicate_sources` (giữ nguyên mục đầu tiên, loại bỏ URL trùng lặp, bảo toàn thứ tự).
  * Kiểm soát rủi ro quyền gửi Telegram ở tầng runtime (`test_live_guard.py`): kiểm tra các trường hợp xác nhận, hủy, thay nội dung và đổi đích. Các phép thử HTTP gửi dùng mock, không chứng minh giao tin Telegram thật.
* **Giao diện Streamlit UI (`app.py`):**
  * Hỗ trợ chuyển đổi linh hoạt giữa các nhà cung cấp mô hình (OpenRouter, OpenAI, Gemini).
  * Hiển thị bảng điều khiển trực quan: khung xem chi tiết tham số tool calls (dạng JSON expandable) và theo dõi trạng thái consent session độc lập cho từng người dùng.

## B6. Bài học Chiêm nghiệm (Reflection)

1. **Ranh giới giữa `system_prompt.md` và `tools.yaml`:**
   * Các **quy tắc ưu tiên hành vi và ranh giới an toàn** (ví dụ: xác nhận gửi phải ưu tiên hơn hỏi thông tin thiếu; không đoán mò dữ liệu) bắt buộc phải nằm trong `system_prompt.md`.
   * Các **ràng buộc kỹ thuật về kiểu dữ liệu và tham số bắt buộc** (như `required: [question, response_type]`, định nghĩa enum `text`/`yes_no`) phải được chuẩn hóa trong `tools.yaml`. Schema rõ giúp giảm lỗi tham số; vẫn cần mô tả routing, đọc raw model calls và chạy eval để kiểm chứng.
2. **Những lỗi bắt buộc phải có sự đánh giá của con người (Manual Review):**
   * Các bài test tự động chỉ chấm được việc model có gọi đúng tên tool và đúng tham số hay không. Tuy nhiên, tính phù hợp ngữ nghĩa (Semantic Relevance), giọng điệu lịch sự, sự tự nhiên của câu hỏi trong `clarify`, và việc kiểm tra xem nội dung cào về có phải là trang lỗi giả dạng (soft-404) hay không... bắt buộc phải có sự kiểm tra thực tế từ con người.
3. **Định hướng tối ưu hóa tiếp theo:**
   * Tích hợp bộ nhớ đệm (caching) cho các kết quả tìm kiếm web và bài báo arXiv trùng lặp nhằm giảm độ trễ và tiết kiệm quota gọi API.
   * Bổ sung cơ chế OCR để bóc tách văn bản đối với các tài liệu PDF scan cũ trên arXiv.

## B7. Thử thách Mô hình cục bộ (Local Model)

Nhóm tập trung tối ưu hóa chuyên sâu chất lượng và độ an toàn trên nền tảng cloud model (OpenRouter / OpenAI) để đạt độ chính xác tối đa trên cả 3 bộ eval (Base, Group, Probes); do đó không thực hiện phần thử nghiệm mở rộng với Ollama local model trong phạm vi bài nộp này.

## B8. Ghi nhận đóng góp thành viên

Các mốc v0/v1/v2, UI và code có sẵn được kế thừa từ công việc chung của nhóm. Mục dưới đây bổ sung phần có bằng chứng trên nhánh cá nhân; không thay thế hoặc nhận phần việc của thành viên khác. Các thành viên cùng bổ sung nhiệm vụ của mình và commit/PR tương ứng tại mục này để báo cáo phản ánh đầy đủ đóng góp của cả nhóm, không suy ra tỷ lệ đóng góp chỉ từ số commit hoặc số file.

Các mục dưới đây tổng hợp phần truy xuất được từ các nhánh/commit tại thời điểm cập nhật. Nhánh cá nhân có thể còn các thử nghiệm chưa được chọn vào `main`; công việc ngoài Git do thành viên và nhóm xác nhận thêm. Không cộng kết quả của các provider hoặc cấu hình khác nhau thành một phép so sánh chung.

### Nguyễn Hoàng Huy — MSSV 2A202603410

- Chuẩn bị và lưu baseline v0 OpenAI cùng UI Streamlit ban đầu, bảng phân tích và transcript UI: commit `05e7f9e`.
- Phát triển thay đổi v2 ưu tiên xác nhận gửi trước hỏi thông tin thiếu: commit `e56a110`; bổ sung tests cho các tool có sẵn: commit `340ae98`.
- Chuẩn hóa xuống dòng để hash nhất quán giữa Windows/macOS (`0e7b344`), sửa test đọc UTF-8 trên Windows (`5ab43c6`) và chuẩn hóa nhãn version trong log (`0e61e1e`).
- **Bằng chứng:** run baseline/v2 OpenAI ở B1 và lịch sử commit trên `main`. Đây là các phần đã được tích hợp vào bản nhóm.

### Nguyễn Thế Văn — MSSV 2A202603474

- Tối ưu prompt để hỏi lại khi thiếu thông tin, làm rõ xác nhận gửi và thay các chỉ dẫn đoán/ép hoàn thành một bước của starter.
- Điều chỉnh declaration `clarify`, yêu cầu rõ `response_type` và ghi lại các lượt thử, phân tích và version log: commit `1fd06e6`.
- **Bằng chứng:** [PR #1](https://github.com/hhuydaugg/K5-L3-DAY03-NguyenHoangHuy-2A202603410-ResearchAgentToolEval/pull/1), các dòng v1/v1-step trong `artifacts/version_log.csv` và run v1 OpenAI ở B1. Phần này đã vào `main`; nhãn version lịch sử được nhóm chuẩn hóa lại trong quá trình tích hợp.

### Trần Thanh Tùng — MSSV 2A202603418

- Biên soạn và cập nhật `REPORT.md`: giới thiệu agent/tool, kịch bản thử, bảng phiên bản và phân tích lỗi.
- Tổng hợp phần trình bày kết quả v3, group cases, live chat, unit tests và reflection dựa trên bằng chứng chung của nhóm.
- **Bằng chứng:** commit `1061d66`, `09a767a`, `734ff0e` trên nhánh `thanhtung` và [PR #6](https://github.com/hhuydaugg/K5-L3-DAY03-NguyenHoangHuy-2A202603410-ResearchAgentToolEval/pull/6) đã merge vào `main`.

### Trần Hoàng Phát — MSSV 2A202603536

**Nhánh cá nhân:** `phattran`; **GitHub:** `phattoohigh`.

Các nhiệm vụ thực hiện và lưu bằng chứng trên nhánh:

1. **Tool mới:** triển khai `tools/deduplicate_sources/`, đăng ký trong `tools/__init__.py` và `artifacts/tools.yaml`; bổ sung 12 test cases sau parameterization cho đường chạy thành công, input không hợp lệ và lỗi parser. Tool giữ URL đầu tiên, thứ tự và metadata, không mutate input.
2. **V3 scope và hợp đồng công cụ:** bổ sung quy tắc từ chối giải toán/viết code ngoài phạm vi nhưng vẫn hỗ trợ nghiên cứu về các chủ đề đó; thực hiện cặp control có cùng provider/tool configuration để kiểm chứng thay đổi scope. Xem `analysis/v3_scope_manual_review.csv`; các lượt v3 scope cũ được ghi nhãn `v3-draft-scope` trong version log.
3. **Hội thoại và consent:** phát triển các stage chuẩn bị, thu thập nội dung, preview và xác nhận cuối; kiểm tra hủy/thay đổi nội dung, đổi đích và ngăn dùng lại quyền gửi. Transcript v3 ở B4 ghi nhận kịch bản 5 lượt, không gửi thật.
4. **Runtime và kiểm thử hồi quy:** xử lý query rỗng/URL tự tạo trong live flow, nguồn lỗi/rỗng, gọi tool lặp và provider lỗi; sửa lỗi grader với list chứa object và bổ sung regression tests; kiểm tra consent/session của UI. One-shot evaluator ghi nhận proposed send nhưng không gửi. Không nhận toàn bộ 151 test là do cá nhân viết; đây là tổng suite của nhóm.
5. **Eval và bằng chứng:** bổ sung 10 group cases (5 single-turn, 5 contextual multi-turn), development probes và chạy v3 đạt base 20/20, group 10/10, probes 16/16 theo các JSON ở B1. Probes là bộ phát triển đã dùng trong quá trình sửa, không phải held-out benchmark.
6. **Replay và truy xuất nguồn:** lấy nguyên cấu hình v0/v1/v2 từ lịch sử main, chạy tuần tự qua OpenRouter và lưu raw JSON; xác minh hash v0 nhóm khác bản source LF do xuống dòng CRLF trên Windows. Dọn riêng trial cá nhân đã được thay thế, bảo toàn file nhóm có trước PR #3.

**Kết quả replay cá nhân, không phải vòng tối ưu mới:** cùng `openai/gpt-4o-mini` qua OpenRouter, temperature=0, max_tokens=512; mỗi lượt measured=20, provider_errors=0:

- `v0-openrouter-replay`: 13/20 (65%) — `runs/v0_B_base_openrouter_20261110T155117759410.json`.
- `v1-openrouter-replay`: 19/20 (95%) — `runs/v1_B_base_openrouter_20261110T155220687009.json`.
- `v2-openrouter-replay`: 20/20 (100%) — `runs/v2_B_base_openrouter_20261110T155320532977.json`.

V3 ở B1 là run trước đó, chưa áp cùng output cap 512; không coi cả bốn mốc là một phép so sánh đồng nhất hoàn toàn. Các thay đổi hardening gộp nhiều bản sửa được tách khỏi thí nghiệm scope đơn yếu tố, không quy mọi cải thiện cho một dòng prompt.

**Dấu vết đóng góp:** [PR #3](https://github.com/hhuydaugg/K5-L3-DAY03-NguyenHoangHuy-2A202603410-ResearchAgentToolEval/pull/3), [PR #5](https://github.com/hhuydaugg/K5-L3-DAY03-NguyenHoangHuy-2A202603410-ResearchAgentToolEval/pull/5) đã merge; commit tiêu biểu `ab7195d` (tool/group cases/tests), `57b3177` (scope có đối chứng), `a204ee8` (hardening), `8238631` (replay), `ac7c3a2` (bảo toàn bằng chứng nhóm). Tác giả các run còn được ghi trong `artifacts/version_log.csv`.

### Vũ Quang Dũng — MSSV 2A202603486

- Phát triển phương án riêng trên nhánh `QuangDung`: bổ sung các tool `filter`, `rank`, `sources`, đăng ký tool, tests và group cases; cập nhật prompt/declaration và chat/encoding cho quá trình thử nghiệm.
- Lưu các lượt eval và transcript Gemini. Các JSON trên nhánh riêng ghi nhận base v1 13/20, v2 15/20, v3 20/20 và group v3 10/10; các lượt này đo đủ số case và không lỗi provider. Đây là kết quả của phương án Gemini, không thay các kết quả OpenAI/OpenRouter ở B1.
- **Bằng chứng nhánh riêng:** commit `5a09a9f`, `fd66227`, `fec8aa0`; [nhánh QuangDung](https://github.com/hhuydaugg/K5-L3-DAY03-NguyenHoangHuy-2A202603410-ResearchAgentToolEval/tree/QuangDung). Các file base v1/v2/v3 Gemini có timestamp lần lượt `20261110T122013639908`, `20261110T122431453288`, `20261110T123228953059`; group v3 là `20261110T123423722288`.
- **Tình trạng tích hợp:** các commit/tool trên nhánh riêng này chưa được merge vào `main` tại thời điểm đối chiếu. Cần review và kiểm tra tương thích trước khi tích hợp; không tính chúng là các tool đang chạy trong bản main hoặc tự động cộng vào số tool mới của bản nộp hiện tại.
