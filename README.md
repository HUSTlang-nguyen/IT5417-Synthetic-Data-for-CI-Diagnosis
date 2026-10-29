# IT5417 — Synthetic Data for CI Diagnosis

Sinh dữ liệu tổng hợp có kiểm chứng hỗ trợ chẩn đoán lỗi CI trong quy trình cộng tác người–agent.

## Toàn đề tài và milestone hiện tại

Mục tiêu nghiên cứu dài hạn là đánh giá dữ liệu synthetic đối với phân loại/khoanh vùng lỗi trên dữ liệu thật. Milestone đầu là **demo pipeline Python trên một repo thật**; chưa có fine-tuning hoặc kết luận hiệu quả ML.

Luồng: **AIDev record → repo/commit → tái hiện trước/sau → seed pass → LLM sinh thay đổi → test độc lập → hoàn tác → người duyệt nhãn.**

properr PR #6: AIDev v5, bảng all_pull_request, record 3256868569. Repo nguồn có Python + Rust; code điều phối của đề tài viết bằng Python. Nguồn, revision, snapshot và giới hạn nằm trong cases/properr-6.

## Bắt đầu

Cần Python >=3.11 và Git. Docker Desktop phải chạy Linux containers. Lệnh chạy từ root repository; phần điều phối không cần cài thư viện Python bên ngoài.

```text
python -m unittest discover -v
python -m ci_demo doctor
python -m ci_demo reproduce --case properr-6
```

Để sinh bằng local model, cài/start Ollama và tải hai model trước buổi demo:

```text
ollama pull qwen2.5-coder:7b-instruct
ollama pull qwen2.5-coder:1.5b-instruct
python -m ci_demo generate --model qwen2.5-coder:7b-instruct --attempts 3
python -m ci_demo verify --run <RUN-ID>
python -m ci_demo report --run <RUN-ID>
python -m ci_demo compare --runs <RUN-7B> <RUN-1.5B>
```

Mỗi lệnh in ID run và đường dẫn report HTML. Thay <RUN-ID> bằng ID thật được in, không nhập cả dấu ngoặc. Trên PC RTX 4070 SUPER có thể chạy `python scripts/demo.py --pull-models` để thực hiện tuần tự hai model và xuất bảng so sánh.

Bảng so sánh giữ cả lượt lỗi/chưa thực hiện trong mẫu số, báo thời gian chưa đo và phát hiện giao thức không tương thích. Script vẫn lưu comparison report nếu demo bị gián đoạn; lệnh `compare` dựng bảng mới từ hai run đã lưu mà không gọi model.

**Trạng thái thực tế:** [PC RTX 4070 SUPER đã chạy](docs/evidence/target-pc/README.md): tái hiện properr thành công, 22 tests pass và đủ sáu lượt LLM. 7B đạt kiểm chứng thực thi 2/3, 1.5B đạt 1/3; nhãn/chất lượng chưa được duyệt để train. [Evidence laptop cũ](docs/evidence/README.md) và [agent log](docs/agent-log.md) được giữ riêng.

## Tài liệu và cấu trúc

- [Kế hoạch thực thi theo tuần dành cho agent](docs/implementation-plan.md): task ID, phụ thuộc, đầu ra, cổng nghiệm thu và điểm tiếp tục.
- [Kịch bản demo và lệnh đầy đủ](docs/demo-runbook.md).
- [Kiến trúc, trạng thái và phục hồi context](docs/architecture.md).
- [Nhật ký theo thứ tự](docs/agent-log.md).
- [Kế hoạch sau góp ý GVHD](docs/revised-plan.md).
- [Nguồn tài liệu nghiên cứu](docs/reference/README.md).
- cases/: provenance nhỏ được commit; .cache/: repo nguồn và môi trường có thể dựng lại.
- runs/: raw output/log/report sinh theo run ID, bị ignore; chỉ tóm tắt evidence cần thiết được commit.

## Giới hạn cần giữ

- Log tái hiện local không phải log CI lịch sử đã tải.
- Lỗi synthetic mới không được gán thành lỗi lịch sử của PR.
- Nhãn agent ở PR không chứng minh actor gây lỗi.
- Đạt kiểm tra thực thi chưa là gold label hoặc phê duyệt dùng để train.
- Mọi lượt sinh, kể cả lỗi, phải giữ trong mẫu số.
- Artifact report luôn ghi rõ xem lại kết quả; không giả làm chạy live.
- Không có fake mode dùng patch viết tay thay output LLM; fixture trong unit tests chỉ kiểm thử phần mềm.
- Không commit models, secrets, clone nguồn hoặc output lớn. Không có cloud fallback.
