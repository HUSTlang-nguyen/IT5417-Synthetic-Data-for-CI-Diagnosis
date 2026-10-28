# Yêu cầu hệ thống hỗ trợ nghiên cứu — Đồ án IT5417

**Ngày cập nhật:** 23/10/2026.  
**Trạng thái:** Đề xuất để trao đổi với giảng viên; chưa phải đặc tả đã được stakeholder phê duyệt hoặc phần mềm đã triển khai.

Tài liệu diễn giải [hướng nghiên cứu](00_bao_cao_dinh_huong_nghien_cuu.md) thành yêu cầu ở mức người dùng. Hiện trạng và mã vấn đề P01–P06 nằm trong [báo cáo As-is](01_as_is_scenario.md).

## 1. Phạm vi và ranh giới

Hệ thống dự kiến hỗ trợ chuẩn bị dữ liệu, sinh tình huống lỗi có kiểm chứng, chẩn đoán sau CI thất bại và đánh giá thực nghiệm. Bản đầu nhận artifact thủ công, chạy theo batch hoặc công cụ nội bộ; không bắt buộc có giao diện web.

Nhiệm vụ chính là loại lỗi và vị trí nghi vấn ở mức file/hàm. Truy vết người–agent chỉ thực hiện trên dữ liệu đủ bằng chứng. Không có yêu cầu chứng minh code hoàn toàn đúng, quy trách nhiệm cá nhân, tự sửa mọi lỗi hoặc triển khai vào CI sản xuất trong release đầu.

Phương án kỹ thuật tham chiếu: Qwen2.5-Coder-7B-Instruct local 4-bit sinh bằng prompting, API dự phòng sau pilot; Qwen2.5-Coder-3B-Instruct được SFT bằng QLoRA cho chẩn đoán. Qwen2.5-Coder-1.5B-Instruct là đối chứng tùy tài nguyên, bản 0.5B phục vụ thử pipeline khi cần; TF-IDF + Logistic Regression là đối chứng phân loại nhẹ. CodeBERT không nằm trong phương án. Các lựa chọn này không thay thế Epic về giá trị người dùng.

## 2. Actor

| Mã | Actor | Tương tác và mục tiêu |
|---|---|---|
| ACT01 | Developer/người xử lý lỗi | Gửi hồ sơ lần CI, xem loại lỗi, vị trí và bằng chứng để chọn nơi kiểm tra |
| ACT02 | Người kiểm duyệt dữ liệu | Xem artifact, gắn/duyệt nhãn, ghi mức bằng chứng và lý do giữ/loại |
| ACT03 | Người thực hiện thí nghiệm | Nhập dữ liệu, cấu hình sinh/kiểm chứng, chia tập, chạy đối chứng và xem kết quả |

Một người có thể giữ nhiều vai trò; chưa yêu cầu quản lý tài khoản/phân quyền sản phẩm. Giảng viên là stakeholder đọc báo cáo, không mặc định là actor vận hành phần mềm. Test runner, bộ lọc và model local là thành phần nội bộ. GitHub/CI và dịch vụ LLM API là hệ thống ngoài; chỉ trở thành actor tích hợp khi có luồng gọi trực tiếp, chưa bắt buộc ở bản đầu.

## 3. Epic hai tầng

Cách hiểu tạm của yêu cầu “hai tầng”: tầng nghiệp vụ thể hiện giá trị đối với bên sử dụng; tầng năng lực thể hiện hệ thống hỗ trợ giá trị đó trong quy trình phát triển/nghiên cứu. Cần đối chiếu template chính thức nếu giảng viên định nghĩa khác.

### 3.1. Tầng giá trị nghiệp vụ

| Mã | Epic từ góc độ người dùng | Giá trị cần kiểm tra |
|---|---|---|
| BE01 | Là người nghiên cứu, tôi muốn có dữ liệu lỗi có nguồn và bằng chứng để huấn luyện, so sánh các phương án đáng tin cậy | Giảm sự mơ hồ của nhãn, quản lý mẫu sinh và tạo kết quả tái lập được |
| BE02 | Là developer, tôi muốn có điểm bắt đầu có căn cứ khi CI thất bại để chọn chỗ cần kiểm tra | Hỗ trợ phân loại và khoanh vùng; hiệu quả thực tế cần đánh giá, chưa cam kết tiết kiệm thời gian |

### 3.2. Tầng năng lực hỗ trợ

| Mã | Epic năng lực | Epic nghiệp vụ cha | Vai trò trong quy trình lớn |
|---|---|---|---|
| EP01 | Chuẩn bị hồ sơ dữ liệu và nhãn có nguồn | BE01 | Nối artifact từ repo/CI/dataset thành đầu vào nghiên cứu |
| EP02 | Tạo thêm tình huống và kiểm chứng bằng thực thi | BE01 | Bổ sung dữ liệu train, giữ cách tái hiện và dấu vết sinh |
| EP03 | Hỗ trợ chẩn đoán có bằng chứng | BE02 | Cung cấp ứng viên để developer kiểm tra trước khi sửa/chạy lại |
| EP04 | Tổ chức và đối chiếu thực nghiệm | BE01 | Đánh giá việc bổ sung dữ liệu bằng cùng protocol |

## 4. Features

| Mã | Feature | Epic | Chức năng ở mức người dùng |
|---|---|---|---|
| F01 | Nhập và chuẩn hóa hồ sơ tình huống | EP01 | Nhận repo/phiên bản, log và code; lưu nguồn, phần thiếu và mã nhóm |
| F02 | Rà soát nhãn và bằng chứng | EP01 | Gắn nhãn theo nhiệm vụ, phân biệt actor với nguyên nhân, ghi lý do duyệt/loại |
| F03 | Sinh biến thể từ train | EP02 | Tạo patch theo nhóm lỗi mục tiêu, lưu seed, prompt và model |
| F04 | Chạy và xác minh tình huống | EP02 | Thu log thật, kết quả trước/sau, kiểm tra test độc lập và quyết định sử dụng |
| F05 | Chẩn đoán loại lỗi và trạng thái | EP03 | Trả loại lỗi có căn cứ hoặc trạng thái phù hợp khi pass/thiếu thông tin |
| F06 | Xếp hạng vị trí và tham chiếu bằng chứng | EP03 | Trả danh sách file/hàm nghi vấn; truy vết bước chỉ khi đủ lịch sử |
| F07 | Quản lý split và xuất bộ dữ liệu | EP04 | Giữ nhóm không chồng lặp, synthetic thuộc train, xuất phiên bản tái lập |
| F08 | So sánh cấu hình và chất lượng dữ liệu | EP04 | Tổng hợp metric, chi phí, mẫu số và kết quả theo lớp/nguồn/seed |

## 5. Ưu tiên và release dự kiến

Must là bắt buộc trong release được gán; Should là bổ sung sau các chức năng Must. Release là thứ tự năng lực, chưa gắn mốc lịch cố định.

| Release | Mục tiêu | Story | Phụ thuộc |
|---|---|---|---|
| R1 | Có dữ liệu thật được quản lý, nhãn rà soát, split cố định và baseline chẩn đoán thủ công | US01, US02, US05, US06, US07 | Dữ liệu mẫu và hướng dẫn gắn nhãn |
| R2 | Sinh/kiểm chứng và so sánh tác dụng synthetic | US03, US04, US08 | Split/seed train và baseline R1 |
| R3 | Mở rộng tích hợp GitHub/CI, truy vết sâu và đối chứng bổ sung | Chưa tách story cam kết | Kết quả pilot, lịch sử đủ bằng chứng và tài nguyên |

## 6. User Story và Acceptance Criteria

Các tiêu chí dưới đây mô tả hành vi cần có và điều kiện kiểm thử; chưa phải kết quả đã đạt. Chất lượng dự đoán ML được đo theo protocol, không thể cam kết model luôn đúng ở từng ca.

### US01 — Nhập hồ sơ tình huống

**Actor:** ACT03. **Feature:** F01. **Ưu tiên:** Must. **Release:** R1.

Là người thực hiện thí nghiệm, tôi muốn nhập hồ sơ từ nhiều nguồn và biết phần còn thiếu để chọn dữ liệu phù hợp từng nhiệm vụ.

- **AC01.1:** Given hồ sơ hợp lệ có nguồn, repo, phiên bản, code và kết quả chạy, When nhập dữ liệu, Then hệ thống gán mã mẫu/mã nhóm, giữ nguồn log và ghi nhận artifact liên quan.
- **AC01.2:** Given hồ sơ thiếu log hoặc chưa xác định đúng phiên bản, When kiểm tra tính đầy đủ, Then hệ thống liệt kê trường thiếu và giữ trạng thái chưa đủ cho nhiệm vụ cần trường đó; không tự bịa dữ liệu thay thế.
- **AC01.3:** Given một record SWE-bench có gold patch, When tạo input chẩn đoán, Then bản sửa đáp án nằm trong phần bằng chứng riêng, không được đưa vào input như diff trước lỗi.

### US02 — Duyệt nhãn theo bằng chứng

**Actor:** ACT02. **Feature:** F02. **Ưu tiên:** Must. **Release:** R1.

Là người kiểm duyệt, tôi muốn xem căn cứ và duyệt riêng từng nhãn để giữ những phần đã xác minh mà không ép kết luận phần còn thiếu.

- **AC02.1:** Given mẫu có log, code và artifact kiểm chứng, When duyệt nhãn, Then hệ thống lưu loại/vị trí/bước liên quan cùng trạng thái xác minh, người duyệt và căn cứ tham chiếu cho từng phần.
- **AC02.2:** Given chỉ biết tác giả commit hoặc nhãn agent của PR, When gắn provenance, Then hệ thống lưu thông tin lịch sử đó nhưng không tự biến thành nhãn tác nhân gây lỗi; cho phép “chưa xác định”.
- **AC02.3:** Given loại lỗi đã xác minh nhưng vị trí chưa đủ rõ hoặc mẫu bị loại, When hoàn tất rà soát, Then hệ thống ghi phần dùng được và lý do phần thiếu/loại; không coi vị trí chưa gắn nhãn là nhãn âm.

### US03 — Sinh biến thể có truy xuất nguồn

**Actor:** ACT03. **Feature:** F03. **Ưu tiên:** Must. **Release:** R2.

Là người thực hiện thí nghiệm, tôi muốn sinh biến thể từ seed train theo nhóm lỗi cần bổ sung để thử tăng cường dữ liệu mà vẫn kiểm soát nguồn gốc.

- **AC03.1:** Given seed thuộc train và cấu hình sinh, When model tạo patch, Then hệ thống lưu mẫu cha, mã nhóm, prompt, model/revision, thiết lập sinh, phương pháp sinh và patch; nguồn mô hình không bị ghi thành thao tác người thật.
- **AC03.2:** Given seed thuộc validation/test hoặc chưa được gán split, When yêu cầu sinh dữ liệu train, Then hệ thống từ chối và nêu lý do.
- **AC03.3:** Given patch và nhãn do model đề xuất, When nhận kết quả sinh, Then mẫu ở trạng thái ứng viên chưa kiểm chứng; không tạo log giả hoặc tự coi nhãn đề xuất là gold.

### US04 — Kiểm chứng mẫu bằng thực thi

**Actor:** ACT03, ACT02. **Feature:** F04. **Ưu tiên:** Must. **Release:** R2.

Là người kiểm duyệt dữ liệu, tôi muốn xem kết quả chạy trước/sau và bản sửa để quyết định mẫu có đủ bằng chứng sử dụng không.

- **AC04.1:** Given ứng viên chủ động tạo lỗi mới và môi trường cố định, When kiểm chứng, Then hệ thống lưu lệnh, dependency/môi trường, log thật và trạng thái các kiểm tra liên quan trước/sau; với lỗi có sẵn từ nguồn, lưu kết quả cặp lỗi/bản sửa theo protocol của nguồn.
- **AC04.2:** Given patch làm yếu/bỏ test, vô hiệu hóa CI, lỗi không tái hiện hoặc không đúng mục tiêu, When áp dụng tiêu chí kiểm chứng, Then mẫu bị loại hoặc chuyển rà soát với lý do; test mới do agent tạo không được làm căn cứ duy nhất.
- **AC04.3:** Given có bản sửa/hoàn tác và kế hoạch chạy lặp, When xác minh nhãn, Then hệ thống lưu kết quả từng lượt và phần nhãn được củng cố; không suy mọi dòng của bản sửa đều là dòng gây lỗi, không ghi “đã xác nhận sau sửa” khi chưa có lần chạy đó.

### US05 — Xem loại lỗi và trạng thái phù hợp

**Actor:** ACT01. **Feature:** F05. **Ưu tiên:** Must. **Release:** R1.

Là developer, tôi muốn nhận loại lỗi hoặc trạng thái xử lý phù hợp để biết nên kiểm tra code, cấu hình, dependency hay bổ sung thông tin.

- **AC05.1:** Given hồ sơ CI thất bại đủ input theo cấu hình, When yêu cầu chẩn đoán, Then hệ thống trả output có cấu trúc với loại lỗi hoặc chưa xác định và bằng chứng từ input; không mặc định mọi failure là lỗi code.
- **AC05.2:** Given lần chạy được cung cấp có trạng thái pass, When xử lý, Then hệ thống trả “không ghi nhận lỗi trong lần kiểm tra” và không ép khoanh vùng lỗi; không khẳng định code hoàn toàn đúng.
- **AC05.3:** Given thiếu log/kết quả cần thiết hoặc chỉ có code chưa chạy, When nhận yêu cầu, Then hệ thống thông báo phần thiếu; không trình bày đây là dự đoán chắc chắn về kết quả CI tương lai.

### US06 — Xem vị trí nghi vấn và bằng chứng

**Actor:** ACT01. **Feature:** F06. **Ưu tiên:** Must. **Release:** R1.

Là developer, tôi muốn xem các file/hàm nghi vấn có thứ tự và căn cứ để chọn nơi bắt đầu kiểm tra.

- **AC06.1:** Given output có vị trí ứng viên, When hiển thị kết quả, Then hệ thống trả tối đa 5 vị trí có thứ tự, đường dẫn tương ứng phiên bản code và bằng chứng từ input; vị trí có thể thuộc code hoặc cấu hình.
- **AC06.2:** Given không đủ căn cứ khoanh vùng hoặc không có nhãn dòng đáng tin, When chẩn đoán, Then hệ thống có thể trả chưa xác định hoặc mức file/hàm; không ép một dòng duy nhất và không coi dòng stack trace mặc nhiên là dòng gây lỗi.
- **AC06.3:** Given thiếu lịch sử hoặc chỉ có metadata author, When hiển thị truy vết, Then phần bước/actor gây lỗi để chưa xác định; chỉ đưa ra bước liên quan khi có lịch sử và căn cứ, tách thông tin này khỏi bên thực hiện bản sửa.

### US07 — Chia tập và xuất dữ liệu tái lập

**Actor:** ACT03. **Feature:** F07. **Ưu tiên:** Must. **Release:** R1.

Là người thực hiện thí nghiệm, tôi muốn cố định split và xuất các phiên bản dữ liệu để so sánh mà không để biến thể cùng lỗi xuất hiện ở cả train và test.

- **AC07.1:** Given mẫu đã chuẩn hóa và các quan hệ nhóm/gần trùng đã rà soát, When tạo split, Then mỗi nhóm chỉ thuộc một tập; lưu danh sách mã mẫu, seed, nguồn và phiên bản. Nếu giữ split benchmark gốc thì không gọi tỷ lệ chia riêng của đồ án là split gốc.
- **AC07.2:** Given ứng viên synthetic có seed train, When được duyệt và xuất dữ liệu, Then ứng viên chỉ bổ sung vào train; validation/test chính vẫn là dữ liệu thật cố định, không cân bằng lại và không nhận biến thể của nhóm train.
- **AC07.3:** Given các mẫu đủ nhãn khác nhau theo nhiệm vụ, When xuất train/evaluation, Then hệ thống giữ schema, nguồn, phần nhãn có thể dùng và kiểm tra không có gold patch/kết quả sau sửa trong input; hiện cảnh báo nếu không đủ nhóm để chia theo cấu hình.

### US08 — So sánh thí nghiệm và chất lượng synthetic

**Actor:** ACT03. **Feature:** F08. **Ưu tiên:** Must. **Release:** R2.

Là người thực hiện thí nghiệm, tôi muốn xem chất lượng dữ liệu và kết quả của các đối chứng để biết synthetic có ích và tốn bao nhiêu chi phí.

- **AC08.1:** Given các kết quả dùng cùng tập đánh giá và quy tắc chấm, When tổng hợp, Then báo Macro-F1/từng lớp, Top-1/Top-5 riêng file/hàm trên mẫu đủ nhãn, số mẫu được chấm, độ hợp lệ output, cấu hình và seed; không chỉ báo Accuracy hoặc lần chạy tốt nhất.
- **AC08.2:** Given so sánh synthetic thô và đã kiểm chứng, When tạo báo cáo, Then công bố số lượng, phân bố lớp, ngân sách train và mức xác minh; nếu chưa kiểm soát thì ghi giới hạn, không quy toàn bộ chênh lệch cho bộ lọc. Synthetic thô dùng log phải có log thực thi thật.
- **AC08.3:** Given có artifact sinh/kiểm chứng/rà soát, When đánh giá dữ liệu, Then báo valid yield với mẫu số tổng ứng viên, lý do loại, tái hiện, đúng nhãn, trùng/đa dạng, tính hợp lý và chi phí/mẫu đạt chuẩn; thiếu số đo được ghi chưa đo, không điền giá trị giả.

## 7. Liên kết yêu cầu

| Vấn đề As-is | Epic nghiệp vụ | Epic năng lực | Feature | Story | Acceptance Criteria | Release |
|---|---|---|---|---|---|---|
| P01 | BE01 | EP01 | F01 | US01 | AC01.1–AC01.3 | R1 |
| P02, P05 | BE01 | EP01 | F02 | US02 | AC02.1–AC02.3 | R1 |
| P05 | BE01 | EP02 | F03 | US03 | AC03.1–AC03.3 | R2 |
| P03, P04 | BE01 | EP02 | F04 | US04 | AC04.1–AC04.3 | R2 |
| P02 | BE02 | EP03 | F05 | US05 | AC05.1–AC05.3 | R1 |
| P01, P02 | BE02 | EP03 | F06 | US06 | AC06.1–AC06.3 | R1 |
| P06 | BE01 | EP04 | F07 | US07 | AC07.1–AC07.3 | R1 |
| P04, P06 | BE01 | EP04 | F08 | US08 | AC08.1–AC08.3 | R2 |

## 8. Kiểm thử chấp nhận và điều kiện hoàn thiện

Các ca kiểm thử hành vi gồm hồ sơ đầy đủ/thiếu trường; pass/fail/thiếu kết quả; chỉ có nhãn loại lỗi; patch động vào test; ứng viên không tái hiện; nhóm trùng qua split; seed test bị dùng sinh; output sai cấu trúc; và báo cáo chưa có số liệu. Chuẩn bị fixture có nhãn/bằng chứng được rà soát; chưa có các fixture hoặc kết quả chạy trong tài liệu này.

Kiểm thử hành vi không thay thế đánh giá ML. Chưa chốt ngưỡng Macro-F1/Top-k, thời gian phản hồi hay quy mô dataset; đặt ngưỡng sau pilot trong phần phát triển, khóa trước test. Với khả năng truy vết, báo cả coverage và phần chưa xác định để tránh chỉ chọn mẫu dễ.

Các điều cần đối chiếu tiếp là template elicitation, cách giảng viên hiểu Epic hai tầng, taxonomy, tập repo, nguồn thao tác người thật, ngân sách API và thời hạn release. Mặc định hiện tại là hỗ trợ nghiên cứu nội bộ, nhập dữ liệu thủ công và giữ lịch sử để tái lập; không đặt thêm các yêu cầu tài khoản, dashboard hoặc triển khai production.

## 9. Căn cứ và trạng thái nguồn

Yêu cầu được tổng hợp từ trao đổi đồ án và ảnh ghi chú giảng viên ngày 23/10/2026, không phải biên bản phỏng vấn hoặc phê duyệt. P01–P06 giữ đúng mức bằng chứng trong As-is. Các tên dataset/model là phương án nghiên cứu, không được coi là yêu cầu nguyên văn của giảng viên.

Ví dụ và giới hạn dữ liệu dựa trên [ghi chú xác minh ngày 22/10](../research/dataset_verification_2026-10-22/verification_notes.md). Tên checkpoint, phương pháp fine-tune và nguồn kỹ thuật được đối chiếu trong mục tài liệu tham khảo của báo cáo nghiên cứu. Hai tài liệu đó là căn cứ khi cập nhật yêu cầu sau pilot.
