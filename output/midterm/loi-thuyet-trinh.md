# Lời thuyết trình bảo vệ giữa kỳ

**Cách dùng:** Đọc các đoạn văn; phần trong ngoặc vuông là nhắc thao tác, không đọc thành tiếng. Mốc thời gian là mục tiêu từ bộ slide, chưa phải thời lượng nói thử đã đo. Có thể dừng ở bảng/sơ đồ; bốn slide dự phòng chỉ dùng khi được hỏi.

## Slide 1 — DỮ LIỆU TỔNG HỢP CHO CHẨN ĐOÁN LỖI CI

**Thời gian: 00:00–00:25 · 25 giây**

[Nhìn hội đồng, chưa cần chỉ vào nội dung slide.]

Em xin phép trình bày tiến độ giữa kỳ của đề tài sinh dữ liệu tổng hợp có kiểm chứng, hỗ trợ chẩn đoán lỗi CI.



## Slide 2 — Mục tiêu và câu hỏi nghiên cứu

**Thời gian: 00:25–01:05 · 40 giây**

Trong bài này, em sẽ đi từ bài toán và cách xây dữ liệu, đến phương pháp huấn luyện và kết quả đã có. Để mà làm rõ dữ liệu đã được tạo, kiểm tra và sử dụng như thế nào, cũng như những giới hạn của kết quả hiện tại.

Khi một lần kiểm tra CI fail, log thường báo lỗi xuất hiện ở đâu, nhưng chưa chắc đó là nơi gây ra lỗi. Bình thường thì dev vẫn cần đọc code và đối chiếu các dấu hiệu để tìm nguyên nhân.

Bài toán của em là cho mô hình đọc log cùng code liên quan, rồi trả lời ba nội dung: loại nguyên nhân kỹ thuật, vị trí file và hàm gây lỗi, cùng một giải thích ngắn.

Câu hỏi nghiên cứu chính là: nếu bổ sung dữ liệu lỗi tổng hợp đã kiểm chứng vào dữ liệu thật, vào cùng một mô hình thì có chẩn đoán tốt hơn không? Em dùng một cấu hình chỉ học dữ liệu thật và một cấu hình học dữ liệu thật cộng với dữ liệu synthetic để so sánh. Phần này em mới train kiểu pilot để xem tính khả thi của nó trước.

## Slide 3 — SFT trong bài toán

**Thời gian: 01:05–01:50 · 45 giây**

SFT trong bài là một mô hình đã được pretrained. Em sử dụng Qwen Coder 3B làm mô hình nền.

Mỗi mẫu train gồm một đầu vào là log và code, cùng một câu trả lời mong muốn ở dạng JSON. Qua các mẫu này, mô hình học cách chuyển những cái log thực thi thành câu trả lời dạng chẩn đoán.

Phần được cập nhật là adapter QLoRA, còn weight nền của model được giữ cố định. Loss tính dựa trên phần câu trả lời, nhưng mà ở đầu vào mô hình vẫn sẽ  đọc toàn bộ context để dự đoán các token của câu trả lời.

Đây là 1 cái ví dụ của input và output

## Slide 4 — Đầu vào và đầu ra chẩn đoán

**Thời gian: 01:50–02:30 · 40 giây**

[Chỉ cột input trước, sau đó chỉ các trường JSON bên phải.]

Bên trái là dữ liệu mô hình được phép xem là: log của phiên bản đang lỗi và phần code liên quan do bước truy xuất lựa chọn. Mô hình không tự đọc toàn bộ repository.

Bên phải là cấu trúc câu trả lời. Cái field cause type là loại nguyên nhân; locations là danh sách các cặp file và hàm; explanation là lời giải thích cơ chế lỗi. Model khi định vị cần đúng cả file và hàm, không chỉ nêu một tên hàm chung.

| Thuật ngữ | Trong dự án này là gì? |
|---|---|
| **Repair patch** | Bản **diff sửa lỗi tham chiếu** từ SWE-bench: thể hiện những dòng được thêm/xóa/sửa để chuyển bản lỗi thành bản đã sửa. |
| **Reference** | **Đáp án chẩn đoán dùng để train/chấm**: loại nguyên nhân, vị trí file/hàm và explanation. Reference hiện tại của ta là **silver**, chưa phải expert gold. |
| **Assessment** | **Hồ sơ phân tích để xây và rà nhãn**: bằng chứng code/log/patch, nhận định nguyên nhân, độ chắc chắn, giới hạn và kiến nghị sử dụng mẫu. Nó giải thích *vì sao đề xuất reference như vậy*. |
| **Edit-site** | **Vị trí cho phép 7B sửa code khi sinh synthetic**, thường được định danh bằng `site_id`. Metadata này cho biết phép sửa diễn ra ở đâu. |

Repair patch, nhãn tham chiếu và assessment được giữ riêng khỏi input. Nếu đưa các thông tin này vào input thì mô hình có thể nhìn thấy đáp án thay vì thực sự chẩn đoán.

## Slide 5 — Kiến trúc pipeline

**Thời gian: 02:30–03:20 · 50 giây**

[Đọc sơ đồ từ hàng trên xuống; chỉ vào 7B và 3B khi phân biệt vai trò.]

Sơ đồ này tóm tắt luồng hiện tại. Đầu tiên thì, dữ liệu nguồn sẽ được tái hiện để xác nhận hành vi trước và sau khi sửa, sau đó đi xây mẫu real silver và chia theo repository.

Ở hàng thứ hai, chỉ bản đã pass của case train mới được dùng làm seed. Generator 7B tạo candidate gây lỗi; candidate được cho vào Docker và bước rà chất lượng để trở thành mẫu synthetic train.

Ở hàng cuối, mô hình chẩn đoán 3B học dữ liệu thật, hoặc dữ liệu thật cộng synthetic. Validation dùng để chọn checkpoint; tập test  dành cho đánh giá cuối. Cả validation với test dùng mẫu real,

Hai vai trò cần tách rõ là 7B sinh dữ liệu và 3B học chẩn đoán. Những cái mẫu Synthetic không được sinh từ seed của validation hoặc test, và không được đưa vào hai tập đánh giá đó.

## Slide 6 — AIDev và SWE-bench

**Thời gian: 03:20–04:00 · 40 giây**

Dự án đã sử dụng hai nguồn là AIDev và SWE-bench, nhưng vai trò hiện tại của 2 cái thằng này nó hơi khác nhau.

AIDev cung cấp thông tin ở mức pull request, repository và provenance. Nguồn này em dùng ở đợt phát triển ban đầu để thử pipeline.

SWE-bench có base revision, patch sửa, test patch và danh sách test cần chuyển từ fail sang pass hoặc cần giữ pass. Các thành phần này hỗ trợ tái hiện có đối chứng.
Tập 250 mẫu real dùng cho pilot SFT hiện tại lấy từ SWE-bench. Tuy có patch sửa tham chiếu, em vẫn phải xây nhãn nguyên nhân và vị trí cho bài toán chẩn đoán; mấy cái này nguồn nó chưa có


Provenance là “lý lịch của dữ liệu”: thông tin để truy ngược một mẫu về nguồn và quá trình tạo ra nó.

Trong dự án, provenance trả lời:
- Mẫu lấy từ dataset nào, case/PR nào, repository và commit nào?
- Đã tái hiện bằng test và môi trường nào, log/hash nằm ở đâu?
- Nếu là synthetic: sinh từ seed nào, model nào tạo, đã sửa gì?
- Nhãn do nguồn cung cấp hay do bước phân tích evidence đề xuất?
Provenance giúp truy vết, không tự chứng minh ai gây lỗi. Người/công cụ tạo PR có thể đang sửa lỗi đã tồn tại từ trước.


Em đã dùng AIDev ở W1 và các đợt development để xây dựng, kiểm tra pipeline. Sang pilot SFT, em ưu tiên SWE-bench vì nguồn này có revision, repair patch, test patch và các test FAIL_TO_PASS, PASS_TO_PASS, thuận lợi hơn cho việc tái hiện trước và sau sửa theo cùng một quy trình.

AIDev cung cấp thông tin PR và provenance, nhưng một PR chưa tự trở thành một mẫu lỗi có đủ code, log tái hiện và nhãn nguyên nhân cho bài toán này. Muốn đưa vào SFT vẫn phải qua các bước xác minh đó.

Vì vậy, tập 250 real hiện tại chỉ dùng SWE-bench để giữ quy trình thu thập nhất quán. AIDev đã đóng góp vào phần development; việc bổ sung vào tập SFT sẽ cần một đợt sàng lọc và kiểm chứng riêng.

SWE-bench cũng chưa cung cấp sẵn toàn bộ nhãn chẩn đoán của em. Loại nguyên nhân, causal file/hàm và explanation vẫn phải được phân tích, hiện ở mức silver.

1.Revision — phiên bản mã nguồn

Xác định chính xác phiên bản code được dùng, thường bằng commit hash. Nhờ vậy, lần chạy sau lấy lại đúng code thay vì dùng bản mới nhất đã thay đổi.

Trong tái hiện một case, ta bắt đầu từ base revision, tức phiên bản trước khi áp bản sửa.

2.Repair patch — bản thay đổi để sửa lỗi

Là diff mô tả những dòng code cần thêm, xóa hoặc thay thế để sửa vấn đề. Áp repair patch lên base để tạo bản fixed.

3.Test patch — bản thay đổi của bộ test

Chứa các test được thêm hoặc sửa để kiểm tra vấn đề. Một test mới có thể chưa tồn tại ở base, nên ta áp cùng test patch lên cả base và fixed để so sánh công bằng:
- Base kiểm tra: code gốc + test patch.
- Fixed kiểm tra: code gốc + repair patch + test patch.

- - 
| Nhóm | Viết đầy đủ | Trên base | Trên fixed | Ý nghĩa |
|---|---|---|---|---|
| **F2P** | FAIL_TO_PASS | Fail | Pass | Kiểm tra vấn đề đã được sửa |
| **P2P** | PASS_TO_PASS | Pass | Pass | Kiểm tra hành vi vốn đúng vẫn được giữ |


Ví dụ: sửa lỗi tính tổng thì test bắt lỗi tính tổng thuộc F2P. Một test kiểm tra chức năng khác đang hoạt động đúng có thể thuộc P2P.

Các danh sách F2P/P2P là kỳ vọng từ nguồn. Ta vẫn phải chạy và đọc log để xác nhận; chúng không phải nhãn nguyên nhân như API/type hay logic/value.


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

Điều kiện mong muốn là test cần sửa thất bại trên base và pass trên bản fixed. Những test cần giữ pass vẫn phải pass. Nhờ dùng cùng test và môi trường đã ghim, kết quả có cơ sở để so sánh. hơn

Pipeline lưu source, test và image hash để tránh dùng nhầm phiên bản. Build fail, collection error, timeout. Ví dụ, thiếu dependency của harness chưa thể tự trở thành nhãn lỗi của chương trình.

Các log thu được là log tái hiện local. Em không gọi chúng là log CI lịch sử, và cũng không khẳng định đã tái dựng toàn bộ môi trường benchmark chính thức.

## Slide 9 — Sàng lọc và kiểm tra chất lượng

**Thời gian: 05:30–06:15 · 45 giây**

Sau bước tái hiện, dữ liệu còn phải qua sàng lọc và rà chất lượng.

Trước hết cần có nguồn, revision, test mục tiêu. Sau đó đối chiếu code, log và patch để kiểm tra nguyên nhân đề xuất có phù hợp với hành vi quan sát được không.

Các trường hợp thiếu evidence, hash không khớp, lỗi môi trường chưa giải quyết hoặc trùng lặp sẽ bị loại. Chỉ khác byte chưa chắc đã khác cơ chế lỗi.

Một cái yêu cầu rõ ràng là tách input khỏi thông tin đáp án. Nhãn, explanation tham chiếu và metadata phép sinh không được lọt vào input chẩn đoán.

## Slide 10 — Dataset pilot đã khóa

**Thời gian: 06:15–07:10 · 55 giây**

[Chỉ bảng chia tập; không đọc lại từng ô.]

Dataset pilot gồm 250 case real. Trong đó có 175 mẫu train, 37 validation và 38 test. Ngoài ra có 101 mẫu synthetic, chỉ dùng trong quá trình train.

M2 học 175 mẫu real. M5 học cùng 175 mẫu real này cộng 101 synthetic, tức 276 mẫu. Hai cấu hình dùng chung validation và test để so sánh trên cùng các tình huống.

Việc chia tập theo repository và nhóm liên quan giúp hạn chế các mẫu gần nhau nằm ở nhiều tập. Mà, dữ liệu train còn tập trung mạnh vào 1 số repo (SymPy) và chỉ có hai nhóm nguyên nhân, nên độ phủ vẫn hạn chế.


## Slide 11 — Sinh candidate bằng 7B

**Thời gian: 07:10–08:00 · 50 giây**

Phần sinh dùng generator 7B trên bản seed đã pass của case train. Cái giao thức hiện tại giới hạn phép sửa ở một edit site Python đã xác định trước bằng phân tích tĩnh.

Thì Edit site là một vị trí trong code được phép sửa “Xác định tĩnh” nghĩa là hệ thống đọc cấu trúc code để xác định trước các vị trí có thể sửa, không cần chạy code để tìm chúng. Mỗi vị trí có một mã định danh, gọi là site_id.

Model trả về đường dẫn, mã site, một dòng replacement và explanation về phép sinh. 
| Trường | Nghĩa |
|---|---|
| `replacement` | Đoạn code thay thế tại vị trí đó |
| `explanation` | Lời giải thích của 7B về thay đổi |

Explanation chỉ là cái con LLM nó giải thích; phải chạy test mới biết thay đổi có thực sự gây lỗi hay không.

Renderer áp dòng thay thế tại vị trí được phép, giữ indentation và các test đã ghim.

Nói chung là, Em lấy phiên bản đã vượt qua test của các case thuộc tập train làm điểm xuất phát. Hệ thống xác định trước các vị trí Python được phép sửa, sau đó yêu cầu model 7B chọn một vị trí và đề xuất code thay thế. Chương trình áp thay đổi đó, giữ nguyên bộ test và lưu câu trả lời gốc. Bản code mới được gọi là candidate và sẽ được đưa vào Docker để kiểm tra xem có thực sự gây lỗi ổn định hay không

Giao thức hiện tại không yêu cầu generator tự gán nhãn nguyên nhân chẩn đoán. Explanation của generator cũng chỉ là thông tin đề xuất, không phải đáp án chuẩn và không đi vào input của 3B.

## Slide 12 — Kiểm chứng candidate trong Docker

Sau khi có candidate, em kiểm chứng trong Docker theo ba bước.

Đầu tiên là baseline pass: chạy bộ test trên code trước khi áp thay đổi. Code nó phải vượt qua test để xác nhận điểm xuất phát nó đang hoạt động.

Tiếp theo, áp thay đổi do generator 7B đề xuất và chạy lại cùng bộ test ba lần. Candidate phải gây lỗi ổn định qua cả ba lần, để giảm khả năng kết quả nó kiểu chỉ do lỗi ngẫu nhiên. Cái này là chạy lại cùng một candidate, không phải sinh ba candidate khác nhau.

Cuối cùng là restoration pass: gỡ thay đổi, khôi phục code ban đầu và chạy test lại. Test phải pass trở lại. Chuỗi pass, fail rồi pass giúp củng cố evidence rằng thay đổi được đưa vào có liên quan trực tiếp đến lỗi quan sát.

Vòng này xác nhận regression quan sát được trong môi trường đã ghim. Sau đó vẫn cần rà tuân thủ prompt, nguyên nhân, tính hợp lý và trùng lặp.  Không phải cứ làm test fail là đã phù hợp để đưa vào tập train

Tiếp theo em làm rõ nhãn nguyên nhân được xây từ những bằng chứng này như thế nào.

## Slide 13 — Nhãn  được xây thế nào?

**Thời gian: 08:50–09:45 · 55 giây**

Taxonomy hiện tại gồm bốn nhóm nguyên nhân: syntax, dependency hoặc configuration, API hoặc type, và logic hoặc value. Khi chưa đủ bằng chứng, mô hình có thể trả unknown.

Cái Nhãn nó sẽ không được suy trực tiếp từ tên exception. Ví dụ, Một ValueError có thể là hậu quả của logic điều khiển sai, còn một lỗi được phát hiện trong test không có nghĩa test là nơi gây ra lỗi.

Cái việc xây nhãn cần link thay đổi code với hành vi trung gian và log quan sát được. Repair patch là một nguồn bằng chứng, nhưng không phải mọi dòng trong patch đều là causal location.

## Slide 14 — Ví dụ real: metadata của marshmallow

**Thời gian: 09:45–11:00 · 75 giây**

[Chỉ code bên trái, giá trị quan sát, rồi target bên phải.]

Đây là một mẫu real train từ marshmallow, để thấy rõ một cặp input và target thực tế.
 repo teên case lỗi thật từ thư viện marshmallow, thuộc tập train.

Trong ví dụ này, metadata là thông tin mô tả một trường dữ liệu, chẳng hạn description và widget. Khi người dùng truyền dictionary metadata vào hàm khởi tạo Field, code xử lý tham số khiến dictionary bị lồng thêm một cấp không mong muốn.

[Chỉ phần giá trị mong đợi và thực tế.]

Test mong muốn description và widget nằm trực tiếp trong field.metadata. Nhưng kết quả thực tế lại có thêm một khóa metadata bọc bên ngoài, nên phép so sánh thất bại.

Model chẩn đoán được cung cấp log lỗi và code liên quan. Target dùng để huấn luyện gồm loại nguyên nhân, file, hàm và lời giải thích. Với mẫu này, nhãn là API/type, vị trí nguyên nhân được xác định ở hàm Field.init trong file fields.py.

Điểm cần phân biệt là dòng assert trong test chỉ phát hiện sai khác; phần xử lý tham số trong hàm khởi tạo mới là nơi gây ra hành vi đó. Reference và patch sửa được giữ riêng, không đưa vào input để model đọc sẵn đáp án
## Slide 15 — Ví dụ synthetic: broadcast trong pvlib

**Thời gian: 11:00–12:15 · 75 giây**

[Chỉ từ not ở seed và vị trí bị bỏ trong candidate.]

Ví dụ thứ hai là một mẫu synthetic train từ pvlib. Đây là lỗi mới do phép sinh trên bản seed đã pass, không phải lỗi lịch sử gốc của case nguồn.

Ở bản seed, khi tham số áp dụng cho toàn hệ thống và giá trị không phải tuple, code nhân rộng scalar thành một tuple có số phần tử bằng số array. Generator 7B bỏ từ not trong điều kiện này.

Sau phép sửa, một scalar không đi vào nhánh broadcast nữa. Nó được đóng thành tuple một phần tử, rồi đi đến bước so chiều dài với số array. Với hệ thống có nhiều array, điều kiện không khớp và code phát ValueError về length mismatch.
  laà trong iìifcaái logbaáoseẽ 

## Slide 16 — Các cấu hình M0 đến M5

**Thời gian: 12:15–13:00 · 45 giây**

Các mã M0 đến M5 biểu diễn các cấu hình đối chứng, không phải sáu kích thước model khác nhau.

M0 là TF-IDF cộng Logistic Regression, chỉ làm phân loại. M1 là base 3B prompt-only, không cập nhật trọng số; M1-P2 là biến thể prompt format được báo riêng.
ưweidghtdđuocươợ 
M2 dùng QLoRA trên real train. M5 cũng dùng cùng base nhưng học real cộng synthetic đã rà. Hai adapter được khởi tạo độc lập, M5 không học tiếp từ M2.
 model
M3 dự kiến đối chứng xử lý mất cân bằng; M4 dự kiến dùng synthetic chưa qua đầy đủ bước rà và lọc nhãn. Hai cấu hình này chưa chạy. Vì vậy, thử nghiệm hiện tại chưa cô lập hết ảnh hưởng của phân bố lớp và chất lượng curation.
 nhuư khacá voiơớ nhuư M5 em vaà tseẽ tieêpế thucụự tucụ thucụự hienêệ
## Slide 17 — Cấu hình SFT bằng QLoRA

**Thời gian: 13:00–13:55 · 55 giây**

Về cấu hình học, base 3B dùng NF4 và double quantization, còn tính toán dùng BF16. LoRA có rank 16, alpha 32 và dropout không phẩy không năm.
Thìcaái  caái phanâầ
Batch trên một GPU là một mẫu, tích lũy gradient qua tám microbatch. Context là 2.048 token và ngân sách output tối đa 384 token. Seed được giữ cố định và loss chỉ tính phần target.

Các cấu hình này giúp triển khai SFT trên GPU local trong phạm vi tài nguyên hiện có. Em chưa có đối chứng để khẳng định đây là cấu hình tối ưu.

Một điểm cần chú ý khi so sánh là M5 có nhiều mẫu hơn M2. Do đó, cùng số epoch không có nghĩa cùng số updates, số token hay cùng chi phí tính toán. Các đại lượng này được lưu để giải trình, thay vì mặc định hai lượt học hoàn toàn ngang nhau về compute.
 
## Slide 18 — Continuation và checkpoint được chọn

**Thời gian: 13:55–14:45 · 50 giây**

[Chỉ dòng đích tổng, sau đó chỉ dòng checkpoint được chọn.]

Ban đầu hai model đã có parent ở step 104. Phần continuation tiếp tục M2 đến 220 updates và M5 đến 350 updates, tương ứng tổng mười epoch ở mỗi cấu hình.

g chọn adapter cuối.

**Thời gian: 14:45–15:20 · 35 giây**

Nhìn theo tiến độ toàn dự án, W1 đã có pipeline trên properr và hai trong ba lượt 7B đạt kiểm chứng thực thi. Các đợt mở rộng sau đó thử 17 case trên 10 repository, giúp mở rộng harness và quy trình rà dữ liệu.

chặng đầu em hóa dataset pà đánh giá cuối.

cái thứ  có kiểm thử phần mềm og, hash để trthìvtổng số là  ết. Những số này phải tách khỏi số mẫu ML; các cohort develo cũnthực hiện g không cộng vào dataset SFT hiện tại.


**Thời gian: 15:20–16:20 · 60 giây**

Trước khi đọc bảng kết quả, em giải thích các chỉ số chính.

Em đánh giá cả phân loại và định vị lỗi. Accuracy là tỷ lệ đúng loại lỗi; Macro-F1 lấy trung bình F1 của bốn lớp, mỗi lớp có weight bằng nhau.

File Top-1 và Hàm Top-1 đo dự đoán đầu tiên có khớp file hoặc cặp file–hàm nó tham chiếu không. Joint yêu cầu đúng cả loại lỗi và hàm trên cùng một mẫu.

Output không hợp lệ vẫn tính vào mẫu số. Hiện chỉ 12/38 mẫu test có hàm tham chiếu trong code được truy xuất; quy tắc chấm yêu cầu điều kiện này để ghi nhận định vị đúng

**Thời gian: 16:20–17:05 · 45 giây**

[Chỉ M1-P2, sau đó so hai hàng M2 và M5.]

Bảng này là validation trên cùng 37 mẫu real. M2 có Macro-F1 khoảng 0.35; M5 khoảng 0.4. Joint lần lượt là bốn và năm mẫu đúng trên 37.



## Slide 22 — Final test trên cùng 38 real

**Thời gian: 17:05–18:05 · 60 giây**

[Chỉ hai hàng M2/M5; nhấn joint bằng nhau, không đọc toàn bảng.]

Đây là kết quả cuối trên cùng 38 mẫu real.

M2 dự đoán đúng loại 22 mẫu, tương ứng khoảng 57,89 phần trăm. M5 đúng 24 mẫu, tương ứng 63,16 phần trăm. Macro-F1 tăng từ khoảng 0.31 tới 0.33.

Về định vị, M5 đúng hàm bảy mẫu so với sáu của M2, nhưng số đúng file giảm từ 18 xuống 16. Joint của cả hai cùng là bốn trên 38 mẫu.


## Slide 23 — M5 hơn và kém M2 ở đâu?

**Thời gian: 18:05–19:05 · 60 giây**

Theo từng mẫu, về phân loại có bốn mẫu chỉ M5 đúng và hai mẫu chỉ M2 đúng. Về hàm, M5 thắng hai và thua một. Nhưng về joint, mỗi model chỉ thắng model còn lại một mẫu, nên tổng joint không tăng.

Phần tăng phân loại tập trung ở Pylint. Trên Pytest, accuracy không đổi nhưng joint của M5 giảm. Như vậy, bổ sung synthetic chưa tạo cải thiện đồng đều ở mọi nhiệm vụ và repository.

Ngoài model, còn hai giới hạn lớn. Thứ nhất, reference hàm vắng khỏi context ở 26 trên 38 mẫu test. Thứ hai, train chỉ có hai lớp nguyên nhân; cả hai SFT đều không nhận đúng các mẫu dependency hoặc configuration của test.

Nhãn vẫn là silver, chỉ có một seed, và các đối chứng M3, M4 chưa chạy. Em chỉ kết luận có cải thiện nhẹ về phân loại trong pilot này, chưa khẳng định synthetic có lợi tổng quát hoặc xác định một mẫu synthetic cụ thể đã gây ra cải thiện.

## Slide 24 — Kết luận giữa kỳ và hướng tiếp theo

**Thời gian: 19:05–20:00 · 55 giây**

Đến giữa kỳ, đề tài đã đi được một vòng từ dữ liệu nguồn đến tạo dataset, SFT và đánh giá . Phần này cho thấy hướng triển khai là khả thi, đồng thời làm rõ các điểm nghẽn của dữ liệu và cách chẩn đoán.

Kết quả hiện tại ghi nhận M5 tăng nhẹ về phân loại so với M2, nhưng joint chưa tăng. Vì vậy, ưu tiên tiếp theo của em là độ nhất quán của label, retrieval và độ phủ lớp repository trên development, sau đó bổ sung đối chứng và nhiều seed.


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
