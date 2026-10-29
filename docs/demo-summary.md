# W1-04 — Tổng kết demo 7B sinh dữ liệu có kiểm chứng

Ngày tổng kết: 29/10/2026, Asia/Bangkok. Đây là replay từ artifact PC đã lưu; soạn tài liệu không gọi model hoặc chạy test mới. [Bản rà ba lượt 7B](pilot-review.md) giữ phần xác nhận của người duyệt ở pending.

## Vai trò và workflow

| Thành phần | Vai trò hiện hành | Trạng thái |
|---|---|---|
| Qwen2.5-Coder-7B-Instruct | Generator duy nhất, sinh thay đổi Python từ seed pass | Đã có ba lượt thực tế trên PC |
| Docker runner | Chạy test gốc, kiểm tra baseline → fail lặp ba lần → restored pass | Có evidence thực thi đã lưu |
| Người duyệt | Xác nhận nhãn, vị trí, tuân thủ prompt, hợp lý và training eligibility | Pending |
| Qwen/Qwen2.5-Coder-3B-Instruct | Chẩn đoán chính; sau này chạy prompt-only/SFT và đánh giá | Chưa triển khai/chạy trong W1 |

Luồng: nguồn AIDev → pin repo/commit → tái hiện base/head → chọn head pass → 7B sinh → Docker kiểm chứng → người duyệt → dữ liệu cho 3B khi đạt các cổng dữ liệu sau này. Không dùng 3B làm generator; model phụ đã loại khỏi workflow hiện hành. Evidence lịch sử giữ nguyên.

## Nguồn và kết quả thật

- Case properr PR #6, AIDev v5 record 3256868569. Base `eff739a28971a66a36d443bfde91c515f7a858ea`; head `8fd30245ed66b5145d651efc9203eb9a911e95d5`. Repo có Python và Rust.
- [Tái hiện PC](evidence/target-pc/historical/report.html): base exit 1 vì thiếu pytest; head exit 0, hai test pass. Đây là tái dựng local, không phải CI lịch sử hoặc bằng chứng actor gây lỗi.
- Run sinh [generate-20261029T054921315491Z](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/manifest.json), [HTML đã lưu](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/report.html); PC RTX 4070 SUPER, host Python 3.11.9, container Python 3.11.2, Ollama 0.40.13. Digest và hash nằm trong bản review. Hai liên kết raw này trỏ checkout gốc trên máy hiện tại; trên máy khác cần artifact root tương ứng, vì raw runs không đi theo Git/worktree.
- Lúc nghiệm thu pilot trước đây: [22 software tests pass gồm Docker thật](evidence/target-pc/software-tests-final.txt). Đây là log lịch sử; kiểm thử phần mềm sau sửa workflow được ghi riêng trong agent-log, không ghi đè log này.

| Lượt 7B | Seed | Giây gọi sinh | Kết quả thực thi | Vấn đề chất lượng |
|---|---:|---:|---|---|
| 01 | 5417 | 39.984 | verification_failed; ba repetitions vẫn pass | Wrapper không tác động test; comment/tên hàm tiết lộ lỗi |
| 02 | 5418 | 4.781 | execution_verified; TypeError ổn định | Sai cách dùng API; comment tiết lộ lỗi; nhãn model không khớp log |
| 03 | 5419 | 4.609 | execution_verified; assertion failure ổn định | Nhân stddev với 1.1; comment tiết lộ lỗi; nhãn model không khớp log |

**Đạt kiểm chứng thực thi: 2/3 lượt 7B.** Mẫu số gồm cả lượt không làm test fail. Không gọi đây là hai mẫu đã duyệt hoặc độ chính xác chẩn đoán; 3B chưa được chạy. Cả ba proposal ghi `syntax`, trong khi lỗi quan sát và cơ chế khác nhau; nhãn xác nhận vẫn pending.

Tổng giây gọi sinh là **49.374**, gồm runtime/model loading; lượt đầu có khởi tạo runtime, load_duration 18.9410453 giây. Không gồm tải model, build image, Docker verification hoặc toàn bộ buổi demo. Chỉ ba lượt trên một case, không phải benchmark tốc độ. Snapshot GPU trong doctor không phải peak VRAM của model.

## Phân biệt các mức đạt

1. **Đạt thực thi:** baseline pass, ba lỗi test có chữ ký ổn định, restored pass. Runner không tự xác nhận nhãn hoặc độ hợp lý.
2. **Đạt tuân thủ/chất lượng:** cần rà prompt, cơ chế lỗi, comment tiết lộ đáp án và tính phù hợp nhiệm vụ. Cả ba output hiện có đều chứa dấu hiệu tiết lộ lỗi.
3. **Được dùng để train:** cần người duyệt và các điều kiện taxonomy, split, evidence, lọc trùng của giai đoạn sau. Hiện chưa có phê duyệt; kiến nghị agent trong review không thay quyết định của người duyệt.

## Replay khoảng năm phút

| Thời gian dự kiến | Nội dung |
|---|---|
| 0:00–0:40 | Nêu bài toán và vai trò 7B sinh / 3B chẩn đoán; nói rõ đang replay |
| 0:40–1:20 | Mở tái hiện properr: base thiếu pytest, head hai test pass; giải thích giới hạn lịch sử |
| 1:20–2:30 | Xem manifest 7B, prompt, hash source/tests và giao thức ba seed |
| 2:30–3:50 | Xem ba diff, baseline/repetitions/restoration; giữ cả lượt không làm test fail trong mẫu số |
| 3:50–4:30 | Đối chiếu TypeError, sai số và nhãn syntax do model đề xuất; nêu comment tiết lộ lỗi |
| 4:30–5:00 | Mở bảng pending cho người duyệt; kết luận khả thi của pipeline và phần chưa được xác nhận |

Không chạy model/test chỉ để replay. Nếu chưa có raw runs trên máy trình bày, khôi phục archive trước; không tạo output hoặc log thay thế. CLI/demo mới chỉ dành cho lượt sinh mới bằng 7B, không dùng để sửa pilot cũ.

## Giới hạn và bước tiếp theo

Một repo, hai test, ba lượt và seed phát triển đã được xem không tạo thành benchmark hoặc test độc lập. Toolchain tái dựng không hoàn toàn hermetic; chưa có peak VRAM, nhãn gold, dataset train, kết quả chẩn đoán 3B, SFT, ablation hoặc interceptor. Kiểm tra trực quan HTML vẫn pending do browser policy chặn file cục bộ; không dùng cách vòng tránh.

W1-04 hoàn tất khi số liệu và liên kết trong tổng kết khớp evidence. W1-03 đã hoàn tất review kết luận: người dùng đồng ý loại 01 khỏi tập mẫu lỗi và giữ 02/03 làm ứng viên có bằng chứng. Nhãn gold/vị trí theo schema và quyền dùng để train vẫn pending; xác nhận được ghi riêng trong pilot-review. Chưa mở rộng W2, sửa prompt hoặc chạy 3B trong lượt triển khai này; task kế tiếp là W2-01 chốt input/output, sau đó taxonomy và tiêu chí dữ liệu cho model chẩn đoán. Chưa tạo slide hoặc sửa tài liệu gốc.
