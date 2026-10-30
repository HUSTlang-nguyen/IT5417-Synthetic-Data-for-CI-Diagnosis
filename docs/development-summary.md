# Tổng kết phát triển dữ liệu CI

Cập nhật tổ chức tài liệu: 30/10/2026, Asia/Bangkok. Đây là bản tổng hợp từ evidence đã lưu; không chạy thí nghiệm mới. Đọc [bản review và kiến nghị](data-review.md) để xem nguyên nhân, bằng chứng và phần cần duyệt.

## Trạng thái hiện tại

Workflow: **AIDev/SWE-bench development → ghim nguồn/commit/test → tái hiện local → seed pass → 7B sinh → Docker kiểm chứng → agent phân tích → người dùng review → dữ liệu cho 3B sau các cổng dữ liệu**. 7B là generator duy nhất; 3B là diagnoser dự kiến, chưa chạy. Đạt runner chưa có nghĩa được duyệt nhãn gold hoặc training.

| Phạm vi | Case nguồn đã thử / repo | Profile thử tái hiện | Seed pass | Lượt 7B thực hiện | Lượt đạt runner | Candidate khác byte đạt runner |
|---|---|---:|---:|---:|---:|---:|
| [W1 properr](#w1) | 1 / 1 | 1 | 1 | 3 | 2 | 2 |
| [Expansion 01](#expansion-01) | 9 / 6 | 9 | 7 | 21 | 6 | 3 |
| [Expansion 02](#expansion-02) | 8 / 5 | 10, gồm 2 hiệu chỉnh | 5 | 15 | 11 | 11 |
| **Hai expansion, không gồm W1** | **17 / 10 repo khác nhau** | **19** | **12 case nguồn** | **36** | **17** | **14** |

Hai expansion sàng lọc 40 case nguồn (20 mỗi đợt); W1 properr được báo riêng. Hai profile `-r1` không phải hai case nguồn mới. Một candidate đạt runner ở đợt 02 vi phạm yêu cầu syntax hợp lệ; raw acceptance được giữ, kiến nghị curation nằm trong review. Các tổng không phải số mẫu được duyệt train hay accuracy chẩn đoán.

W1 đã được người dùng đồng ý kết luận/kiến nghị giữ-loại; review expansion 01/02 còn chờ. Mọi nhãn gold/vị trí chính thức và training eligibility vẫn pending. Kiểm thử phần mềm mới nhất đã lưu: **58 discovered, 57 pass, 1 legacy Docker opt-in skip**; đây là evidence có trước lần gom tài liệu, không phải lượt test mới.

**Bước tiếp theo: W2-04 (`doing`)** — hoàn thiện grouping/near-duplicate và protocol split, chọn nguồn đánh giá độc lập trước vòng train. W3-03 vẫn `waiting_user`; chưa có final split, inference 3B hoặc SFT.

## Mục lục

- [W1: kết quả, giới hạn và replay khoảng năm phút](#w1)
- [Expansion 01: nguồn, mẫu số, thời gian và lỗi](#expansion-01)
- [Expansion 02: v3 và hai profile hiệu chỉnh](#expansion-02)
- [Review chi tiết và các quyết định](data-review.md)

Các mục dưới giữ số đo và bối cảnh tại từng đợt. Thời gian gọi model, active budget và integrity audit là các khoản khác nhau; không cộng phần budget kế thừa lần thứ hai hoặc suy thời gian chưa đo. Raw runs/cache không đi theo Git clone; các liên kết local cần artifact root/archive tương ứng.

<a id="w1"></a>

## W1-04 — Tổng kết demo 7B sinh dữ liệu có kiểm chứng

Ngày tổng kết: 29/10/2026, Asia/Bangkok. Đây là replay từ artifact PC đã lưu; soạn tài liệu không gọi model hoặc chạy test mới. [Bản rà ba lượt 7B](data-review.md#w1) đã được người dùng đồng ý kiến nghị giữ/loại; nhãn gold/vị trí chính thức và training approval vẫn pending.

<a id="w1-vai-trò-và-workflow"></a>

### Vai trò và workflow

| Thành phần | Vai trò hiện hành | Trạng thái |
|---|---|---|
| Qwen2.5-Coder-7B-Instruct | Generator duy nhất, sinh thay đổi Python từ seed pass | Đã có ba lượt thực tế trên PC |
| Docker runner | Chạy test gốc, kiểm tra baseline → fail lặp ba lần → restored pass | Có evidence thực thi đã lưu |
| Người duyệt | Đã đồng ý kiến nghị giữ/loại W1; nhãn, vị trí chính thức và training eligibility xét riêng | Kiến nghị đã duyệt; gold/training pending |
| Qwen/Qwen2.5-Coder-3B-Instruct | Chẩn đoán chính; sau này chạy prompt-only/SFT và đánh giá | Chưa triển khai/chạy trong W1 |

Luồng: nguồn AIDev → pin repo/commit → tái hiện base/head → chọn head pass → 7B sinh → Docker kiểm chứng → người duyệt → dữ liệu cho 3B khi đạt các cổng dữ liệu sau này. Không dùng 3B làm generator; model phụ đã loại khỏi workflow hiện hành. Evidence lịch sử giữ nguyên.

<a id="w1-nguồn-và-kết-quả-thật"></a>

### Nguồn và kết quả thật

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

<a id="w1-phân-biệt-các-mức-đạt"></a>

### Phân biệt các mức đạt

1. **Đạt thực thi:** baseline pass, ba lỗi test có chữ ký ổn định, restored pass. Runner không tự xác nhận nhãn hoặc độ hợp lý.
2. **Đạt tuân thủ/chất lượng:** cần rà prompt, cơ chế lỗi, comment tiết lộ đáp án và tính phù hợp nhiệm vụ. Cả ba output hiện có đều chứa dấu hiệu tiết lộ lỗi.
3. **Được dùng để train:** cần người duyệt và các điều kiện taxonomy, split, evidence, lọc trùng của giai đoạn sau. Hiện chưa có phê duyệt; kiến nghị agent trong review không thay quyết định của người duyệt.

<a id="w1-replay-khoảng-năm-phút"></a>

### Replay khoảng năm phút

| Thời gian dự kiến | Nội dung |
|---|---|
| 0:00–0:40 | Nêu bài toán và vai trò 7B sinh / 3B chẩn đoán; nói rõ đang replay |
| 0:40–1:20 | Mở tái hiện properr: base thiếu pytest, head hai test pass; giải thích giới hạn lịch sử |
| 1:20–2:30 | Xem manifest 7B, prompt, hash source/tests và giao thức ba seed |
| 2:30–3:50 | Xem ba diff, baseline/repetitions/restoration; giữ cả lượt không làm test fail trong mẫu số |
| 3:50–4:30 | Đối chiếu TypeError, sai số và nhãn syntax do model đề xuất; nêu comment tiết lộ lỗi |
| 4:30–5:00 | Mở bảng kiến nghị W1 đã được đồng ý và các trường gold/training còn pending; nêu giới hạn của pipeline |

Không chạy model/test chỉ để replay. Nếu chưa có raw runs trên máy trình bày, khôi phục archive trước; không tạo output hoặc log thay thế. CLI/demo mới chỉ dành cho lượt sinh mới bằng 7B, không dùng để sửa pilot cũ.

<a id="w1-giới-hạn-và-bước-tiếp-theo"></a>

### Giới hạn và bước tiếp theo

Một repo, hai test, ba lượt và seed phát triển đã được xem không tạo thành benchmark hoặc test độc lập. Toolchain tái dựng không hoàn toàn hermetic; chưa có peak VRAM, nhãn gold, dataset train, kết quả chẩn đoán 3B, SFT, ablation hoặc interceptor. Kiểm tra trực quan HTML vẫn pending do browser policy chặn file cục bộ; không dùng cách vòng tránh.

W1-04 hoàn tất khi số liệu và liên kết trong tổng kết khớp evidence. W1-03 đã hoàn tất review kết luận: người dùng đồng ý loại 01 khỏi tập mẫu lỗi và giữ 02/03 làm ứng viên có bằng chứng. Nhãn gold/vị trí theo schema và quyền dùng để train vẫn pending; xác nhận được ghi riêng trong pilot-review. Tại mốc W1 chưa triển khai W2 hoặc chạy 3B. Hiện W2-01/02 đã có hợp đồng development và taxonomy nháp, hai đợt mở rộng đã hoàn tất; task kế tiếp là W2-04 grouping/near-duplicate và vai trò split trước vòng train. 3B vẫn chưa chạy. Chưa tạo slide hoặc sửa tài liệu gốc.

<a id="expansion-01"></a>

## Tổng kết đợt development 01

Ngày 30/10/2026. [Batch HTML](../runs/batch-20261029T173420443187Z/report.html), [manifest](../runs/batch-20261029T173420443187Z/manifest.json), [registry](../data-manifests/expansion-01.json), [review để người dùng đọc](data-review.md#expansion-01), [số liệu tổng hợp](evidence/expansion-01/summary.json).

<a id="expansion-01-kết-quả-thật"></a>

### Kết quả thật

| Chỉ số | AIDev | SWE-bench Lite dev | Tổng |
|---|---:|---:|---:|
| Case sàng lọc | 10 | 10 | 20 |
| Case đã thử tái hiện | 4 | 5 | 9 |
| Giả thuyết local đạt đối chiếu nghiêm ngặt | 2 | 4 | 6 |
| Case có fixed seed pass | 2 | 5 | 7 |
| Lượt 7B đã gọi | 6 | 15 | 21 |
| Lượt đạt thực thi | 0 | 6 | 6 |

Chín case đã thử thuộc **6 repo**. Giới hạn ban đầu là 10 case/30 lượt; không bù case thiếu điều kiện ở nguồn này bằng nguồn khác. Sáu AIDev bị loại ở sàng lọc do giấy phép tại revision ghim chưa rõ hoặc xung đột proprietary; còn bốn case đủ điều kiện thử. Năm case SWE còn lại không được chọn do quota năm/nguồn, không phải kết luận chúng không tái hiện được.

Mẫu số được giữ rõ: **27 lượt yêu cầu** cho chín case đã chọn; 21 lượt thực hiện và sáu lượt chưa thực hiện vì hai case không có seed pass. Kết quả trên các lượt đã gọi: **6/21 đạt thực thi**, **10 invalid_output**, **5 không làm test fail**. Trên toàn số lượt yêu cầu là **6/27**; còn ba slot tới capacity 30 chưa có case nguồn được chọn.

Sáu lượt đạt chỉ gồm **3 candidate khác byte**, đều thuộc hai case pydicom. Có tổng cộng 11 candidate hợp lệ, gồm sáu hash khác nhau. Đây không phải sáu mẫu độc lập, sáu nhãn gold hoặc kết quả chẩn đoán 3B.

<a id="expansion-01-thời-gian-và-tài-nguyên"></a>

### Thời gian và tài nguyên

Batch chạy từ **00:34:20 đến 00:40:31 +07**, ngày 30/10/2026. Active time batch ghi nhận **456,233 giây**, gồm **85,124 giây discovery đã đo** và khoảng 371,109 giây xử lý batch; thời gian viết code nằm ngoài. Tổng thời gian các lời gọi sinh là **76,484 giây**, bao gồm load/runtime, không phải tốc độ steady-state.

Kiểm tra inventory image sau batch mất thêm **3,937 giây**. Tổng hai khoản active đã đo là **460,170 giây**, thấp hơn ngân sách 6 giờ. Đây là các khoản được ghi nhận, không phải đo toàn bộ thời gian tác giả thao tác; một số metadata follow-up nhỏ không có timer riêng. Không dùng thời gian làm việc trong chat để suy throughput.

Doctor xác nhận Docker Linux, RTX 4070 SUPER và Ollama local hoạt động. Dung lượng trống trước batch được đo 163,49 GiB sau khi người dùng giải phóng storage. Không đo peak VRAM hoặc suy bộ nhớ model từ snapshot; không tải/chạy 3B hay model phụ. Không tự prune Docker.

<a id="expansion-01-các-điểm-không-đạt-và-giới-hạn"></a>

### Các điểm không đạt và giới hạn

- PyLabRobot: upstream fixture cần ghi `test_logs`, bị chặn bởi read-only filesystem; không có seed pass.
- chunkify: source archive chứa symlink, bị từ chối trước build; không có test/model run cho case đó.
- marshmallow #1359: có base failure và fixed pass, nhưng tám identifier PASS_TO_PASS nguồn bị cắt tại khoảng trắng. Matcher exact giữ `historical_supported=false`; không sửa manifest để nâng số thành công.
- Generator hay trả before không khớp, edit không đổi hoặc lời giải thích hướng sửa lỗi; mười output bị giữ invalid. Năm candidate thực thi được nhưng không làm test fail. Không retry hoặc sửa tay output để tăng yield.
- Nhãn generator của cả sáu lượt đạt là syntax, trong khi evidence là lỗi logic/validation gây ValueError/KeyError. Nhãn nguồn, đề xuất agent và phê duyệt người dùng được tách riêng.
- Các case/SWE split được dùng cho development có chủ đích, không đại diện hai dataset. Test mục tiêu và recipe local không đồng nghĩa toàn bộ harness chuẩn SWE-bench. Các case đã xem không làm test độc lập cuối cùng.
- Diff raw v2 trên Windows có newline translation thừa; before/after và candidate đầy đủ vẫn khớp hash. Đã sửa writer cho run sau, không thay artifact cũ.

<a id="expansion-01-kiểm-tra-và-bàn-giao"></a>

### Kiểm tra và bàn giao

Đã đối chiếu **78 JUnit / 2.580 testcase records có lặp**, 11 candidate hashes/phép edit, host inventories của tám environment và tracked source/test bytes trong cả hai role của tám image. Sau test-freeze, mỗi cặp base/fixed chỉ khác đúng file sản phẩm đã đăng ký; không có khác biệt conftest/fixture ẩn. **202 file W1 được bảo vệ và 968 file raw mới được ghi inventory giữ nguyên hash.**

Kiểm thử phần mềm cuối: **49 discovered, 48 pass, một legacy Docker test opt-in skip**. Các Docker build/test thật của batch là bằng chứng tích hợp riêng; không gọi skip đó là đã chạy. [Log phần mềm](evidence/expansion-01/software-tests.txt). Kiểm tra bao gồm case/gate tách biệt, edit duy nhất, source patch vào đúng export, timeout/error giữ mẫu số, không đưa reference fields vào prompt, tamper refusal, resume không gọi lại generation chưa rõ kết quả, OS lock và HTML escaping.

Raw artifacts ở `runs/` và `.cache/expansion/`, không đi theo Git clone. Snapshot/patch/setup/license evidence được giữ local; registry và summary nhỏ có thể version hóa. Archive khôi phục của đợt được ghi ở [evidence README](evidence/expansion-01/README.md).

W2-01/02 đủ dùng cho development, W2-03 có registry và pilot nhiều repo thực tế. Bước tiếp theo là **W2-04: hoàn thiện grouping/near-duplicate và vai trò split trước vòng train**. Bản review mới sẵn sàng để người dùng đọc; gold labels/training eligibility vẫn pending. Chưa bắt đầu SFT, benchmark cuối hoặc 3B inference.

<a id="expansion-02"></a>

## Tổng kết development 02 — thêm case và giao thức site v3

Ngày 30/10/2026. [Registry](../data-manifests/expansion-02.json), [profile hiệu chỉnh](../data-manifests/expansion-02-corrections.json), [số liệu thực](evidence/expansion-02/summary.json), [review kỹ thuật](data-review.md#expansion-02), [grouping/duplicate snapshot](../data-manifests/development-groups-v1.json).

<a id="expansion-02-kết-quả-mới"></a>

### Kết quả mới

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

<a id="expansion-02-khác-biệt-so-với-đợt-01"></a>

### Khác biệt so với đợt 01

- Đợt 02 bổ sung failure được kiểm chứng ở **astroid, pvlib và FastAPI**, ngoài pydicom của đợt 01.
- V3 cho model chọn `site_id` từ source đã pin rồi trả một dòng replacement không có indentation. Pipeline thêm lại indentation/newline nguyên trạng theo hợp đồng; không sửa nội dung model để cho test fail. Các site cho ba lượt được phân bổ riêng khi có đủ site.
- Prompt có excerpt của upstream tests và source; **7B không còn bị yêu cầu tự gán nhãn chẩn đoán** trong v3. Raw v2/W1 và self-label cũ giữ nguyên. Model, options, budget token và các seed 5417/5418/5419 không đổi.
- Test IDs nguồn chỉ được resolve bằng exact match hoặc **một** tên parameterized test đầy đủ có prefix nguồn bị cắt. Plain/fuzzy/ambiguous prefixes bị từ chối; mapping từng ID được lưu trong manifest. astroid-1866 vẫn chưa resolve được ID có escape newline, nên flag lịch sử còn false dù fixed seed pass.
- AST được parse tĩnh từ seed/test nguồn để lập site/excerpt; không import hoặc chạy candidate trên host. Runtime Docker vẫn không mạng/read-only/không đặc quyền và có giới hạn.

Hai cohort khác case và giao thức, nên các tỷ lệ này chưa là đối chứng chứng minh v3 tốt hơn v2 hoặc synthetic cải thiện chẩn đoán.

<a id="expansion-02-lỗi-được-giữ-và-profile-hiệu-chỉnh"></a>

### Lỗi được giữ và profile hiệu chỉnh

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

<a id="expansion-02-thời-gian-kiểm-tra-và-bàn-giao"></a>

### Thời gian, kiểm tra và bàn giao

Đợt chính chạy **06:52:40–06:58:36 +07**; hai profile hiệu chỉnh chạy **06:59:44–07:01:37 +07**. Tổng budget charge được ghi nhận là **527,436 giây**: profile hiệu chỉnh kế thừa 414,546 giây đã charge của đợt chính, không cộng khoản này lần thứ hai. Các metadata fallback chưa có timer đầy đủ không được giả làm số đo chính xác; thời gian coding nằm ngoài. Tổng thời gian 15 lời gọi model **50,406 giây**, có loading/runtime, không là steady-state benchmark.

Integrity audit kiểm tra **6 image**, cả base/fixed source/test inventories đều khớp. Đã đọc **87 JUnit / 2.822 testcase records có lặp**, replay phép thay thế cho 14 candidate hợp lệ, kiểm tra hash và acceptance signatures. **1.087 file run/evidence có trước đợt và 1.018 raw file mới được ghi inventory giữ nguyên byte.** Raw artifacts không đi theo clone.

Phần mềm hiện có **58 tests: 57 pass, một legacy Docker test opt-in skip**; [output thật](evidence/expansion-02/software-tests.txt). Đây là software fixtures, tách khỏi Docker/model experiment evidence.

Cộng hai đợt mở rộng: **40 case nguồn sàng lọc, 17 case nguồn đã thử trên 10 repo**, thêm hai profile hiệu chỉnh không tính nguồn mới; **36 lượt 7B, 17 lượt đạt runner, 14 candidate khác byte đạt runner**. Trong đó một candidate v3 vi phạm valid-syntax như review nêu. Snapshot grouping chứa 40 nguồn / 42 profile records / 20 repo groups, gồm cả case bị loại; 20 groups không có nghĩa đã chạy 20 repo. Exact duplicates và lexical-edit suggestions được ghi riêng, không tự xóa hay phê duyệt mẫu.

Tất cả vẫn là development; **gold labels, training eligibility và test split cuối chưa được phê duyệt**. Bước tiếp theo W2-04 là xử lý grouping/near-duplicate và chọn nguồn đánh giá chưa dùng phát triển, trước vòng train. Chưa chạy 3B/SFT hoặc sửa evidence W1/đợt 01.
