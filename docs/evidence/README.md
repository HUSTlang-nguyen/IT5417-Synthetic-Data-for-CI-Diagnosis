# Bằng chứng nghiệm thu

## PC RTX 4070 SUPER — cập nhật 29/10/2026, 12:52 +07

[Evidence PC riêng](target-pc/README.md): tái hiện thật thành công, 22 software tests pass gồm Docker thật, đã chạy đủ sáu lượt LLM. 7B đạt kiểm chứng thực thi 2/3; 1.5B đạt 1/3. Nhãn/chất lượng vẫn chờ người duyệt; đây chưa là gold data hoặc đánh giá hiệu quả ML.

## Snapshot laptop phát triển — 02:35 +07

Phần dưới và `validation-summary.json` ghi trạng thái laptop tại thời điểm cũ, được giữ nguyên làm evidence; không phải cấu hình hay trạng thái hiện tại của PC.

Ngày 29/10/2026, Asia/Bangkok. Artifact đã lưu; mở báo cáo không thực hiện lần chạy live.

- **Tái hiện thật:** [HTML](historical/report.html), [manifest](historical/manifest.json), [base stderr](historical/historical-base.stderr.txt), [head stdout](historical/historical-head.stdout.txt), [JUnit](historical/historical-head.junit.xml). Run reproduce-20261028T193510880404Z: base exit 1 (thiếu pytest), head exit 0 (2 passed). Commit/file inventory được lưu trong manifest/base-source/head-source.
- **Phần mềm:** [14 tests pass](software-tests.txt), gồm unit tests và test Docker thật.
- **Fixture runner:** [summary](runner-fixture/test-summary.json) và log/JUnit. Fixture viết tay chỉ kiểm thử runner: baseline pass, ứng viên fail ba lần, hoàn tác pass. **Không phải output LLM, số lượt nghiên cứu = 0.**
- **Môi trường:** [summary](validation-summary.json). Laptop RTX 3050 4 GB, Python 3.13.12 điều phối Docker Linux; trong image là Python 3.11. Ollama chưa có. **PC RTX 4070 SUPER và cả hai model chưa chạy/đo.**

Kết quả hỗ trợ giả thuyết dependency của PR tại local; không phải raw CI lịch sử hoặc bằng chứng actor gây lỗi. Nhãn synthetic vẫn chờ người duyệt.

HTML structure/escaping đã kiểm bằng unit test. Chưa kiểm tra trực quan: browser policy phiên này chặn URL file://. Cần mở report.html rà tiếng Việt/bố cục trên máy đích.

Run đầy đủ, cache, clone nguồn và weights bị ignore. Các log/tóm tắt nhỏ ở đây được commit để xem lại sau khi clone.
