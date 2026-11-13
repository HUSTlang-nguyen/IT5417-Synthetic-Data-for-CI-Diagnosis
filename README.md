# IT5417 — Synthetic Data for CI Diagnosis

Sinh dữ liệu tổng hợp có kiểm chứng hỗ trợ chẩn đoán lỗi CI trong quy trình cộng tác người–agent.

## Toàn đề tài và milestone hiện tại

**Bộ bảo vệ giữa kỳ:** [slide HUST, báo cáo LaTeX, cheatsheet A4 và ghi chú ôn tập](docs/midterm/README.md). 24 slide chính +4 dự phòng cho 20 phút; báo cáo 11 trang nội dung. Các tệp PPTX/PDF và source LaTeX bàn giao tại `output/midterm/`; thông tin họ tên/MSSV trên bìa để trống.

**13/11 — đã hoàn tất pilot và final test:** [validation](docs/evaluation-validation.md), [test/chi phí](docs/evaluation-results.md), [phân tích lỗi và synthetic](docs/evaluation-error-analysis.md). Trên cùng38realtest, M2 accuracy22/38, M5 24/38; joint cùng4/38. M1-P2 dùng **prompt mới**, giữ parser strict. Nhãn silver, chưa có gold. Các kết quả nhỏ chưa chứng minh synthetic có lợi tổng quát.

Mục tiêu nghiên cứu dài hạn là đánh giá dữ liệu synthetic đối với phân loại/khoanh vùng lỗi trên dữ liệu thật. Milestone đầu là **demo pipeline Python trên một repo thật**; pilot SFT và đánh giá tiếp theo được version hóa riêng, không thay kết quả demo lịch sử.

Luồng demo W1: **AIDev record → repo/commit → seed pass → 7B sinh → Docker kiểm chứng → người duyệt → dữ liệu cho 3B chẩn đoán.** Generator duy nhất là `qwen2.5-coder:7b-instruct`; model chẩn đoán chính là `Qwen/Qwen2.5-Coder-3B-Instruct`. Model phụ đã bỏ khỏi workflow; evidence lịch sử giữ nguyên.

**Dataset v1:** đã rà265real silver, khóa riêng cho pilot **250real (175train/37validation/38test) +101synthetic train**. Target matched175 của protocol v1.0 còn thiếu74; không coi pilot là hoàn tất mục tiêu cũ. [Bằng chứng](docs/evidence/dataset-v1-progress/README.md), [protocol gốc](docs/experiment-protocol.md), [dataset card](docs/dataset-card.md), [điểm tiếp tục](docs/implementation-plan.md#điểm-tiếp-tục-hiện-tại). Không gọi lại request unknown hoặc reset cap sinh. Core pipeline dùng standard library; ML có [dependency ghim](requirements-ml.txt) trong môi trường riêng.

[Kết quả thực đạt và phần chưa hoàn thành](docs/results.md).

**Training đã hoàn tất:** [pilot v1.1](docs/experiment-protocol-v1.1.md), [continuation v1.2](docs/experiment-protocol-v1.2.md) đến tổng10epoch cho M2/M5. Cảhai chọn checkpointparent104 theo validation; không dùng adapterepoch10 để test. [Lệnh train/continue/resume và monitor](docs/training-runbook.md) được giữ để tái lập; không cần chạy lại để xem kết quả.

Đọc nhanh: [trạng thái dữ liệu hiện hành](data-manifests/dataset-v1-status.json), [dung lượng/giữ dữ liệu/DVC](docs/data-storage.md). Không cần chạy lại audit hoặc thí nghiệm để trả lời tiến độ từ checkpoint.

Backend học tùy chọn: `.cache/ml-v1/Scripts/python.exe -m ci_demo.sft --manual --model M0|M1|M2|M5`. Evaluation có [manifest riêng](data-manifests/evaluation-v1.json) và khóa test chung để ngăn trial thứhai; finaltest hiện đã hoàn tất. Chỉ đọc/tạo lại phân tích từ artifact bằng `python -m ci_demo.evaluation_report --run evaluation-20261112T210848574175Z`, không gọi model. Raw dataset/model/run nằm local ngoài Git; clone chỉ mang code/tài liệu và evidence nhỏ.

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

**Trạng thái thực tế:** [Tổng kết W1](docs/development-summary.md#w1): tái hiện properr thành công; 7B đạt kiểm chứng thực thi 2/3, chưa được duyệt để train. [Bản rà ba lượt 7B](docs/data-review.md#w1) đã được người dùng đồng ý kết luận/kiến nghị giữ-loại; gold/training vẫn pending. Evidence PC/laptop và log 22-test nghiệm thu cũ được giữ nguyên; kiểm thử sau thay đổi workflow được ghi riêng trong [agent log](docs/agent-log.md).

## Review dữ liệu với agent

Dùng skill [ci-data-review](.agents/skills/ci-data-review/SKILL.md), ví dụ: `$ci-data-review Rà mẫu lỗi CI từ các artifact tôi cung cấp, giải thích nguyên nhân và đề xuất kết luận để tôi review.` Skill cũng có thể được chọn theo yêu cầu rà dữ liệu CI phù hợp.

Agent đọc code/diff/log, đối chiếu evidence và giải thích nhãn/vị trí đề xuất; người dùng review kết luận và các lựa chọn còn quan trọng. Skill không tự chạy lại thí nghiệm hoặc biến lời đồng ý tiếp tục thành duyệt nhãn/training. Nếu raw artifacts không nằm trong worktree, cung cấp đường dẫn run/archive; không cần tải lại model để review. Hướng dẫn đánh giá leakage phụ thuộc input chẩn đoán thực tế, không tự loại mẫu chỉ vì comment.

## Tài liệu và cấu trúc

- [Tổng kết phát triển](docs/development-summary.md): số liệu W1 và hai expansion, thời gian, giới hạn, replay và bước tiếp theo.
- [Review dữ liệu](docs/data-review.md): phân tích từng mẫu, kiến nghị và trạng thái xác nhận.

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

[Đợt mở rộng 01](docs/development-summary.md#expansion-01) đã thử 9 case/6 repo từ AIDev và SWE Lite dev; 21 lượt 7B, 6 đạt thực thi nhưng chỉ 3 candidate khác byte. [Review kỹ thuật](docs/data-review.md#expansion-01) đã được người dùng đồng ý kiến nghị giữ/loại; gold/training vẫn pending. W1 properr và evidence cũ giữ nguyên.

```text
python -m ci_demo batch --manifest data-manifests/expansion-01.json
python -m ci_demo batch --resume <BATCH-ID>
```

Raw artifacts/patches/cache không đi theo clone; đọc [runbook](docs/demo-runbook.md) trước khi bắt đầu run mới. Resume batch đã hoàn tất chỉ trả trạng thái đã lưu, không gọi lại model/test. [Task contract](docs/task-contract.md) và [hướng dẫn nhãn](docs/labeling-guide.md) phân biệt source evidence, generator proposal, agent assessment và human approval.

### Kết quả đợt 02 đã chạy

[Đợt 02](docs/development-summary.md#expansion-02): sàng lọc thêm 20 nguồn, thử 8 case mới và 2 profile hiệu chỉnh; 15 lượt 7B, 11 đạt runner/11 candidate khác byte ở astroid, pvlib và FastAPI. Một candidate gây lỗi cú pháp vi phạm prompt v3; người dùng đã đồng ý loại khỏi subset v3 valid-Python và giữ các mẫu nhân tạo cho phân tích development, chưa đưa vào train. [Xác nhận review](docs/data-review.md#xac-nhan-expansion-01-02) ghi phạm vi riêng khỏi gold/training.

Cộng hai đợt: **40 nguồn sàng lọc, 17 case nguồn đã thử/10 repo, 36 lượt sinh, 17 lượt đạt runner/14 candidate khác byte**. Những số này chưa phải gold/training approval. [cases/README](cases/README.md) phân biệt source case với profile; [grouping snapshot](data-manifests/development-groups-v1.json) giữ development, chưa tạo split cuối.
