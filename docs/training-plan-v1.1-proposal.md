# Đề xuất chuyển sang baseline và pilot SFT v1.1

Trạng thái cập nhật 12/11/2026: người dùng đã yêu cầu **triển khai code để tự chạy sau**. Đã chuẩn bị [protocol v1.1](experiment-protocol-v1.1.md), lock và [runbook](training-runbook.md); chưa thực thi train. Các mục dưới đây giữ nội dung đề xuất trước triển khai, gồm mô tả giới hạn code tại thời điểm đó. [Kết quả vòng 1.0](results.md) vẫn chưa đạt mục tiêu 250 real + 175 synthetic + M0/M1/M2/M5; ngân sách thu thập cũ không đổi. Study thủ công mới bắt đầu khi người dùng chạy lệnh model, theo chính sách thời gian trong protocol v1.1.

## Quyết định đề xuất

Dừng sinh thêm trong vòng hiện hành, dùng250real và101synthetic đã audit để làm pilot học/đánh giá. Tỷ lệsynthetic:realtrain là101:175≈0,58:1;1:1 là lựa chọn thiết kế thí nghiệm trước đó, không phải yêu cầu kỹ thuật của SFT. Chỉ đổi tỷ lệ khi phương án mới được chốt rõ, không sửa số liệu vòng1.0 hoặc gọi goal cũ hoàn tất.

Giữ175realtrain/37validation/38test và vai tròrepo. Dữ liệu vẫn silver, actorrealunknown và goldpending. Classification và file/function localization tiếp tục là hai nhiệm vụ chính; giải thích ngắn được học cùngJSON. Không train generator7B, không train nhãn người/agent gây lỗi, không thêm mô hình phụ.

| Model | Dữ liệu học | Vai trò |
|---|---|---|
| M0 TF-IDF+LogisticRegression |175realtrain| Baseline phân loại; không đánh giá khoanh vùng bằng classifier này |
| M1 Qwen2.5-Coder-3B-Instruct | Không cập nhật trọng số | Baseline prompt-only trên cùnginput |
| M2 QLoRA3B |175realtrain| SFTreal-only |
| M5 QLoRA3B |175real+101synthetic=276train| Đối chứng thêm synthetic |

M2/M5 tạo adapter mới từ cùng3Bbase revision, độc lập với nhau và với phép chạy thử. Cùng37realvalidation để chọn checkpoint; chỉ mở38realtest sau khi mọi cấu hình/checkpoint được khóa.

## Việc phải sửa trước khi người dùng tự train

1. Tạo protocol/manifestv1.1 mới từ lựa chọn351 đã audit; giữ manifestv1.0. Tách cổng theo từng thí nghiệm: M0/M1/M2 cần real/split/support/evidence đã khóa; M5 thêm101synthetic chất lượng đúngtrain groups theo tỷ lệ mới. Không bỏ kiểm tra hash, nguồn nhãn, trùng lặp hoặc leakage để vượt cổng.
2. Giữ inputretrieval-v2 cho pilot so sánh này. Chỉ59/175realtrain có referencefunction trong code sau tokenization, nên phải báo lỗi truy xuất riêng. Không phải trần cứng accuracy vì model còn thấylog. Không sửa retrieval từ các lỗi validation/test đã xem; muốn phát triểnretrieval tiếp thì chỉ dùngtrain và tạo phiên bản riêng trước dự đoán nghiên cứu.
3. Giữ configNF4QLoRA/r16/alpha32/dropout0,05/lr1e-4/batch1/accum8/context2048/response384/seed5417. Với mixed276, công thức hiện hành cho104optimizerupdates, dùng cùng104choM2/M5; lưu token/exposure thực, không gọi đó là compute bằng nhau tuyệt đối. Hai checkpointvalidation dự kiếnstep52/104. Đây chưa là số update đã chạy.
4. Chạy kiểm tra ngắn về forward/backward, finite loss, VRAM và lưu/nạp adapter trên dữ liệutrain; không dùng làm điểm nghiên cứu. Đo thời gian optimizerstep và suy luậnvalidation để xét cap2h mỗiSFT và deadline gốc; nếu không đủ thì báo phần chưa làm, không tự gia hạn.
5. Hoàn thiện lệnh khởi chạy và resume dành cho người dùng. Hiện`ci_demo/sft.py`có CLI, losslogs, optimizer/RNGcheckpoint và reloadverification, nhưng gọi`trainer.train()`chưa có đường resume-from-checkpoint. Không hứa khôi phục train tự động chỉ vì checkpoint đã tồn tại. Resume phải giữ dataset/model/config identity và không gọi lại validation đã hoàn tất.
6. Thêm theo dõi GPU trong runSFT và hướng dẫn lệnh rõ ràng. Hiện`gpu_trace`chạy cho batchsinh7B; SFT lưu peakCUDAallocated/reserved nhưng chưa tự ghi CSVGPUtemperature/utilization theo thời gian. Không gọi đó là dashboardTensorBoard/W&B: hiện`report_to=[]`.

Chỉ cần kiểm thử các gate/resume/monitor thay đổi; không chạy lại datasetpilot, Dockerreproduction hoặc toàn bộdeepaudit để viết phương án này.

## Thứ tự thực hiện đề xuất

Khóa bảnv1.1 → M0/M1baseline → kiểm tra train ngắn → M2 → M5 → chọn checkpoint bằng joint class/functionTop1 trênvalidation → khóa cấu hình → finaltest một lần. Giữ response-onlyloss vàJSONtarget. Không coi trainingloss giảm là bằng chứng model định vị đúng.

Ngân sách gốc hết hạn13/11/2026lúc02:19:29+07. Không dự báo chắc thời gianSFT từ phép đo inference24,515s; phải đo backward/update trước. Nếu sửa deadline/cap, ghi thành quyết định ngân sách mới trước side effect.

## Người dùng tự theo dõi

Mở terminal riêng tạiVSCode/PowerShell:

```powershell
nvidia-smi -l 1
```

XemGPU-Util,Memory-Usage,nhiệt độ và tiến trìnhPython. `Ctrl+C`trong terminalmonitor chỉ dừng monitor, không dừng terminaltrain. Có thể dùng truy vấn gọn:

```powershell
nvidia-smi --query-gpu=timestamp,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw --format=csv -l 1
```

Lệnh được mô tả trong[NVIDIA nvidia-smi](https://docs.nvidia.com/deploy/nvidia-smi/index.html). Mức sử dụngGPU vàVRAM không thay điểmvalidation;GPU thấp lúc load/tokenize/savecheckpoint không tự là lỗi. Khi sangbackward phải xác nhận code thực dùngCUDA, loss hữu hạn và step tiến lên.

LogSFT hiện lưu ở`runs/learning-m2-<timestamp>/`hoặc`runs/learning-m5-<timestamp>/`:

| File | Đọc để biết |
|---|---|
| `training-events.jsonl` | step, loss/lr/gradnorm khiTrainer cung cấp, token/exposure và peakVRAM |
| `training-config.json`, `trainer-arguments.json` | model/data/config đã dùng |
| `validation-step-*/metrics.json` | classification/localization/joint score, invalid output và retrieval coverage |
| `checkpoint-selection.json` | Vì sao chọn checkpoint |
| `checkpoints/checkpoint-*` | Adapter và trạng tháitrainer/optimizer/RNG theo khả năngbackend |
| `training-summary.json`, `reload-verification.json` | Chi phí thực và kiểm tra adapter lưu/nạp |
| `manifest.json` | Trạng thái hoàn tất/lỗi vàrunidentity |

Không cung cấp lệnh train như thể đã sẵn sàng: hiện gate1.0 vẫn từ chối101synthetic và resume/continuousGPUtrace cần hoàn thiện trước bàn giao tự chạy.
