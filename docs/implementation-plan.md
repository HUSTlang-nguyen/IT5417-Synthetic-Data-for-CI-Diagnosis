# Kế hoạch thực thi theo tuần dành cho agent

Cập nhật context: 13/11/2026, Asia/Bangkok; đã chốt validation, final test và phân tích pilot. Đây là danh sách công việc để agent tiếp tục triển khai toàn đề tài, không chỉ mô tả kiến trúc hoặc ghi lại việc đã làm.

## Cách dùng khi bắt đầu hoặc khôi phục context

1. Đọc [architecture](architecture.md), các mục mới nhất trong [agent-log](agent-log.md), rồi file này; kiểm tra Git status trước khi sửa.
2. Làm task chưa xong đầu tiên có đủ điều kiện phụ thuộc, bắt đầu ở mục **Điểm tiếp tục hiện tại**. Không bắt đầu lại task đã có evidence chỉ vì mất context.
3. Trước khi làm, đổi trạng thái task thành `doing`. Khi hoàn thành, ghi artifact và kết quả kiểm tra vào agent-log; cập nhật trạng thái/điểm tiếp tục ở đây. Thay đổi kiến trúc hoặc giao thức phải cập nhật architecture.
4. `done` cần đầu ra và bằng chứng đạt điều kiện hoàn thành. Viết code xong không đồng nghĩa thí nghiệm hoặc nhãn đã được xác nhận.
5. Nếu cần dữ liệu, phần cứng hoặc quyết định của người dùng, ghi rõ ở task (`waiting_user`/`blocked`), tiếp tục việc độc lập có ích. Không tự điền nhãn gold, kết quả hoặc quyết định phạm vi còn mở.

Trạng thái: `todo` / `doing` / `waiting_user` / `blocked` / `done` / `deferred`. Đây là trạng thái task trong tài liệu, không phải trạng thái một công cụ quản lý goal.

**Lịch dự kiến:** sáu tuần tương đối theo thứ tự dưới đây; tuần 1 là chặng demo đầu đang khép lại. Chưa có deadline lịch được xác nhận, vì vậy không tự gán ngày kết thúc. Mỗi chặng có thể kéo dài; chỉ chuyển qua cổng nghiệm thu khi đủ bằng chứng. Task độc lập có thể chuẩn bị trước, nhưng không bỏ qua điều kiện dữ liệu/nhãn.

## Điểm tiếp tục hiện tại

- **13/11 — W6-04 `done` (bộ tài liệu giữa kỳ):** [Tài liệu và hướng dẫn](midterm/README.md), outputtại`output/midterm/`:24slidechính+4backupHUST4:3,cónotes20phút; reportLaTeX11trangnộidung/14tổng; cheatsheet1A4; ghi chú6trang vàsourcezip. Đã render/đối chiếu số liệu,template/media vàhashhai ví dụ train; không model/train/Docker/testlại/Gitpush. **Tiếp theo: người dùng điền thông tin bìa, review/tập trình bày và trao đổi phần kiến thức còn thiếu.** Các checkpoint thực nghiệm giữ nguyên, không tự bắt đầu nghiên cứu mới.

  Bổ sung theo yêu cầu: [lời thuyết trình đầy đủ](midterm/talk-script.md), PDF/Markdown ở `output/midterm/loi-thuyet-trinh.*`; mốc24slide tổng1200s,4phần dựphòng riêng. Thời gian là dự kiến, chưa nói thử đo thực tế; slide/kết quả không đổi.

  Báo cáo PDF đã điền Nguyễn Hoàng Kiên — 20250735E và bỏ các dòng ngày cập nhật số liệu trên bìa/header; source LaTeX và archive đã đồng bộ. Bìa slide chưa đổi.

  Theo yêu cầu tiếp theo, báo cáo dùng tên hiển thị M1 cho baseline prompt-only, bỏ đoạn bàn về thay đổi prompt. Giữ nguyên bảng số liệu, danh tính run và cấu hình/evidence đã khóa; không đổi các đầu ra khác.

  Bàn giao Git hoàn tất 13/11: giữ stash dự phòng, kiểm thử lại132tests (131pass/1skip), commit/push toàn bộ phần continuation/evaluation/tài liệu và đồng bộ main. Đã xác nhận remote main/codex cùng780300f trước commit ghi nhận bàn giao; hai worktree sạch. Dataset/model/raw runs không đưa lên Git; task tiếp theo vẫn là review/tập trình bày.

- **13/11 — ba phần evaluation đã hoàn tất:** [validation](evaluation-validation.md), [test/cost](evaluation-results.md), [phân tích lỗi/synthetic](evaluation-error-analysis.md). Run `evaluation-20261112T210848574175Z`, một trial38realtest;37+114=151request mới finished, giữ nguyên checkpointparent104 và parser. M1-P2 ghi rõ prompt mới. M2/M5accuracy22/38vs24/38, jointcùng4/38; silver/goldpending. [Receipt](evidence/dataset-v1-progress/evaluation-integrity-20261113.json);132softwaretests:131pass/1skip. **Task kế tiếp: W6-04 `waiting_user` — bàn phạm vi slide/báo cáo bảo vệ giữa kỳ.** Không tự chấm lại test, chọn lại model từ test, train/generate/Docker/push. Targetmatched175 và ablation chưa thực hiện vẫn chưa hoàn tất; các checkpoint cũ bên dưới giữ lịch sử.

- **13/11 — continuation đã hoàn tất:** M2child183346đạt220updates/10epochs, M5child192802đạt350updates/10epochs; exposures/hash/reload đạt. Cảhai chọnparent104 vì joint không tăng; Macro-F1epoch10 giảm. [Evidence](evidence/dataset-v1-progress/continuation-validation-complete-20261113.json). **Task kế tiếp:** hoàn thiện giải trình M1formatinvalid và khóa lựa chọn, chuẩn bị để người dùng chấm38realtest bằng lệnh riêng; không tự mởtest hoặc tăngepochs. Sau đó W6-03phân tích lỗi/chi phí và W6-04báo cáo. Các checkpoint setup/waiting_user phía dưới giữ lịch sử, đã được mốc này thay thế.

- **Continuation v1.2 setup hoàn tất 13/11:** [protocol](experiment-protocol-v1.2.md), [lệnh continue/resume](training-runbook.md#tiếp-tục-m2m5-đến-tổng-10-epoch), manifest ghim parent104. M2 thêm116updates→220, M5 thêm246→350; cùng tổng10epoch, LRcontinuation2e-5,3h/model. Full123tests:122pass/1skip; cả hai Check aliases pass, chưa tạo study hoặc gọi model. **Task kế tiếp `waiting_user`: người dùng tự chạy `train.ps1 M2 -Continue`, rồi M5; resume dùng `-Continue -Resume CHILD_RUN_ID`.** Giữ các kết quả pilot bên dưới; không tự train, test cuối hoặc push. Đề xuất fresh-base/176 cũ bị phương án continuation đã duyệt thay thế.

- **Checkpoint 13/11 lúc00:39:** bốn model đã hoàn tất validation; M5 finished00:36:59, chọn104/reload/hash đạt. [Bảng cuối](results.md): M2F1 .3515/joint4/37; M5F1 .4060/joint5/37. **Task kế tiếp: chốt ngân sách học tiếp hoặc khóa pilot trước finaltest**. Đề xuất176updates mỗi SFT từ cùngbase (M2≈8epochs/M5≈5,03) mới là tư vấn, chưa duyệt/thực thi, không sửa protocol/cap104. Cần xử lý cách diễn giải M1formatinvalid và hạn chế retrieval/lớp trước kết luận; test cuối chưa mở.

- **Checkpoint 13/11 lúc00:32:** đã đối chiếu [điểm validation bốn model](results.md), cùng37mẫu/prompt hashes, tính lại khớp. M5 đangrunning, step52 là tạm thời; chưa có kết quả chọn checkpoint cuối/reload. M1 strictJSONinvalid37/37 (raw đều Markdown-fenced), cần giải thích yếu tố format khi so SFT, không tự sửa parser/điểm. **Task kế tiếp: kiểm tra M5 hoàn tất rồi tổng hợp W5-04 trước final test**; không gọi lại model để kiểm tra điểm. [Evidence](evidence/dataset-v1-progress/validation-comparison-20261113.json).

- **Checkpoint 21:30 ngày 12/11:** M0/M1 validation hoàn tất; M2 `learning-m2-20261112T135209594691Z` có training_finished21:29:06,104updates≈4,73epochs, chọn checkpoint104, reload/hash đạt. Validation37: accuracy28/37, Macro-F1 .3515, functionTop1 5/37, jointTop1 4/37. **Task kế tiếp: người dùng chạy M5**, chưa mở finaltest hoặc tăng ngân sách; M5 chưa có fit operation tại lần kiểm tra. [Evidence M2](evidence/dataset-v1-progress/m2-validation-20261112.json).

- **Cập nhật 20:37 ngày 12/11:** người dùng đã chạy M0, run `learning-m0-20261112T133340821343Z` có `validation_finished`. Sửa cảnh báo tokenizer ở bước đếm raw log, không đổi prompt/crop/hyperparameter, không chạy lại M0. 16 kiểm thử liên quan pass; [đối chiếu prompt thật](evidence/dataset-v1-progress/tokenizer-warning-fix-20261112.json). Task tiếp theo vẫn do người dùng bắt đầu: M1 và smoke M2, rồi hai SFT theo [runbook](training-runbook.md); chưa mở final test.

- **Bàn giao mới nhất — setup pilot v1.1 hoàn tất, chưa chạy model:** người dùng muốn tự gọi từng lệnh M0/M1/M2/M5. [Protocol v1.1](experiment-protocol-v1.1.md), [manifest](../data-manifests/training-v1.1.json), [runbook](training-runbook.md), [readiness](evidence/dataset-v1-progress/manual-training-readiness-20261112.json) và [kiểm thử 116: 115 pass/1 skip](evidence/dataset-v1-progress/software-tests-manual-v11-final.txt). Dataset 250 real + 101 synthetic đã khóa riêng; không đổi số liệu, target/cap/unknown của vòng v1.0. Không gọi model, smoke hoặc Docker trong lượt setup.
- **Task kế tiếp cụ thể: `waiting_user` — người dùng chạy `.\scripts\train.ps1 -Check`, rồi M0/M1 và smoke M2 trước hai SFT dài khi sẵn sàng.** Chỉ hỗ trợ từ run/log thật sau khi có lệnh; không tự bắt đầu train. Study thủ công chưa tạo, không có calendar cutoff, cap cộng dồn giữ hai giờ mỗi SFT/evaluation; xem protocol mới. Goal v1.0 vẫn thiếu 74 synthetic và chưa hoàn tất.
- **Bàn giao Git:** code setup đã push tại `c0acbcc` trên `origin/codex/w1-review-skill`, chưa merge main. Pull chỉ mang code/tài liệu; runtime/data/model nằm local, lock ghim worktree đã chuẩn bị như [runbook](training-runbook.md).

### Checkpoint vòng thu thập v1.0 và lịch sử phát triển

- **Goal thực thi đã được duyệt ngày 12/11:** [protocol dataset v1/SFT](experiment-protocol.md) khóa mục tiêu 250 real, synthetic bằng real train, M0/M1/M2/M5 và thời hạn 13/11 02:19:29 +07. Điều này thay điểm dừng lập plan trước đó; W2-04 đang triển khai split/lineage, W4/W5 chỉ hoàn tất khi đủ gate và artifact thật. Run hiện hành tham chiếu qua `.cache/active-experiment.json`.

- **Checkpoint thực thi:** 2026-11-12T19:30:07+07:00: chọn250real silver(175train/37validation/38test) từ265real đã rà;105synthetic export,101sau loại trừ cuối, thiếu74/175. Tổng372lời gọi7B/197lượt đạt runner. Software106:105pass/1skip. M0/M1/M2/M5 nghiên cứu chưa chạy; data gate chưa đạt.
- **Điểm dừng v1.0:** đã bàn giao [kết quả thật](results.md) và phần thiếu 74 synthetic. Group review partial351 đã xong; matched175 và lock theo v1.0 chưa đạt. Không tăng cap/replay unknown hoặc báo mục tiêu cũ đã hoàn tất. Pilot v1.1 được người dùng yêu cầu sau đó có gate/lock riêng; muốn tiếp tục sinh vẫn cần quyết định ngân sách/thí nghiệm tiếp theo.


- **Mốc lập kế hoạch lịch sử:** [phiên thảo luận](planning-session-2026-11-12.md) giữ các lựa chọn và câu hỏi trước phê duyệt. Điểm dừng khi đó đã được goal thực thi thay thế; không dùng đoạn lịch sử này để dừng runtime hiện tại.
- **Phạm vi đang thực thi:** 250 tình huống real đủ điều kiện; phân loại nguyên nhân và file/hàm đều là nhiệm vụ chính. Protocol hiện hành thay các quota 60 real, 18–36 synthetic và 120 request cũ. Đây là mục tiêu, chưa phải số thực đạt.

- **Báo cáo đã gom:** [tổng kết phát triển](development-summary.md) và [review dữ liệu](data-review.md) là hai tài liệu chính, chia W1/đợt 01/đợt 02. Sáu đường dẫn cũ giữ chỉ dẫn/anchor. Đã kiểm tra 320 liên kết/anchor, giữ 44 anchor cũ và hash 2.518 file được bảo vệ. Đây là cập nhật tài liệu; W2-04 `doing`, W3-03 `doing` sau khi duyệt kiến nghị giữ/loại, gold/training vẫn pending.

- **Đợt 02 hoàn tất thêm dữ liệu:** [tổng kết](development-summary.md#expansion-02), [review](data-review.md#expansion-02). 8 case nguồn mới + 2 profile hiệu chỉnh, 15 lượt 7B, 11 đạt runner/11 hash khác byte; 1 syntax-violation phải xét riêng khi curate. Cộng hai đợt: 17 case nguồn đã thử/10 repo, 36 lượt, 17 đạt runner/14 hash khác byte. Gold/training vẫn pending.
- **W2-04 đã có đầu ra trung gian:** [development-groups-v1.json](../data-manifests/development-groups-v1.json) và module audit chỉ đọc nhận diện repo/shared-commit groups, exact duplicates và lexical-edit suggestions. 40 source records/42 profile records không có nghĩa 42 case nguồn; chưa có split cuối.

- **Đợt mở rộng 01 đã chạy xong:** [tổng kết](development-summary.md#expansion-01), [review](data-review.md#expansion-01), [registry](../data-manifests/expansion-01.json). Sàng lọc 20, thử 9 case/6 repo, 7 seed pass, gọi 21 lượt 7B, 6 lượt đạt thực thi nhưng chỉ 3 candidate khác byte. Active time được batch ghi nhận 456,233s; integrity image thêm 3,937s. Mẫu số 27 lượt yêu cầu, 6 chưa chạy; gold/training pending, toàn bộ development. W1 không chạy lại.

- **Công cụ hỗ trợ đã tạo và áp dụng:** [skill ci-data-review](../.agents/skills/ci-data-review/SKILL.md) hướng dẫn agent phân tích kỹ thuật và giải thích evidence cho người dùng review; metadata cho phép dùng theo ngữ cảnh hoặc gọi `$ci-data-review`. Kết quả áp dụng cho ba lượt 7B nằm trong bản rà R2; skill không tự phê duyệt dữ liệu. Người dùng đã đồng ý ba kiến nghị; W1-03 `done` ở phạm vi review kết luận/giữ-loại, các trường nhãn gold/training vẫn pending. Kiểm tra skill được ghi riêng trong agent-log.
- **Task kế tiếp: W2-04 (`doing`) — hoàn thiện nhóm/trùng lặp và vai trò split trước vòng train.** W2-01/02 đủ dùng cho development; W2-03 đã có registry và pilot thật. [Review mở rộng](data-review.md#xac-nhan-expansion-01-02) đã được người dùng đồng ý kết luận/kiến nghị giữ-loại hai đợt; chưa duyệt gold/training. Người dùng đã đồng ý ba kết luận/kiến nghị W1-03 qua chat; ghi nhận tại bảng xác nhận trong bản review. Phần W2 development đã được triển khai trong đợt mở rộng được người dùng yêu cầu sau bàn giao Git W1. [Bản rà R2 bằng ci-data-review](data-review.md#w1) giải thích code → hành vi → log, độ chắc chắn và kiến nghị: loại 01 khỏi tập synthetic-failure, giữ 02/03 như ứng viên lỗi API/type và logic có bằng chứng. Phần kết luận/giữ-loại đã được người dùng đồng ý; nhãn/vị trí xác nhận và training approval vẫn pending. Comment vi phạm prompt nhưng leakage chỉ là rủi ro có điều kiện khi input 3B chưa chốt.
- W1-01 hiệu chỉnh vai trò đã xong: chỉ 7B sinh, 3B chẩn đoán ở giai đoạn sau; 31 host tests pass, một Docker integration test bỏ qua có chủ đích. Không chạy lại model/pilot. [Tổng kết W1-04](development-summary.md#w1) hoàn tất; W1-03 đã hoàn tất review kết luận; không coi dữ liệu đã được duyệt gold/training khi các trường tương ứng còn pending.
- Pilot PC đã chạy: properr head pass hai test; log nghiệm thu cũ có 22 kiểm thử phần mềm pass. 7B đạt kiểm chứng thực thi 2/3. Đây chưa phải số mẫu được duyệt để train; 3B chẩn đoán chưa chạy. Model phụ đã bỏ khỏi cấu hình/workflow, không tải/gọi/chạy/rà tiếp; evidence lịch sử giữ nguyên.
- Run 7B W1 đã rà và được người dùng đồng ý kiến nghị: `generate-20261029T054921315491Z`. [Evidence đã commit](evidence/target-pc/README.md); raw run/ZIP nằm local, không đi theo Git clone. Nếu thiếu raw artifacts, khôi phục archive phù hợp hoặc yêu cầu cung cấp; không dựng lại output bằng tay.
- Không tải lại model/chạy lại pilot chỉ để cập nhật tài liệu. Giữ nguyên kết quả vòng đầu, kể cả các lượt bị loại.

## Nguồn dữ liệu dự kiến: AIDev và SWE-bench

Phạm vi nguồn giữ theo [báo cáo nghiên cứu §4](reference/00_bao_cao_dinh_huong_nghien_cuu.md): **AIDev/AIDev-pop và subset SWE-bench phù hợp**. W1 mới triển khai case properr từ AIDev; việc roadmap trước đó chỉ nhắc AIDev là thiếu chi tiết, không phải quyết định loại SWE-bench.

| Nguồn | Phần tận dụng | Phần cần chuẩn bị cho nhiệm vụ chẩn đoán |
|---|---|---|
| AIDev/AIDev-pop | PR, repo/commit và metadata agent; dữ liệu chi tiết tùy subset | Tái hiện/log, nguyên nhân/vị trí và nhãn được rà; metadata PR không chứng minh ai gây lỗi |
| SWE-bench, subset phù hợp (cân nhắc Lite/Verified) | Repo/base commit, mô tả vấn đề, gold solution patch, test patch, FAIL_TO_PASS và PASS_TO_PASS | Chọn task phù hợp, tái hiện và lưu log; ánh xạ taxonomy/vị trí kèm evidence và người duyệt. Chưa chọn subset cuối hoặc tích hợp harness |

SWE-bench có **đáp án sửa lỗi và các test mục tiêu**, giúp giảm công thu thập/kiểm chứng. Nó không cung cấp sẵn mọi nhãn chẩn đoán của đồ án: loại lỗi theo taxonomy riêng, dòng nguyên nhân đã xác nhận hoặc provenance người–agent. Các dòng trong patch là nơi sửa, không tự động là toàn bộ dòng gây lỗi. Không đưa gold patch vào input như diff gây lỗi; giữ nó ở phần tham chiếu/đáp án khi chấm hoặc review. [Cấu trúc nguồn chính thức](https://www.swebench.com/SWE-bench/guides/datasets/).

W2-03 chọn case và ghi nguồn/revision; W2-04 chốt vai trò train/validation/test theo nhóm và rà trùng giữa hai nguồn. Nếu giữ benchmark ngoài với split gốc, không lấy các instance đó làm seed sinh hoặc dữ liệu train. Nếu tự chia subset, công bố protocol riêng. Mẫu `astropy__astropy-12907` đã được đọc trong báo cáo nghiên cứu thuộc phần phát triển, không dùng để khẳng định test độc lập chưa từng xem. Đã chạy năm case SWE Lite dev trong đợt mở rộng 01; nhãn chẩn đoán chính thức mới vẫn pending.

## Tuần 1 — Hoàn tất demo và rà chất lượng pilot

| ID | Trạng thái | Việc làm theo thứ tự | Đầu ra / điều kiện hoàn thành |
|---|---|---|---|
| W1-01 | done | Hiệu chỉnh theo quyết định mới: 7B sinh duy nhất, 3B chẩn đoán; demo một generator và giữ evidence cũ | CLI/config/session/report: 31 host tests pass, một Docker test skip; 358 file evidence/case giữ nguyên hash. Không gọi lại model. [Architecture](architecture.md) |
| W1-02 | done | Tái hiện properr và giữ pilot PC đã chạy như evidence lịch sử; không chạy lại khi đổi phạm vi | [PC evidence](evidence/target-pc/README.md): log nghiệm thu cũ 22 tests pass; 7B ba lượt, 2/3 đạt thực thi; không tự gán gold hoặc sửa artifact lịch sử |
| W1-03 | done | Đã áp dụng ci-data-review, đối chiếu source/test/candidate hash và 15 bộ stage JSON/JUnit của ba lượt 7B; giải thích cơ chế và độ chắc chắn. Không gọi model/Docker/test | [Review W1](data-review.md#w1) R2: 01 không gây lỗi test; 02 TypeError do dùng method như số; 03 sai hệ số; kiến nghị sử dụng có điều kiện, leakage chưa chốt khi input chưa rõ. Người dùng đã đồng ý loại 01, giữ 02/03 làm ứng viên và các giải thích tương ứng; nhãn gold/vị trí theo schema/training vẫn pending |
| W1-04 | done | Tổng hợp demo 7B từ số đo thật và vấn đề chất lượng; dựa bản review W1-03 | [Tổng kết W1](development-summary.md#w1): ba lượt, 2/3 đạt thực thi, tổng giây gọi sinh 49.374, giới hạn và replay năm phút; số liệu/liên kết đã kiểm tra. Chưa tạo slide |

**Cổng G1:** artifact chạy thật có thể xem lại, kết quả không bị sửa tay, mọi lượt có trạng thái; có bảng review nêu rõ phần chưa được duyệt. Có thể chuẩn bị tuần 2 khi review còn pending, nhưng chưa coi mẫu là dữ liệu train.

## Tuần 2 — Chốt bài toán, nhãn và subset dữ liệu thật

| ID | Trạng thái | Phụ thuộc / hành động | Đầu ra / điều kiện hoàn thành |
|---|---|---|---|
| W2-01 | done | Dựa W1-03/04 và revised-plan, định nghĩa input/output chẩn đoán cho cả AIDev và SWE-bench, thông tin được phép thấy (tách gold patch khỏi input), vai trò AI/code/người; ghi câu hỏi workflow/interceptor còn mở | [task-contract.md](task-contract.md) development v0.1: input/output review, reference fields tách riêng, unknown và các quyết định tương lai; chưa có 3B inference/training schema cuối. Không tự implement interceptor |
| W2-02 | done | Từ W2-01, lập taxonomy nhỏ và hướng dẫn gắn nhãn; phân biệt metadata/đáp án nguồn với nhãn chẩn đoán đã rà | [labeling-guide.md](labeling-guide.md) development v0.1: mô tả nhãn tạm thời, phản ví dụ, mức vị trí và thủ tục người duyệt; taxonomy cuối/gold labels vẫn pending. Không ép actor/nhãn khi nguồn không đủ |
| W2-03 | done | Chọn subset/case từ AIDev/AIDev-pop và SWE-bench theo tiêu chí có mục đích; ghim nguồn/revision và mở rộng harness từng repo; chưa tải toàn bộ dataset | [Registry expansion-01](../data-manifests/expansion-01.json): 20 screened, 9 attempted/6 repo, 6 strict-supported, 7 fixed-pass; có nguồn/revision/test recipe/license và lý do loại. Như [tổng kết](development-summary.md#expansion-01); không tuyên bố đại diện nguồn. Raw code/data ở thư mục bị ignore. Mục tiêu thăm dò 10–20 tình huống từ tài liệu nghiên cứu là dự kiến, không phải quota đã hoàn thành hoặc yêu cầu 20 repo/label |
| W2-04 | doing | Dựa registry và W2-02, xác định group id, duplicate family giữa AIDev/SWE-bench và vai trò train/validation/test trước vòng sinh mở rộng; chốt benchmark ngoài hay protocol chia subset riêng | Đang làm: registry và development-groups-v1 có 20 repo groups cho 40 nguồn đã xem, hai profile correction tách riêng; audit có exact/lexical edit duplicates và shared-commit alias evidence. Còn near-duplicate giữa nguồn và train/validation/test; tất cả case đợt 01 giữ development. Đã có protocol và repo-role plan trước thực thi dataset v1; chưa có final dataset đủ gate. properr/case đã dùng phân tích pilot thuộc phần phát triển, không gọi là test chưa từng xem. Tỷ lệ 70/15/15 chỉ là phương án, phải đối chiếu số nhóm/lớp thực tế |

**Cổng G2:** có subset thật tái hiện được, dữ liệu đủ input và nhãn được duyệt cho nhiệm vụ đã chọn; mỗi nhóm chỉ ở một split. Nếu support quá ít, giảm taxonomy/phạm vi và ghi lý do trước khi mở rộng sinh. Không dùng synthetic để che việc chưa có test thật độc lập.

## Tuần 3 — Hoàn thiện sinh và kiểm chứng trên phần phát triển

| ID | Trạng thái | Phụ thuộc / hành động | Đầu ra / điều kiện hoàn thành |
|---|---|---|---|
| W3-01 | doing | Từ review 7B W1-03 và train groups W2-04, thiết kế vòng prompt/budget mới xử lý bug-disclosing comments và thay đổi kém hợp lý; chỉ dùng generator 7B | Đã thử v2 và single-line-site-v3 trên các cohort riêng, giữ options/seed/model 7B; v3 bỏ generator self-label, dùng static sites/test excerpts; raw requests/prompts/digests được lưu. Vẫn cần xử lý instruction drift/invalid output và chốt train groups trước vòng tiếp theo. Không ghi đè pilot đầu; không sửa output model để biến mẫu lỗi thành mẫu đạt |
| W3-02 | doing | Sinh trên seed pass của **train groups**, chạy baseline → fail ổn định → hoàn tác; mở rộng allowlist/test command theo từng repo đã cấu hình | [Đợt 01](development-summary.md#expansion-01) đã có 21 lượt development, 6 execution_verified/3 hash khác byte. Đây là pilot được người dùng cho phép trước split cuối, chưa phải vòng train groups; tests giữ nguyên, container không mạng và có giới hạn. Lỗi JSON/build/timeout/không làm test fail được giữ trong tổng lượt |
| W3-03 | doing | Rà nhãn, vị trí, hợp lý và trùng lặp; phân biệt kiểm chứng thực thi với toàn bộ tiêu chí dùng để train | [Review đợt 01](data-review.md#expansion-01) và [đợt 02](data-review.md#expansion-02) hoàn tất phân tích kỹ thuật; 14 hash khác byte đạt runner, có một syntax/prompt violation và marker-plausibility cần curation. Người dùng đã đồng ý kết luận/kiến nghị giữ-loại: giữ ứng viên development, loại syntax-violation khỏi subset v3 valid-Python và giữ marker/offset để phân tích development, chưa train. [Xác nhận](data-review.md#xac-nhan-expansion-01-02). Còn hoàn thiện nhãn/vị trí/curation sau W2-04; raw review stubs, formal labels và training eligibility vẫn pending, chưa đủ đóng task |

**Cổng G3:** giao thức tái lập được, ứng viên đủ evidence và bộ tiêu chí nhận/loại được ghi rõ. Không kết luận khả năng sinh hoặc chẩn đoán tổng quát từ một case hay tỷ lệ thực thi 2/3 của 7B.

## Tuần 4 — Khóa protocol và đóng gói dataset

| ID | Trạng thái | Phụ thuộc / hành động | Đầu ra / điều kiện hoàn thành |
|---|---|---|---|
| W4-01 | done (pilot v1.1) | Chốt protocol dựa phần phát triển W2/3: nhiệm vụ, splits, nhãn, model chẩn đoán, metric, ngân sách, seeds và cấu hình ưu tiên | [Protocol v1.1](experiment-protocol-v1.1.md), cấu hình seed/context/update và quyết định study thủ công. V1.0 giữ nguyên; chỉ real-only/real+synthetic được chuẩn bị, chưa có pass+fail ablation |
| W4-02 | done (pilot v1.1); blocked (target v1.0) | Đóng gói real train/validation/test và synthetic từ train groups theo schema thống nhất | [Manifest v1.1](../data-manifests/training-v1.1.json) ghim lock 351, provenance/hash/group review và 175/37/38 real + 101 synthetic. Matched-175 v1.0 vẫn thiếu 74; không đóng goal cũ. Raw/cache/model ngoài Git |
| W4-03 | done (lựa chọn pilot) | Kiểm tra leakage, near-duplicate, nhãn pending, trường đáp án lộ trong input và tính đầy đủ evidence | Deep audit 352 → subset 351 sau semantic dedup, review ràng buộc hash, không giao repo/group hoặc exact duplicates giữa splits; gold pending, silver dùng trong pilot có ghi rõ. [Readiness](evidence/dataset-v1-progress/manual-training-readiness-20261112.json); không lặp deep scan khi setup |

**Cổng G4:** dataset/protocol được version hóa và kiểm tra tái lập. Tỷ lệ/chia tập/filter không đổi vì điểm test. Cross-validation theo nhóm trong development là tùy protocol/số liệu; synthetic chỉ nằm ở phần train tương ứng của mỗi fold nếu dùng, test cuối vẫn độc lập.

## Tuần 5 — Baseline và thí nghiệm chính

| ID | Trạng thái | Phụ thuộc / hành động | Đầu ra / điều kiện hoàn thành |
|---|---|---|---|
| W5-01 | done (pilot) | M0 TF-IDF + Logistic Regression cho **phân loại**, người dùng đã chạy | Classifier `learning-m0-20261112T133340821343Z` tái sử dụng; validation6/37,test9/38. Không localization hoặc refit. [Kết quả](evaluation-results.md) |
| W5-02 | done (pilot) | M1 prompt-only, giữ kết quả cũ và lượt M1-P2 được duyệt riêng | M1 cũ37/37fencedJSON bị strictparser từ chối. M1-P2 **prompt mới**, cùng usercode/log; validation29/37,test16/38, invalid1/37và8/38. Không normalize response. [Giải trình](evaluation-validation.md) |
| W5-03 | done (pilot) | M2/M5 parent và continuation do người dùng chạy | Parent104 và child đến220/350updates đều hoàn tất; cảhai chọnparent104, reload/hash đạt. [Evidence continuation](evidence/dataset-v1-progress/continuation-validation-complete-20261113.json); chỉ adapter đã chọn được test |
| W5-04 | done (pilot evaluation v1) | Chốt validation, giải trình format M1 và phân biệt best/epoch10 | [Bảng validation](evaluation-validation.md), [manifest](../data-manifests/evaluation-v1.json). M2/M5 giữparent104 dù child10epoch; M1-P2 không làm đổi selection. Prompt khác nhau ghi rõ, strictparser và nhãn silver giữ nguyên |

**Cổng G5:** có baseline thật và cấu hình cuối truy vết được. Chỉ nói tác dụng fine-tuning/synthetic khi đối chứng tương ứng tồn tại; hai lượt 7B đạt thực thi hiện tại chưa đủ thay thế dataset huấn luyện và chưa được duyệt để train.

## Tuần 6 — Đối chứng bổ sung, đánh giá và báo cáo

| ID | Trạng thái | Phụ thuộc / hành động | Đầu ra / điều kiện hoàn thành |
|---|---|---|---|
| W6-01 | todo | Thực hiện M3/M4 và fail-only/pass+fail theo protocol/tài nguyên; đánh dấu deferred kèm lý do nếu chưa thể | Bảng ablation có task/input/model/split/ngân sách tương ứng. M4 vẫn có thực thi/log; khác ở xác minh nhãn/lọc đầy đủ, không trộn mẫu thiếu an toàn hoặc thiếu input vào train |
| W6-02 | done (pilot evaluation v1) | Khóa trước suy luận, test một lần trên cùng38real | Run `evaluation-20261112T210848574175Z` giữ strictparser/checkpoint104/cohort và prompt riêng;114testrequest finished. [Bảng đầy đủ](evaluation-results.md), [receipt](evidence/dataset-v1-progress/evaluation-integrity-20261113.json). Không chấm checkpoint khác; silver, không phải gold benchmark |
| W6-03 | done (pilot evaluation v1) | Phân tích lỗi và hiệu quả synthetic, parent+continuation cost | [Phân tích](evaluation-error-analysis.md):38case paired/format/retrieval/hash,8chuỗi causal chi tiết; M5 thắng4/thua2 về class, jointthắng1/thua1. M2/M5cost4387/6324s; không quy nhân quả từ một seed hoặc đổi nhãn sau test. M3/M4 và các ablation chưa làm vẫn riêng W6-01 |
| W6-04 | done (giữa kỳ) | Bộ tài liệu theo kế hoạch đã duyệt, chờ người dùng review/tập trình bày | [Source/readme](midterm/README.md);28slide(24+4),notes1200s,reportLaTeX11trangchính/14tổng,cheatsheet1A4,ghi chú6trang,PDF/PPTX/sourcezip. Render,16bảngnative,9template-media và37rawhashhai ví dụđạt; nhãnsilver,khôngthínghiệmlại/push. Báo cáo cuối kỳ và cácablation chưa nằm trong mốc này |

**Cổng G6:** các kết luận đều trỏ được đến thí nghiệm/evidence; hạn chế và phần chưa làm được ghi công khai. M6 sinh cho lớp hiếm, model chẩn đoán bổ sung và interceptor không mặc định là việc đã triển khai.

## Quy tắc bàn giao cuối mỗi phiên

- Ghi task ID, file/run/config đã tạo, kiểm tra pass/fail, lỗi gặp và điều kiện còn thiếu vào agent-log theo Bangkok.
- Cập nhật trạng thái task, evidence và **một task kế tiếp cụ thể** ở đầu file này; không đánh dấu cả tuần done khi còn nhãn/đối chứng chưa xong.
- Cập nhật architecture nếu thay interface/schema/protocol/runtime. Lưu quyết định nghiên cứu riêng trong protocol; không dùng nhật ký thay cho cấu hình thí nghiệm.
- Giữ raw evidence bất biến; sửa report bằng cách dựng lại từ artifact, đổi thí nghiệm bằng run/version mới. Chỉ chạy lại khi có lý do và ghi mối liên hệ với run cũ.
- Kiểm tra phù hợp với thay đổi; chỉnh Markdown không cần chạy lại model/Docker. Trước commit/push, kiểm tra diff, link, secrets và file lớn; không stage cache/weights/raw data. Không xóa stash backup đang được giữ theo yêu cầu trước.

Nguồn và thứ tự ưu tiên: yêu cầu mới nhất của người dùng → quyết định đã chốt trong protocol → [revised-plan](revised-plan.md) / [nghiên cứu §6–10](reference/00_bao_cao_dinh_huong_nghien_cuu.md) → lộ trình dự kiến này. Architecture/evidence phản ánh trạng thái thật, không suy hoàn thành từ bản kế hoạch. Khi đổi phạm vi hoặc lịch đã thống nhất, sửa roadmap và ghi lý do.
