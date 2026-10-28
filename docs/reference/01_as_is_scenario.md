# Báo cáo As-is Scenario — Đồ án IT5417

**Ngày cập nhật:** 23/10/2026.  
**Chủ đề:** Dữ liệu tổng hợp có kiểm chứng cho chẩn đoán lỗi CI trong cộng tác người–agent.  
**Trạng thái:** Mô tả hiện trạng sơ bộ theo khung elicitation tạm; chưa đối chiếu template chính thức của giảng viên.

Tài liệu này độc lập với thiết kế giải pháp. Phần đề xuất nằm trong [báo cáo nghiên cứu](00_bao_cao_dinh_huong_nghien_cuu.md) và [tài liệu yêu cầu](02_yeu_cau_he_thong.md).

## 1. Mục đích và cách thu thập thông tin

Mục đích là xác định cách xử lý lỗi và chuẩn bị dữ liệu trước khi có hệ thống nghiên cứu đề xuất, các bên liên quan, khó khăn và phần cần xác minh. Phạm vi gồm hai hoạt động: developer tìm nguyên nhân sau CI thất bại và người nghiên cứu xây dữ liệu chẩn đoán.

Thông tin hiện có đến từ trao đổi định hướng với người thực hiện đồ án, báo cáo ngày 16/10/2026, tài liệu nguồn và việc đọc mẫu AIDev/SWE-bench ngày 22/10/2026. Chưa thực hiện phỏng vấn developer, quan sát công việc hoặc đo thời gian xử lý CI. Không có biên bản stakeholder xác nhận quy trình thực tế.

| Ký hiệu | Cách hiểu |
|---|---|
| E — Bằng chứng đã đọc | Có tài liệu hoặc record cụ thể để đối chiếu; không đồng nghĩa đã tái hiện bằng thực thi |
| A — Giả định hiện trạng | Quy trình/tình huống dùng để phân tích, cần khảo sát người dùng xác nhận |
| Q — Câu hỏi mở | Thông tin còn thiếu, chưa dùng như một sự thật đã được kiểm chứng |

## 2. Bối cảnh, stakeholder và mục tiêu hiện tại

Một thay đổi code có thể kích hoạt CI, với các bước cài dependency, kiểm tra và chạy test. Khi có agent tham gia, code có thể tiếp tục được người hoặc agent sửa. Giả định cần xem xét là người xử lý lỗi phải nối thông tin phân tán giữa log, diff và lịch sử, thay vì có sẵn một hồ sơ chẩn đoán hoàn chỉnh.

| Bên liên quan | Mục tiêu/quan tâm | Cơ sở hiện tại |
|---|---|---|
| Developer/người xử lý CI | Tìm nguyên nhân, chọn vị trí kiểm tra và sửa đúng vấn đề | A: nhu cầu dự kiến, chưa phỏng vấn |
| Người kiểm duyệt dữ liệu | Có nhãn đủ căn cứ, phân biệt điều biết và chưa biết | A: vai trò nghiên cứu đề xuất |
| Người thực hiện thí nghiệm | Có tập dữ liệu và protocol so sánh công bằng, tái lập được | E: định hướng đã trao đổi với người thực hiện |
| Giảng viên hướng dẫn | Theo dõi tính rõ ràng, khả thi và bằng chứng của đề tài | E: yêu cầu tài liệu được cung cấp qua ảnh; chưa có bản template đầy đủ |
| Chủ repo/người duy trì | Có thể cung cấp lịch sử hoặc làm rõ thay đổi nếu được tiếp cận | Q: chưa có cam kết tham gia |

Các vai trò có thể do cùng một người đảm nhiệm. GitHub, CI và dataset công khai là nguồn/công cụ của hiện trạng; không giả định đã được tích hợp vào một hệ thống của đồ án.

## 3. AS-01 — Developer xử lý một lần CI thất bại

**Mục tiêu:** Tìm nguyên nhân phù hợp và kiểm tra tác dụng của bản sửa.  
**Kích hoạt:** Có thông báo một lần CI thất bại.  
**Tiền điều kiện giả định:** Người xử lý truy cập được repo, ít nhất một phần kết quả chạy và phiên bản cần xem.  
**Mức bằng chứng:** A — luồng giả định để elicitation, chưa quan sát người dùng thực hiện.

| Bước hiện tại dự kiến | Thông tin vào | Thao tác và kết quả |
|---|---|---|
| 1. Xác định lần chạy | Thông báo, run/job, commit/attempt | Chọn đúng lần thất bại, tránh nhầm với retry hoặc phiên bản đã sửa |
| 2. Đọc biểu hiện lỗi | Log, test report, trạng thái job/step | Tìm thông báo lỗi và kiểm tra bị hỏng |
| 3. Xem thay đổi | Code, diff, dependency, workflow | Lập giả thuyết lỗi code, cấu hình, dependency hoặc môi trường |
| 4. Lần lại lịch sử | Commit, review, lượt sửa nếu có | Xác định bước thay đổi liên quan; chưa mặc định tác giả commit là người tạo lỗi |
| 5. Thử bản sửa | Giả thuyết và môi trường chạy | Sửa/hoàn tác, chạy lại và so sánh kết quả |
| 6. Ghi nhận kết luận | Kết quả trước/sau | Giữ bằng chứng đủ căn cứ hoặc ghi chưa xác định |

**Ngoại lệ cần khảo sát:** Log không còn tải được; nhiều workflow/attempt; lỗi không ổn định; dependency cũ không còn cài được; môi trường không giống CI; nhiều thay đổi tương tác. Nếu các kiểm tra pass, kết luận chỉ giới hạn trong lần kiểm tra đó.

**Đầu ra hiện tại dự kiến:** Giả thuyết nguyên nhân, vị trí cần kiểm tra, bản sửa và kết quả chạy lại. Chưa xác minh developer thường lưu chúng ở đâu, theo định dạng nào hoặc có lưu đủ lịch sử hay không. Không có số liệu để khẳng định hệ thống tương lai giảm được bao nhiêu thời gian.

## 4. AS-02 — Người nghiên cứu chuẩn bị dữ liệu chẩn đoán

**Mục tiêu:** Chọn tình huống có thể dùng để huấn luyện và đánh giá.  
**Kích hoạt:** Cần khảo sát nguồn dữ liệu và phạm vi đề tài.  
**Hiện trạng thực tế của đồ án:** Đã đọc tài liệu/schema và mẫu; chưa triển khai thu thập diện rộng, chạy kiểm chứng hoặc huấn luyện.

| Bước | Trạng thái hiện tại | Phần còn thiếu |
|---|---|---|
| 1. Xác định nhiệm vụ | E: đã chuyển từ pass/fail sang chẩn đoán | Chốt mức nhãn khả thi sau pilot |
| 2. Khảo sát nguồn | E: đã đọc AIDev, SWE-bench và một số mẫu | Chọn subset/repo cuối cùng |
| 3. Đối chiếu dữ liệu cần/có | E: có ghi chú về log, diff, nhãn và lịch sử còn thiếu | Chưa đo coverage trên tập đại diện |
| 4. Tái hiện tình huống | Q: mới có phương án | Chưa có log/test report do đồ án thực thi |
| 5. Gắn nhãn và chia tập | Q: mới có thiết kế | Chưa có taxonomy khóa, gold labels hoặc split |
| 6. Bổ sung synthetic và so sánh | Q: chưa thực hiện | Chưa biết valid yield, chi phí hoặc tác dụng học |

Ở thời điểm này chưa có hệ thống nào của đồ án tự động nối đủ các bước trên. Phần chưa thực hiện được ghi là khoảng trống, không mô tả như một workflow vận hành đã đo được.

## 5. Dữ liệu và bằng chứng hiện có

| Bằng chứng | Điều đã đọc được | Điều chưa thể kết luận |
|---|---|---|
| AIDev và subset AIDev-pop | Có PR-level agent label; subset chi tiết có commit/diff và review | Không sẵn raw CI log, nhãn nguyên nhân/dòng lỗi hoặc tác giả thật của mọi chỉnh sửa |
| properr PR #6 | PR sửa bước cài dependency test để bao gồm pytest | Chưa chạy trước/sau; chưa xác định bên tạo lỗi ban đầu |
| QuantumVestAI PR #347 | Diff sửa quan hệ User; mô tả báo lỗi import khi thử test | Chưa chứng minh lỗi import do diff đó gây ra |
| SWE-bench, Astropy #12907 | Có base commit, bản sửa, test patch và danh sách test trước/sau | Chưa có kết quả tái hiện trên máy hiện tại; không có nhãn cộng tác người–agent |

Các bằng chứng E này được đọc ngày 22/10/2026. Mẫu đọc thuận tiện không đại diện thống kê cho toàn dataset. Các artifact và giới hạn được ghi tại [ghi chú xác minh](../research/dataset_verification_2026-10-22/verification_notes.md).

## 6. Vấn đề cần giải quyết

| Mã | Vấn đề/khó khăn | Căn cứ và giới hạn |
|---|---|---|
| P01 | Thông tin cần chẩn đoán nằm ở nhiều artifact, cần nối đúng phiên bản/lần chạy | A từ AS-01; chưa đo thời gian nối hoặc tỷ lệ thiếu thực tế |
| P02 | Biểu hiện lỗi, vị trí sửa, actor và nguyên nhân dễ bị đồng nhất | E: ví dụ PR và cấu trúc nguồn chưa cho phép suy luận trực tiếp các nhãn này |
| P03 | Việc tái hiện phụ thuộc môi trường và test, có thể tốn tài nguyên | Q: chưa đo tỷ lệ tái hiện hay chi phí trên cấu hình hiện có |
| P04 | Dữ liệu sinh có thể sai nhãn, lặp, quá giả tạo hoặc lộ đáp án | A: rủi ro nghiên cứu cần kiểm tra, chưa có batch synthetic để thống kê |
| P05 | Nguồn có sẵn chưa đáp ứng đủ schema/nhãn; một số lớp có thể ít mẫu | E: thiếu một số trường; Q: chưa đo mất cân bằng hay quy mô nhãn chuẩn |
| P06 | Cần tách tác dụng dữ liệu khỏi mô hình, số mẫu, thời lượng train và rò rỉ | A: yêu cầu thiết kế thực nghiệm, chưa có kết quả so sánh |

## 7. Giả định và câu hỏi cần xác minh

- **A01:** Log, code và ít nhất một phần lịch sử có thể ghép về cùng phiên bản ở subset được chọn.
- **A02:** Có thể xây một taxonomy nhỏ và đủ mẫu thật có nhãn để đánh giá độc lập.
- **A03:** Một phần tình huống tái hiện được trên tài nguyên hiện có; đây là điều pilot cần chứng minh.
- **Q01:** Developer thực tế ưu tiên loại lỗi, vị trí hay lịch sử thay đổi? Họ cần xem bằng chứng ở mức nào?
- **Q02:** Lỗi thường gặp và số mẫu độc lập của từng lớp là bao nhiêu? Bao nhiêu mẫu có đủ nhãn vị trí/provenance?
- **Q03:** Có những PR nào chứng minh người thật và agent cùng chỉnh sửa trong chính chuỗi đang xét?
- **Q04:** Mẫu nào là lỗi code, cấu hình/dependency hoặc môi trường không ổn định? Chi phí chạy lại và kiểm nhãn là bao nhiêu?
- **Q05:** Giảng viên yêu cầu cụ thể những trường nào trong template elicitation và diễn giải Epic hai tầng ra sao?

Các câu hỏi là đầu vào cho khảo sát/pilot tiếp theo, không phải lý do để coi giả định là sự thật. Chưa có stakeholder xác nhận chính thức taxonomy, số mẫu, release hoặc chỉ tiêu ML.

## 8. Nguồn tham khảo

- [AIDev](https://huggingface.co/datasets/hao-li/AIDev), [SWE-bench dataset](https://www.swebench.com/SWE-bench/guides/datasets/): khảo sát cấu trúc và đọc mẫu 22/10/2026; chưa chạy lại.
- [properr PR #6](https://github.com/kurtbrose/properr/pull/6), [QuantumVestAI PR #347](https://github.com/daparthi001/QuantumVestAI_App_Source_Code/pull/347), [Astropy PR #12907](https://github.com/astropy/astropy/pull/12907): đọc metadata/diff 22/10/2026; không coi mô tả PR là log thực thi đã xác minh.
- Báo cáo định hướng ngày 16/10/2026 và nội dung trao đổi đồ án: nguồn xác định mục tiêu, không phải kết quả khảo sát người dùng.
- Ảnh ghi chú sáu mục giảng viên yêu cầu, được cung cấp ngày 23/10/2026: căn cứ tổ chức tài liệu; chưa có file template chính thức để đối chiếu.
