# Hướng dẫn nhãn — bản nháp development v0.1

Ngày 30/10/2026. Hoàn thiện công cụ rà của W2-02, chưa phê duyệt taxonomy cuối hoặc nhãn gold của bất kỳ mẫu mới nào. Áp dụng cùng [task contract](task-contract.md).

## Taxonomy tạm thời

| Mô tả đề xuất | Khi có bằng chứng | Không tự suy |
|---|---|---|
| syntax | Python parser báo SyntaxError/IndentationError gắn với code đang xét | Mọi test failure đều là syntax |
| import/dependency/configuration | Thiếu dependency, import không giải quyết được hoặc cấu hình/lệnh gây lỗi | Mọi ImportError đều do môi trường; có thể do code dùng sai API |
| API/type | Dùng sai kiểu, signature, thuộc tính/phương thức gây exception phù hợp code/log | Mọi TypeError đều cùng nguyên nhân hoặc đều là lỗi cú pháp |
| logic/value | Code chạy nhưng hành vi/giá trị không đạt assertion, có chuỗi nguyên nhân được giải thích | Mọi assertion failure đều định vị ngay được dòng gây lỗi |
| other/unknown | Cơ chế ngoài nhóm trên hoặc chưa đủ evidence để phân biệt | Ép mẫu vào một lớp để đủ quota |

Đây là các mô tả làm việc; chưa ánh xạ bắt buộc sang enum dataset huấn luyện. Enum logic/import/syntax/other của generator chỉ là metadata tự khai. Giữ nguyên nhãn nguồn, nhãn generator và mapping đề xuất; không sửa dữ liệu cũ để khớp taxonomy mới.

## Căn cứ và vị trí

1. Đối chiếu repo/commit, source/test/candidate hashes, image identity và artifact thực thi.
2. Nối diff → code/hành vi → log/JUnit. Test assertion/stack trace chỉ ra nơi phát hiện; xác định riêng file/hàm/dòng nguyên nhân theo đúng phiên bản candidate.
3. Ghi rõ điều đã chứng minh và suy luận. Độ chắc chắn cao cần nhiều bằng chứng phù hợp; không gán phần trăm tùy ý. Nếu chỉ thu hẹp được file/hàm thì giữ mức đó.
4. Với SWE-bench, reference repair patch giúp điều tra/chấm; vùng sửa không tự thành toàn bộ gold causal lines. FAIL_TO_PASS/PASS_TO_PASS là kỳ vọng từ nguồn; kết quả local phải được đọc riêng.
5. Với AIDev, không suy actor gây lỗi từ nhãn agent ở mức PR. Ghi khác biệt giữa upstream test tại base/head và test harness cố định đã dùng cho reconstruction.

## Chất lượng và lộ đáp án

Đánh giá riêng execution acceptance, tuân thủ prompt, tính hợp lý, chất lượng nhãn và mục đích sử dụng. Comment do generator nói rõ ý đồ có thể vi phạm prompt; rủi ro leakage phụ thuộc input chẩn đoán thực tế. Stack trace/số dòng trong log được phép là evidence. Không lọc bằng từ khóa bug/regression đơn thuần.

Nếu input chứa code với comment chỉ ý đồ thì ghi thông tin gợi ý cụ thể; không tự xóa comment khỏi raw. Nếu chưa đóng gói input, nêu rủi ro có điều kiện. Nhãn/explanation/gold patch nằm ngoài input theo task contract.

## Agent chuẩn bị, người dùng review

Mỗi mẫu có: kết luận ngắn; bằng chứng và liên kết; giải thích nguyên nhân/độ chắc chắn; kiến nghị sử dụng; quyết định còn cần người dùng. Agent thực hiện phân tích kỹ thuật bằng `$ci-data-review`, không yêu cầu người dùng tự dò lại toàn bộ code/log.

Các raw review stub giữ pending. Bản phân tích là artifact phái sinh có dẫn nguồn; không sửa raw output/log/test. Đồng ý tiếp tục hoặc đồng ý giữ/loại không tự phê duyệt taxonomy, mọi dòng nguyên nhân hay training. Chỉ ghi tên/ngày/phạm vi xác nhận có bằng chứng trực tiếp; không lấy danh tính từ Git/OS.
