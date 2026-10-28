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
