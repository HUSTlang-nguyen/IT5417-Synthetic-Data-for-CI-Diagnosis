# Kịch bản demo đầu tiên

## Phạm vi và kết luận được phép

Demo một mẫu repo thật (properr PR #6, record AIDev v5 3256868569) và các lỗi mới do model sinh trên bản head đã pass. Đây là kiểm tra khả thi của pipeline, không phải benchmark, kết quả fine-tuning, bằng chứng actor lịch sử gây lỗi hoặc dữ liệu gold đã duyệt.

Workflow: user yêu cầu sinh ca lỗi -> code điều phối gọi LLM -> ứng viên chỉ sửa file Python cho phép -> test độc lập trong Docker -> log thật -> người rà nhãn.

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
ollama pull qwen2.5-coder:1.5b-instruct
python -m ci_demo generate --model qwen2.5-coder:7b-instruct --attempts 3
python -m ci_demo verify --run <RUN-ID-IN-RA-O-TREN>
python -m ci_demo report --run <RUN-ID>
```

Lặp generate/verify/report cho 1.5B cùng giao thức. Hoặc chạy tuần tự toàn bộ trên PC:

```text
python scripts/demo.py --pull-models
```

Nếu đã có passing seed và image được xác minh trên PC: thêm --skip-reproduce. Script vẫn kiểm tra image ID và baseline trước khi sinh.

Script tạo comparison manifest/report ngay khi bắt đầu, cập nhật sau từng stage và giữ báo cáo khi môi trường hoặc một model lỗi. Model còn lại vẫn được thử nếu lỗi xảy ra trong stage của riêng model đầu. Mỗi model luôn có mẫu số ba; lượt chưa thực hiện hiển thị riêng, thời gian chưa đo là chưa biết.

Để dựng lại bảng so sánh từ hai run đã lưu, không gọi lại model hoặc chạy test:

```text
python -m ci_demo compare --runs <RUN-7B> <RUN-1.5B>
```

Lệnh tạo comparison run mới, không sửa evidence của hai run đầu vào. So sánh kiểm tra cùng source, source/test hash, prompt, options và image ID; giao thức khác nhau hoặc stage chưa xong được ghi `comparison_incomplete` và trả exit 1. Nhãn vẫn chờ người duyệt. Tổng thời gian sinh chỉ cộng các lượt có số đo, không phải toàn bộ wall time hoặc phép đo VRAM.

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

## Trình diễn khoảng 5 phút

1. Nêu nguồn dataset, PR và commit; tách tái hiện lịch sử khỏi synthetic.
2. Mở báo cáo reproduce: base không có pytest, head chạy test. Nếu kết quả không đúng giả thuyết, phải nói rõ.
3. Chạy generate một model với ba lượt, hoặc mở kết quả đã lưu và ghi rõ không live.
4. Chạy verify; chỉ ra baseline, ba lần ứng viên và restoration. Không nhầm fail build với lỗi test.
5. Mở report HTML: diff, log, timing, rejected attempts và review pending. So hai model bằng cùng mẫu số.
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
