# Lời thuyết trình bảo vệ giữa kỳ

**Cách dùng:** Đọc các đoạn văn; phần trong ngoặc vuông là nhắc thao tác, không đọc thành tiếng. Mốc thời gian là mục tiêu từ bộ slide, chưa phải thời lượng nói thử đã đo. Có thể dừng ở bảng/sơ đồ; bốn slide dự phòng chỉ dùng khi được hỏi.

## Slide 1 — DỮ LIỆU TỔNG HỢP CHO CHẨN ĐOÁN LỖI CI

**Thời gian: 00:00–00:25 · 25 giây**

[Nhìn hội đồng, chưa cần chỉ vào nội dung slide.]

Em xin phép trình bày tiến độ giữa kỳ của đề tài sinh dữ liệu tổng hợp có kiểm chứng, hỗ trợ chẩn đoán lỗi CI.

Trong phần trình bày này, em sẽ đi từ bài toán và cách xây dữ liệu, đến phương pháp huấn luyện và kết quả đã có. Trọng tâm là làm rõ dữ liệu đã được tạo, kiểm tra và sử dụng như thế nào, cũng như những giới hạn của kết quả hiện tại.

## Slide 2 — Mục tiêu và câu hỏi nghiên cứu

**Thời gian: 00:25–01:05 · 40 giây**

Khi một lần kiểm tra CI thất bại, log thường cho biết lỗi xuất hiện ở đâu, nhưng chưa chắc đó là nơi gây ra lỗi. Người phát triển vẫn cần đọc code và đối chiếu các dấu hiệu để tìm nguyên nhân.

Bài toán của em là cho mô hình đọc log cùng code liên quan, rồi trả lời ba nội dung: loại nguyên nhân kỹ thuật, vị trí file và hàm, cùng một giải thích ngắn.

Câu hỏi nghiên cứu chính là: nếu bổ sung dữ liệu lỗi tổng hợp đã kiểm chứng vào dữ liệu thật, cùng một mô hình nền có chẩn đoán tốt hơn không? Em dùng một cấu hình chỉ học dữ liệu thật và một cấu hình học dữ liệu thật cộng synthetic để so sánh. Phần giữa kỳ là thử nghiệm thăm dò, chưa phải kết luận tổng quát.

## Slide 3 — SFT trong bài toán này

**Thời gian: 01:05–01:50 · 45 giây**

SFT trong đề tài là học thêm trên một mô hình đã được huấn luyện sẵn. Em sử dụng Qwen Coder 3B làm mô hình nền, không huấn luyện mô hình ngôn ngữ từ đầu.

Mỗi mẫu train gồm một đầu vào là log và code, cùng một câu trả lời mong muốn ở dạng JSON. Qua các mẫu này, mô hình học cách chuyển bằng chứng thực thi thành câu trả lời chẩn đoán.

Phần được cập nhật là adapter QLoRA, còn trọng số nền được giữ cố định. Loss chỉ tính trên phần câu trả lời target. Điều này không có nghĩa mô hình bỏ qua đầu vào: mô hình vẫn đọc toàn bộ context để dự đoán các token của câu trả lời.

Để thấy rõ hơn mô hình đang học gì, em trình bày cấu trúc đầu vào và đầu ra ở slide tiếp theo.

## Slide 4 — Đầu vào và đầu ra chẩn đoán

**Thời gian: 01:50–02:30 · 40 giây**

[Chỉ cột input trước, sau đó chỉ các trường JSON bên phải.]

Bên trái là dữ liệu mô hình được phép xem: log của phiên bản đang lỗi và phần code liên quan do bước truy xuất lựa chọn. Mô hình không tự đọc toàn bộ repository trong phiên bản hiện tại.

Bên phải là cấu trúc câu trả lời. Trường cause type là loại nguyên nhân; locations là danh sách các cặp file và hàm; explanation là lời giải thích cơ chế lỗi. Định vị cần đúng cả file và hàm, không chỉ nêu một tên hàm chung.

Repair patch, nhãn tham chiếu và nhận định rà dữ liệu được giữ riêng khỏi input. Nếu đưa các thông tin này vào đầu vào thì mô hình có thể nhìn thấy đáp án thay vì thực sự chẩn đoán.

## Slide 5 — Kiến trúc pipeline

**Thời gian: 02:30–03:20 · 50 giây**

[Đọc sơ đồ từ hàng trên xuống; chỉ vào 7B và 3B khi phân biệt vai trò.]

Sơ đồ này tóm tắt luồng hiện tại. Ở hàng đầu, dữ liệu nguồn được tái hiện để xác nhận hành vi trước và sau sửa, sau đó xây mẫu real silver và chia theo repository.

Ở hàng thứ hai, chỉ bản đã pass của case train mới được dùng làm seed. Generator 7B tạo candidate gây lỗi; candidate qua Docker và bước rà chất lượng để trở thành dữ liệu synthetic train.

Ở hàng cuối, mô hình chẩn đoán 3B học dữ liệu thật, hoặc dữ liệu thật cộng synthetic. Validation dùng để chọn checkpoint; tập test thật được dành cho đánh giá cuối.

Hai vai trò cần tách rõ là 7B sinh dữ liệu và 3B học chẩn đoán. Synthetic không được sinh từ seed của validation hoặc test, và không được đưa vào hai tập đánh giá đó.

## Slide 6 — AIDev và SWE-bench cung cấp gì?

**Thời gian: 03:20–04:00 · 40 giây**

Dự án đã sử dụng hai nguồn là AIDev và SWE-bench, nhưng vai trò hiện tại của chúng khác nhau.

AIDev cung cấp thông tin ở mức pull request, repository và provenance. Nguồn này được dùng ở W1 và các đợt phát triển ban đầu để thử pipeline. Thông tin công cụ tạo PR chưa đủ để kết luận ai gây ra lỗi.

SWE-bench có base revision, patch sửa, test patch và danh sách test cần chuyển từ fail sang pass hoặc cần giữ pass. Các thành phần này hỗ trợ tái hiện có đối chứng.

Tập 250 mẫu real dùng cho pilot SFT hiện tại lấy từ SWE-bench. Tuy có patch sửa tham chiếu, em vẫn phải xây nhãn nguyên nhân và vị trí cho bài toán chẩn đoán; đó không phải các nhãn đã có sẵn hoàn toàn từ nguồn.

## Slide 7 — Case, repo và lượt sinh

**Thời gian: 04:00–04:35 · 35 giây**

Trước khi nói về quy mô, em làm rõ đơn vị dữ liệu.

Một case là một tình huống lỗi gắn với một repository, một revision và các test mục tiêu. Một repository có thể đóng góp nhiều case. Nhiều test fail cũng có thể cùng bắt nguồn từ một lỗi.

Một seed có thể có nhiều lượt sinh và các output có thể trùng nhau. Ba lần chạy fail ổn định chỉ là ba phép kiểm chứng của cùng candidate, không tạo thêm ba mẫu độc lập.

Vì vậy, em tách số case nguồn, lượt sinh, lượt đạt thực thi và candidate khác byte. Các con số này phản ánh những bước khác nhau của pipeline.

## Slide 8 — Tái hiện lỗi thật

**Thời gian: 04:35–05:30 · 55 giây**

[Chỉ hai hàng base và base cộng repair trong bảng.]

Với SWE-bench, em dùng cùng một test patch trên hai phiên bản. Phiên bản thứ nhất là base chưa sửa; phiên bản thứ hai là base đã áp repair patch tham chiếu.

Điều kiện mong muốn là test cần sửa thất bại trên base và pass trên bản fixed. Những test cần giữ pass vẫn phải pass. Nhờ dùng cùng test và môi trường đã ghim, kết quả có cơ sở để so sánh.

Pipeline lưu source, test và image hash để tránh dùng nhầm phiên bản. Build fail, collection error, timeout và lỗi ứng dụng được ghi riêng. Ví dụ, thiếu dependency của harness chưa thể tự trở thành nhãn lỗi của chương trình.

Các log thu được là log tái hiện local. Em không gọi chúng là log CI lịch sử, và cũng không khẳng định đã tái dựng toàn bộ môi trường benchmark chính thức.

## Slide 9 — Sàng lọc và kiểm tra chất lượng

**Thời gian: 05:30–06:15 · 45 giây**

Sau bước tái hiện, dữ liệu còn phải qua sàng lọc và rà chất lượng.

Trước hết cần có nguồn, revision, test mục tiêu và bằng chứng giấy phép rõ ràng. Sau đó đối chiếu code, log và patch để kiểm tra nguyên nhân đề xuất có phù hợp với hành vi quan sát được không.

Các trường hợp thiếu evidence, hash không khớp, lỗi môi trường chưa giải quyết hoặc trùng lặp phải được xử lý riêng. Chỉ khác byte chưa chắc đã khác cơ chế lỗi.

Một yêu cầu xuyên suốt là tách input khỏi thông tin đáp án. Nhãn, explanation tham chiếu và metadata phép sinh không được lọt vào input chẩn đoán. Qua được runner mới xác nhận một điều kiện thực thi, chưa tự xác nhận chất lượng nhãn hay tính phù hợp để train.

## Slide 10 — Dataset pilot đã khóa

**Thời gian: 06:15–07:10 · 55 giây**

[Chỉ bảng chia tập; không đọc lại từng ô.]

Dataset pilot đã khóa gồm 250 tình huống real silver. Trong đó có 175 mẫu train, 37 validation và 38 test. Ngoài ra có 101 mẫu synthetic, chỉ dùng trong train.

M2 học 175 mẫu real. M5 học cùng 175 mẫu real này cộng 101 synthetic, tức 276 mẫu. Hai cấu hình dùng chung validation và test để so sánh trên cùng các tình huống.

Việc chia tập theo repository và nhóm liên quan giúp hạn chế các mẫu gần nhau nằm ở nhiều tập. Tuy vậy, dữ liệu train còn tập trung mạnh vào SymPy và chỉ có hai nhóm nguyên nhân, nên độ phủ vẫn hạn chế.

Mục tiêu ban đầu là 175 synthetic, hiện còn thiếu 74. Em trình bày rõ pilot riêng dùng 101 mẫu hiện có, không coi đó là đã hoàn tất mục tiêu dữ liệu ban đầu.

## Slide 11 — Sinh candidate bằng 7B

**Thời gian: 07:10–08:00 · 50 giây**

Phần sinh dùng generator 7B trên bản seed đã pass của case train. Giao thức hiện tại giới hạn phép sửa ở một edit site Python đã xác định trước bằng phân tích tĩnh.

Model trả về đường dẫn, mã site, một dòng replacement và explanation về phép sinh. Renderer áp dòng thay thế tại vị trí được phép, giữ indentation và các test đã ghim.

Giao thức hiện tại không yêu cầu generator tự gán nhãn nguyên nhân chẩn đoán. Explanation của generator cũng chỉ là thông tin đề xuất, không phải đáp án chuẩn và không đi vào input của 3B.

Nếu output sai cấu trúc, sửa sai vị trí, timeout hoặc không làm test fail, lượt đó vẫn được lưu trong tổng lượt. Pipeline không sửa response hoặc test để biến một lần sinh không đạt thành mẫu đạt.

## Slide 12 — Kiểm chứng candidate trong Docker

**Thời gian: 08:00–08:50 · 50 giây**

[Chỉ lần lượt ba ô PASS, FAIL ba lần, PASS.]

Vòng kiểm chứng bắt đầu bằng baseline pass để xác nhận passing seed và môi trường đang dùng. Sau đó cùng một candidate được chạy ba lần với cùng test, yêu cầu fail ổn định theo policy. Cuối cùng khôi phục seed và kiểm tra restoration pass.

Các candidate chỉ được thực thi trong Docker cô lập, không mạng, không đặc quyền, có giới hạn tài nguyên và timeout. Candidate không chạy trên host.

Vòng này xác nhận regression quan sát được trong môi trường đã ghim. Sau đó vẫn cần rà tuân thủ prompt, nguyên nhân, tính hợp lý và trùng lặp. Một candidate có thể làm test fail nhưng vẫn không phù hợp để đưa vào tập train.

Tiếp theo em làm rõ nhãn nguyên nhân được xây từ những bằng chứng này như thế nào.

## Slide 13 — Nhãn silver được xây thế nào?

**Thời gian: 08:50–09:45 · 55 giây**

Taxonomy hiện tại gồm bốn nhóm nguyên nhân: syntax, dependency hoặc configuration, API hoặc type, và logic hoặc value. Khi chưa đủ bằng chứng, mô hình có thể trả unknown.

Nhãn không được suy trực tiếp từ tên exception. Một ValueError có thể là hậu quả của logic điều khiển sai, còn một lỗi được phát hiện trong test không có nghĩa test là nơi gây ra lỗi.

Việc xây nhãn cần nối thay đổi code với hành vi trung gian và log quan sát được. Repair patch là một nguồn bằng chứng, nhưng không phải mọi dòng trong patch đều là causal location.

Các nhãn hiện tại được gọi là silver vì đã có phân tích evidence và lưu giới hạn, nhưng chưa được xác nhận thành chuyên gia gold. Trong pilot, em sử dụng silver có ghi rõ mức bằng chứng này, không trình bày đó là một bộ nhãn gold hoàn chỉnh.

## Slide 14 — Ví dụ real: metadata của marshmallow

**Thời gian: 09:45–11:00 · 75 giây**

[Chỉ code bên trái, giá trị quan sát, rồi target bên phải.]

Đây là một mẫu real train từ marshmallow, để thấy rõ một cặp input và target thực tế.

Trong hàm khởi tạo Field, code nhận các keyword còn lại qua hai dấu sao metadata, rồi gán mapping đó vào thuộc tính self metadata. Khi caller truyền một tham số tên metadata chứa description và widget, cấu trúc thu được bị lồng thêm một cấp metadata.

Test yêu cầu field metadata chứa trực tiếp hai khóa description và widget. Log assertion cho thấy giá trị thực tế lại là một dictionary có khóa metadata ở ngoài. Như vậy, vấn đề nằm ở cách constructor tiếp nhận giao diện tham số, không chỉ ở dòng assert phát hiện sai khác.

Reference silver đề xuất nhãn API/type và vị trí là file fields.py của marshmallow, hàm khởi tạo của lớp Field. Trên slide hiển thị hai trường target; explanation đầy đủ được giữ trong snapshot và ghi chú.

Code và log trên đây là phần trích để trình bày. Trong dữ liệu thực tế, input vẫn tách riêng khỏi reference và patch sửa. Ví dụ này cũng cho thấy vì sao có patch tham chiếu vẫn cần phân tích thêm để xây nhãn dùng cho SFT.

## Slide 15 — Ví dụ synthetic: broadcast trong pvlib

**Thời gian: 11:00–12:15 · 75 giây**

[Chỉ từ not ở seed và vị trí bị bỏ trong candidate.]

Ví dụ thứ hai là một mẫu synthetic train từ pvlib. Đây là lỗi mới do phép sinh trên bản seed đã pass, không phải lỗi lịch sử gốc của case nguồn.

Ở bản seed, khi tham số áp dụng cho toàn hệ thống và giá trị không phải tuple, code nhân rộng scalar thành một tuple có số phần tử bằng số array. Generator 7B bỏ từ not trong điều kiện này.

Sau phép sửa, một scalar không đi vào nhánh broadcast nữa. Nó được đóng thành tuple một phần tử, rồi đi đến bước so chiều dài với số array. Với hệ thống có nhiều array, điều kiện không khớp và code phát ValueError về length mismatch.

Python ở đây vẫn hợp cú pháp. Reference silver là logic/value tại hàm validate per array, vì nguyên nhân là điều kiện điều khiển broadcast bị đảo. ValueError chỉ là biểu hiện ở bước kiểm tra sau đó.

Diff trên slide dùng để giải thích phép sinh cho người nghe. Trong pilot chẩn đoán, vị trí edit và explanation của generator không được đưa vào input để tránh gợi đáp án. Mẫu vẫn phải qua baseline, ba lần fail ổn định, restoration và rà chất lượng trước khi được giữ.

## Slide 16 — Các cấu hình M0 đến M5

**Thời gian: 12:15–13:00 · 45 giây**

Các mã M0 đến M5 biểu diễn các cấu hình đối chứng, không phải sáu kích thước model khác nhau.

M0 là TF-IDF cộng Logistic Regression, chỉ làm phân loại. M1 là base 3B prompt-only, không cập nhật trọng số; M1-P2 là biến thể prompt format được báo riêng.

M2 dùng QLoRA trên real train. M5 cũng dùng cùng base nhưng học real cộng synthetic đã rà. Hai adapter được khởi tạo độc lập, M5 không học tiếp từ M2.

M3 dự kiến đối chứng xử lý mất cân bằng; M4 dự kiến dùng synthetic chưa qua đầy đủ bước rà và lọc nhãn. Hai cấu hình này chưa chạy. Vì vậy, thử nghiệm hiện tại chưa cô lập hết ảnh hưởng của phân bố lớp và chất lượng curation.

## Slide 17 — Cấu hình SFT bằng QLoRA

**Thời gian: 13:00–13:55 · 55 giây**

Về cấu hình học, base 3B dùng NF4 và double quantization, còn tính toán dùng BF16. LoRA có rank 16, alpha 32 và dropout không phẩy không năm.

Batch trên một GPU là một mẫu, tích lũy gradient qua tám microbatch. Context là 2.048 token và ngân sách output tối đa 384 token. Seed được giữ cố định và loss chỉ tính phần target.

Các cấu hình này giúp triển khai SFT trên GPU local trong phạm vi tài nguyên hiện có. Em chưa có đối chứng để khẳng định đây là cấu hình tối ưu.

Một điểm cần chú ý khi so sánh là M5 có nhiều mẫu hơn M2. Do đó, cùng số epoch không có nghĩa cùng số updates, số token hay cùng chi phí tính toán. Các đại lượng này được lưu để giải trình, thay vì mặc định hai lượt học hoàn toàn ngang nhau về compute.

## Slide 18 — Continuation và checkpoint được chọn

**Thời gian: 13:55–14:45 · 50 giây**

[Chỉ dòng đích tổng, sau đó chỉ dòng checkpoint được chọn.]

Ban đầu hai model đã có parent ở step 104. Phần continuation tiếp tục M2 đến 220 updates và M5 đến 350 updates, tương ứng tổng mười epoch ở mỗi cấu hình.

Quá trình này giữ phần đã học và trạng thái optimizer, không khởi tạo lại adapter từ base. Phần học tiếp dùng lịch learning rate riêng đã chốt.

Tuy nhiên, model dùng để test không mặc định là checkpoint cuối. Em chọn theo joint trên validation, hòa thì chọn checkpoint sớm hơn. Các mốc học tiếp không tăng joint, nên cả hai vẫn chọn parent104.

Vì vậy, cần phân biệt ngân sách đã tiêu là mười epoch với adapter thực sự được chọn, tương ứng khoảng bốn phẩy bảy ba epoch của M2 và hai phẩy chín chín của M5. Chi phí học tiếp vẫn được tính dù không chọn adapter cuối.

## Slide 19 — Các phần đã hoàn thành

**Thời gian: 14:45–15:20 · 35 giây**

Nhìn theo tiến độ toàn dự án, W1 đã có pipeline trên properr và hai trong ba lượt 7B đạt kiểm chứng thực thi. Các đợt mở rộng sau đó thử 17 case trên 10 repository, giúp mở rộng harness và quy trình rà dữ liệu.

Tiếp theo là thu thập, sàng lọc và khóa dataset pilot gồm 250 real cùng 101 synthetic, rồi thực hiện baseline, hai SFT, continuation và đánh giá cuối.

Dự án cũng có kiểm thử phần mềm và lưu log, hash để truy vết. Những số này phải tách khỏi số mẫu ML; các cohort development trước đó cũng không cộng vào dataset SFT hiện tại.

## Slide 20 — Các chỉ số đánh giá

**Thời gian: 15:20–16:20 · 60 giây**

Trước khi đọc bảng kết quả, em giải thích các chỉ số chính.

Accuracy là tỷ lệ dự đoán đúng loại lỗi. Macro-F1 là trung bình F1 của bốn lớp cố định, mỗi lớp có cùng trọng số. Trong scorer hiện tại, lớp không có support vẫn đóng góp không, nên không thể đọc Macro-F1 như một phiên bản khác của accuracy.

File Top-1 yêu cầu file đầu tiên khớp reference. Hàm Top-1 yêu cầu cặp file và hàm đầu tiên khớp. Top-5 xét trong tối đa năm vị trí đầu.

Joint, hay đúng loại cộng hàm, yêu cầu cả hai điều kiện đúng trên cùng một mẫu. Đây không phải tích của hai tỷ lệ riêng. Các output sai JSON hoặc schema vẫn nằm trong mẫu số.

Scorer hiện còn có điều kiện reference phải nằm trong phần code đã truy xuất để tính credit định vị. Ở test, reference hàm có trong context của 12 trên 38 mẫu. Vì vậy kết quả định vị cần được đọc cùng hạn chế của retrieval và cách chấm toàn pipeline.

## Slide 21 — Kết quả validation trên 37 real

**Thời gian: 16:20–17:05 · 45 giây**

[Chỉ M1-P2, sau đó so hai hàng M2 và M5.]

Bảng này là validation trên cùng 37 mẫu real. M2 có Macro-F1 khoảng không phẩy ba năm hai; M5 khoảng không phẩy bốn không sáu. Joint lần lượt là bốn và năm mẫu đúng trên 37.

M1-P2 phải được ghi riêng vì dùng prompt mới để yêu cầu JSON trực tiếp. M1 cũ có 37 response chứa JSON trong Markdown, nhưng parser strict từ chối toàn bộ. Do đó, điểm không của M1 cũ không có nghĩa toàn bộ nội dung chẩn đoán đều sai.

P2 giữ nguyên user code và log, không train lại trọng số. Sự thay đổi format này là một yếu tố cần giải trình khi so với SFT. Kết quả M1-P2 không được dùng để chọn lại checkpoint M2 hoặc M5.

## Slide 22 — Final test trên cùng 38 real

**Thời gian: 17:05–18:05 · 60 giây**

[Chỉ hai hàng M2/M5; nhấn joint bằng nhau, không đọc toàn bảng.]

Đây là kết quả cuối trên cùng 38 mẫu real silver. Cấu hình, prompt riêng của từng model và checkpoint đã được khóa trước khi chấm.

M2 dự đoán đúng loại 22 mẫu, tương ứng khoảng 57,89 phần trăm. M5 đúng 24 mẫu, tương ứng 63,16 phần trăm. Macro-F1 tăng từ khoảng không phẩy ba một ba lên không phẩy ba ba tám.

Về định vị, M5 đúng hàm bảy mẫu so với sáu của M2, nhưng số đúng file giảm từ 18 xuống 16. Joint của cả hai cùng là bốn trên 38 mẫu. M1-P2 có tám output invalid do Markdown; parser vẫn giữ nguyên, không tự bỏ fence để cứu điểm.

Tập test có 21 mẫu thuộc lớp phổ biến nhất. Chỉ luôn đoán lớp đó cũng đạt khoảng 55,26 phần trăm accuracy, nên em không lấy accuracy tổng làm kết luận duy nhất. Phân tích tiếp theo cần nhìn vào từng mẫu và từng nhóm lỗi.

## Slide 23 — M5 hơn và kém M2 ở đâu?

**Thời gian: 18:05–19:05 · 60 giây**

Theo từng mẫu, về phân loại có bốn mẫu chỉ M5 đúng và hai mẫu chỉ M2 đúng. Về hàm, M5 thắng hai và thua một. Nhưng về joint, mỗi model chỉ thắng model còn lại một mẫu, nên tổng joint không tăng.

Phần tăng phân loại tập trung ở Pylint. Trên Pytest, accuracy không đổi nhưng joint của M5 giảm. Như vậy, bổ sung synthetic chưa tạo cải thiện đồng đều ở mọi nhiệm vụ và repository.

Ngoài model, còn hai giới hạn lớn. Thứ nhất, reference hàm vắng khỏi context ở 26 trên 38 mẫu test. Thứ hai, train chỉ có hai lớp nguyên nhân; cả hai SFT đều không nhận đúng các mẫu dependency hoặc configuration của test.

Nhãn vẫn là silver, chỉ có một seed, và các đối chứng M3, M4 chưa chạy. Em chỉ kết luận có cải thiện nhẹ về phân loại trong pilot này, chưa khẳng định synthetic có lợi tổng quát hoặc xác định một mẫu synthetic cụ thể đã gây ra cải thiện.

## Slide 24 — Kết luận giữa kỳ và hướng tiếp theo

**Thời gian: 19:05–20:00 · 55 giây**

Đến giữa kỳ, đề tài đã đi được một vòng từ dữ liệu nguồn đến tạo dataset, SFT và đánh giá cuối có bằng chứng truy vết. Phần này cho thấy hướng triển khai là khả thi, đồng thời làm rõ các điểm nghẽn của dữ liệu và cách chẩn đoán.

Kết quả hiện tại ghi nhận M5 tăng nhẹ về phân loại so với M2, nhưng joint chưa tăng. Vì vậy, ưu tiên tiếp theo của em là độ nhất quán nhãn, retrieval và độ phủ lớp, repository trên development, sau đó bổ sung đối chứng và nhiều seed.

Em sẽ không dùng lại tập test đã mở để chỉnh prompt hoặc nhãn rồi báo như một đánh giá độc lập mới. Những thay đổi tiếp theo cần có protocol và cách đánh giá phù hợp.

Em xin kết thúc phần trình bày. Em cảm ơn thầy cô đã lắng nghe và mong nhận được góp ý cho hướng phát triển tiếp theo.

## Slide 25 — Dự phòng: taxonomy và nguồn nhãn

**Thời gian: Dự phòng — ngoài thời lượng 20 phút**

[Dự phòng, chỉ dùng khi được hỏi về taxonomy hoặc nguồn nhãn.]

Bốn nhóm trong bảng là taxonomy của bài toán chẩn đoán, không phải nhãn nguyên nhân có sẵn hoàn toàn trong SWE-bench. Nguồn cung cấp repair patch, test patch và F2P, P2P; phần loại lỗi, causal file và hàm cần được phân tích từ code, log và patch.

Ví dụ, tên exception chỉ mô tả biểu hiện. Một ValueError có thể xuất phát từ điều kiện xử lý sai, như ví dụ pvlib. Khi chưa đủ evidence, cần ghi phần chưa xác định hoặc unknown. Nhãn silver có nguồn và giới hạn; chưa tự chuyển thành expert gold vì đã tái hiện thành công.

## Slide 26 — Dự phòng: prompt và parser M1

**Thời gian: Dự phòng — ngoài thời lượng 20 phút**

[Dự phòng, chỉ dùng khi được hỏi vì sao M1 cũ bằng không hoặc prompt khác nhau.]

M1 cũ có JSON bên trong Markdown ở cả 37 response validation, nhưng parser yêu cầu JSON trực tiếp nên từ chối toàn bộ. Em giữ nguyên kết quả và raw output đó.

Lượt M1-P2 thay đúng hai đoạn system prompt để yêu cầu JSON rõ hơn, giữ nguyên user code, log và ngân sách, không cập nhật trọng số. Lượt mới có một invalid trên validation và tám invalid trên test.

Vì vậy, em ghi M1-P2 là prompt mới. Em không mô tả mọi model dùng cùng prompt, không sửa parser hoặc bỏ Markdown sau khi nhìn kết quả, và không quy toàn bộ chênh lệch với SFT cho năng lực chẩn đoán.

## Slide 27 — Dự phòng: kết quả theo lớp và repo

**Thời gian: Dự phòng — ngoài thời lượng 20 phút**

[Dự phòng, chỉ dùng khi được hỏi về lệch lớp hoặc kết quả theo repository.]

Test gồm 21 logic/value, chín API/type và tám dependency/configuration; không có syntax. M5 nhận đúng nhiều hơn ở logic/value, từ 15 lên 18 mẫu, nhưng API/type giảm từ bảy xuống sáu. Cả hai model không nhận đúng mẫu dependency/configuration nào.

Kết quả này cần xem cùng phân bố train: synthetic chủ yếu bổ sung logic/value và không bổ sung hai lớp còn thiếu. Theo repository, phần tăng accuracy nằm ở Pylint; Flask và Pytest có accuracy bằng nhau giữa M2, M5. Đây là lý do em báo từng lớp, từng repo thay vì chỉ một con số accuracy chung.

## Slide 28 — Dự phòng: cấu hình và chi phí

**Thời gian: Dự phòng — ngoài thời lượng 20 phút**

[Dự phòng, chỉ dùng khi được hỏi về thời gian học hoặc công bằng ngân sách.]

Tổng wall time của parent cộng continuation là 4.387 giây ở M2 và 6.324 giây ở M5. Các số này tính cả phần học tiếp dù cuối cùng vẫn chọn checkpoint parent104; validation lồng nhau không được cộng hai lần.

Hai model cùng tiêu ngân sách mười epoch nhưng M5 có nhiều mẫu, nhiều updates và token hơn. Vì vậy, em chưa coi đó là một so sánh đã kiểm soát hoàn toàn compute. Wall time cũng không phải số phép tính GPU hoặc chi phí tiền.

Nếu muốn tách ảnh hưởng số lượng dữ liệu khỏi ngân sách học, cần thêm đối chứng cùng updates hoặc token theo protocol riêng, thay vì dùng kết quả test hiện tại để điều chỉnh lại thí nghiệm.
