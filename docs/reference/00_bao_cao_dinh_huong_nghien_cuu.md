# Báo cáo định hướng nghiên cứu — Đồ án IT5417

**Tên đề tài dự kiến:** Ứng dụng mô hình ngôn ngữ lớn sinh dữ liệu tổng hợp có kiểm chứng hỗ trợ chẩn đoán lỗi CI trong quy trình cộng tác người–agent.

**Ngày cập nhật:** 23/10/2026.  
**Giảng viên hướng dẫn:** Vũ Thị Hương Giang.  
**Trạng thái:** Định hướng và thiết kế thực nghiệm; chưa triển khai pipeline, sinh dữ liệu hoặc huấn luyện mô hình.

Đây là tài liệu chính về hướng nghiên cứu. [Báo cáo As-is](01_as_is_scenario.md) mô tả hiện trạng và [tài liệu yêu cầu](02_yeu_cau_he_thong.md) diễn giải các năng lực hỗ trợ nghiên cứu thành Epic, Feature, User Story và tiêu chí nghiệm thu.

## 1. Bối cảnh và vấn đề

CI là quy trình tự động kiểm tra phần mềm sau thay đổi, thường gồm cài dependency, kiểm tra cú pháp, biên dịch và chạy test. Khi một lần CI thất bại, developer phải kết hợp log, code, diff và lịch sử để tìm nguyên nhân. Diff là phần biểu diễn code được thêm, xóa hoặc sửa giữa các phiên bản.

Trong quy trình có coding agent, code có thể trải qua nhiều lượt agent và người cùng chỉnh sửa. Biết ai tạo một commit chưa đủ kết luận ai tạo ra lỗi. Một sự cố cũng có thể đến từ cấu hình, dependency hoặc môi trường, trong khi code nghiệp vụ vẫn đúng.

Đề tài nghiên cứu cách tạo thêm tình huống lỗi bằng LLM, kiểm chứng chúng bằng thực thi và đánh giá giá trị đối với chẩn đoán. Nhóm lỗi ít mẫu là use case dự kiến; việc thiếu mẫu hoặc mất cân bằng phải được xác nhận trên train, không mặc định từ đầu.

## 2. Mục tiêu, câu hỏi và phạm vi

**Câu hỏi trung tâm:** Dữ liệu tổng hợp được kiểm chứng có giúp mô hình chẩn đoán lỗi CI tốt hơn trên dữ liệu thật, đặc biệt ở nhóm ít mẫu, so với chỉ dùng dữ liệu thật và các đối chứng đơn giản không?

- **RQ1 — Chất lượng dữ liệu:** Bao nhiêu tình huống sinh ra sử dụng được, tái hiện ổn định và có nhãn đủ bằng chứng? Chi phí để có một mẫu dùng được là bao nhiêu?
- **RQ2 — Giá trị huấn luyện:** Bổ sung synthetic đã kiểm chứng có cải thiện phân loại và khoanh vùng so với real-only, xử lý mất cân bằng đơn giản và synthetic chưa xác minh nhãn đầy đủ không?
- **RQ3 — Khả năng áp dụng:** Cải thiện có ổn định giữa các lớp, nguồn dữ liệu và seed không? Có tổng quát sang repo chưa gặp nếu dữ liệu cho phép không?

Nhiệm vụ chính là phân loại lỗi và xếp hạng vị trí ở mức file/hàm. Khoanh vùng dòng và truy vết người–agent chỉ đánh giá trên subset đủ nhãn. Khởi đầu ưu tiên Python và một số repo chạy lại được; số repo, taxonomy và quy mô train chưa khóa.

Giá trị dự kiến gồm một cấu trúc dữ liệu có bằng chứng, quy trình sinh/kiểm chứng và thực nghiệm đối chứng. Đây chưa phải đóng góp đã được chứng minh; cần tiếp tục đối chiếu nghiên cứu liên quan trước khi kết luận tính mới.

### Chẩn đoán, dự đoán và SFT là các khái niệm khác nhau

| Khái niệm | Đầu vào và mục đích |
|---|---|
| Chẩn đoán sau CI thất bại | Biết lần chạy đã fail; dùng log hiện tại và code để tìm loại lỗi, vị trí và thay đổi liên quan |
| Dự đoán trước khi chạy | Chỉ dùng dữ liệu có trước lần chạy; dự đoán kết quả tương lai. Đây chưa là nhiệm vụ chính |
| SFT | Cách fine-tune LLM bằng cặp yêu cầu–đáp án, áp dụng cho nhiệm vụ chẩn đoán |
| QLoRA | Cách giảm bộ nhớ khi fine-tune: giữ mô hình nền ở dạng 4-bit và học adapter bổ sung |

Định nghĩa SFT và QLoRA được đối chiếu từ tài liệu TRL/PEFT [S5, S6]. CI pass chỉ có nghĩa các kiểm tra đã chạy không phát hiện lỗi, không bảo đảm chương trình đúng trong mọi trường hợp. Đầu vào pass được trả trạng thái “không ghi nhận lỗi trong lần kiểm tra”; đầu vào thiếu kết quả hoặc log cần thiết được trả trạng thái thiếu thông tin. Không ép mọi input thành một lỗi code.

## 3. Thiết kế dữ liệu và nhiệm vụ ML

### 3.1. Đơn vị mẫu và các nhóm trường

Một mẫu là **một tình huống lỗi tại một phiên bản code, kèm dữ liệu thực thi và bằng chứng xây nhãn**. Các retry, bản sửa và biến thể của cùng tình huống phải giữ chung mã nhóm.

| Nhóm | Nội dung dự kiến | Vai trò |
|---|---|---|
| Định danh | Mã mẫu, nguồn, repo, commit, PR/run/attempt nếu có, mã nhóm và mẫu cha | Quản lý nguồn, chia tập và chống trùng |
| Input | Log, code tại phiên bản lỗi, diff trước lần thất bại nếu có, lịch sử đến thời điểm đó | Thông tin mô hình được phép xem |
| Nhãn | Loại lỗi, tập vị trí có bằng chứng, bước thay đổi liên quan và actor nếu đủ rõ | Đáp án huấn luyện/đánh giá |
| Bằng chứng | Môi trường, dependency, lệnh, log gốc, test report, bản sửa/hoàn tác và lần chạy lại | Xác minh nhãn; tách khỏi input |
| Trạng thái | Nhãn nào đã xác minh, người rà soát, thiếu gì, lý do giữ/loại, phiên bản schema | Kiểm soát chất lượng từng nhiệm vụ |
| Sinh dữ liệu | Model/revision, prompt, cấu hình sinh, thời gian, chi phí và loại phương pháp | Tái lập và đo hiệu suất |

Log lấy từ GitHub CI và log từ môi trường tái hiện phải có trường phân biệt nguồn. Một lần test local được tái hiện không tự trở thành raw log của CI lịch sử.

### 3.2. Input và output

Input cốt lõi là log lỗi và code liên quan. Diff, cấu hình và lịch sử được bổ sung khi nguồn có đủ dữ liệu; ghi rõ phần thiếu. Không dùng gold patch của SWE-bench thay cho diff gây lỗi.

Output có cấu trúc gồm trạng thái xử lý, loại lỗi hoặc chưa xác định, danh sách tối đa 5 file/hàm nghi vấn, bằng chứng tham chiếu từ input và bước thay đổi liên quan nếu đủ lịch sử. Mục cấu hình hoặc dependency cũng là vị trí hợp lệ khi đó là phạm vi nghi vấn.

Taxonomy ban đầu có thể gồm cú pháp/kiểu dữ liệu, logic, dependency và cấu hình. Cần điều chỉnh sau khi đọc pilot thuộc tập phát triển. “Test fail” là biểu hiện, chưa phải nguyên nhân; `ModuleNotFoundError` cũng có thể do sai import thay vì thiếu thư viện. Mẫu nhiều nguyên nhân hoặc chưa rõ được đánh dấu riêng, không ép vào một nhãn đơn.

Mẫu thiếu nhãn vị trí vẫn có thể dùng cho phân loại nếu nhãn loại lỗi đã đủ bằng chứng. Khi SFT, chỉ tạo đáp án cho phần đã xác minh; phân biệt “chưa có nhãn” với kết luận “hệ thống không xác định được”. Không biến mọi vị trí chưa được gắn nhãn thành vị trí âm.

### 3.3. Ví dụ minh họa tự xây dựng

Hàm tính tổng ban đầu cộng giá và phí; test kỳ vọng 110 và chạy thành công. Agent đổi nhầm thành phép trừ; cùng test nhận 90 và thất bại. Người khôi phục phép cộng, chạy lại thành công. Có thể đề xuất nhãn lỗi logic, vị trí là hàm tính tổng, bước liên quan là bước agent sửa.

Đây là ví dụ giả định để giải thích schema, chưa được thực thi và không phải record dataset. Chuỗi pass–fail–pass trong ví dụ là bằng chứng minh họa, không là kết quả thực nghiệm. LLM đóng vai người vẫn phải ghi là dữ liệu do mô hình sinh, không gắn nhãn thao tác người thật.

## 4. Nguồn dữ liệu và khoảng trống

Khảo sát ngày 22/10/2026 đã kiểm tra tài liệu, metadata và một số record; chưa dựng môi trường hoặc tái hiện test. Chi tiết, phiên bản và snapshot nằm trong [ghi chú xác minh](../research/dataset_verification_2026-10-22/verification_notes.md).

| Nguồn | Phần tận dụng | Phần cần xây thêm |
|---|---|---|
| AIDev/AIDev-pop | PR có dấu vết agent; subset chi tiết có review, commit và file diff | Log CI, tái hiện, nhãn nguyên nhân/vị trí và chuỗi cộng tác có bằng chứng |
| SWE-bench, subset phù hợp | Repo, base commit, vấn đề, patch sửa, test patch và danh sách test trước/sau | Log tái hiện, taxonomy, nhãn vị trí được rà soát; không có sẵn provenance người–agent |
| Tình huống tự xây | Chủ động ghi actor và bổ sung cơ chế lỗi cần nghiên cứu | Chi phí thao tác người thật, kiểm chứng và đánh giá tính thực tế |

AIDev v5 cung cấp các bảng chuẩn hóa; bảng phụ chi tiết thuộc AIDev-pop, không mặc định có cho mọi PR. Nhãn agent ở mức PR không xác nhận tác giả từng dòng hay nguyên nhân lỗi. Các bản cũ có hạn chế phân trang; cần ghim revision và kiểm tra phần lịch sử còn thiếu [S1].

SWE-bench là benchmark giải quyết vấn đề phần mềm, không mặc định là dataset nguyên nhân CI. Lite có 23 mẫu dev và 300 mẫu test; Verified có 500 mẫu test theo lần kiểm tra 22/10. Chỉ chọn task phù hợp chẩn đoán; không coi mọi issue là một lần CI đã thất bại [S2].

### Các ví dụ thật đã đọc

- **AIDev, properr PR #6:** record `3256868569`, nhãn `OpenAI_Codex`. Diff thêm pytest vào nhóm dependency test và đổi lệnh cài thành `pip install .[test]`. Đây là ứng viên lỗi dependency/cấu hình; chưa chạy trước/sau để xác nhận. PR không chứng minh ai tạo lỗi ban đầu [S3a].
- **AIDev, QuantumVestAI PR #347:** record `3256865969` sửa quan hệ trong model User, nhưng mô tả báo lỗi import `services.api_client`. Nội dung PR chưa chứng minh diff đó gây lỗi; lời báo trong Testing không thay thế raw log [S3b].
- **SWE-bench Verified, `astropy__astropy-12907`:** patch sửa hàm `_cstack` tại `astropy/modeling/separable.py`, giữ ma trận con thay cho điền toàn giá trị 1. Record liệt kê 2 FAIL_TO_PASS và 13 PASS_TO_PASS. Có cơ sở thử nhãn lỗi logic/file/hàm, nhưng các con số này là dữ liệu nguồn, không là kết quả chạy trên máy hiện tại [S3c].

Các mẫu đã dùng để tìm hiểu, thiết kế prompt hoặc lọc dữ liệu thuộc tập phát triển của nghiên cứu, không dùng để khẳng định đánh giá độc lập cuối cùng. Giữ source, nhãn gốc, mapping và giấy phép nguồn; việc nối nhiều nguồn không làm chúng tự có cùng phân phối.

## 5. Sinh dữ liệu tổng hợp có kiểm chứng

**Dữ liệu tổng hợp** là tình huống do mô hình/quy trình tạo ra. Đưa dữ liệu này vào train là một hình thức **tăng cường dữ liệu**. Chuẩn hóa schema và xử lý mất cân bằng là hai công việc khác nhau.

Quy trình dự kiến:

1. Chốt nhóm lỗi và thiếu hụt từ train; chọn seed thuộc train, lưu quan hệ cha–con.
2. Chuẩn bị repo, dependency và lệnh. Với lỗi chủ động tạo mới, xác nhận các kiểm tra liên quan đang pass; với lỗi thật có sẵn, kiểm tra cặp trước/sau sửa theo thiết kế nguồn.
3. Prompt model tạo patch. Tách nguồn “lỗi phát sinh khi agent làm yêu cầu” và “lỗi chủ động cài có kiểm soát”, vì độ tự nhiên có thể khác nhau.
4. Áp dụng patch, chạy kiểm tra, lưu exit code, log gốc và report. Không sinh log bằng LLM rồi dùng làm bằng chứng thực thi.
5. Thử bản sửa/hoàn tác trong cùng môi trường, kiểm tra lỗi có tái hiện và thu hẹp vị trí/bước liên quan. Không suy mọi dòng sửa đều là dòng gây lỗi.
6. Loại patch không áp dụng được, lỗi sai mục tiêu, mẫu trùng hoặc thiếu bằng chứng. Rà soát theo lớp và cách sinh, lưu trạng thái xác minh riêng từng nhãn.

Test dùng làm căn cứ phải độc lập với patch đang đánh giá. Phát hiện việc xóa/bỏ qua test, làm yếu assertion hoặc vô hiệu hóa CI. Test mới do agent viết có thể bổ sung, không là bằng chứng duy nhất. Với lỗi không ổn định, giữ trạng thái riêng thay vì gán nhãn chắc chắn.

SWE-smith là nguồn tham khảo phương pháp: chạy test trước/sau thay đổi để xác định tình huống làm hỏng các kiểm tra có sẵn và lưu artifact thực thi [S4]. Đề tài cần bổ sung xác minh taxonomy, vị trí, provenance và tính hợp lý; chỉ làm test fail chưa đủ.

## 6. Tiền xử lý và chia tập

Giữ log gốc; bản đưa vào model loại mã màu, chuẩn hóa đường dẫn tạm và bỏ thông tin nhạy cảm nếu có. Giữ tên lỗi, hàm, file và ngữ cảnh cần chẩn đoán. Loại trùng cả văn bản và tình huống; các nhóm gần trùng phải được xử lý trước khi khóa split.

Trích log quanh lỗi và chọn file/hàm bằng thông tin có tại thời điểm thất bại, chẳng hạn stack trace và diff quan sát được. Không dùng gold location để chọn sẵn đúng file. Nếu khâu lấy ứng viên bỏ sót vị trí đúng, ghi nhận đó là lỗi của toàn quy trình; đo riêng tỷ lệ giữ được vị trí đúng.

### Protocol chia tập dự kiến

| Tập | Tỷ lệ khởi đầu trên dữ liệu thật của đồ án | Mục đích |
|---|---|---|
| Train |  70% | Học tham số, tính thống kê lớp và làm seed sinh synthetic |
| Validation | 15% | Chọn checkpoint, prompt, ngưỡng lọc và tỷ lệ synthetic; không làm seed sinh |
| Test | 15% | Đánh giá cuối khi các lựa chọn đã cố định |

Chia theo nhóm PR/tình huống/chuỗi sửa lỗi, cố giữ phân bố lớp khi đủ nhóm; không random từng dòng. Biến thể, retry và patch liên quan của cùng nhóm không đi qua các split. Tập test chính giữ dữ liệu thật và phân bố đã chọn; không cân bằng lại. Fit TF-IDF và mọi thống kê tiền xử lý trên train, sau đó áp dụng cho các tập còn lại.

Tỷ lệ 70/15/15 áp dụng cho dataset đồ án tự xây, **không phải split gốc SWE-bench**. Nếu giữ Verified làm benchmark ngoài, giữ protocol đó và rà trùng với toàn bộ dữ liệu phát triển; nếu tự chia lại thì công bố rõ đây là protocol riêng. Chưa có split đã tạo. Với ít dữ liệu, có thể dùng cross-validation theo nhóm trong phần phát triển và vẫn giữ test độc lập. Đánh giá khác repo là thí nghiệm bổ sung khi đủ dữ liệu.

## 7. Phương án mô hình

| Vai trò | Phương án đã chọn cho kế hoạch |
|---|---|
| Sinh dữ liệu local | `Qwen/Qwen2.5-Coder-7B-Instruct`, 4-bit, prompting, chưa fine-tune |
| Sinh dữ liệu dự phòng | API model mạnh hơn nếu pilot  thấy cần thiết; model, ngân sách và ngưỡng chuyển chưa chốt |
| Chẩn đoán chính | `Qwen/Qwen2.5-Coder-3B-Instruct`, SFT bằng QLoRA |
| Đối chứng nhỏ hơn | `Qwen/Qwen2.5-Coder-1.5B-Instruct` nếu đủ thời gian |
| Kiểm tra pipeline | Bản 0.5B khi cần; chưa là thí nghiệm chính |
| Đối chứng phân loại nhẹ | TF-IDF + Logistic Regression |


Chọn Instruct vì cần làm theo yêu cầu và trả đáp án có cấu trúc; vẫn có thể SFT tiếp. Bản Base chỉ được cân nhắc nếu phát sinh câu hỏi nghiên cứu riêng về thích nghi mô hình nền. Model card xác nhận các checkpoint 3B/7B là bản instruction-tuned [S7, S8]. “3B” là cỡ tham số, không phải tên thế hệ Qwen3.

SFT nhận input và đáp án đã xác minh, dùng chat template của checkpoint, ưu tiên tính loss trên phần đáp án. QLoRA học adapter thay vì full fine-tuning. Độ dài, batch, learning rate, rank adapter và số epoch được chọn trong phần phát triển, chưa khóa bằng suy đoán. Lưu checkpoint/revision, cấu hình và seed để tái lập.

Baseline TF-IDF + Logistic Regression chỉ đối chiếu nhiệm vụ phân loại với cùng thông tin khả dụng; không so khả năng sinh giải thích với LLM. Vai trò của baseline là kiểm tra liệu tín hiệu từ vựng đơn giản đã giải quyết được phần lớn nhiệm vụ hay chưa. Model sinh 7B có thể lớn hơn model chẩn đoán 3B vì chỉ cần suy luận. Khi thử API, giữ nguồn sinh riêng và đo theo chi phí/mẫu đạt chuẩn.

## 8. Thiết kế thí nghiệm

| Mã | Cấu hình | Mục đích |
|---|---|---|
| M0 | TF-IDF + Logistic Regression trên dữ liệu thật | Mốc phân loại nhẹ |
| M1 | Qwen 3B Instruct chỉ dùng prompt | Khả năng mô hình nền trước SFT của đề tài |
| M2 | Cùng Qwen 3B, SFT dữ liệu thật | Tác dụng của fine-tuning |
| M3 | Như M2, thêm đối chứng class weights hoặc lấy mẫu lại theo nhóm | So với xử lý mất cân bằng đơn giản |
| M4 | Cùng Qwen 3B, SFT thật + synthetic chưa xác minh nhãn đầy đủ | Đối chứng chất lượng dữ liệu |
| M5 | Cùng Qwen 3B, SFT thật + synthetic đã kiểm chứng | Tác dụng của dữ liệu bổ sung có bằng chứng |
| M6 | Như M5, sinh có mục tiêu cho lớp hiếm | Bổ sung nếu tài nguyên và phân bố train cho phép |

M4 vẫn phải thực thi để có log thật; “chưa xác minh” nói đến nhãn và các bước lọc đầy đủ. Vì thế M4–M5 đo tác dụng của xác minh/lọc sau thực thi, không cô lập riêng tác dụng của việc chạy code. Mẫu không an toàn hoặc không đủ input không được đưa vào chỉ để tạo đối chứng.

Khi so M4–M5, khớp số lượng và phân bố nhãn theo quy tắc công bố; có thể lấy ngẫu nhiên từ nguồn thô đủ lớn để tạo đối chứng tương ứng. Giữ cùng checkpoint nền, cách lấy input, validation/test và quy tắc chọn checkpoint. Báo cả số lượt cập nhật, số token train và chi phí; nếu khác đáng kể, thêm so sánh cùng ngân sách cập nhật/token để tách ảnh hưởng dữ liệu khỏi thời lượng học.

Validation dùng chọn cấu hình; khóa lựa chọn trước khi chấm test. Không điều chỉnh prompt/filter từ lỗi test. Mục tiêu cuối lặp 3 seed nếu tài nguyên cho phép, báo từng lần và độ dao động, không chỉ điểm tốt nhất. Nếu chỉ chạy một lần phải nêu giới hạn. Chưa kỳ vọng trước rằng synthetic luôn cải thiện.

## 9. Metric và kiểm soát dữ liệu sinh kém chất lượng

### 9.1. Chất lượng chẩn đoán

| Nhiệm vụ | Metric và cách đọc |
|---|---|
| Phân loại lỗi | Macro-F1 chính; Precision/Recall/F1 và số mẫu từng lớp; confusion matrix |
| Khoanh vùng | Top-1/Top-5: tỷ lệ tình huống có ít nhất một vị trí đúng trong k đề xuất; tách mức file/hàm/dòng |
| Trích ứng viên | Tỷ lệ tình huống mà tập ứng viên chứa ít nhất một vị trí đúng |
| Truy vết | Độ đúng bước và actor trên subset có gold; công bố số mẫu và coverage kết luận |
| Trạng thái xử lý | Tỷ lệ ép chẩn đoán lỗi trên mẫu pass; tỷ lệ trả thiếu thông tin/chưa xác định phù hợp |
| Vận hành | Độ hợp lệ của output có cấu trúc, thời gian suy luận và VRAM đỉnh |

Macro-F1 lấy trung bình F1 của các lớp với trọng số bằng nhau; vẫn phải xem support và recall lớp hiếm [S10]. Chỉ chấm từng nhiệm vụ trên mẫu đủ nhãn và công bố mẫu số. Với nhiều vị trí đúng, thêm Recall@k để tránh chỉ tìm được một vị trí nhưng báo đủ thành công. Top-k phải tính cả mẫu bị bỏ sót ở bước lấy ứng viên, không chỉ những mẫu thuận lợi.

Mẫu pass và thiếu thông tin cần được xây thành tập kiểm tra riêng cho các trạng thái tương ứng; chưa có sẵn từ mọi nguồn. Không trộn Accuracy phân loại trạng thái với Macro-F1 phân loại nguyên nhân lỗi. SFT cần ví dụ trạng thái đã rà soát nếu muốn học trực tiếp hành vi đó.

### 9.2. Chất lượng synthetic

| Khía cạnh | Cách đo dự kiến |
|---|---|
| Áp dụng được | Số patch áp dụng thành công / tổng ứng viên sinh |
| Valid yield | Số mẫu vượt toàn bộ tiêu chí đã công bố / tổng ứng viên sinh; nêu số bị loại từng bước |
| Tái hiện | Số mẫu lặp lại cùng lỗi qua các lần chạy quy định / số mẫu được chạy lặp; pilot bắt đầu 3 lần/mẫu được kiểm tra |
| Đúng nhãn | Tỷ lệ nhãn được xác nhận qua rà soát độc lập, tách loại lỗi/vị trí/provenance và mức bằng chứng |
| Trùng và đa dạng | Trùng exact/gần trùng theo patch/code; số nhóm cơ chế lỗi khác nhau và phân bố theo lớp/repo/hàm |
| Tính hợp lý | Rà soát thay đổi phù hợp yêu cầu/repo, test không bị làm yếu, lỗi có cơ chế rõ và không lộ đáp án |
| Chi phí | Thời gian và tiền trên mỗi mẫu đạt chuẩn; tách sinh, thực thi và rà soát |
| Tác dụng học | Chênh lệch metric trên test thật giữa các cấu hình kiểm soát |

“Slop” được hiểu ở đây là dữ liệu sinh hời hợt, lặp hoặc ít giá trị học. Ví dụ: cố tình gây exception vô nghĩa, lặp cùng lỗi chỉ đổi tên biến, chèn comment tiết lộ vị trí, hoặc nhãn logic nhưng thực chất fail do môi trường. Không có một điểm số tự động duy nhất xác nhận mọi khía cạnh này.

LLM có thể hỗ trợ đề xuất nhãn và rà soát, nhưng không để chính model sinh làm trọng tài duy nhất. Rà soát thủ công theo lớp/nguồn/cách sinh, ưu tiên người thứ hai cho mẫu khó nếu có; báo số mẫu kiểm tra và mức thống nhất. Mẫu hợp lệ về thực thi vẫn có thể không giúp huấn luyện. Phân tích riêng lỗi nhãn, khác phân phối, mẫu quá dễ, lộ đáp án và thiếu đa dạng khi kết quả không cải thiện.

## 10. Tài nguyên, pilot và tiến độ theo giai đoạn

Ryzen 5 7500F, RTX 4070 SUPER 12 GB, RAM 32 GB. Nguồn bổ sung là Kaggle T4 ×2.

| Tài nguyên | Công việc ưu tiên | Điểm cần đo/quản lý |
|---|---|---|
| PC | Lọc dữ liệu, đọc nhãn, dựng môi trường, chạy kiểm chứng và demo | Dung lượng Docker, CPU/RAM, bắt đầu một tình huống mỗi lượt |
| GPU PC | Sinh bằng 7B 4-bit, thử SFT/inference 3B | VRAM thực tế, độ dài mẫu, tốc độ và mức cắt ngữ cảnh |
| Kaggle | Huấn luyện/đối chứng trên dataset đã chuẩn bị, lưu checkpoint | Quota, thời lượng phiên và lưu trữ thực tế của tài khoản |

Đề xuất WSL2/Ubuntu và Docker cho môi trường chạy lại trên PC. Tài liệu SWE-bench khuyến nghị ít nhất 120 GB trống và RAM 16 GB trở lên; image/cache có thể tăng nhiều, nên 236 GB trống chỉ là điểm xuất phát cho pilot, không bảo đảm đủ mọi thí nghiệm [S9]. Không suy hai T4 là một GPU 32 GB; bắt đầu một GPU rồi mới đánh giá nhu cầu phân phối. Chưa benchmark tốc độ hoặc bộ nhớ của 3B/7B.

- **Giai đoạn 1 — Chốt dữ liệu và nhãn:** Chọn ứng viên repo, taxonomy nhỏ, hướng dẫn gắn nhãn và tiêu chí loại. Sản phẩm: bảng nguồn và quyết định phạm vi.
- **Giai đoạn 2 — Pilot tái hiện:** Thử 10–20 tình huống trong phần phát triển, lưu log và lý do thất bại. Sản phẩm: chi phí, tỷ lệ tái hiện, khả năng xây nhãn. Đây chưa là quy mô đủ để kết luận hiệu quả ML.
- **Giai đoạn 3 — Pilot model và sinh:** Thử tổng độ dài input–đáp án 2.048/4.096 token, batch nhỏ; đo VRAM, tốc độ và tỷ lệ mất ngữ cảnh. Thử 7B local trước, API chỉ là phương án cần cân nhắc sau số liệu pilot.
- **Giai đoạn 4 — Khóa protocol và tạo train:** Chốt nhóm chia tập; sinh từ train, kiểm chứng và tạo bộ đối chứng khớp số lượng/phân bố.
- **Giai đoạn 5 — Huấn luyện và đánh giá:** Chạy các cấu hình ưu tiên M0/M1/M2/M5, sau đó M3/M4 để kiểm tra các giải thích thay thế; chỉ kết luận tác dụng lọc nếu đã có đối chứng phù hợp. M6 và model 1.5B là mở rộng.
- **Giai đoạn 6 — Phân tích và báo cáo:** Báo kết quả theo lớp/nguồn/seed, chi phí và giới hạn; demo chẩn đoán trên dữ liệu nhập thủ công, hướng dẫn tái lập.

Nếu pilot thiếu dữ liệu thật có nhãn, giảm taxonomy hoặc phạm vi nhiệm vụ trước khi mở rộng sinh. Chưa chốt số mẫu cuối, ngân sách API, hyperparameter hoặc ngưỡng hiệu năng; quyết định từ pilot và validation, không từ test. Tạm gác yêu cầu 11 repo theo phạm vi đã thống nhất.

## 11. Tài liệu tham khảo và thời điểm kiểm tra

Các nhận định và thiết kế thực nghiệm trong báo cáo là đề xuất của đồ án. Ngày cập nhật tài liệu không đồng nghĩa mọi nguồn đều được tải lại cùng ngày.

- **S1 — AIDev:** [dataset v5](https://huggingface.co/datasets/hao-li/AIDev/tree/v5), [dataset card](https://huggingface.co/datasets/hao-li/AIDev). Kiểm tra 22/10/2026; metadata revision và mẫu đã lưu trong ghi chú xác minh. Chưa kiểm tra toàn bộ dataset.
- **S2 — SWE-bench:** [cấu trúc dataset](https://www.swebench.com/SWE-bench/guides/datasets/), [Lite](https://www.swebench.com/lite.html), [Verified](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified). Kiểm tra cấu trúc/split và mẫu 22/10/2026. Dùng số split thực tế đã đối chiếu, không lấy số tổng quan chưa nhất quán.
- **S3a — PR properr:** [PR #6](https://github.com/kurtbrose/properr/pull/6). Đọc metadata/diff 22/10/2026, chưa chạy lại.
- **S3b — PR QuantumVestAI:** [PR #347](https://github.com/daparthi001/QuantumVestAI_App_Source_Code/pull/347). Đọc metadata/diff 22/10/2026, chưa chạy lại.
- **S3c — PR Astropy:** [PR #12907](https://github.com/astropy/astropy/pull/12907). Đối chiếu record và PR ngày 22/10/2026, chưa chạy lại.
- **S4 — SWE-smith:** [sinh tình huống](https://swesmith.com/guides/create_instances/), [validation/evaluation](https://swesmith.com/guides/harnesses/). Đọc phương pháp 22/10/2026; chưa tái lập trong đồ án.
- **S5 — TRL:** [SFT Trainer](https://huggingface.co/docs/trl/sft_trainer). Đọc 22/10/2026; dùng để tham khảo cách huấn luyện, chưa chạy trainer.
- **S6 — PEFT:** [quantization và QLoRA](https://huggingface.co/docs/peft/developer_guides/quantization). Đối chiếu lại 23/10/2026; không là số đo VRAM của máy hiện tại.
- **S7 — Qwen 3B:** [Qwen2.5-Coder-3B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct). Đối chiếu model card 23/10/2026; khi triển khai cần lưu revision và license cụ thể của checkpoint.
- **S8 — Qwen 7B:** [Qwen2.5-Coder-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct). Đối chiếu model card 23/10/2026; chưa tải/chạy model.
- **S9 — SWE-bench Docker:** [hướng dẫn Docker](https://www.swebench.com/SWE-bench/guides/docker_setup/). Đối chiếu yêu cầu tài nguyên 23/10/2026.
- **S10 — scikit-learn:** [F1](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html), [TF-IDF](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html), [chia tập theo nhóm và lớp](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html). Đọc định nghĩa 22/10/2026.
- **S11 — Kaggle:** [Notebooks](https://www.kaggle.com/docs/notebooks). Tham khảo giới hạn phiên ngày 22/10/2026; trang mở lại 23/10 không trả nội dung đủ để xác nhận giới hạn mới, nên cần kiểm tra quota và tài nguyên trong phiên thực tế trước khi chạy.
