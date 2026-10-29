# IT5417 — Synthetic Data for CI Diagnosis

Sinh dữ liệu tổng hợp có kiểm chứng hỗ trợ chẩn đoán lỗi CI trong quy trình cộng tác người–agent.

## Toàn đề tài và milestone hiện tại

Mục tiêu nghiên cứu dài hạn là đánh giá dữ liệu synthetic đối với phân loại/khoanh vùng lỗi trên dữ liệu thật. Milestone đầu là **demo pipeline Python trên một repo thật**; chưa có fine-tuning hoặc kết luận hiệu quả ML.

Luồng demo W1: **AIDev record → repo/commit → seed pass → 7B sinh → Docker kiểm chứng → người duyệt → dữ liệu cho 3B chẩn đoán.** Generator duy nhất là `qwen2.5-coder:7b-instruct`; model chẩn đoán chính là `Qwen/Qwen2.5-Coder-3B-Instruct`, chưa triển khai/chạy. Model phụ đã bỏ khỏi workflow; evidence lịch sử giữ nguyên.

properr PR #6: AIDev v5, bảng all_pull_request, record 3256868569. Repo nguồn có Python + Rust; code điều phối của đề tài viết bằng Python. Nguồn, revision, snapshot và giới hạn nằm trong cases/properr-6.

## Bắt đầu

Cần Python >=3.11 và Git. Docker Desktop phải chạy Linux containers. Lệnh chạy từ root repository; phần điều phối không cần cài thư viện Python bên ngoài.

```text
python -m unittest discover -v
python -m ci_demo doctor
python -m ci_demo reproduce --case properr-6
```

Để sinh bằng local model, cài/start Ollama và tải generator 7B trước buổi demo:

```text
ollama pull qwen2.5-coder:7b-instruct
python -m ci_demo generate --model qwen2.5-coder:7b-instruct --attempts 3
python -m ci_demo verify --run <RUN-ID>
python -m ci_demo report --run <RUN-ID>
```

Mỗi lệnh in ID run và đường dẫn report HTML. Thay <RUN-ID> bằng ID thật được in, không nhập cả dấu ngoặc. Trên PC RTX 4070 SUPER, `python scripts/demo.py --pull-models` chỉ tải và chạy generator 7B, ba lượt. Thêm `--skip-reproduce` khi đã có passing seed hợp lệ tại local.

Demo lưu manifest/report `generation_demo` trước preflight, giữ mẫu số ba, lượt lỗi/chưa thực hiện và thời gian chưa đo; liên kết doctor/reproduction/generation được lưu theo từng stage. CLI không còn lệnh so sánh hai generator. Báo cáo comparison lịch sử vẫn đọc được, không sửa raw artifacts.

**Trạng thái thực tế:** [Tổng kết W1](docs/demo-summary.md): tái hiện properr thành công; 7B đạt kiểm chứng thực thi 2/3, chưa được duyệt để train. [Bản rà ba lượt 7B](docs/pilot-review.md) chờ người duyệt. Evidence PC/laptop và log 22-test nghiệm thu cũ được giữ nguyên; kiểm thử sau thay đổi workflow được ghi riêng trong [agent log](docs/agent-log.md).

## Review dữ liệu với agent

Dùng skill [ci-data-review](.agents/skills/ci-data-review/SKILL.md), ví dụ: `$ci-data-review Rà mẫu lỗi CI từ các artifact tôi cung cấp, giải thích nguyên nhân và đề xuất kết luận để tôi review.` Skill cũng có thể được chọn theo yêu cầu rà dữ liệu CI phù hợp.

Agent đọc code/diff/log, đối chiếu evidence và giải thích nhãn/vị trí đề xuất; người dùng review kết luận và các lựa chọn còn quan trọng. Skill không tự chạy lại thí nghiệm hoặc biến lời đồng ý tiếp tục thành duyệt nhãn/training. Nếu raw artifacts không nằm trong worktree, cung cấp đường dẫn run/archive; không cần tải lại model để review. Hướng dẫn đánh giá leakage phụ thuộc input chẩn đoán thực tế, không tự loại mẫu chỉ vì comment.

## Tài liệu và cấu trúc

- [Kế hoạch thực thi theo tuần dành cho agent](docs/implementation-plan.md): task ID, phụ thuộc, đầu ra, cổng nghiệm thu và điểm tiếp tục.
- [Kịch bản demo và lệnh đầy đủ](docs/demo-runbook.md).
- [Kiến trúc, trạng thái và phục hồi context](docs/architecture.md).
- [Nhật ký theo thứ tự](docs/agent-log.md).
- [Kế hoạch sau góp ý GVHD](docs/revised-plan.md).
- [Nguồn tài liệu nghiên cứu](docs/reference/README.md).
- [cases/](cases/README.md): mỗi case có `cases/<id>/case.json`, gồm properr W1 và cấu hình mở rộng; [data-manifests/](data-manifests/expansion-01.json): registry/chọn nhóm; .cache/: repo nguồn và môi trường.
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

## Đợt development nhiều repo

Kết quả thực đo của đợt 01:

| Hạng mục | Kết quả |
|---|---|
| Sàng lọc và tái hiện | 20 case sàng lọc → 9 case thử tái hiện, trên 6 repo |
| Seed và lượt sinh | 7 seed pass → 21 lượt sinh bằng 7B |
| Kiểm chứng thực thi | 6 lượt đạt, gồm 3 candidate khác byte; đều từ pydicom |
| Kiểm thử phần mềm | 49 kiểm thử: 48 pass, 1 legacy Docker opt-in skip |

Đây là số liệu development; chưa phải nhãn gold, số mẫu được duyệt train hoặc accuracy chẩn đoán.

[Đợt mở rộng 01](docs/expansion-01-summary.md) đã thử 9 case/6 repo từ AIDev và SWE Lite dev; 21 lượt 7B, 6 đạt thực thi nhưng chỉ 3 candidate khác byte. [Review kỹ thuật](docs/expansion-01-review.md) chờ người dùng; gold/training vẫn pending. W1 properr và evidence cũ giữ nguyên.

```text
python -m ci_demo batch --manifest data-manifests/expansion-01.json
python -m ci_demo batch --resume <BATCH-ID>
```

Raw artifacts/patches/cache không đi theo clone; đọc [runbook](docs/demo-runbook.md) trước khi bắt đầu run mới. Resume batch đã hoàn tất chỉ trả trạng thái đã lưu, không gọi lại model/test. [Task contract](docs/task-contract.md) và [hướng dẫn nhãn](docs/labeling-guide.md) phân biệt source evidence, generator proposal, agent assessment và human approval.
