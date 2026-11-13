# Kết quả kỹ thuật evaluation v1

Run `evaluation-20261112T210848574175Z`; chấm một lần trên **38 real test**, nhãn silver. [Protocol](evaluation-protocol-v1.md), [validation](evaluation-validation.md), [manifest](../data-manifests/evaluation-v1.json).

Hoàn tất lúc 04:35:01 +07 ngày 13/11/2026. [Phân tích lỗi và synthetic](evaluation-error-analysis.md), [đối chiếu khóa/request/hash](evidence/dataset-v1-progress/evaluation-integrity-20261113.json), [kiểm thử phần mềm: 131 pass, 1 skip](evidence/dataset-v1-progress/software-tests-evaluation-final-v1.txt). Cùng một phiên đã resume sau ba lần GPU preflight bận; toàn bộ 151 request đều finished, không gọi trùng hoặc đổi cấu hình.

**M1-P2 dùng prompt mới**; M2/M5 dùng prompt cũ và checkpoint104 đã chọn. User code/log, base3B và giới hạn suy luận giữ nguyên. M0 là classifier. Parser strict, không bỏ Markdown hoặc sửa response.

## Test — bảng chính

| Model | Accuracy | Macro-F1 | File Top-1 / Top-5 | Hàm Top-1 / Top-5 | Joint | Invalid / unknown |
|---|---:|---:|---:|---:|---:|---:|
| M0 | 23.68% | 0.1106 | — / — | — / — | — | — / — |
| M1-P2 | 42.11% | 0.2549 | 15.79% / 21.05% | 5.26% / 7.89% | 2.63% | 8 / 0 |
| M2 | 57.89% | 0.3132 | 47.37% / 47.37% | 15.79% / 15.79% | 10.53% | 0 / 0 |
| M5 | 63.16% | 0.3375 | 42.11% / 42.11% | 18.42% / 18.42% | 10.53% | 0 / 0 |

Dấu — của M0 là không áp dụng. Invalid/missing/unknown vẫn nằm trong mẫu số38. Macro-F1 lấy trung bình bốn lớp cố định, gồm lớp support0.

## Support và confusion

| Nhãn silver | Support test |
|---|---:|
| API/type | 9 |
| logic/value | 21 |
| dependency/configuration | 8 |

Dự đoán luôn lớp phổ biến nhất đạt 21/38 = 55.26% accuracy; cần đọc Macro-F1 và từng lớp thay vì chỉ accuracy.

### M0

| Nhãn thật | syntax | dependency/configuration | API/type | logic/value | unknown | invalid |
|---|---:|---:|---:|---:|---:|---:|
| syntax | 0 | 0 | 0 | 0 | 0 | 0 |
| dependency/configuration | 0 | 0 | 8 | 0 | 0 | 0 |
| API/type | 0 | 0 | 8 | 1 | 0 | 0 |
| logic/value | 0 | 0 | 20 | 1 | 0 | 0 |

| Lớp | Support | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| syntax | 0 | 0.0000 | 0.0000 | 0.0000 |
| dependency/configuration | 8 | 0.0000 | 0.0000 | 0.0000 |
| API/type | 9 | 0.2222 | 0.8889 | 0.3556 |
| logic/value | 21 | 0.5000 | 0.0476 | 0.0870 |

### M1-P2

| Nhãn thật | syntax | dependency/configuration | API/type | logic/value | unknown | invalid |
|---|---:|---:|---:|---:|---:|---:|
| syntax | 0 | 0 | 0 | 0 | 0 | 0 |
| dependency/configuration | 0 | 0 | 0 | 6 | 0 | 2 |
| API/type | 1 | 0 | 3 | 4 | 0 | 1 |
| logic/value | 1 | 0 | 2 | 13 | 0 | 5 |

| Lớp | Support | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| syntax | 0 | 0.0000 | 0.0000 | 0.0000 |
| dependency/configuration | 8 | 0.0000 | 0.0000 | 0.0000 |
| API/type | 9 | 0.6000 | 0.3333 | 0.4286 |
| logic/value | 21 | 0.5652 | 0.6190 | 0.5909 |

### M2

| Nhãn thật | syntax | dependency/configuration | API/type | logic/value | unknown | invalid |
|---|---:|---:|---:|---:|---:|---:|
| syntax | 0 | 0 | 0 | 0 | 0 | 0 |
| dependency/configuration | 0 | 0 | 4 | 4 | 0 | 0 |
| API/type | 0 | 0 | 7 | 2 | 0 | 0 |
| logic/value | 0 | 0 | 6 | 15 | 0 | 0 |

| Lớp | Support | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| syntax | 0 | 0.0000 | 0.0000 | 0.0000 |
| dependency/configuration | 8 | 0.0000 | 0.0000 | 0.0000 |
| API/type | 9 | 0.4118 | 0.7778 | 0.5385 |
| logic/value | 21 | 0.7143 | 0.7143 | 0.7143 |

### M5

| Nhãn thật | syntax | dependency/configuration | API/type | logic/value | unknown | invalid |
|---|---:|---:|---:|---:|---:|---:|
| syntax | 0 | 0 | 0 | 0 | 0 | 0 |
| dependency/configuration | 0 | 0 | 2 | 6 | 0 | 0 |
| API/type | 0 | 0 | 6 | 3 | 0 | 0 |
| logic/value | 0 | 0 | 3 | 18 | 0 | 0 |

| Lớp | Support | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| syntax | 0 | 0.0000 | 0.0000 | 0.0000 |
| dependency/configuration | 8 | 0.0000 | 0.0000 | 0.0000 |
| API/type | 9 | 0.5455 | 0.6667 | 0.6000 |
| logic/value | 21 | 0.6667 | 0.8571 | 0.7500 |

## So sánh cặp M2/M5 trên cùng từng mẫu

| Tiêu chí | Cả hai đúng | Chỉ M2 đúng | Chỉ M5 đúng | Cả hai sai |
|---|---:|---:|---:|---:|
| classification_correct | 20 | 2 | 4 | 12 |
| function_top1_correct | 5 | 1 | 2 | 30 |
| joint_top1_correct | 3 | 1 | 1 | 33 |

Các số là quan sát trên38mẫu thuộc3repo; không tuyên bố khác biệt có ý nghĩa thống kê hoặc synthetic có lợi tổng quát.

## Theo repo

| Repo | Model | Accuracy | Macro-F1 | Hàm Top-1 | Joint |
|---|---|---:|---:|---:|---:|
| flask | M0 | 66.67% | 0.2000 | — | — |
| flask | M1-P2 | 33.33% | 0.1667 | 0.00% | 0.00% |
| flask | M2 | 66.67% | 0.2000 | 33.33% | 33.33% |
| flask | M5 | 66.67% | 0.2000 | 33.33% | 33.33% |
| pylint | M0 | 10.53% | 0.0476 | — | — |
| pylint | M1-P2 | 36.84% | 0.1591 | 5.26% | 5.26% |
| pylint | M2 | 52.63% | 0.2512 | 5.26% | 0.00% |
| pylint | M5 | 63.16% | 0.3037 | 15.79% | 5.26% |
| pytest | M0 | 31.25% | 0.1507 | — | — |
| pytest | M1-P2 | 50.00% | 0.2750 | 6.25% | 0.00% |
| pytest | M2 | 62.50% | 0.3333 | 25.00% | 18.75% |
| pytest | M5 | 62.50% | 0.3250 | 18.75% | 12.50% |

## Phân nhóm lỗi (các nhóm có thể chồng nhau)

| Nhóm | M1-P2 | M2 | M5 |
|---|---:|---:|---:|
| classification_disagreement_with_silver | 14 | 16 | 14 |
| format_or_schema_failure | 8 | 0 | 0 |
| localization_mismatch_with_visible_reference | 6 | 6 | 5 |
| reference_function_absent_from_retrieved_context | 26 | 26 | 26 |
| reference_match_not_counted_due_to_visibility_gate | 0 | 3 | 3 |

Reference function có trong retrieved code: **12/38**; reference file: **21/38**. Scorer hiện chặn credit định vị nếu reference không nằm trong retrieved context. `reference_match_not_counted_due_to_visibility_gate` là chẩn đoán về giới hạn scorer, không phải bảng điểm mới.

Lỗi phân loại/định vị là bất đồng với **silver reference**, không tự động chứng minh model sai hoặc reference đúng tuyệt đối. Nhãn/lựa chọn khác được ghi pending, không sửa sau khi thấy test. Các giới hạn taxonomy đã được ghi trong assessment trước đánh giá.

## Chi phí thực đo

| Nguồn | Wall run nguồn/child (s) | Parent + continuation (s) | Lượt mẫu train tích lũy | Input / target tokens train tích lũy |
|---|---:|---:|---:|---:|
| M0 | 16.00 | — | — | — / — |
| M1 | 363.00 | — | — | — / — |
| M2 | 2170.00 | 4387.0 | 1750 | 2621890 / 151830 |
| M5 | 4218.00 | 6324.0 | 2760 | 4149110 / 221320 |

| Phase mới | Response đã lưu | Giây inference | Giây phase gồm load | Input / output tokens | Peak CUDA allocated / reserved (GiB) |
|---|---:|---:|---:|---:|---:|
| test-M0 | 0 | 0.00 | — | 0 / 0 | — |
| test-M1-P2 | 38 | 375.77 | 383.0620 | 55958 / 6193 | 2.425 / 3.014 |
| test-M2 | 38 | 315.37 | 321.4380 | 56186 / 2988 | 2.537 / 3.160 |
| test-M5 | 38 | 275.80 | 281.8440 | 56186 / 2734 | 2.537 / 3.160 |
| validation-M1-P2 | 37 | 372.75 | 380.9380 | 52817 / 6100 | 2.426 / 3.014 |

M1 nguồn là lượt validation prompt cũ; M1-P2 validation/test mới tách riêng. M2 parent 2.217s + child 2.170s = 4.387s; M5 parent 2.106s + child 4.218s = 6.324s. Exposure/token là tổng tích lũy đến epoch10, không chỉ phần học thêm. Parent+continuation đã loại việc cộng trùng validation lồng nhau. Giây inference không gồm load; phase gồm load và overhead. CUDA reserved khác VRAM vật lý; số đo monitor toàn GPU nằm trong run. Không bịa chi phí tiền hoặc thời gian chưa đo.

Evaluation dùng 1.445/7.200 giây theo hợp các operation đã reserve, gồm ba lần dừng vì GPU bận trước lời gọi kế tiếp. Có đúng 37 validation + 114 test request mới, tất cả finished; role inference của study v1.2 hiện là 373/1.500, generator 0. Không reset ngân sách. M0 chấm 38 bản ghi bằng classifier đã fit, không phát request 3B. Xem receipt để phân biệt thời gian phase/inference và thời gian tính ngân sách.

## Case index và bằng chứng

| Case | Silver | M2 loại/hàm/joint | M5 loại/hàm/joint | Reference hàm trong context | Raw evidence |
|---|---|---|---|---|
| pallets__flask-4160 | API/type | 1/1/1 | 1/1/1 | có | [log](../runs/reproduce-20261111T233102382247Z/historical-base.stdout.txt) |
| pallets__flask-4575 | logic/value | 0/0/0 | 0/0/0 | không | [log](../runs/reproduce-20261112T000956887994Z/historical-base.stdout.txt) |
| pallets__flask-5014 | API/type | 1/0/0 | 1/0/0 | không | [log](../runs/reproduce-20261111T210940635480Z/historical-base.stdout.txt) |
| pylint-dev__pylint-4175 | logic/value | 0/0/0 | 1/0/0 | có | [log](../runs/reproduce-20261111T200516893096Z/historical-base.stdout.txt) |
| pylint-dev__pylint-4492 | dependency/configuration | 0/0/0 | 0/1/0 | có | [log](../runs/reproduce-20261112T001215506951Z/historical-base.stdout.txt) |
| pylint-dev__pylint-4661 | dependency/configuration | 0/0/0 | 0/0/0 | không | [log](../runs/reproduce-20261111T233558145128Z/historical-base.stdout.txt) |
| pylint-dev__pylint-4669 | logic/value | 1/0/0 | 1/0/0 | không | [log](../runs/reproduce-20261111T201848395177Z/historical-base.stdout.txt) |
| pylint-dev__pylint-4703 | logic/value | 1/0/0 | 1/0/0 | không | [log](../runs/reproduce-20261111T205904315602Z/historical-base.stdout.txt) |
| pylint-dev__pylint-4812 | dependency/configuration | 0/1/0 | 0/1/0 | có | [log](../runs/reproduce-20261111T202555799166Z/historical-base.stdout.txt) |
| pylint-dev__pylint-4858 | logic/value | 1/0/0 | 1/0/0 | không | [log](../runs/reproduce-20261111T205219658892Z/historical-base.stdout.txt) |
| pylint-dev__pylint-4970 | logic/value | 1/0/0 | 1/0/0 | không | [log](../runs/reproduce-20261111T195629737828Z/historical-base.stdout.txt) |
| pylint-dev__pylint-5201 | dependency/configuration | 0/0/0 | 0/0/0 | không | [log](../runs/reproduce-20261112T001525385741Z/historical-base.stdout.txt) |
| pylint-dev__pylint-5743 | API/type | 1/0/0 | 0/0/0 | có | [log](../runs/reproduce-20261111T210040921504Z/historical-base.stdout.txt) |
| pylint-dev__pylint-5859 | logic/value | 1/0/0 | 1/0/0 | không | [log](../runs/reproduce-20261111T202109567559Z/historical-base.stdout.txt) |
| pylint-dev__pylint-6059 | logic/value | 1/0/0 | 1/0/0 | không | [log](../runs/reproduce-20261111T203516841649Z/historical-base.stdout.txt) |
| pylint-dev__pylint-6357 | logic/value | 1/0/0 | 1/0/0 | có | [log](../runs/reproduce-20261111T234743009042Z/historical-base.stdout.txt) |
| pylint-dev__pylint-6358 | dependency/configuration | 0/0/0 | 0/0/0 | không | [log](../runs/reproduce-20261111T234921954503Z/historical-base.stdout.txt) |
| pylint-dev__pylint-6386 | dependency/configuration | 0/0/0 | 0/0/0 | không | [log](../runs/reproduce-20261112T001300157930Z/historical-base.stdout.txt) |
| pylint-dev__pylint-6506 | logic/value | 0/0/0 | 1/0/0 | có | [log](../runs/reproduce-20261111T203023469360Z/historical-base.stdout.txt) |
| pylint-dev__pylint-6517 | logic/value | 1/0/0 | 1/0/0 | không | [log](../runs/reproduce-20261111T200549532331Z/historical-base.stdout.txt) |
| pylint-dev__pylint-7228 | API/type | 0/0/0 | 1/0/0 | không | [log](../runs/reproduce-20261111T204917830266Z/historical-base.stdout.txt) |
| pylint-dev__pylint-7993 | logic/value | 1/0/0 | 1/1/1 | có | [log](../runs/reproduce-20261111T201220091415Z/historical-base.stdout.txt) |
| pytest-dev__pytest-10081 | logic/value | 1/0/0 | 1/0/0 | không | [log](../runs/reproduce-20261112T012724615509Z/historical-base.stdout.txt) |
| pytest-dev__pytest-10343 | logic/value | 1/1/1 | 1/1/1 | có | [log](../runs/reproduce-20261112T012855605698Z/historical-base.stdout.txt) |
| pytest-dev__pytest-10552 | API/type | 0/0/0 | 0/0/0 | không | [log](../runs/reproduce-20261112T012429852145Z/historical-base.stdout.txt) |
| pytest-dev__pytest-10624 | logic/value | 1/0/0 | 1/0/0 | không | [log](../runs/reproduce-20261112T012843354590Z/historical-base.stdout.txt) |
| pytest-dev__pytest-7499 | logic/value | 1/1/1 | 1/0/0 | có | [log](../runs/reproduce-20261112T012540779445Z/historical-base.stdout.txt) |
| pytest-dev__pytest-7500 | logic/value | 0/0/0 | 1/0/0 | không | [log](../runs/reproduce-20261112T012701089566Z/historical-base.stdout.txt) |
| pytest-dev__pytest-7535 | logic/value | 1/0/0 | 1/0/0 | không | [log](../runs/reproduce-20261112T012517280171Z/historical-base.stdout.txt) |
| pytest-dev__pytest-7673 | logic/value | 0/0/0 | 0/0/0 | không | [log](../runs/reproduce-20261112T012406242509Z/historical-base.stdout.txt) |
| pytest-dev__pytest-7749 | logic/value | 0/0/0 | 0/0/0 | không | [log](../runs/reproduce-20261112T012907376461Z/historical-base.stdout.txt) |
| pytest-dev__pytest-7982 | logic/value | 1/0/0 | 1/0/0 | không | [log](../runs/reproduce-20261112T010016777213Z/historical-base.stdout.txt) |
| pytest-dev__pytest-8250 | API/type | 1/1/1 | 1/1/1 | có | [log](../runs/reproduce-20261112T012646787229Z/historical-base.stdout.txt) |
| pytest-dev__pytest-8365 | dependency/configuration | 0/1/0 | 0/1/0 | có | [log](../runs/reproduce-20261112T012609540984Z/historical-base.stdout.txt) |
| pytest-dev__pytest-8422 | API/type | 1/0/0 | 1/0/0 | không | [log](../runs/reproduce-20261112T012306727341Z/historical-base.stdout.txt) |
| pytest-dev__pytest-9064 | dependency/configuration | 0/0/0 | 0/0/0 | không | [log](../runs/reproduce-20261112T012633764425Z/historical-base.stdout.txt) |
| pytest-dev__pytest-9279 | API/type | 1/0/0 | 0/0/0 | không | [log](../runs/reproduce-20261112T012447797294Z/historical-base.stdout.txt) |
| pytest-dev__pytest-9359 | API/type | 1/0/0 | 1/0/0 | không | [log](../runs/reproduce-20261112T012712195207Z/historical-base.stdout.txt) |

Chi tiết38mẫu, prediction và source/patch/hash audit nằm trong [analysis.json](../runs/evaluation-20261112T210848574175Z/analysis/analysis.json). Source chỉ đọc bằng text/AST, không thực thi; hash log/manifest/patch/source của cả38mẫu khớp. Các log là tái hiện local, không phải telemetry CI lịch sử. [Phân tích lỗi](evaluation-error-analysis.md) giải thích tám chuỗi code→hành vi→log, gồm cả ba trường hợp M2/M5 bất đồng điểm định vị hàm. Raw runs/cache chỉ có ở worktree đã chuẩn bị, không đi theo Git clone.

## Giới hạn kết luận

- Một seed, dữ liệu nhỏ và ba repo test; train tập trung vào SymPy, thiếu support syntax/dependency-config.
- M1-P2 khác prompt M2/M5. M0 không định vị; không coi dấu — là điểm0.
- Cả hai continuation đủ10epoch nhưng chọn parent104, tương ứng4,73epoch(M2)/2,99epoch(M5). Chỉ các adapter đã chọn được chấm test; không chấm thêm epoch10 hoặc tăng epoch từ test.
- Nhãn silver chưa được xác nhận thành gold. Không xác định người/AI gây lỗi từ các điểm này.
- Không làm slide hoặc báo cáo bảo vệ giữa kỳ trong đợt này.
