# Protocol v1.2 — tiếp tục checkpoint 104 đến tổng 10 epoch

Người dùng đã duyệt continuation, thay đề xuất train lại adapter. Chỉ chuẩn bị code; người dùng tự chạy. Cấu hình ghim tại [training-v1.2.json](../data-manifests/training-v1.2.json); dataset vẫn là lock v1.1, silver, không đổi nhãn/input/split. [Kết quả pilot](results.md) giữ nguyên.

| Model | Parent run | Bắt đầu | Đích tổng | Updates còn lại | Validation mới |
|---|---|---:|---:|---:|---|
| M2 | learning-m2-20261112T135209594691Z | 104 / 4,7314 epoch | 220 / 10 epoch | 116 | 132, 176, 220 (epoch 6/8/10) |
| M5 | learning-m5-20261112T170153056333Z | 104 / 2,9855 epoch | 350 / 10 epoch | 246 | 210, 280, 350 (epoch 6/8/10) |

M2 dùng175real; M5 dùng175real+101synthetic, cùng37validation/38test. Base3Brevision, LoRAr16/alpha32/dropout.05/all-linear, NF4/BF16, batch1/accum8, seed5417, context2048/output384 không đổi. Chỉ LR/scheduler của phần tiếp tục thay đổi: LR bắt đầu2e-5, không warmup, sau k updates mới là `2e-5 * max(0, 1-k/N)` với N116/246. Đây không phải run10epoch được lên lịch từ đầu.

## Khôi phục và bất biến

Study mới chỉ được tạo khi người dùng gọi lệnh model, có pointer riêng `.cache/manual-learning-v1.2.json`. Không sửa parent hoặc pointer/ngân sách v1.0/v1.1. Parent manifest, config, dữ liệu đã chuẩn bị, thứ tự sample IDs, metrics và checkpoint52/104 được ghim hash. Adapter/optimizer/scheduler/RNG/Trainer/exposure phải đủ và khớp trước khi chạy.

Bootstrap nạp adapter và toàn bộ trạng thái104; thay riêng scheduler và LR, giữ optimizer moments. Child resume khôi phục scheduler hiện hành, không reset. Data skip lấy global step và thứ tự shuffle seedable theo epoch, tránh wrapper skip của Accelerate đặt lại iteration. Prefix exposure của parent phải khớp sampler5417 trước khi chấp nhận; fixture CPU kiểm tra cả M5 chỉ còn4mẫu ở epoch3. Kết thúc phải có mỗi mẫu10 committed exposures:1750/2760. Phần tính lại sau checkpoint vẫn được giữ trong event logs, không tính thành exposure mới đã commit.

Checkpoint mới lưu mỗi epoch nguyên tiếp theo, không prune. Khi resume, thư mục checkpoint mới tách riêng; thiếu checkpoint con hoàn chỉnh thì từ chối thay vì tự bootstrap lại. Chống chạy trùng bằng model lock; cùng lệnh đã hoàn tất trả artifact cũ. Khác code/config/model/data/study thì không resume ngầm.

## Ngân sách và đánh giá

Cap mỗi model10800s cộng dồn, gồm load/save/reload/validation; evaluation7200s,1500requests chẩn đoán,0generator,20GiBtrống. Không deadline lịch. Khoảng mất dấu sau force-kill có thể bị tính cho đến lúc ghi nhận. Các cổng chạy ở ranh giới operation/update, không cưỡng bức ngắt CUDA kernel. Không reset pointer để gia hạn. Cost lineage báo cả thời gian parent và các interval child, nested validation chỉ tính một lần.

Không early stopping. Kế thừa validation52/104 đã ghim, không gọi lại. Chọn joint class/functionTop1 tốt nhất trong checkpoint cũ/mới; hòa chọn globalstep sớm hơn. Báo riêng điểm epoch10 và checkpoint được chọn. Nếu checkpoint parent thắng, giữ nó làm ứng viên hợp lệ qua lineage/hash; không giả là adapter đã học đủ10epoch. M0/M1 reuse run đã ghim, parser/scorer/retrieval giữ nguyên, bao gồm lỗi format M1.

Final test vẫn là lệnh riêng sau khi cả hai continuation hoàn tất. Lock kiểm tra v1.2 chung, dataset/base/prompt/batch/seed, lineage và đích220/350, không đòi updates bằng nhau. Không ghép một continuation với một pilot cũ hoặc checkpoint ngoài lineage. Không mở test trong setup, không tự tải model/gọi Docker/sinh lại dữ liệu.

Lệnh chạy/resume và giới hạn runtime chưa đo: [runbook](training-runbook.md#tiếp-tục-m2m5-đến-tổng-10-epoch).
