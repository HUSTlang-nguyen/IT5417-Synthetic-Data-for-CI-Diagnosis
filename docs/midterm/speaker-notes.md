# Ghi chú thuyết trình — 20 phút

## 1. DỮ LIỆU TỔNG HỢP CHO CHẨN ĐOÁN LỖI CI

25 giây. Em trình bày tiến độ đề tài Synthetic Data for CI Diagnosis. Trọng tâm là cách xây dữ liệu có bằng chứng thực thi, cách dùng dữ liệu để SFT mô hình chẩn đoán và những gì kết quả hiện tại cho phép kết luận. Báo cáo cập nhật đến ngày 13/11/2026. Nguồn: docs/evaluation-results.md và docs/implementation-plan.md.

## 2. Mục tiêu và câu hỏi nghiên cứu

40 giây. Mục tiêu không chỉ là nhận biết test thất bại. Cần chỉ ra nguyên nhân kỹ thuật và khoanh vùng code gây lỗi. Câu hỏi chính là synthetic có giúp mô hình chẩn đoán tốt hơn trên lỗi thật không. So sánh M2 với M5 giữ cùng base và tập đánh giá. Hiện dữ liệu nhỏ và nhãn silver nên em trình bày đây là kết quả thăm dò. Nguồn: docs/experiment-protocol-v1.1.md.

## 3. SFT trong bài toán này

45 giây. SFT là supervised fine-tuning, khác với huấn luyện một mô hình ngôn ngữ từ đầu. Trong một cuộc hội thoại train có system instruction, user chứa log/code và assistant là target. Response-only loss chỉ tính token assistant, nhưng model vẫn đọc input để dự đoán. Khi sử dụng không còn target, model phải tự sinh JSON. LoRA học ma trận cập nhật nhỏ; QLoRA giữ base lượng tử hóa. Nguồn: docs/experiment-protocol-v1.1.md; https://arxiv.org/abs/2106.09685; https://arxiv.org/abs/2305.14314.

## 4. Đầu vào và đầu ra chẩn đoán

40 giây. Phần trái là những gì model được xem: log của phiên bản đang lỗi và code liên quan do retrieval chọn. Phần phải là schema target: cause_type, danh sách vị trí và explanation. File và qualified function đi cùng nhau, không chỉ dự đoán tên hàm chung. Repair patch, reference, edit-site và assessment nằm riêng. Ví dụ schema trên slide chỉ minh họa cấu trúc, không phải một prediction được đo. Nguồn: ci_demo/ml.py; docs/experiment-protocol-v1.1.md.

## 5. Kiến trúc pipeline

50 giây. Đọc theo ba hàng. Đầu tiên tái hiện SWE-bench để xây real silver và chia theo repo. Chỉ seed pass của train được dùng cho generator 7B. Candidate qua Docker và curation tạo synthetic train. Cuối cùng model 3B học real hoặc real cộng synthetic; validation chọn checkpoint rồi test cuối trên real. AIDev thuộc các đợt development trước đó, không phải nguồn real của pilot SFT hiện tại. Nguồn: docs/architecture.md; docs/midterm/facts.json.

## 6. AIDev và SWE-bench cung cấp gì?

40 giây. AIDev được dùng để bắt đầu với properr và thử pipeline PR-level. SWE-bench có base revision, repair patch, test patch và F2P/P2P nên phù hợp tái hiện có đối chứng. Tuy có patch sửa tham chiếu, nguồn không cung cấp sẵn taxonomy nguyên nhân hoặc mọi causal function cho bài toán chẩn đoán. Tập 250 real hiện tại lấy từ SWE-bench. Không gọi kết quả này là điểm benchmark sửa code SWE-bench chính thức. Nguồn: https://huggingface.co/datasets/hao-li/AIDev; https://arxiv.org/abs/2310.06770; docs/dataset-card.md.

## 7. Case, repo và lượt sinh

35 giây. Đơn vị dữ liệu cần tách khỏi đơn vị thực thi. Một case có thể có nhiều test fail do cùng cơ chế, nhiều profile môi trường hoặc ba request sinh. Vì vậy không lấy số lần chạy, số test fail hoặc số byte hash khác nhau để tự khẳng định số tình huống độc lập. Lọc trùng byte còn cần thêm rà trùng cơ chế. Nguồn: docs/task-contract.md; docs/experiment-protocol.md.

## 8. Tái hiện lỗi thật

55 giây. Với SWE-bench, áp cùng test patch trên base và base cộng repair patch. Cần thấy F2P chuyển fail sang pass, P2P vẫn pass. Môi trường, test và source phải ghim bằng hash. Không dùng một lỗi thiếu dependency của harness làm nhãn lỗi chương trình. Log ở đây là local reconstruction, không phải raw CI lịch sử. Base fail/fixed pass hỗ trợ hành vi ở test đã chọn, không chứng minh đã tái dựng toàn bộ môi trường benchmark. Nguồn: docs/experiment-protocol.md; docs/architecture.md.

## 9. Sàng lọc và kiểm tra chất lượng

45 giây. Pipeline cần nhiều cổng vì test fail chỉ là một quan sát. Một candidate đạt runner vẫn có thể vi phạm prompt hoặc có thay đổi kém hợp lý. Thiếu artifact hay hash sai phải báo thiếu bằng chứng. Curation giữ riêng đề xuất generator, phân tích có evidence và xác nhận gold. Không sửa raw logs hoặc response để làm dữ liệu đẹp hơn. Nguồn: docs/labeling-guide.md; docs/evaluation-error-analysis.md.

## 10. Dataset pilot đã khóa

55 giây. Dataset hiện có 250 real chia175train,37validation và38test;101synthetic chỉ thêm vào train. M2 học175mẫu, M5 học276mẫu, hai model có cùng validation/test. Repo train gồm marshmallow, pvlib, pydicom, astroid và SymPy; validation là Sphinx; test là Flask, Pylint, Pytest. Train tập trung mạnh vào SymPy. Đây là pilot v1.1 riêng; mục tiêu matched175synthetic của v1.0 còn thiếu74. Nguồn: docs/midterm/facts.json; data-manifests/training-v1.1.json.

## 11. Sinh candidate bằng 7B

50 giây. Giao thức v3 yêu cầu thay một dòng tại site cho phép. Renderer giữ indentation và line ending. Model không tự trả nhãn diagnosis trong schema v3; explanation phép sinh chỉ là provenance, không đưa vào input 3B. Prompt/options/seed được version hóa, không ghi đè W1 hay v2. Output sai JSON, sai site, timeout hoặc không làm test fail vẫn giữ trong tổng lượt. Nguồn: docs/task-contract.md#bổ-sung-giao-thức-development-v3--30102026; docs/architecture.md.

## 12. Kiểm chứng candidate trong Docker

50 giây. Baseline pass xác nhận seed và môi trường đang dùng. Sau đó cùng candidate phải fail ba lần ổn định, rồi khôi phục seed và test pass. Candidate chỉ chạy trong Docker không mạng và có giới hạn tài nguyên, không chạy trên host. Qua runner vẫn phải rà nhãn, hợp lý và trùng lặp. Ba failure repetitions là ba phép đo cùngcandidate, không cộng thành ba mẫu. Nguồn: docs/demo-runbook.md; docs/experiment-protocol.md.

## 13. Nhãn silver được xây thế nào?

55 giây. Bốn lớp mô tả nguyên nhân kỹ thuật, không ánh xạ trực tiếp tên exception. Evidence gồm code/diff, test/log, base/fixed hoặc restoration. Patch sửa giúp điều tra, nhưng vị trí sửa có thể chứa cleanup không phải nguyên nhân. Silver có đánh giá bằng evidence; không phải chuyên gia gold. Việc được phép dùng silver trong pilot không tự phê duyệt gold. Hàng unknown là từ chối kết luận khi thiếu bằng chứng, không phải nhóm train thứnăm. Nguồn: docs/experiment-protocol.md; docs/labeling-guide.md.

## 14. Ví dụ real: metadata của marshmallow

75 giây. Case marshmallow-code__marshmallow-1702 thuộc real train. Hàm Field.__init__ nhận metadata qua arbitrary keyword **metadata rồi gán self.metadata. Khi caller truyền metadata={description:foo,widget:select}, dictionary bị lồng thêm cấp metadata, khác mapping mà test yêu cầu. Nhãn silver API/type nằm tại src/marshmallow/fields.py::Field.__init__. Trên slide là trích đoạn input và hai trường target; explanation đầy đủ giữ nguyên trong facts/real-target.txt. Code được bỏ các dòng không liên quan để dễ đọc, không phải bản đầy đủ model đã nhận. Nguồn: docs/midterm/facts.json; run reproduce-20261112T045454708980Z; input hash01c05f244e22167ef8d141ddf7764628891e62d3df23cd7a473c90fb0e32eac4; upstream marshmallow source/test, license evidence ởrun.

## 15. Ví dụ synthetic: broadcast trong pvlib

75 giây. Mẫu synthetic-generate-20261112T064546343496Z-1 thuộc train. Passing seed broadcast scalar khi system_wide và values không phải tuple. 7B bỏ not, làm scalar không được nhân rộng cho nhiềuarray; lengthcheck phát ValueError. Nhãn logic/value mô tả sai điều kiện, không phải syntax. Causal function là PVSystem._validate_per_array. Đây là lỗi mới từ fixed seed, không đồng nhất lỗi lịch sử case1216. Trên slide có diff để giải thích phép sinh; diff/site không phải input 3B trong pilot. Nguồn: docs/midterm/facts.json; generate-20261112T064546343496Z/attempt-01/change.diff; verify-20261112T064639827687Z; candidate SHA7d058c9af91700e270a30ee3ab157b3e4b8c90497dab9d4d65e13e9f8d59bed5; pvlib BSD license evidence ởreproduction.

## 16. Các cấu hình M0 đến M5

45 giây. M0 là classifier văn bản, chỉ phân loại. M1 prompt-only giữ trọng số; P2 là biến thể format riêng. M2 học real, M5 học real cộng synthetic đã rà, với hai adapter độc lập từ cùng base. M3 xử lý mất cân bằng và M4 đối chứng curation chưa chạy. M4 vẫn cần log thực thi và điều kiện an toàn; không phải bỏ runner. Nguồn: docs/experiment-protocol-v1.1.md; docs/reference/00_bao_cao_dinh_huong_nghien_cuu.md.

## 17. Cấu hình SFT bằng QLoRA

55 giây. Cấu hình dùng base3B NF4 double quant, tính BF16; LoRA rank16, alpha32, dropout0,05. Batch/device1, accumulation8, context2048, output384 và seed5417. Loss chỉ tính target. Parent dùng104 updates và LR1e-4. Số token và exposure được lưu; không tuyên bố hai SFT có cùng compute. Đây là cấu hình pilot, chưa phải cấu hình tối ưu. Nguồn: data-manifests/training-v1.1.json; docs/experiment-protocol-v1.2.md.

## 18. Continuation và checkpoint được chọn

50 giây. M2 học tiếp từ104 lên220 updates, M5 lên350, cùng tổng10 epoch. Continuation giữ adapter, optimizer moments, RNG và vị trí dữ liệu; lịch LR mới bắt đầu2e-5 rồi giảm về0. Joint validation không tăng, quy tắc hòa chọn sớm giữ parent104. Vì vậy adapter test thuộc khoảng4,73/2,99 epoch, khác với ngân sách đã tiêu. Chi phí child vẫn được tính. Nguồn: docs/evaluation-validation.md; continuation-validation-complete-20261113.json.

## 19. Các phần đã hoàn thành

35 giây. W1 chứng minh luồng một repo; các expansion mở rộng harness và review. Sau đó đã khóa250 real và101 synthetic, chạy SFT, continuation và final test. Số development40 sàng lọc,17 case thử,36 lượt sinh và17 lượt đạt thuộc cohort riêng, không cộng vào351 bản ghi SFT.132 software tests cũng không phải số mẫu ML. Target175 synthetic và các ablation còn mở. Nguồn: docs/development-summary.md; docs/results.md; docs/evidence/dataset-v1-progress/software-tests-evaluation-final-v1.txt.

## 20. Các chỉ số đánh giá

60 giây. Accuracy đo đúng loại lỗi. Macro-F1 là trung bình F1 bốn lớp cố định, không trọng số theo support; syntax không có support vẫn tính0. File Top-1 xét file đầu tiên, Hàm Top-1 xét cặp file/hàm đầu tiên. Joint cần cùng mẫu đúng cả loại và hàm, không phải tích hai tỷ lệ. Scorer còn có gate retrieval visibility. Invalid nằm trong mẫu số; M0 không định vị. Nguồn: ci_demo/diagnosis.py; docs/evaluation-protocol-v1.md.

## 21. Kết quả validation trên 37 real

45 giây. Validation dùng cùng37 real. M1-P2 ghi rõ prompt mới; M2/M5 giữ prompt cũ và parent104. M1 cũ có37 response fenced JSON, nên strict parser từ chối toàn bộ; điểm lịch sử được giữ. P2 chỉ đổi yêu cầu format, không thay user code/log. Luôn đoán logic/value cũng đạt29/37 accuracy, do đó cần đọc F1 và định vị, không chỉ accuracy. Nguồn: docs/evaluation-validation.md và evaluation-validation-20261113.json.

## 22. Final test trên cùng 38 real

60 giây. Trước test đã khóa cấu hình, prompt riêng, checkpoint và danh tính38 mẫu. M0 dùng classifier có sẵn; ba model3B có114 request test, một trial. M5 đúng24 loại, M2 đúng22; Hàm Top-1 là7/38 so6/38, joint cùng4/38. File của M5 giảm từ18 xuống16. M1-P2 có8 invalid do Markdown, không tự bỏ fence. Majority baseline đã đạt55,26% accuracy. Nguồn: docs/evaluation-results.md; evaluation-integrity-20261113.json.

## 23. M5 hơn và kém M2 ở đâu?

60 giây. Theo từng mẫu, về class M5 thắng4/thua2; về hàm thắng2/thua1; về joint thắng1/thua1. Gain class nằm ở Pylint. Pytest có accuracy bằng nhau nhưng joint giảm. Đúng file/hàm chưa bảo đảm explanation đúng. Reference hàm vắng khỏi context26/38, silver có giới hạn và train thiếu hai lớp. Một seed cùng việc chưa chạy M3/M4 chưa đủ quy lợi ích nhân quả cho synthetic. Nguồn: docs/evaluation-error-analysis.md.

## 24. Kết luận giữa kỳ và hướng tiếp theo

55 giây. Kết luận giữa kỳ là đã đi trọn pipeline có evidence, với cải thiện nhẹ về phân loại trong pilot. Chưa chứng minh lợi ích tổng quát. Ưu tiên nhãn, retrieval, causal absence/path convention trên development, sau đó mở rộng lớp/repo và đối chứng. Không dùng38 test đã mở để chỉnh prompt hoặc nhãn rồi báo lại như một test độc lập. Phần còn lại dành cho hỏi đáp. Nguồn: docs/evaluation-error-analysis.md; docs/implementation-plan.md.

## 25. Dự phòng: taxonomy và nguồn nhãn (dự phòng)

Bốn lớp là taxonomy chẩn đoán của đề tài. SWE-bench cung cấp repair/test patch và F2P/P2P; phân tích silver nối chúng với code/log để đề xuất nguyên nhân. Exception không tự xác định nhãn. Ví dụ SyntaxError của source trung gian có thể bắt nguồn từ logic preprocessing. Khi thiếu bằng chứng cần qualification hoặc unknown, không ép lớp để đủ quota. Nguồn: docs/experiment-protocol.md; docs/labeling-guide.md.

## 26. Dự phòng: prompt và parser M1 (dự phòng)

M1 cũ có37 fenced JSON nên strict parse từ chối cả37. P2 thay đúng hai đoạn system prompt đã duyệt, từ173 xuống167 token; user code/log không đổi, không thêm code bằng token tiết kiệm. P2 validation có1 invalid, test có8 invalid. Không chuẩn hóa response, không thử nhiều prompt rồi chọn điểm. Vì vậy M1-P2 được ghi riêng. Nguồn: docs/evaluation-protocol-v1.md.

## 27. Dự phòng: kết quả theo lớp và repo (dự phòng)

Test có21 logic/value,9 API/type,8 dependency/configuration và0 syntax. M2 đúng logic15/21, API7/9; M5 là18/21 và6/9. Cả hai dependency0/8. Train chỉ có logic và API nên đây là khoảng trống lớp. Gain class chủ yếu ở Pylint; bảng từng lớp giúp giải trình Macro-F1 và giới hạn thay vì chỉ nhìn accuracy tổng. Nguồn: docs/evaluation-results.md; facts.json.

## 28. Dự phòng: cấu hình và chi phí (dự phòng)

M2 parent2217s cộng child2170s thành4387s; M5 parent2106s cộng child4218s thành6324s. Đã tính phần học tiếp dù không chọn adapter child. M1 cũ363s; bốn phase inference mới1339,692s chưa gồm load, evaluation charge1445s.151 request mới, không gọi trùng. Wall time không phải FLOPs hoặc GPU compute; chưa quy thành tiền. Nguồn: docs/evaluation-results.md; docs/evidence/dataset-v1-progress/evaluation-integrity-20261113.json.
