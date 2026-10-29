# Kế hoạch thực thi theo tuần dành cho agent

Cập nhật: 29/10/2026, Asia/Bangkok. Đây là danh sách công việc để agent tiếp tục triển khai toàn đề tài, không chỉ mô tả kiến trúc hoặc ghi lại việc đã làm.

## Cách dùng khi bắt đầu hoặc khôi phục context

1. Đọc [architecture](architecture.md), các mục mới nhất trong [agent-log](agent-log.md), rồi file này; kiểm tra Git status trước khi sửa.
2. Làm task chưa xong đầu tiên có đủ điều kiện phụ thuộc, bắt đầu ở mục **Điểm tiếp tục hiện tại**. Không bắt đầu lại task đã có evidence chỉ vì mất context.
3. Trước khi làm, đổi trạng thái task thành `doing`. Khi hoàn thành, ghi artifact và kết quả kiểm tra vào agent-log; cập nhật trạng thái/điểm tiếp tục ở đây. Thay đổi kiến trúc hoặc giao thức phải cập nhật architecture.
4. `done` cần đầu ra và bằng chứng đạt điều kiện hoàn thành. Viết code xong không đồng nghĩa thí nghiệm hoặc nhãn đã được xác nhận.
5. Nếu cần dữ liệu, phần cứng hoặc quyết định của người dùng, ghi rõ ở task (`waiting_user`/`blocked`), tiếp tục việc độc lập có ích. Không tự điền nhãn gold, kết quả hoặc quyết định phạm vi còn mở.

Trạng thái: `todo` / `doing` / `waiting_user` / `blocked` / `done` / `deferred`. Đây là trạng thái task trong tài liệu, không phải trạng thái một công cụ quản lý goal.

**Lịch dự kiến:** sáu tuần tương đối theo thứ tự dưới đây; tuần 1 là chặng demo đầu đang khép lại. Chưa có deadline lịch được xác nhận, vì vậy không tự gán ngày kết thúc. Mỗi chặng có thể kéo dài; chỉ chuyển qua cổng nghiệm thu khi đủ bằng chứng. Task độc lập có thể chuẩn bị trước, nhưng không bỏ qua điều kiện dữ liệu/nhãn.

## Điểm tiếp tục hiện tại

- **Task kế tiếp: W1-03.** Chuẩn bị `docs/pilot-review.md` từ evidence thật; ghi nhận xét đề xuất và các ô cần người duyệt, giữ trạng thái pending.
- Pilot PC đã chạy: properr head pass hai test; 22 kiểm thử phần mềm pass; đủ sáu lượt sinh. 7B đạt kiểm chứng thực thi 2/3, 1.5B 1/3. Đây chưa phải số mẫu được duyệt để train.
- Run 7B: `generate-20261029T054921315491Z`; 1.5B: `generate-20261029T055021908791Z`. [Evidence đã commit](evidence/target-pc/README.md); raw run/ZIP nằm local, không đi theo Git clone. Nếu thiếu raw artifacts, khôi phục archive phù hợp hoặc yêu cầu cung cấp; không dựng lại output bằng tay.
- Không tải lại model/chạy lại pilot chỉ để cập nhật tài liệu. Giữ nguyên kết quả vòng đầu, kể cả các lượt bị loại.

## Tuần 1 — Hoàn tất demo và rà chất lượng pilot

| ID | Trạng thái | Việc làm theo thứ tự | Đầu ra / điều kiện hoàn thành |
|---|---|---|---|
| W1-01 | done | Dựng package Python, CLI, runner cô lập, manifest/report và context docs | Mã hiện có; kiểm tra thực thi và hash test. [Architecture](architecture.md) |
| W1-02 | done | Tái hiện properr trên PC; chạy hai model, ba lượt mỗi model; giữ mọi thất bại | [PC evidence](evidence/target-pc/README.md): 22 tests pass, sáu lượt và comparison tương thích; không tự gán gold |
| W1-03 | todo | Rà cả sáu lượt: hai output cắt, một ứng viên không làm test fail, ba ứng viên đạt thực thi. So diff/log của bốn ứng viên có file | `docs/pilot-review.md`: run/attempt, nguồn evidence, lỗi quan sát, nhãn/vị trí đề xuất, tuân thủ prompt, tính hợp lý, quyết định sử dụng và người duyệt. Các trường xác nhận để pending đến khi người duyệt trả lời |
| W1-04 | todo | Tổng hợp demo từ số đo thật và vấn đề chất lượng; phụ thuộc bản review dự thảo W1-03 | `docs/demo-summary.md`: workflow, kết quả 2x3, định nghĩa đạt thực thi/được duyệt, thời gian gồm gì, giới hạn và việc tiếp theo. Nếu cần slide, outline không quá 20 slide; chưa sửa slide gốc chỉ vì tạo roadmap |

**Cổng G1:** artifact chạy thật có thể xem lại, kết quả không bị sửa tay, mọi lượt có trạng thái; có bảng review nêu rõ phần chưa được duyệt. Có thể chuẩn bị tuần 2 khi review còn pending, nhưng chưa coi mẫu là dữ liệu train.

## Tuần 2 — Chốt bài toán, nhãn và subset dữ liệu thật

| ID | Trạng thái | Phụ thuộc / hành động | Đầu ra / điều kiện hoàn thành |
|---|---|---|---|
| W2-01 | todo | Dựa W1-03/04 và revised-plan, định nghĩa input/output chẩn đoán, thông tin được phép thấy, vai trò AI/code/người; ghi câu hỏi workflow/interceptor còn mở | `docs/task-contract.md`: ví dụ input/output, phạm vi phân loại/khoanh vùng/trạng thái, unknown/thiếu thông tin và các quyết định chưa chốt. Không tự implement interceptor |
| W2-02 | todo | Từ W2-01, lập taxonomy nhỏ và hướng dẫn gắn nhãn | `docs/labeling-guide.md`: định nghĩa, phản ví dụ, mức file/hàm/dòng, trường hợp chưa xác định, nguồn bằng chứng và thủ tục người duyệt. Không ép actor/nhãn khi nguồn không đủ |
| W2-03 | todo | Chọn thêm repo/case theo tiêu chí có mục đích; mở rộng harness từng repo, chưa tải toàn bộ AIDev | Registry nhỏ trong `data-manifests/`: nguồn/revision/id/base/head/test command/giấy phép, lý do chọn/loại, chi phí và kết quả tái hiện thật. Raw code/data ở thư mục bị ignore. Mục tiêu thăm dò 10–20 tình huống từ tài liệu nghiên cứu là dự kiến, không phải quota đã hoàn thành hoặc yêu cầu 20 repo/label |
| W2-04 | todo | Dựa registry và W2-02, xác định group id, duplicate family và vai trò train/validation/test trước vòng sinh mở rộng | `docs/experiment-protocol.md` bản nháp + split manifest có hash. properr/case đã dùng phân tích pilot thuộc phần phát triển, không gọi là test chưa từng xem. Tỷ lệ 70/15/15 chỉ là phương án, phải đối chiếu số nhóm/lớp thực tế |

**Cổng G2:** có subset thật tái hiện được, dữ liệu đủ input và nhãn được duyệt cho nhiệm vụ đã chọn; mỗi nhóm chỉ ở một split. Nếu support quá ít, giảm taxonomy/phạm vi và ghi lý do trước khi mở rộng sinh. Không dùng synthetic để che việc chưa có test thật độc lập.

## Tuần 3 — Hoàn thiện sinh và kiểm chứng trên phần phát triển

| ID | Trạng thái | Phụ thuộc / hành động | Đầu ra / điều kiện hoàn thành |
|---|---|---|---|
| W3-01 | todo | Từ review W1-03 và train groups W2-04, thiết kế vòng prompt/budget mới xử lý output cắt, bug-disclosing comments và thay đổi kém hợp lý | Giao thức version mới: prompt/options/model digest/seed/ngân sách/lý do thay đổi. Không ghi đè vòng 2x3 đầu; không sửa output model để biến mẫu lỗi thành mẫu đạt |
| W3-02 | todo | Sinh trên seed pass của **train groups**, chạy baseline → fail ổn định → hoàn tác; mở rộng allowlist/test command theo từng repo đã cấu hình | Run manifests, raw requests/outputs/diff/log/timeout/cost; tests giữ nguyên, container không mạng và có giới hạn. Lỗi JSON/build/timeout/không làm test fail được giữ trong tổng lượt |
| W3-03 | todo | Rà nhãn, vị trí, hợp lý và trùng lặp; phân biệt kiểm chứng thực thi với toàn bộ tiêu chí dùng để train | Review records có người duyệt, bảng lý do loại/yield theo lớp/nguồn; các nhãn chưa xác nhận vẫn pending, không tự thành gold |

**Cổng G3:** giao thức tái lập được, ứng viên đủ evidence và bộ tiêu chí nhận/loại được ghi rõ. Không kết luận hai model tốt hơn nhau một cách tổng quát từ một case hoặc chỉ số 2/3 và 1/3.

## Tuần 4 — Khóa protocol và đóng gói dataset

| ID | Trạng thái | Phụ thuộc / hành động | Đầu ra / điều kiện hoàn thành |
|---|---|---|---|
| W4-01 | todo | Chốt protocol dựa phần phát triển W2/3: nhiệm vụ, splits, nhãn, model chẩn đoán, metric, ngân sách, seeds và cấu hình ưu tiên | `docs/experiment-protocol.md` version khóa + decision log. Chốt tách riêng hai trục thật-only/thật+synthetic và fail-only/pass+fail; nếu thiếu nguồn pass thì ghi chưa thực hiện, không tự coi head pass là một mẫu chẩn đoán đã có nhãn |
| W4-02 | todo | Đóng gói real train/validation/test và synthetic từ train groups theo schema thống nhất | Dataset version + manifests/checksums/source lineage + `docs/dataset-card.md`. Raw dataset bị ignore; chỉ metadata nhỏ hợp lệ đi vào Git |
| W4-03 | todo | Kiểm tra leakage, near-duplicate, nhãn pending, trường đáp án lộ trong input và tính đầy đủ evidence | Lệnh kiểm tra có report: không giao nhóm/duplicate family giữa splits; validation/test thật không chứa synthetic; TF-IDF/statistics chỉ fit train. Không dùng validation/test làm seed sinh |

**Cổng G4:** dataset/protocol được version hóa và kiểm tra tái lập. Tỷ lệ/chia tập/filter không đổi vì điểm test. Cross-validation theo nhóm trong development là tùy protocol/số liệu; synthetic chỉ nằm ở phần train tương ứng của mỗi fold nếu dùng, test cuối vẫn độc lập.

## Tuần 5 — Baseline và thí nghiệm chính

| ID | Trạng thái | Phụ thuộc / hành động | Đầu ra / điều kiện hoàn thành |
|---|---|---|---|
| W5-01 | todo | Từ G4, implement loader/evaluation và M0 TF-IDF + Logistic Regression cho **phân loại** | CLI/config/report; pipeline fit train, metric có support/confusion matrix. Đây là baseline từ đề xuất nghiên cứu, không đánh giá khả năng sinh giải thích hoặc khoanh vùng bằng classifier |
| W5-02 | todo | Chạy M1 prompt-only; pilot runtime của model chẩn đoán dự kiến 3B Instruct trước SFT | Lưu checkpoint revision/chat template/context, tốc độ và VRAM thực đo. Model sinh 7B/1.5B không mặc nhiên là model chẩn đoán |
| W5-03 | todo | Khi dữ liệu/VRAM cho phép, chạy M2 SFT real-only và M5 real+verified-synthetic theo protocol | Config/checkpoint/log/chi phí; cùng checkpoint nền và input/validation; kiểm soát lượng dữ liệu/phân bố và công bố số token/update. Mọi thay đổi vì OOM tạo config mới |
| W5-04 | todo | Dùng validation chọn checkpoint/tham số theo protocol đã khóa; chưa mở test để sửa cấu hình | Bảng kết quả phát triển + cấu hình cuối. Nếu thiếu thời gian/dữ liệu, ghi thiếu thí nghiệm thay vì tạo kết quả hoặc kết luận hiệu quả |

**Cổng G5:** có baseline thật và cấu hình cuối truy vết được. Chỉ nói tác dụng fine-tuning/synthetic khi đối chứng tương ứng tồn tại; ba mẫu đạt thực thi hiện tại chưa đủ thay thế dataset huấn luyện.

## Tuần 6 — Đối chứng bổ sung, đánh giá và báo cáo

| ID | Trạng thái | Phụ thuộc / hành động | Đầu ra / điều kiện hoàn thành |
|---|---|---|---|
| W6-01 | todo | Thực hiện M3/M4 và fail-only/pass+fail theo protocol/tài nguyên; đánh dấu deferred kèm lý do nếu chưa thể | Bảng ablation có task/input/model/split/ngân sách tương ứng. M4 vẫn có thực thi/log; khác ở xác minh nhãn/lọc đầy đủ, không trộn mẫu thiếu an toàn hoặc thiếu input vào train |
| W6-02 | todo | Sau G5 và các lựa chọn đã khóa, chấm test thật độc lập | Macro-F1 và từng lớp; Top-k đúng mẫu số nếu triển khai khoanh vùng; trạng thái pass/unknown chấm riêng. Lặp seeds theo khả năng, báo từng lượt và độ dao động, không chỉ điểm tốt nhất |
| W6-03 | todo | Phân tích sai, slop/lộ đáp án, chất lượng nhãn, chi phí và giới hạn; đóng gói tái lập | `docs/results.md`, kết quả tổng hợp nhỏ, manifests và runbook khôi phục. Không quy cải thiện cho filtering nếu thiếu đối chứng phù hợp, không mặc định synthetic có lợi |
| W6-04 | todo | Chuẩn bị báo cáo/demo và bảng giải trình GVHD từ kết quả thật | Outline không quá 20 slide, bảng sửa gì/ở đâu, demo live hoặc replay ghi rõ, danh sách giới hạn. Dựng slide theo yêu cầu thực tế và skill liên quan; giữ nguyên tài liệu gốc nếu chưa được yêu cầu sửa |

**Cổng G6:** các kết luận đều trỏ được đến thí nghiệm/evidence; hạn chế và phần chưa làm được ghi công khai. M6 sinh cho lớp hiếm, model chẩn đoán bổ sung và interceptor không mặc định là việc đã triển khai.

## Quy tắc bàn giao cuối mỗi phiên

- Ghi task ID, file/run/config đã tạo, kiểm tra pass/fail, lỗi gặp và điều kiện còn thiếu vào agent-log theo Bangkok.
- Cập nhật trạng thái task, evidence và **một task kế tiếp cụ thể** ở đầu file này; không đánh dấu cả tuần done khi còn nhãn/đối chứng chưa xong.
- Cập nhật architecture nếu thay interface/schema/protocol/runtime. Lưu quyết định nghiên cứu riêng trong protocol; không dùng nhật ký thay cho cấu hình thí nghiệm.
- Giữ raw evidence bất biến; sửa report bằng cách dựng lại từ artifact, đổi thí nghiệm bằng run/version mới. Chỉ chạy lại khi có lý do và ghi mối liên hệ với run cũ.
- Kiểm tra phù hợp với thay đổi; chỉnh Markdown không cần chạy lại model/Docker. Trước commit/push, kiểm tra diff, link, secrets và file lớn; không stage cache/weights/raw data. Không xóa stash backup đang được giữ theo yêu cầu trước.

Nguồn và thứ tự ưu tiên: yêu cầu mới nhất của người dùng → quyết định đã chốt trong protocol → [revised-plan](revised-plan.md) / [nghiên cứu §6–10](reference/00_bao_cao_dinh_huong_nghien_cuu.md) → lộ trình dự kiến này. Architecture/evidence phản ánh trạng thái thật, không suy hoàn thành từ bản kế hoạch. Khi đổi phạm vi hoặc lịch đã thống nhất, sửa roadmap và ghi lý do.
