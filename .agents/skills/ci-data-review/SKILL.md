---
name: ci-data-review
description: "Rà soát mẫu dữ liệu lỗi CI từ code/diff, log và manifest; phân tích nguyên nhân, đề xuất nhãn/vị trí và giải thích evidence để người dùng review. Dùng cho dữ liệu thật hoặc synthetic, không dùng cho ETL chung, chạy sinh dữ liệu hoặc huấn luyện model."
---

# Rà dữ liệu lỗi CI có bằng chứng

Agent đảm nhận phân tích kỹ thuật; người dùng review kết luận, lập luận và các lựa chọn còn quan trọng. Chuẩn bị đủ bằng chứng để người dùng không phải tự lần lại code/log từ đầu.

## Xác định phạm vi trước khi rà

- Đọc hướng dẫn repo, [architecture](../../../docs/architecture.md) và [implementation plan](../../../docs/implementation-plan.md); lấy vai trò model và phạm vi được phép từ cấu hình/tài liệu hiện hành. Tôn trọng quyết định bỏ model hoặc case; không mở rộng sang các artifact ngoài yêu cầu.
- Xác định mã case/run/attempt, repo/commit và nguồn thật/historical hay synthetic. Tách lỗi gốc lịch sử khỏi lỗi mới do generator tạo; metadata actor của PR không chứng minh ai gây lỗi.
- Tìm raw artifacts trong phạm vi người dùng cung cấp và vị trí đã biết. Worktree có thể chỉ có code/docs, không có runs/cache. Nếu thiếu, chỉ rõ file nào thiếu và cần đường dẫn/archive nào; không tái dựng output bằng tay hoặc chạy lại thí nghiệm để lấp chỗ trống.
- Đọc [review-guide](references/review-guide.md) khi đối chiếu artifact, phân tích chất lượng hoặc soạn bản review; dùng tiêu chí và mẫu đầu ra tại đó.

## Phân tích từ evidence hiện có

1. Đối chiếu danh tính nguồn, phiên bản source/tests/candidate và hash nếu manifest có ghi. Đọc diff, log/stdout/stderr, JUnit và trạng thái thực thi theo giao thức đã ghi. Không áp số attempt hoặc điều kiện của một case cho mọi nguồn.
2. Tách bốn lớp: sự kiện quan sát; nhãn/lời giải thích generator tự khai; nhận định và kiến nghị của agent; xác nhận trực tiếp của người dùng. Không dùng nhãn tự khai làm đáp án chuẩn.
3. Nối thay đổi code với giá trị/hành vi, exception hoặc assertion trong log. Phân biệt nơi phát hiện lỗi trong test/stack trace với file/hàm/dòng nguyên nhân. Trích đoạn ngắn và dẫn file/dòng đã kiểm tra.
4. Đề xuất nguyên nhân, nhãn và vị trí kèm mức chắc chắn có lý do. Taxonomy chưa chốt thì dùng mô tả tạm thời, không ép nhãn vào enum của generator. Giữ chưa xác định khi evidence chưa đủ.
5. Đánh giá riêng điều kiện thực thi, tuân thủ prompt, tính hợp lý và điều kiện dùng dữ liệu. Xét lộ đáp án theo input chẩn đoán thực tế: comment không tự động là leakage; stack trace/số dòng log là evidence hợp lệ. Input chưa chốt thì ghi rủi ro có điều kiện, không tự loại mẫu chỉ vì có comment.

## Trình bày để người dùng review

Mỗi mẫu có năm phần, có thể gộp bảng khi rà nhiều mẫu:

1. **Kết luận ngắn:** lỗi gì đã quan sát, điều kiện thực thi nào đạt/chưa đạt/chưa kiểm tra.
2. **Bằng chứng:** thay đổi code và log hỗ trợ, kèm liên kết file/dòng, nguồn và hash khi đã kiểm tra.
3. **Giải thích nguyên nhân:** chuỗi nhân quả, nhãn/vị trí đề xuất, độ chắc chắn và phần còn là suy luận.
4. **Đánh giá sử dụng:** prompt/hợp lý/leakage, kiến nghị giữ/loại/chờ evidence cho mục đích cụ thể, điều kiện và lý do.
5. **Người dùng cần quyết định:** chỉ câu hỏi còn quan trọng sau phân tích. Người dùng có thể bác bỏ lập luận hoặc yêu cầu kiểm tra thêm; không yêu cầu họ tự chẩn đoán lại từ đầu.

## Giới hạn tác vụ

- Review mặc định chỉ đọc evidence; không gọi/tải model, chạy Docker/test hay thực thi candidate trên host. Nếu cần thí nghiệm mới, mô tả lý do và phạm vi riêng; skill review không tự cấp quyền cho bước đó.
- Giữ raw logs, code sinh, source/tests và manifest gốc bất biến. Chỉ tạo/cập nhật bản phân tích dẫn nguồn trong phạm vi được yêu cầu; không sửa output để làm mẫu đạt hoặc âm thầm cập nhật review.json gốc.
- Không tự ghi reviewer/ngày phê duyệt, confirmed label/location, gold hoặc training approval. Chỉ ghi nhận xác nhận khi người dùng đã nói rõ phạm vi; đồng ý tiếp tục công việc không đồng nghĩa duyệt nhãn hay cho dùng để train. Không biến pending thành approved do test pass hoặc agent tự tin.
- Không chốt lại taxonomy, input/output chẩn đoán hay protocol thay người dùng. Có thể hoàn tất phân tích tạm thời, ghi thiếu sót và đề xuất quyết định mà không bịa kết quả hoặc buộc mọi tác vụ khác phải dừng.
