# Kịch bản demo đầu tiên

## Phạm vi và kết luận được phép

Demo một mẫu repo thật (properr PR #6, record AIDev v5 3256868569) và các lỗi mới do model sinh trên bản head đã pass. Đây là kiểm tra khả thi của pipeline, không phải benchmark, kết quả fine-tuning, bằng chứng actor lịch sử gây lỗi hoặc dữ liệu gold đã duyệt.

Workflow: user yêu cầu sinh ca lỗi -> code điều phối gọi LLM -> ứng viên chỉ sửa file Python cho phép -> test độc lập trong Docker -> log thật -> người rà nhãn.

Vai trò hiện hành: 7B là generator duy nhất; 3B là model chẩn đoán chính ở giai đoạn sau, chưa tải/chạy trong W1. Model phụ đã bỏ khỏi cấu hình và workflow. Dùng [demo-summary](demo-summary.md) và [pilot-review](pilot-review.md) để replay ba lượt 7B hiện có; không chạy lại chỉ để soạn tài liệu.

## Trước buổi demo trên PC

- Clone repo private và mở terminal ở root repo.
- Cần Python >=3.11, Git, Docker Desktop Linux engine hoạt động, NVIDIA driver và Ollama local. Máy mục tiêu RTX 4070 SUPER 12 GB cần được kiểm tra thực tế.
- Cài/start Ollama theo https://docs.ollama.com/windows. Không cần API key, không dùng cloud.
- Chạy doctor trước. Không chuyển tiếp endpoint Ollama ra Internet.
- Tải model và build image trước buổi họp; các bước này cần mạng/dung lượng và có thể mất thời gian.
- Không cài pytest trong venv base của container: sẽ che mất giả thuyết dependency của PR.

## Lệnh (PowerShell hoặc terminal tương đương)

```text
python -m ci_demo doctor
python -m unittest discover -v
python -m ci_demo reproduce --case properr-6
ollama pull qwen2.5-coder:7b-instruct
python -m ci_demo generate --model qwen2.5-coder:7b-instruct --attempts 3
python -m ci_demo verify --run <RUN-ID-IN-RA-O-TREN>
python -m ci_demo report --run <RUN-ID>
```

Hoặc chạy trọn phiên sinh bằng 7B, ba lượt, trên PC:

```text
python scripts/demo.py --pull-models
```

Nếu đã có passing seed và image được xác minh trên PC: thêm --skip-reproduce. Script vẫn kiểm tra image ID và baseline trước khi sinh.

Script tạo demo manifest/report trước preflight, checkpoint sau doctor/reproduction/generation và kết thúc sau verify. `--pull-models` chỉ tải 7B. Lỗi môi trường/download/generation/verification dừng phiên, trả exit 1 và giữ `demo_incomplete` cùng liên kết evidence đã có; không retry model tự động. Mẫu số luôn ba, lượt chưa thực hiện hiển thị riêng, thời gian chưa đo là chưa biết.

`generation_demo` kết thúc `demo_finished` khi đủ ba lượt có trạng thái cuối và stage verify hoàn tất; có thể không có mẫu nào đạt. Tổng thời gian gọi sinh chỉ cộng các lượt có số đo, không phải toàn bộ wall time hoặc peak VRAM. Nhãn vẫn chờ người duyệt. Không có lệnh `compare` hoặc nhánh legacy trong CLI/demo hiện hành; báo cáo comparison lịch sử giữ nguyên, bộ đọc report vẫn hỗ trợ định dạng cũ.

Nếu unit tests trên Windows báo lỗi quyền ghi ở thư mục tạm hệ thống, đặt thư mục tạm trong cache của repo trước khi chạy lại:

```powershell
New-Item -ItemType Directory -Force .cache/test-temp | Out-Null
$env:TEMP = (Resolve-Path .cache/test-temp).Path
$env:TMP = $env:TEMP
python -m unittest discover -v
```

PC hiện tại dùng bản Ollama portable tại `.cache/tools/ollama/ollama.exe`. Sau khi khởi động lại PC, nếu cần bật lại bản này (PowerShell, từ root repo):

```powershell
$env:OLLAMA_MODELS = Join-Path (Resolve-Path .cache).Path 'models'
$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:PATH = (Resolve-Path .cache/tools/ollama).Path + ';' + $env:PATH
Start-Process -FilePath (Resolve-Path .cache/tools/ollama/ollama.exe).Path -ArgumentList 'serve' -WindowStyle Hidden
```

Chỉ chạy bước bật server nếu chưa có Ollama ở cổng 11434; dùng `doctor` để kiểm tra. Runtime và weights đều nằm trong cache bị ignore; clone Git không kèm các file này.

## Đợt development nhiều case (v2)

Đợt đầu có registry tại `data-manifests/expansion-01.json`: 20 case sàng lọc (10/nguồn), chọn tối đa 5/nguồn, 4/repo. Nguồn SWE Lite dev trong đợt này thuộc development. Tài liệu nhiệm vụ và nhãn nháp nằm ở [task-contract](task-contract.md) và [labeling-guide](labeling-guide.md). Không dùng đợt này như test độc lập.

```text
python scripts/screen_expansion.py
python -m ci_demo batch --manifest data-manifests/expansion-01.json
python -m ci_demo batch --resume <BATCH-ID>
python -m ci_demo reproduce --case <REGISTERED-CASE-ID>
python -m ci_demo generate --case <REGISTERED-CASE-ID> --model qwen2.5-coder:7b-instruct --attempts 3
python -m ci_demo verify --run <GENERATION-RUN-ID>
```

Screening script đọc raw metadata đã lưu trong `.cache/expansion`, không tự tải toàn dataset. Từ clone mới cần artifact root/snapshot nguồn đúng hash trước khi chạy; không dựng lại raw patch bằng tay. Case configs nhỏ được version hóa, raw source/patch/weights không vào Git. Mỗi case có recipe Python/dependencies, test targets và tài nguyên rõ ràng; SWE recipes là reconstruction theo test mục tiêu, không thay toàn bộ harness chính thức.

Batch checkpoint trước mọi stage và sau kết quả, dùng source/image/gate riêng theo case và revision. Ngân sách 6 giờ active runtime tính cả discovery đã đo; coding nằm ngoài. Trước mỗi thao tác kiểm tra thời gian và tối thiểu 20 GiB trống. Build tối đa 20 phút, test 5 phút, model call 3 phút; stage đang chạy được giới hạn theo timeout đã khai báo. Không tự retry lỗi môi trường/model, tải 3B hoặc prune Docker.

Resume bỏ qua stage hoàn tất; nếu stage gián đoạn có manifest chưa hoàn tất, đánh dấu kết quả chưa biết và không gọi lại model/test của stage đó. Thời gian bị mất do interruption được báo thành một cận ngân sách riêng, không giả làm số đo thật. Muốn thử lại một case lỗi cần thí nghiệm mới với lý do/giao thức mới; không dùng resume để che lần thất bại.

V2 dùng một phép thay thế `before → after` khớp đúng một lần trong một file Python; raw response và candidate đầy đủ được giữ. Generation và verification là các run riêng có liên kết, không sửa generation đã hoàn tất. Passing gate kiểm tra toàn inventory source/test và image ID. Runtime không mạng, read-only, user 65534, drop capabilities và giới hạn tài nguyên. Recipe TCM khai báo tmpfs `logs/` vì logger upstream cần ghi; source/tests/candidate và raw evidence vẫn không được ghi.

Đạt thực thi chỉ là baseline pass → ba fail có chữ ký ổn định → restored pass. Review bằng `$ci-data-review` đọc artifacts đã lưu; gold labels/training vẫn pending. Báo đủ số selected/requested/unexecuted, cả lỗi build/timeout/output không hợp lệ và thời gian thực đo.

## Replay W1 đã lưu khoảng 5 phút

1. Nêu nguồn dataset, PR và commit; tách tái hiện lịch sử khỏi synthetic.
2. Mở báo cáo reproduce: base không có pytest, head chạy test. Nếu kết quả không đúng giả thuyết, phải nói rõ.
3. Chạy generate một model với ba lượt, hoặc mở kết quả đã lưu và ghi rõ không live.
4. Chạy verify; chỉ ra baseline, ba lần ứng viên và restoration. Không nhầm fail build với lỗi test.
5. Mở report HTML: diff, log, timing, lượt không đạt và review pending. Giữ mẫu số đủ ba lượt 7B; phân biệt đạt thực thi với được duyệt để train.
6. Kết luận khả thi/điểm hỏng, không khẳng định synthetic cải thiện ML.

## Đầu ra và phục hồi

Lệnh in run ID và đường dẫn report. Evidence nằm trong runs/<id>, bị Git ignore. Sao lưu thư mục run khi cần chuyển máy hoặc trình diễn offline; đây là dữ liệu nguồn và model output, không kèm secret.

Không chỉnh candidate.py sau khi sinh; verify kiểm tra hash. Không ghi đè run đã verify. Muốn thử lại hãy tạo run mới.

Kiểm tra Docker runner sau reproduce trong PowerShell: `$env:CI_DEMO_DOCKER_TESTS='1'; python -m unittest discover -v`. Fixture này chỉ kiểm thử phần mềm, không gọi LLM hoặc tạo kết quả nghiên cứu. Xóa biến sau bằng `Remove-Item Env:CI_DEMO_DOCKER_TESTS`.

Nếu Ollama/PC chưa sẵn sàng, reproduce vẫn chạy riêng. Không dùng patch tự viết thay cho output LLM rồi gọi là model-generated. Unit tests có fixture/mock chỉ kiểm tra pipeline, không tính vào kết quả sinh.

## Giới hạn

- Cấu hình Docker tái dựng local, không khôi phục chính xác image GitHub Actions lịch sử.
- Các toolchain/runtime được lưu cùng evidence; model tag có thể đổi nên lưu digest mỗi run.
- Một repo không đại diện AIDev. properr gồm Python và Rust, không phải bộ repo Python thuần.
- Nhãn và tính hợp lý cần người duyệt; pass-fail-pass chưa tự xác nhận nguyên nhân hoặc tác giả.
- Chưa có fine-tuning, interceptor, đối chứng pass/fail hoặc test độc lập cuối cùng.
