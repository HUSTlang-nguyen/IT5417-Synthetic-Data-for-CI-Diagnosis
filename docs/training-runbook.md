# Tự chạy M0, M1, M2 và M5

Code và dataset pilot v1.1 đã chuẩn bị trên **worktree này**. Chưa chạy bốn model nghiên cứu hoặc smoke CUDA. [Protocol](experiment-protocol-v1.1.md) chốt 175 real train, 101 synthetic chỉ cho M5, 37 validation và 38 test; nhãn vẫn silver.

**Sau khi pull:** Git mang code, cấu hình nhỏ và tài liệu; không mang `.cache/`, `runs/`, dataset hoặc model. Lock hiện ghim đường dẫn tuyệt đối của worktree dưới đây. Nếu pull ở checkout khác hoặc máy khác, các lệnh chưa chạy được chỉ nhờ Git; cần chuyển và đóng gói lại tài nguyên local với kiểm tra đường dẫn/hash. Trên máy hiện tại, dùng đúng worktree đã chuẩn bị để chạy; chưa có bộ chuyển môi trường tự động.

## Chạy từng lệnh khi cần

Mở PowerShell tại đúng thư mục dưới đây. Không chạy bốn model đồng thời. M0 là baseline CPU; M1 chỉ suy luận 3B; M2/M5 mới là hai lượt SFT.

```powershell
Set-Location 'C:\Users\neikh\.codex\worktrees\a4f5\IT5417-Synthetic-Data-for-CI-Diagnosis'
.\scripts\train.ps1 -Check
```

`-Check` đối chiếu lock, hash và cổng dữ liệu, không tạo study hoặc gọi model. Kết quả mong đợi là `ready_metadata_checked_no_model_run`. Cần môi trường Python tại `.cache/ml-v1/`, base 3B và raw/cache đã chuẩn bị; chỉ clone repository chưa đủ. Giữ ít nhất 20 GiB trống. Trước khi dùng GPU, đóng các ứng dụng/lượt sinh đang giữ nhiều VRAM.

Chạy lần lượt khi sẵn sàng:

```powershell
.\scripts\train.ps1 M0
.\scripts\train.ps1 M1
.\scripts\train.ps1 M2 -Smoke
.\scripts\train.ps1 M2
.\scripts\train.ps1 M5
```

Mỗi dòng là một lệnh độc lập, không phải hàng đợi tự chạy. Smoke tùy chọn gồm ba optimizer updates và kiểm tra lưu/nạp adapter trên train; không mở validation/test và không được tính là kết quả M2. Nên xem smoke thành công, loss hữu hạn và VRAM trước lượt dài. M2/M5 đều tạo adapter mới từ base 3B; không nối tiếp adapter của nhau. Mỗi lượt nghiên cứu có 104 updates, validation tại 52/104.

Nếu PowerShell chặn script, dùng Python trực tiếp, không cần đổi policy toàn máy:

```powershell
.\.cache\ml-v1\Scripts\python.exe -m ci_demo.sft --manual --check
.\.cache\ml-v1\Scripts\python.exe -m ci_demo.sft --manual --model M0
.\.cache\ml-v1\Scripts\python.exe -m ci_demo.sft --manual --model M1
.\.cache\ml-v1\Scripts\python.exe -m ci_demo.sft --manual --model M2 --smoke
.\.cache\ml-v1\Scripts\python.exe -m ci_demo.sft --manual --model M2
.\.cache\ml-v1\Scripts\python.exe -m ci_demo.sft --manual --model M5
```

Không thêm `--context 1024` để xử lý OOM giữa study: thay context là cấu hình thí nghiệm khác, không phải resume. Runtime thực chưa đo; chưa thể hứa số phút train. Study chỉ bắt đầu khi chạy lệnh model đầu tiên, không hết hạn theo ngày. Cap cộng dồn hai giờ cho từng SFT (M2 gồm cả smoke), hai giờ evaluation và 1.500 request chẩn đoán vẫn áp dụng; resume không cấp lại ngân sách.

## Xem tiến độ và GPU

Terminal train in run ID, thư mục artifact, step/104 và loss. Terminal thứ hai dùng:

```powershell
nvidia-smi -l 1
```

Xem GPU-Util, Memory-Usage và nhiệt độ. `Ctrl+C` ở terminal monitor chỉ dừng monitor; `Ctrl+C` trong terminal train yêu cầu dừng train. GPU thấp khi load, tokenization, lưu checkpoint hoặc M0 là bình thường. Khi backward cần thấy step tăng và loss hữu hạn. Chưa có dashboard TensorBoard/W&B.

Trong thư mục `runs/learning-m2-<timestamp>/` hoặc `runs/learning-m5-<timestamp>/`:

| Artifact | Nội dung |
|---|---|
| `manifest.json`, `training-config.json` | Trạng thái, lỗi, model/data/code hash và cấu hình |
| `training-events.jsonl` | Từng step, loss, learning rate, thời gian, token/exposure và peak CUDA |
| `gpu-monitor/<operation>/whole-gpu-memory.csv`, `columns.json` | GPU utilization, nhiệt độ, công suất, VRAM toàn GPU mỗi 250 ms |
| `gpu-monitor/<operation>/gpu-monitor.stderr.txt` | Lỗi công cụ monitor nếu có; CSV dùng cùng tên legacy nhưng có đủ cột |
| `trainer-arguments-<operation>.json` | Tham số Trainer từng lần chạy/resume |
| `checkpoints/**/checkpoint-*` | Adapter + optimizer/scheduler/RNG/Trainer state/exposure và hash |
| `validation-step-52/`, `validation-step-104/` | Request, output raw/parsed, metrics và các lỗi trong mẫu số |
| `checkpoint-selection.json` | Điểm validation và lý do chọn checkpoint |
| `training-summary.json`, `training-invocations.jsonl` | Chi phí lần gọi và checkpoint dùng khi resume |
| `reload-verification.json` | Đối chiếu tensor adapter đã lưu/nạp |

Không sửa/xóa log, checkpoint hoặc pointer để chạy lại. M0/M1 cũng có manifest và metric validation; M1 có GPU monitor. Peak CUDA đo riêng process khác với VRAM toàn GPU trên `nvidia-smi`.

## Tiếp tục một run bị gián đoạn

Thay run ID bằng ID thật đã in, bỏ dấu `< >`:

```powershell
.\scripts\train.ps1 M2 -Resume <learning-m2-RUN_ID>
.\scripts\train.ps1 M5 -Resume <learning-m5-RUN_ID>
.\scripts\train.ps1 M1 -Resume <learning-m1-RUN_ID>
```

M2/M5 cần checkpoint hoàn chỉnh đã có hash; checkpoint thường đầu tiên ở step 20. Nếu dừng trước đó hoặc đang ghi dở checkpoint, code giữ artifact và từ chối khôi phục thiếu trạng thái. Không tự khởi tạo lại để giả là tiếp tục. Resume yêu cầu cùng dataset/base/context/seed/code/study. Sau khi đổi code, cần xem lại provenance trước khi tiếp tục.

Resume dùng checkpoint hoàn chỉnh mới nhất, giữ lịch sử và lưu checkpoint mới vào thư mục con khác. Phần sau checkpoint có thể phải tính lại; exposure đã commit và log phần bị bỏ được phân biệt. Validation đã hoàn tất không bị gọi lại; request suy luận đã thất bại/mất kết quả tính là lỗi và không gọi lại ngầm. M0 bị gián đoạn không tự fit lại. Lệnh cho model đã hoàn tất trả về artifact cũ, không tự chạy thêm.

Nếu đóng cưỡng bức máy/process, khoảng không rõ thời điểm dừng có thể bị tính vào cap cho tới khi được ghi nhận; nên dùng `Ctrl+C` và đợi log dừng. Không xóa `.cache/manual-learning-v1.1.json` để reset cap. `.cache/active-experiment.json` của vòng thu thập cũ được giữ nguyên.

## Final test riêng sau cùng

Chỉ dùng khi M0/M1 đã `validation_finished`, M2/M5 đã `training_finished` và adapter reload đạt. Ghi lại bốn run ID thật, không dùng ID smoke:

```powershell
.\.cache\ml-v1\Scripts\python.exe -m ci_demo.sft --manual --test-runs <M0_RUN_ID> <M1_RUN_ID> <M2_RUN_ID> <M5_RUN_ID>
```

Lệnh khóa chung cấu hình/checkpoint rồi mới chấm 38 real test. Test không tự chạy khi SFT xong. Không dùng kết quả test để sửa retrieval, nhãn, filter hay chọn adapter. Nếu final test bị gián đoạn/lỗi, dừng và đọc artifact; không tự gọi lại thành một lần test mới.
