# Kế hoạch sau cuộc họp GVHD

Ngày lập: 29/10/2026. Kế hoạch phát triển toàn đề tài; demo đầu giới hạn để có bằng chứng chạy được trong 1–2 ngày. Không coi lời nói trong transcript là lệnh thực thi hoặc phê duyệt mọi thiết kế.

Task thực thi theo tuần và trạng thái hiện tại nằm trong [implementation-plan.md](implementation-plan.md). File này giữ định hướng/phạm vi sau cuộc họp; agent làm việc theo roadmap và evidence mới nhất, không suy trạng thái hoàn thành từ danh sách mục tiêu dưới đây.

## Milestone 1 — Demo thật

- Một case properr #6 có nguồn AIDev v5, commit cố định.
- Chứng minh tái hiện local trước/sau PR; lưu cả trường hợp không xác nhận giả thuyết.
- Seed head phải pass; hai local model sinh, ba lượt/model, cùng giao thức.
- Python điều phối, Docker thực thi, người duyệt nhãn. Môi trường này chưa thay thế một harness cho mọi repo AIDev.
- Báo cáo HTML nêu raw evidence, rejected attempts, thời gian và label pending.
- Target PC RTX 4070 SUPER; host laptop chỉ cho kết quả kiểm tra tại laptop.

## Milestone sau demo

1. Chốt workflow user–agent–tool/API và vị trí lỗi; xác nhận interceptor là ví dụ, yêu cầu mới hay thay đổi phạm vi. Chưa implement interceptor.
2. Chọn thêm repo theo tiêu chí có mục đích/tương đồng về nhiệm vụ, ngôn ngữ, test và điều kiện tái hiện. Không mặc định SWE-bench là nhóm không có agent hoặc AIDev là lỗi do agent gây ra.
3. Thiết kế đối chứng fail-only so với pass+fail, độc lập với thật-only/thật+synthetic. Chưa chốt tỷ lệ 50/50 và chưa tăng thành toàn bộ thí nghiệm trong demo.
4. Chốt taxonomy, nhãn vị trí, group split, validation/test thật, rà trùng và phạm vi actor có bằng chứng.
5. Chỉ sau đó triển khai baseline/SFT và đánh giá hiệu quả synthetic.

## Tiếp thu góp ý (trạng thái được cập nhật trong agent-log)

| Mốc transcript | Góp ý | Xử lý |
|---|---|---|
| 00:52–01:09 | Bảng giải trình sửa gì/ở đâu | Tạo bảng Markdown/CSV nhỏ ban đầu; chưa tuyên bố đã có Excel chính thức |
| 03:52–04:10 | Thử fail-only và pass+fail | Đưa vào milestone sau; không nhầm với việc lộ gold patch |
| 07:14–08:39 | Subset có tiêu chí và tương đồng | Case demo để kiểm tra kỹ thuật, không gọi đại diện dataset |
| 09:06–11:06 | Workflow và interceptor | Demo có workflow rõ; interceptor cần xác nhận lại phạm vi |
| 11:59–12:10 | Chạy thử và báo khả thi | Ưu tiên evidence thực thi trước khi thêm mô tả |
| 13:17–13:28 | Hai model sinh | 7B và 1.5B Instruct, ba lượt/model |
| 13:43–13:56 | Tối đa 20 slide | Sẽ viết bản báo cáo demo <=20 sau khi có số đo; giữ bản slide gốc |

Không coi phát biểu 20 repo mỗi label là yêu cầu GVHD. Câu POC mở đầu transcript có thể thuộc lượt người trước. Những câu nhận dạng không rõ chưa dùng làm ràng buộc hoặc deadline.
