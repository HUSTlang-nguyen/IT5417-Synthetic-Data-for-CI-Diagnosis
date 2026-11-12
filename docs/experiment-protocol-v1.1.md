# Protocol v1.1 — pilot học với dữ liệu đã rà

Ngày chốt: 12/11/2026, Asia/Bangkok. Người dùng yêu cầu chuẩn bị code để tự chạy M0/M1/M2/M5 sau. Việc chốt này cho phép dùng **silver** trong pilot; không xác nhận nhãn thành gold. Chưa có kết quả của bốn model.

## Phạm vi và dữ liệu

Đây là pilot riêng, tiếp nối [đề xuất](training-plan-v1.1-proposal.md). [Protocol v1.0](experiment-protocol.md) và [kết quả vòng thu thập](results.md) giữ nguyên: mục tiêu synthetic 175 còn thiếu 74; goal cũ chưa hoàn tất. Không sinh thêm hoặc gọi lại các operation unknown để chuẩn bị pilot.

Manifest cấu hình: [training-v1.1.json](../data-manifests/training-v1.1.json). Dataset lock local: `.cache/dataset-v1/locked-v1.1.json`, SHA-256 `f3d7869bb77d48b5ea460ec1722a50c0de36e45e81cf8c6d5e40b6368931222b`. Các đường dẫn cache trong lock thuộc worktree đã chuẩn bị; một clone Git khác chưa đủ để train.

| Split | Real silver | Synthetic silver | Repo |
|---|---:|---:|---|
| Train | 175 | 101, chỉ M5 | SymPy, pvlib, astroid, pydicom, marshmallow |
| Validation | 37 | 0 | Sphinx |
| Test | 38 | 0 | Pylint, pytest, Flask |

Train real: 134 `logic/value`, 41 `API/type`; synthetic: 95 và 6 tương ứng. Repo/group không giao split. Lựa chọn 351 kế thừa deep audit 352, loại một semantic duplicate và có group review ràng buộc hash. Họ Vector còn lại được ghi là hai cơ chế khác nhau, tương quan trong train. Không coi mọi mẫu là độc lập.

Input chỉ chứa log thực thi và code liên quan qua retrieval-v2; gold repair patch, reference và assessment tách riêng. Real là tái hiện local, không gọi log local là log CI lịch sử. Mục tiêu JSON gồm loại nguyên nhân, vị trí file/hàm và giải thích ngắn. Phân loại và định vị file/hàm là hai nhiệm vụ chính; chưa học quy lỗi cho người hay AI. Nhãn silver là nhận định có evidence, không phải xác nhận chuyên gia.

## Các đối chứng

| Model | Fit trên | Đánh giá |
|---|---|---|
| M0 TF-IDF + Logistic Regression | 175 real train | Chỉ phân loại |
| M1 3B prompt-only | Không cập nhật trọng số | Phân loại, định vị, JSON hợp lệ |
| M2 3B QLoRA | 175 real train | Như M1 |
| M5 3B QLoRA | 175 real + 101 synthetic train | Như M1 |

M2/M5 khởi tạo adapter **độc lập từ cùng base**, không SFT tiếp adapter của nhau hoặc smoke. Base `Qwen/Qwen2.5-Coder-3B-Instruct`, revision `488639f1ff808d1d3d0ba301aef8c11461451ec5`, local-only, kiểm tra inventory hash trước chạy. Generator 7B không tham gia train/evaluation.

Giữ NF4, LoRA rank 16/alpha 32/dropout 0,05/all-linear, learning rate 1e-4, BF16, batch 1, accumulation 8, seed 5417, context 2048 và output tối đa 384 token. Response-only loss. **104 optimizer updates mỗi SFT**, tính từ `ceil(3 × 276 / 8)`, không phải ba epoch bằng nhau trên hai tập. Lưu số token và lượt thấy từng mẫu thực tế; không tuyên bố FLOPs/token bằng nhau. Không tự hạ context khi OOM.

Checkpoint mỗi 20 updates, thêm 52/104; validation tại 52 và 104. Chọn joint class/function Top-1, hòa chọn step sớm hơn. Lưu optimizer, scheduler, RNG, Trainer state, adapter và exposure cùng hash. Resume chỉ nhận checkpoint hoàn chỉnh, cùng run/model/data/config/code/study; không gọi lại validation đã hoàn tất. Request bị gián đoạn không được gọi lại ngầm và vẫn nằm trong mẫu số lỗi. Các update sau checkpoint có thể phải tính lại; log cũ vẫn giữ.

Smoke tùy chọn dùng ba updates trên real train, không validation/test; trạng thái `calibration_finished`, tách khỏi M2 nghiên cứu và không được dùng thay M2 trong final test. Lần smoke đầu sẽ là phép kiểm tra CUDA/backward/reload thực; setup hiện chỉ kiểm thử bằng backend giả lập.

## Ngân sách cho các lệnh chạy thủ công

Theo yêu cầu chạy lúc người dùng muốn, study mới chỉ được tạo ở **lệnh model đầu tiên**, không có hạn chót theo ngày lịch. Pointer `.cache/manual-learning-v1.1.json` tách khỏi `.cache/active-experiment.json`; thời hạn và cap của vòng thu thập v1.0 không đổi.

Mỗi SFT có cap cộng dồn 7.200 giây, gồm smoke của M2, load/save và validation; evaluation M0/M1/final test có cap chung 7.200 giây. Tối đa 1.500 request chẩn đoán, **0 request sinh**, giữ cổng trống ít nhất 20 GiB. Các interval operation lồng nhau chỉ tính một lần. Pause sau khi dừng có ghi nhận không tính vào active time; khoảng mất dấu của process bị kill có thể bị tính cho tới khi được ghi nhận. Resume không reset cap. Không xóa pointer để tạo lại ngân sách.

Các cổng thời gian chạy trước operation/update; đây không phải watchdog cưỡng bức ngắt một CUDA kernel đang chạy. Nếu hết cap, lỗi hoặc OOM thì dừng và giữ artifact, không tự sửa cấu hình/gia hạn. Thời gian train thực chưa đo; không dùng tốc độ inference trước đó để hứa ETA SFT.

## Báo cáo và giới hạn

Sau bốn run hoàn tất và lựa chọn validation đã khóa mới mở final test một lần bằng lệnh riêng. Không đổi retrieval/filter/taxonomy từ điểm test. Giữ mẫu số cả invalid/missing predictions; báo Macro-F1, từng lớp, file/function Top-k và joint metrics. M0 không có localization score. Không tự mở test sau mỗi lệnh train.

Retrieval hiện chỉ đưa reference function vào code của 59/175 real train, 7/37 validation, 12/38 test và 44/101 synthetic sau tokenization. Đây là hạn chế input, không là trần accuracy cứng vì còn log; không điều chỉnh từ held-out. Train tập trung mạnh vào SymPy (158/175 real, 88/101 synthetic); dữ liệu nhỏ, lệch repo/lớp, silver và chỉ một seed. Kết quả pilot không đủ tuyên bố benchmark tổng quát hoặc tác dụng synthetic khi chưa có đủ đối chứng.

Lệnh, log, GPU và resume: [training runbook](training-runbook.md). [Readiness](evidence/dataset-v1-progress/manual-training-readiness-20261112.json) chỉ chứng minh kiểm tra metadata/hash; không chứng minh đã train.
