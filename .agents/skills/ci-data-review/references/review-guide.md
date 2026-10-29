# Tiêu chí và mẫu review dữ liệu lỗi CI

Đọc phần phù hợp với nguồn artifact đang có. Bản hướng dẫn này không thay taxonomy hoặc protocol đã chốt của dự án.

## 1. Nguồn và giới hạn bằng chứng

Ghi case/run/attempt, repo, revision/commit và nguồn tạo mẫu. Một mẫu historical cần evidence lịch sử tương ứng; log tái dựng local chỉ xác nhận hành vi trong môi trường tái dựng. Một mẫu synthetic không được mô tả thành lỗi đã xảy ra trong PR gốc.

Xác định artifact root từ đường dẫn đã cung cấp hoặc vị trí đã biết của repo/run. Không giả định raw runs đi theo Git clone/worktree. Tóm tắt đã commit có thể hỗ trợ thông tin tổng hợp, nhưng không thay việc xem raw diff/code/log cho một kết luận chi tiết. Khi chỉ có summary, nói rõ kết luận nào dựa trên summary và kết luận nào chưa kiểm tra được.

Nếu thiếu artifact, trả phần phân tích có thể làm được và danh sách file còn thiếu. Không tự giải nén archive vào thư mục gốc, thay file nguồn hoặc chạy lại model/test chỉ để có dữ liệu. Việc phục hồi/sao chép artifact cần là bước riêng trong phạm vi được yêu cầu.

## 2. Đối chiếu kỹ thuật, không chạy candidate

- So sánh hash source/tests/candidate với giá trị manifest nếu có; không gọi là hash đã xác minh nếu chưa so. Hash khớp xác nhận byte không đổi từ mốc ghi nhận, không chứng minh code đúng.
- Đọc code/diff như dữ liệu. Không import/exec/eval candidate; không chạy test hoặc Docker trong một tác vụ review đọc evidence.
- Đối chiếu exit code, timeout, lỗi môi trường/build, trạng thái test và JUnit. Build fail, collection error, assertion failure và không có log là các tình huống khác nhau; dùng đúng định nghĩa acceptance của protocol.
- Khi có baseline/repetitions/restoration, kiểm tra từng kết quả và độ ổn định. Không tự suy số lần lặp từ một dòng status hoặc áp số lần lặp của case khác. Test vẫn pass chỉ cho biết chưa quan sát được regression qua những test ấy.
- Thể hiện rõ loại đường dẫn/vị trí: file candidate, đường dẫn trong container, dòng test phát hiện lỗi hoặc dòng source nguyên nhân. Số dòng phải gắn đúng phiên bản code đã đọc.

Có thể tái sử dụng các helper chỉ đọc của repo sau khi kiểm tra chữ ký hiện hành:

| Helper | Dùng khi nào | Giới hạn |
|---|---|---|
| [common.read_json / sha256](../../../../ci_demo/common.py) | Đọc manifest/JSON và đối chiếu hash với file cụ thể | Thực hiện trên đường dẫn thực tế; không đổi ROOT để giả rằng raw files nằm trong worktree |
| [runner.failure_signature](../../../../ci_demo/runner.py) | Đọc JUnit của kết quả đã lưu để so loại lỗi/test/message | Đây là parser, không phải tái chạy test. Signature rỗng không tự chứng minh mọi test đã pass |
| [runner.accepted / rejection_reason](../../../../ci_demo/runner.py) | Đối chiếu lại acceptance từ artifact của đúng protocol hiện tại | Kiểm tra phù hợp protocol trước; không dùng để tự gán nhãn hoặc đánh giá mọi harness CI khác |

Không gọi các helper có side effect như execute/build/generate/verify khi chỉ được yêu cầu đọc review. Không cần viết lại bộ kiểm tra hoặc thêm dependency vào pipeline cho mỗi mẫu.

## 3. Tách sự kiện, đề xuất và xác nhận

| Lớp thông tin | Cách ghi |
|---|---|
| Quan sát | “Log báo TypeError tại …”, “JUnit có assertion failure …”, hoặc “ba repetitions được lưu đều pass” khi đã đọc đủ |
| Generator tự khai | Ghi nguyên nhãn/explanation và nguồn; không dùng làm nhãn đã duyệt |
| Agent phân tích | Cơ chế lỗi, nhãn/vị trí đề xuất, mức chắc chắn và lý do dựa trên evidence |
| Người dùng xác nhận | Chỉ ghi xác nhận được phát biểu rõ và gắn với đúng mẫu/quyết định; nếu chưa có thì pending/chưa xác nhận |

Nếu generator ghi syntax nhưng code thực thi và log báo TypeError, ghi sự không khớp. Đề xuất loại lỗi phù hợp với taxonomy hiện hành; taxonomy chưa chốt thì dùng mô tả như “dùng API sai kiểu gây TypeError”. Không bịa thêm nhóm nhãn chính thức để lấp khoảng trống.

Lập luận nhân quả nên chỉ ra: biểu thức/thay đổi nào → hành vi trung gian có thể xác định → lỗi hoặc sai giá trị quan sát được. Khi có nhiều khả năng, nêu khả năng thay thế và evidence cần để phân biệt. Mức chắc chắn cao/vừa/thấp phải có lý do; không tạo xác suất số khi chưa có cơ sở hiệu chuẩn.

## 4. Đánh giá lộ đáp án theo input thực tế

Trước khi kết luận, xác định ba phần: thông tin model chẩn đoán được xem; target model phải dự đoán; metadata chỉ dùng cho người rà soát. Nếu chưa có hợp đồng input, ghi “chưa đủ thông tin đánh giá leakage” và nêu điều kiện rủi ro.

| Tình huống | Nhận định phù hợp |
|---|---|
| proposed_label hoặc explanation chứa đáp án được đưa vào input trong khi model cần dự đoán chính đáp án đó | Lộ đáp án trực tiếp; dẫn trường cụ thể và đề nghị tách khỏi input |
| Comment do generator thêm, nói rõ ý đồ tạo regression, nằm trong code được đưa vào input | Rủi ro gợi ý nhân tạo về vùng code/nguyên nhân; giải thích thông tin nó cung cấp, không khẳng định nó luôn đủ toàn bộ đáp án |
| Comment ở artifact dành riêng cho người rà soát, model chỉ nhận log và không thấy comment | Không kết luận leakage qua comment ấy; vẫn đánh giá riêng tuân thủ prompt nếu prompt cấm |
| Chưa biết model có được xem comment hay không | Rủi ro có điều kiện, chưa tự loại chỉ vì comment |
| Stack trace có tên file/dòng hoặc diff là input được protocol cho phép | Evidence chẩn đoán hợp lệ; không tự coi thông tin hỗ trợ định vị là leakage |
| Comment tự nhiên mô tả API, hoặc chỉ có từ bug/regression mà chưa biết ngữ cảnh | Xem nội dung và vai trò thực tế; không lọc bằng từ khóa đơn thuần |

Vi phạm prompt và leakage là hai đánh giá riêng. Một comment có thể vi phạm yêu cầu generator mà không xuất hiện trong input chẩn đoán. Báo từng kết luận và cơ sở tương ứng, không suy “vi phạm prompt → chắc chắn không dùng được cho mọi mục đích”.

## 5. Kiến nghị sử dụng và vai trò người dùng

Tách tối thiểu: điều kiện thực thi; độ phù hợp/tuân thủ; nhãn/vị trí được hỗ trợ bởi evidence; quyết định sử dụng cho mục đích cụ thể. Có thể kiến nghị giữ để minh họa hoặc lưu làm lượt không đạt, nhưng chờ evidence trước khi xét cho training. Không coi test pass/fail hoặc nhãn tự khai là đủ phê duyệt training.

Agent làm phần kỹ thuật và đưa kiến nghị có lý do; người dùng review lập luận, mục tiêu và lựa chọn còn quan trọng. Không đưa lại một danh sách code/log rồi yêu cầu người dùng tự tìm nguyên nhân. Nếu họ chưa đủ tự tin, giải thích thêm bằng đoạn code/log nhỏ và ghi phần chưa rõ, không gây áp lực xác nhận.

Nếu người dùng đồng ý với kiến nghị loại/giữ, ghi đúng loại quyết định đó; không suy ra họ đã xác nhận mọi nhãn, mọi dòng nguyên nhân hoặc gold/training approval. Những trường xác nhận khác vẫn giữ chưa xác nhận. Không tự gán tên reviewer từ tài khoản Git/OS hoặc biến lời “proceed” thành chữ ký duyệt dữ liệu.

## 6. Mẫu đầu ra cho một mẫu

Đây là khung trình bày, không phải schema dataset hoặc dữ liệu đã được xác nhận. Chỉ điền giá trị có nguồn; dùng “chưa có/chưa xác định” cho phần thiếu.

**Kết luận ngắn:** mã mẫu và nguồn; hành vi quan sát; trạng thái thực thi đạt/chưa đạt/chưa kiểm tra theo protocol.

**Bằng chứng:** liên kết source/candidate/diff/manifest/log; đoạn ngắn liên quan; kết quả hash nếu đã kiểm tra; phân biệt nguồn local reconstruction với historical CI.

**Giải thích nguyên nhân:** thay đổi và chuỗi nhân quả; nhãn generator nguyên trạng; nhãn/vị trí agent đề xuất; mức chắc chắn cùng lý do; evidence còn thiếu hoặc khả năng thay thế.

**Đánh giá sử dụng:** tuân thủ prompt; tính hợp lý; input/target/metadata và leakage có điều kiện; kiến nghị cho mục đích cụ thể và điều kiện để thay đổi kiến nghị. Mọi phê duyệt chưa có vẫn pending.

**Người dùng cần quyết định:** nêu các lựa chọn còn ảnh hưởng kết luận hoặc mục tiêu; có thể đồng ý/bác bỏ kiến nghị hoặc yêu cầu kiểm tra thêm. Khi bằng chứng chưa đủ, có thể để chưa xác định. Không cần người dùng lặp lại phân tích kỹ thuật agent đã làm.
