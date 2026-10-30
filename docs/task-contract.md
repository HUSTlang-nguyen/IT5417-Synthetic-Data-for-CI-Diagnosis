# Hợp đồng chẩn đoán — development v0.1

Ngày 30/10/2026. Áp dụng cho đợt mở rộng đầu; chưa khóa protocol đánh giá cuối và chưa triển khai model chẩn đoán 3B.

## Đơn vị và nguồn

Một case nguồn là một tình huống gắn với repo/revision và một bộ test độc lập đã định danh. Một lượt synthetic là một output của 7B trên seed của case đó; ba lượt cùng case không thành ba case nguồn độc lập.

AIDev cung cấp PR-level provenance. SWE-bench Lite cung cấp bài toán, reference repair/test patch và danh sách test mục tiêu. Đợt này dùng các case được chọn từ cả hai nguồn cho **development**. Case, repo và duplicate family đã xem không được gọi là test độc lập cuối cùng. Chưa chia train/validation/test hoặc phê duyệt train.

## Input được phép

- Log thật của lần chạy cần chẩn đoán: stdout/stderr, exit code, timeout, JUnit và môi trường/lệnh test liên quan. Stack trace và số dòng là bằng chứng hợp lệ.
- Code tương ứng với lần chạy và revision/hash; ghi rõ phần nào là excerpt. Code candidate đầy đủ vẫn nằm trong raw artifacts để người rà đối chiếu.
- Diff chỉ khi xác định được hai trạng thái và vai trò của diff. Với synthetic, có thể dùng passing-seed → candidate nếu biến thể input đã khai báo. Với SWE-bench, gold repair patch là đáp án tham chiếu, không phải diff tạo lỗi.

Không đưa gold repair patch, nhãn tham chiếu, proposed_label, explanation của generator hoặc nhận định reviewer vào input để model dự đoán chính thông tin đó. Những trường này ở phần reference/review riêng. Không tự coi PR actor là tác giả gây lỗi.

Giai đoạn hiện tại chưa tạo tập input huấn luyện. Khi đóng gói sau này, phải khai báo chính xác log/code/diff nào được đưa vào từng biến thể và rà comment/metadata trên input đó. Giữ raw code nguyên trạng; không xóa comment trong raw để biến output thành mẫu đạt.

## Đầu ra review tối thiểu

| Trường | Ý nghĩa |
|---|---|
| case_id / run_id / attempt | Truy vết đơn vị nguồn và lượt sinh |
| observed_status | pass / failure / environment_error / timeout / unknown theo artifact |
| observed_failure | Exception/assertion hoặc triệu chứng có bằng chứng |
| generator_proposal | Nhãn/lời giải thích model nguyên trạng, chưa xác nhận |
| agent_assessment | Cơ chế, nhãn/vị trí đề xuất, mức chắc chắn có lý do và kiến nghị |
| evidence | File/hash/log/JUnit/dòng hỗ trợ; phân biệt nơi test phát hiện và nơi code gây lỗi |
| human_confirmation | Chỉ quyết định người dùng đã phát biểu rõ; mặc định pending |
| training_eligibility | pending cho tới khi có tiêu chí dữ liệu và phê duyệt riêng |

Thiếu log, hash sai hoặc chưa xác định được nguyên nhân thì ghi unknown/phần thiếu. Không suy đáp án từ tên case, comment hoặc generator self-label. Environment error không tự trở thành nhãn lỗi ứng dụng.

## Tái hiện và sinh

AIDev v2 dùng base/head được ghim cùng bộ upstream regression tests từ head đã lưu hash; đây là local reconstruction với harness cố định, không phải nguyên trạng CI lịch sử. Tách `historical_supported` khỏi `head_passed`: seed pass có thể đủ cho thí nghiệm synthetic dù giả thuyết lịch sử chưa được xác nhận.

SWE-bench dùng cùng test patch trên base và base + reference repair patch; đối chiếu FAIL_TO_PASS/PASS_TO_PASS. Patch sửa và patch test có hash riêng. Các recipe là reconstruction giới hạn theo test mục tiêu, không phải khẳng định tương đương mọi môi trường của benchmark chính thức.

Giao thức `single-file-exact-edit-v2` cung cấp excerpt từ seed pass và test target cho 7B; yêu cầu `path`, `before`, `after`, `proposed_label`, `explanation`. `before` phải khớp đúng một lần trong file đã pin. Pipeline áp dụng đúng phép thay thế, lưu candidate đầy đủ, diff và raw output. Đây là giao thức mới; output/giao thức properr W1 không đổi. Model/options/ba seed vẫn giữ hiện hành; schema nhãn generator không quyết định taxonomy chẩn đoán.

Baseline pass → ba candidate fail ổn định → restored pass chỉ xác nhận điều kiện thực thi. Không tự xác nhận gold label, tính đại diện hoặc training eligibility. Docker không mạng, không đặc quyền và có giới hạn tài nguyên; candidate không chạy trên host.

## Bổ sung giao thức development v3 — 30/10/2026

V3 mới chỉ thay giao diện generator, không đổi input/output diagnosis hay trạng thái phê duyệt: `path`, `site_id`, `replacement`, `explanation`. Không có trường generator diagnosis label được yêu cầu. Site catalog được tạo tĩnh từ seed pass; replacement là một dòng không có leading indentation, renderer giữ indentation/line ending gốc. Per-attempt source/test excerpts, allowed sites và request/raw response đều lưu để replay. Các lượt v2 và W1 vẫn dùng giao thức đã lưu của chúng.

Site catalog, selected site_id, replacement/proposal và generator-localized excerpt là provenance của phép sinh, không tự trở thành input 3B. Đặc biệt không đưa selected site vào input khi model phải dự đoán vị trí. Bug-introducing diff hoặc stack trace vẫn là evidence hợp lệ nếu biến thể task cho phép rõ; metadata tiết lộ phép edit được giữ riêng.

Một candidate v3 gây lỗi cú pháp dù prompt yêu cầu Python hợp lệ: runner acceptance, prompt compliance và training eligibility phải đánh giá riêng. Profile correction là trial của source_case_id cũ, có reason/trial_of và budget kế thừa; không nâng số case nguồn độc lập. Grouping snapshot giữ toàn bộ development; lexical duplicate suggestions không tự là semantic-equivalence/gold decision.

## Phần chưa triển khai sau hai đợt

3B inference, SFT, interceptor, benchmark cuối và chính sách trộn train chưa thuộc đợt này. Các quyết định đó tiếp tục theo [roadmap](implementation-plan.md); review theo [hướng dẫn nhãn](labeling-guide.md) và skill của repo.
