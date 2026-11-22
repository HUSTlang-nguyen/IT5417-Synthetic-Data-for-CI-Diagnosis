# Dataset v2 và dataset portable trên Git

Được người dùng duyệt và bắt đầu goal ngày 23/11/2026 (Asia/Bangkok). Kế hoạch này thay bước chờ sau giữa kỳ, không thay lịch sử v1.

## Mục tiêu và cổng

- 700 real train, 150 real validation, 150 real test mới, 700 synthetic train; số tái sử dụng đã nằm trong các mục tiêu này.
- Ít nhất 8/3/3 repo theo train/validation/test; repo, fork, shared commit và duplicate family không qua split. Mỗi repo tối đa140real train,140synthetic train,60validation hoặc60test.
- Bốn lớp syntax, dependency/configuration, API/type, logic/value; tối thiểu30real train và10mẫu mỗi held-out split/lớp. Phân loại và file/hàm đều là nhiệm vụ chính. Nhãn silver có evidence, không tự thành expert gold.
- SWE-bench chính, AIDev bổ sung chọn lọc, không quota nguồn. Ghim revision và license/attribution trước xuất bản.
- V1 train có thể tái sử dụng sau audit/quota; synthetic chỉ giữ khi seed thuộc train v2. V1 validation/test chỉ là development lịch sử, không chuyển vào train/test v2. Repo held-out v2 chưa dùng phát triển trong dự án.

## Giới hạn bất biến qua resume

- 48giờ thực thi máy cộng dồn: download/build/reproduction/generation/verification/audit, không tính viết code, đọc review hay chờ người dùng. Không reset budget v1.
- Sàng lọc tối đa5000source identities, thử tối đa2000case mới, tối đa3000request7B mới. Không replay unknown. Tối đa một profile môi trường hiệu chỉnh có lý do/case.
- Docker và7B tuần tự, metadata/download độc lập tối đa2tác vụ. Build1200s/test300s/model180s. Baseline pass → ba fail ổn định → restoration pass; candidate chỉ chạy Docker cô lập.
- Không bắt đầu stage mới khi hết giờ, ổ artifact/Docker còn dưới40GiB hoặc artifact tăng100GiB so với baseline. Không tự prune/xóa cache/raw.
- Không gọi3B, train, chạy nhiều training seed, chấm model trên test hay sửa kết quả v1. Đợt train sau ưu tiên seed5417, kế hoạch riêng.

## Các mốc theo thứ tự

1. Khôi phục liên kết Git an toàn; kiểm tra artifact hiện có; tạo study/spec/status v2 riêng. Không reset/ghi đè file để khớp remote.
2. Đóng gói đúng351mẫu v1.1 (175/37/38real +101synthetic) vào research-data/v1.1; bảo toàn input/target/ID và liên kết hash lock gốc. Dùng manifest tương đối có hash riêng; không thay lock/lineage v1. Kiểm thử ở đường dẫn khác, không raw/Docker/model.
3. Rà50real/30synthetic train/development theo ci-data-review: taxonomy, causal location, plausibility, duplicates. Agent giải thích code→hành vi→log để người dùng review kết luận. Xác định module/missing definition và các trường hợp thiếu evidence.
4. Sàng lọc, khóa repo roles/dự phòng theo metadata trước thực nghiệm. Real cần failing/fixed cùng immutable harness, F2P/P2P khi có. Lỗi recipe không thành lỗi nguồn; profile không thành source case mới.
5. Cải thiện retrieval trên train/development; hỗ trợ SyntaxError bằng excerpt quan sát khi AST lỗi; không query bằng repair/reference/edit site. Khóa retrieval trước held-out export; context2048/output384. Lưu coverage trước/sau crop; không loại mẫu chỉ vì retrieval miss.
6. 7B sinh từ passing seed thuộc700real train đã chọn; tối đa2lô×3lượt/site khác nhau/case, seed/options hiện hành, max3000request mới. Giao thức sửa một dòng Python hợp lệ; không ép sinh syntax (bổ sung từ real). Candidate đạt runner còn phải qua curation/semantic dedup. Khác byte chưa đủ độc lập.
7. Audit/export research-data/v2, review/evidence, kiểm tra phục hồi, báo cáo theo source/repo/class và publish đủ điều kiện.

## Dataset Git và archive

- Giữ cấu trúc input/reference/assessment/metadata, manifest/splits/checksums/dataset card/provenance/license. Không để reference held-out đi vào train/retrieval/prompt. Chỉ xuất snapshot tuyển chọn, không mọi intermediate.
- Mỗi file dưới10MiB, tổng gói v1.1+v2 dưới100MiB. Vượt thì báo, không tự thêmLFS/DVC. Credential/privacy check trước publication; transformation phái sinh phải có trace, raw bất biến.
- Raw dataset/runs/full source/Docker/model/checkpoints ngoài Git. Evidence ngoài Git cần archive/checksum và restore test; không xóa bản gốc trong goal. Recipe rebuild không bảo đảm cùng image ID.
- Clone sạch phải đọc/validate package mà không có đường dẫn máy cũ, raw, model hay Docker. Không tuyên bố có thể resume checkpoint cũ chỉ từ Git.

## Kiểm thử và nghiệm thu

- Test quota/split/fork/duplicate/alias giữa nguồn; hash/path traversal, thiếu log, causal absence/module, input-reference boundary, syntax fallback.
- Test baseline/fixed/candidate/restoration failures, timeout/storage/budget stop, interrupted resume không duplicate request hoặc reset cap.
- Test portable package ở đường dẫn khác; checksum, mẫu số, attribution và source lock hash; xác nhận v1 bất biến. Chạy software suite trước đợt thật, nghiệm thu tích hợp bằng artifact thật.
- Snapshot data-manifests/dataset-v2-status.json cập nhật từng milestone: denominators, reuse/new, source/repo/class, coverage, time/requests/storage, lỗi, worker/stage, next action. Không audit lại toàn bộ chỉ để trả lời trạng thái.
- Đủ toàn bộ cổng mới khóa dataset; hết budget/thiếu cổng thì partial có lý do, không giảm cổng/ép nhãn hoặc báo goal đạt.
- Sau nghiệm thu commit/push code/docs/package đủ điều kiện lên nhánh codex, không tự merge main. Bàn giao phần đạt/thiếu, vị trí dữ liệu và bước tiếp theo; training tách riêng.

## Trạng thái

- A0 doing: khôi phục Git và inventory, chưa chạy dữ liệu mới.
- A1 todo: portable v1.1 và kiểm thử.
- B–E todo: calibration review, screening/roles, real/synthetic, audit/publication.
