# Evaluation v1 — M1-P2, selected checkpoints and one final test

Được người dùng giao thực hiện13/11/2026: chốt validation, chạy finaltest và phân tích lỗi/chi phí; chưa làm slide hoặc báo cáo bảo vệ giữa kỳ. Đây là quyền suy luận đánh giá riêng, không cho phép train thêm/generate/Docker/push. [Manifest khóa](../data-manifests/evaluation-v1.json) ghi dataset/model/prompt/code hashes và cohort37/38.

## Điều kiện cố định

- M0 classifier đã fit; M1-P2 là cùng base3B prompt-only với prompt mới; M2/M5 là checkpoint104 được chọn từ lịch sử continuation đã hoàn tất10epoch. Không chọn lại theo M1-P2 hoặc test, không chấm test cho epoch10.
- Prompt M1-P2 thay đúng hai đoạn đã duyệt (173→167systemtokens). Khôi phục usermessage với thuật toán cũ, kiểm tra toàn bộ prepared data/hash khớp M1 cũ trước khi thay systemmessage. Không thêmcode/log nhờ6token tiết kiệm. M2/M5 giữprompt cũ; báo chú thích **M1-P2: prompt mới**.
- Seed5417, localNF4double/BF16, context2048/output384, greedy và parserstrictJSON giữ nguyên. Không bỏ Markdown, sửa output hay reference. M1 cũ 37/37JSON nằm trong fence nhưng strictparse thất bại; giữ nguyên điểm0 trong lịch sử, không diễn giải thành mọi chẩn đoán sai.
- Cùng37realvalidation và38realtest đã khóa, nhãn silver; M0 chỉ phân loại. Metricgốc: Macro-F1 cố định4lớp (kể cả lớp support0), confusion/support/perclass, accuracy, file/functionTop1/5, joint, invalid/unknown. Localization tiếp tục yêu cầu reference có trong retrievedcontext; báo coverage riêng.

## Thứ tự và bảo toàn

Softwaretests trước; một lượtM1-P2validation37, không tối ưu prompt qua nhiều lần. Sau đó kiểm traGPU rảnh (ít nhất6GiBtrống,util≤10%), model/hash/lineage và ổ đĩa20GiB; khóa danh tính38mẫu, usermessagehashes, prompt từngmodel, parser và checkpoint trước testinference. Test thứ tựM0→M1-P2→M2→M5, tối đa114request3B. Tổnglượt mới≤151, dùng budgetevaluation7200s/request1500 của studyv1.2 hiện hành, không reset.

Entrypoint: `python -m ci_demo.evaluation --manifest data-manifests/evaluation-v1.json`; explicitresume bằng `--resume EVALUATION_RUN_ID`. Globalmodellock và pointerevaluation-v1 chặn trial trùng. Study final-config-lock dùng chung với legacytestpath để không vô tình mở trial thứhai.

Request được reserve trước khi gọi. Resume tái sử dụng phase đã xong và response có hash; failed/unknown request không gọi lại, vẫn tính lỗi trong mẫu số. Chỉ gọi các mẫu chưa thử, giữ nguyên run/lock/input. Ctrl+C/lỗi lưu trạng thái và đóng masteroperation; forcekill khoảngmấtdấu có thể bị tính vào cap. Testlock không đổi sau khi đã có prediction; hết cap hoặc bất biến sai thì dừng/báo phần thiếu, không tự tạo trial mới. Các cổng thời gian ở ranh giớioperation, không cưỡng bứcngắtCUDAkernel.

## Đầu ra và giới hạn

Request/raw/parsed/timing/token/CUDAmemory/GPUCSV riêng trong run mới. Điểmvalidation M0/M2/M5 reuse với hash; bảng chínhM0/M1-P2/M2/M5 và lịch sửM1cũ, táchbestcheckpoint/epoch10. Testbảng38mẫu, support/lỗiđịnhdạng và win/loss M5/M2 theo từngmẫu, từngrepo; không loại invalid/missing hoặc dùng testđể sửa pipeline.

Phân tích kỹ thuật đọc code/diff/log/assessment đã lưu, phân biệt quan sát với nhận định; nhãnnghi ngờ giữpending. Không tự sửa silver→gold. Chi phí gồmparent+continuation, M1cũ+M1-P2, validation/test; không cộngtrùng nestedoperation. PeakCUDAallocated/reserved khácVRAMtoànGPU, không gọireserved làdunglượngphysical. Mộtseed/38mẫu/3repo và prompt khác nhau hạn chế kếtluận; không tuyên bố lợiíchsynthetic chắcchắn hoặc quy mọi khác biệtSFT cho kiến thứcchẩnđoán.
