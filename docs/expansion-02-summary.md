# Tổng kết development 02 — thêm case và giao thức site v3

Ngày 30/10/2026. [Registry](../data-manifests/expansion-02.json), [profile hiệu chỉnh](../data-manifests/expansion-02-corrections.json), [số liệu thực](evidence/expansion-02/summary.json), [review kỹ thuật](expansion-02-review.md), [grouping/duplicate snapshot](../data-manifests/development-groups-v1.json).

## Kết quả mới

| Hạng mục | Đợt chính | Hai profile hiệu chỉnh | Không đếm trùng |
|---|---:|---:|---|
| Case nguồn đã sàng lọc | 20 (10 AIDev + 10 SWE Lite dev) | Dùng lại pool đó | 20 nguồn mới |
| Profile thử tái hiện | 8 | 2 | 10 lần thử, 8 case nguồn trên 5 repo |
| Giả thuyết local được hỗ trợ theo matcher đã khai báo | 3 | 1 | 4 case nguồn |
| Seed fixed pass | 4 | 1 | 5 case nguồn |
| Lượt 7B thực hiện | 12 | 3 | 15 |
| Lượt đạt theo runner | 10 | 1 | 11, cũng là 11 candidate khác byte |

Mẫu số profile: 24 lượt yêu cầu đợt chính + 6 lượt ở hai profile hiệu chỉnh = **30 slot**; 15 slot thực hiện, 15 chưa thực hiện vì không có passing seed. Không gọi hai profile hiệu chỉnh là hai case nguồn mới. Raw parent và profile cũ giữ nguyên; mỗi `-r1` có `source_case_id`, `trial_of` và lý do riêng.

Trong 15 output có **11 execution_verified, 3 verification_failed vì không làm test fail, 1 invalid_output vì không đổi dòng**. Một candidate execution_verified gây IndentationError, vi phạm prompt v3 yêu cầu source hợp lệ; cần phân biệt acceptance của runner với chất lượng/protocol. Agent kiến nghị loại nó khỏi subset v3 valid-Python khi curate; không xóa raw hoặc tự phê duyệt các candidate khác.

## Khác biệt so với đợt 01

- Đợt 02 bổ sung failure được kiểm chứng ở **astroid, pvlib và FastAPI**, ngoài pydicom của đợt 01.
- V3 cho model chọn `site_id` từ source đã pin rồi trả một dòng replacement không có indentation. Pipeline thêm lại indentation/newline nguyên trạng theo hợp đồng; không sửa nội dung model để cho test fail. Các site cho ba lượt được phân bổ riêng khi có đủ site.
- Prompt có excerpt của upstream tests và source; **7B không còn bị yêu cầu tự gán nhãn chẩn đoán** trong v3. Raw v2/W1 và self-label cũ giữ nguyên. Model, options, budget token và các seed 5417/5418/5419 không đổi.
- Test IDs nguồn chỉ được resolve bằng exact match hoặc **một** tên parameterized test đầy đủ có prefix nguồn bị cắt. Plain/fuzzy/ambiguous prefixes bị từ chối; mapping từng ID được lưu trong manifest. astroid-1866 vẫn chưa resolve được ID có escape newline, nên flag lịch sử còn false dù fixed seed pass.
- AST được parse tĩnh từ seed/test nguồn để lập site/excerpt; không import hoặc chạy candidate trên host. Runtime Docker vẫn không mạng/read-only/không đặc quyền và có giới hạn.

Hai cohort khác case và giao thức, nên các tỷ lệ này chưa là đối chứng chứng minh v3 tốt hơn v2 hoặc synthetic cải thiện chẩn đoán.

## Lỗi được giữ và profile hiệu chỉnh

| Case/profile | Kết quả và giới hạn |
|---|---|
| PyLabRobot #528 gốc | Bộ nhận diện test chưa chấp nhận `resource_tests.py` nằm ngoài thư mục tests. Lỗi được giữ, không sinh |
| PyLabRobot #528-r1 | Đã sửa nhận diện `*_tests.py`, giữ tmpfs logs/test_logs. Guard tiếp tục chặn vì base/head còn khác test serializer không được khai báo. Không nới guard hoặc tạo trial thứ ba; cần xác định lại đúng commit transition trước khi thử tiếp |
| shillis13/python #33 | Archive có symlink `scripts/chatConverter.py`; export từ chối. Không chạy test/model và không theo symlink |
| FastAPI #15232 gốc | Build có xung đột pytest 7.4.4 với inline-snapshot yêu cầu >=8.3.4 |
| FastAPI #15232-r1 | Recipe ghim pytest 8.3.5 và load rõ `inline_snapshot.pytest_plugin`, vẫn tắt plugin autoload. Base fail/fixed pass; ba lượt sinh, một đạt thực thi |
| astroid #1333 | Một upstream test tạo symlink trong CWD read-only; fixed có 1 failure. Không có seed và không gọi model |
| astroid #1866 | Fixed pass nhưng một source FAIL_TO_PASS ID bị cắt/escape không resolve; giữ flag lịch sử false. Synthetic chỉ khởi động từ gate pass độc lập |

GitHub metadata API chạm rate limit; public patch/Git refs được đọc với provenance riêng. sshpilot-418 có public patch head khác live pull ref nên không chọn; không chế dữ liệu API hoặc lặng lẽ thay commit. Bảy AIDev không đủ điều kiện chạy trong pool được giữ với lý do, không bù bằng thêm SWE vượt quota.

## Thời gian, kiểm tra và bàn giao

Đợt chính chạy **06:52:40–06:58:36 +07**; hai profile hiệu chỉnh chạy **06:59:44–07:01:37 +07**. Tổng budget charge được ghi nhận là **527,436 giây**: profile hiệu chỉnh kế thừa 414,546 giây đã charge của đợt chính, không cộng khoản này lần thứ hai. Các metadata fallback chưa có timer đầy đủ không được giả làm số đo chính xác; thời gian coding nằm ngoài. Tổng thời gian 15 lời gọi model **50,406 giây**, có loading/runtime, không là steady-state benchmark.

Integrity audit kiểm tra **6 image**, cả base/fixed source/test inventories đều khớp. Đã đọc **87 JUnit / 2.822 testcase records có lặp**, replay phép thay thế cho 14 candidate hợp lệ, kiểm tra hash và acceptance signatures. **1.087 file run/evidence có trước đợt và 1.018 raw file mới được ghi inventory giữ nguyên byte.** Raw artifacts không đi theo clone.

Phần mềm hiện có **58 tests: 57 pass, một legacy Docker test opt-in skip**; [output thật](evidence/expansion-02/software-tests.txt). Đây là software fixtures, tách khỏi Docker/model experiment evidence.

Cộng hai đợt mở rộng: **40 case nguồn sàng lọc, 17 case nguồn đã thử trên 10 repo**, thêm hai profile hiệu chỉnh không tính nguồn mới; **36 lượt 7B, 17 lượt đạt runner, 14 candidate khác byte đạt runner**. Trong đó một candidate v3 vi phạm valid-syntax như review nêu. Snapshot grouping chứa 40 nguồn / 42 profile records / 20 repo groups, gồm cả case bị loại; 20 groups không có nghĩa đã chạy 20 repo. Exact duplicates và lexical-edit suggestions được ghi riêng, không tự xóa hay phê duyệt mẫu.

Tất cả vẫn là development; **gold labels, training eligibility và test split cuối chưa được phê duyệt**. Bước tiếp theo W2-04 là xử lý grouping/near-duplicate và chọn nguồn đánh giá chưa dùng phát triển, trước vòng train. Chưa chạy 3B/SFT hoặc sửa evidence W1/đợt 01.
