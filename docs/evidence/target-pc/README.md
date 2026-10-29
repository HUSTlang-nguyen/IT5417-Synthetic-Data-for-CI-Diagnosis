# Bằng chứng trên PC RTX 4070 SUPER

Ngày 29/10/2026, Asia/Bangkok. Đây là lượt chạy PC riêng, không thay thế evidence laptop trước đó.

- [Tổng kết từ manifest thật](validation-summary.json): Python host 3.11.9, Docker Linux, Ollama 0.40.13, GPU được xác nhận. Snapshot bộ nhớ trong doctor không phải peak VRAM khi chạy model.
- [Tái hiện properr](historical/report.html): base exit 1 do thiếu pytest; head exit 0, hai test pass. Đây là tái dựng local, không phải log GitHub CI lịch sử.
- [22 kiểm thử phần mềm pass](software-tests-final.txt), gồm fixture Docker thật. [Log 21 test trước đó](software-tests.txt) được giữ riêng. Fixture không phải output LLM.

| Model | Đạt kiểm chứng thực thi / số lượt | Kết quả khác | Tổng giây gọi sinh đã đo |
|---|---:|---|---:|
| qwen2.5-coder:7b-instruct | 2/3 | Một ứng viên không làm test fail | 49.374 |
| qwen2.5-coder:1.5b-instruct | 1/3 | Hai output bị cắt ở 1536 token | 16.078 |

Hai model dùng cùng source, test, prompt, options và image ID; ba seed 5417/5418/5419. Sáu lượt đều được giữ trong mẫu số. Thời gian từng lượt, model digest và nguyên nhân loại nằm trong JSON tổng kết. Các giây trên gồm runtime/model loading, không gồm tải model, Docker verification hay toàn bộ buổi chạy. Lượt đầu 7B có khởi tạo runtime; không suy hiệu năng tổng quát từ ba lượt trên một case.

**Chất lượng còn chờ rà:** output 7B thêm comment tiết lộ lỗi dù prompt cấm; ứng viên 7B số 2 gây TypeError, số 3 sai giá trị số. Ứng viên 1.5B số 3 để dở danh sách `__all__`, gây lỗi syntax khi thu thập test. Các trường hợp này đạt điều kiện thực thi của runner nhưng chưa được duyệt tính hợp lý, taxonomy, vị trí hay sử dụng để train. Không có nhãn gold được tự gán.

Full evidence được giữ tại các thư mục `runs/` bị Git ignore:

- `reproduce-20261029T053446089841Z`.
- `generate-20261029T054921315491Z` (7B).
- `generate-20261029T055021908791Z` (1.5B).
- `comparison-20261029T053856421402Z` (script demo).
- `comparison-20261029T055142213496Z` (dựng lại offline bằng CLI, không gọi lại model).
- `doctor-20261029T055141374481Z` (kiểm tra môi trường cuối).

Bản ZIP `.cache/archives/target-pc-runs-20261029.zip` giữ toàn bộ run hiện có, không chứa weights hoặc clone nguồn. Archive/cache không đi theo Git clone. HTML đã kiểm tra cấu trúc, escaping và liên kết; kiểm tra trực quan vẫn chờ vì browser security policy chặn file cục bộ.
