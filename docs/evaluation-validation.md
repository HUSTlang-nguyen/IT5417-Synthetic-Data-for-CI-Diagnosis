# Validation đã chốt — evaluation v1

Cùng37realvalidation, nhãn silver, strictJSON. M1-P2 dùng **prompt mới**; M2/M5 dùng prompt cũ. Không train lại hoặc chọn checkpoint theo M1-P2. [Protocol](evaluation-protocol-v1.md), [evidence](evidence/dataset-v1-progress/evaluation-validation-20261113.json).

| Model | Accuracy | Macro-F1 | File Top-1/5 | Hàm Top-1/5 | Joint Top-1 | Invalid / unknown |
|---|---:|---:|---:|---:|---:|---:|
| M0 | 16.22% | 0.0835 | —/— | —/— | — | — / — |
| M1-P2 | 78.38% | 0.3642 | 24.32%/29.73% | 16.22%/16.22% | 10.81% | 1 / 1 |
| M2 | 75.68% | 0.3515 | 24.32%/24.32% | 13.51%/13.51% | 10.81% | 0 / 0 |
| M5 | 81.08% | 0.4060 | 24.32%/24.32% | 13.51%/13.51% | 13.51% | 1 / 0 |

M0 chỉ phân loại; dấu — là không áp dụng. M1cũ vẫn0/37theo strictparser vì37response bắt đầu bằngMarkdownfence; cả37cóJSONđọc được bên trong, chưa thay đổi điểm cũ. M1-P2 đã có36/37output hợp lệ theo schema,1invalid và1unknown; không thử thêm prompt sau kết quả này.

Macro-F1 lấy trung bình bốn lớp cố định, gồm syntax cósupport0. Validation chỉ cóSphinx và29/37logic/value; dự đoán luônlogic/value được78,38%accuracy. M1-P2 chỉ cải thiện format không chứng minh mọi suy luận đúng; M2/M5localization còn chịu coverage7/37referencefunctions.

## Support và từng lớp

| Model | Lớp | Support | Precision | Recall | F1 |
|---|---|---:|---:|---:|---:|
| M0 | syntax | 0 | 0.0000 | 0.0000 | 0.0000 |
| M0 | dependency/configuration | 4 | 0.0000 | 0.0000 | 0.0000 |
| M0 | API/type | 4 | 0.1143 | 1.0000 | 0.2051 |
| M0 | logic/value | 29 | 1.0000 | 0.0690 | 0.1290 |
| M1-P2 | syntax | 0 | 0.0000 | 0.0000 | 0.0000 |
| M1-P2 | dependency/configuration | 4 | 0.0000 | 0.0000 | 0.0000 |
| M1-P2 | API/type | 4 | 0.6667 | 0.5000 | 0.5714 |
| M1-P2 | logic/value | 29 | 0.8438 | 0.9310 | 0.8852 |
| M2 | syntax | 0 | 0.0000 | 0.0000 | 0.0000 |
| M2 | dependency/configuration | 4 | 0.0000 | 0.0000 | 0.0000 |
| M2 | API/type | 4 | 0.3636 | 1.0000 | 0.5333 |
| M2 | logic/value | 29 | 0.9231 | 0.8276 | 0.8727 |
| M5 | syntax | 0 | 0.0000 | 0.0000 | 0.0000 |
| M5 | dependency/configuration | 4 | 0.0000 | 0.0000 | 0.0000 |
| M5 | API/type | 4 | 0.5714 | 1.0000 | 0.7273 |
| M5 | logic/value | 29 | 0.8966 | 0.8966 | 0.8966 |

Confusion matrices và toàn bộsupport/metrics nằm trongevidenceJSON; rawresponses vẫn ởrunlocal.

## Checkpoint được chọn và epoch10

| Model | Điểm checkpoint104 (F1 / joint) | Điểm epoch10 (F1 / joint) | Chọn |
|---|---|---|---|
| M2 | 0,3515 / 4/37 | 0,3226 / 4/37 | Parent104; hòa joint chọn sớm |
| M5 | 0,4060 / 5/37 | 0,3731 / 5/37 | Parent104; hòa joint chọn sớm |

Continuation đã chạy đủ10epoch ở cảhai, nhưng adapter được chọn tương ứng4,73epoch(M2)/2,99epoch(M5). Test chỉ chấm các checkpoint đã chọn, không chấm lại epoch10. Vì vậy phải phân biệt ngân sách đã tiêu với số lượt học của adapter dùng để dự đoán.
