# Rà dữ liệu đợt mở rộng 01

Ngày 30/10/2026; dùng `ci-data-review`, chỉ đọc artifact mới sau khi batch kết thúc. Không chạy lại test/model để viết review. [Tổng kết](expansion-01-summary.md), [batch manifest](../runs/batch-20261029T173420443187Z/manifest.json), [HTML](../runs/batch-20261029T173420443187Z/report.html).

## Kết luận để người dùng review

21 lượt sinh từ 7 seed pass: **10 output không hợp lệ, 5 candidate không làm test fail, 6 lượt đạt thực thi**. Sáu lượt đạt gồm **3 candidate khác byte, cùng thuộc pydicom**; không coi các output trùng là mẫu độc lập. Agent kiến nghị giữ ba candidate khác byte để phát triển/review, chưa duyệt training. Các lượt còn lại giữ làm evidence thất bại; chưa tự biến thành đối chứng pass.

Đã đối chiếu 78 JUnit với 2.580 testcase records; source/test của 8 image khớp inventory hai role, 11 candidate hợp lệ khớp hash và phép edit nguyên trạng. Con số testcase records bao gồm lặp, không phải 2.580 test độc lập. [Integrity audit](../runs/integrity-20261029T174127403846Z/manifest.json). Tất cả xác nhận người dùng, gold labels và training eligibility mới vẫn pending.

## Tình trạng chín case nguồn

| Case | Điều quan sát và giải thích | Giới hạn / kiến nghị |
|---|---|---|
| PyLabRobot #527 | Base/fixed đều gặp fixture không ghi được `/source/<role>/test_logs`; không có seed pass | Lỗi môi trường cô lập của recipe, chưa kết luận về lỗi serializer. Dừng case, không sinh/rerun. [Fixed log](../runs/reproduce-20261029T173420448441Z/historical-fixed.stdout.txt) |
| marshmallow #1343 | Base TypeError với nested data sai kiểu; patch mở catch từ KeyError sang KeyError/TypeError, fixed pass; matcher nguồn đạt | Giả thuyết local được hỗ trợ; chưa có gold cause label. [Base log](../runs/reproduce-20261029T173514330728Z/historical-base.stdout.txt), [fixed](../runs/reproduce-20261029T173514330728Z/historical-fixed.stdout.txt) |
| TCM #364 | Base không kill subprocess khi timeout; upstream test mock kiểm tra `kill_called` thất bại. Head kill rồi collect output; test pass | Đã chứng minh hành vi trên mock subprocess trong Docker, chưa phải chạy ImageMagick thật. [Base](../runs/reproduce-20261029T173605084115Z/historical-base.stdout.txt), [fixed](../runs/reproduce-20261029T173605084115Z/historical-fixed.stdout.txt) |
| marshmallow #1359 | Base `AttributeError: 'Tuple' object has no attribute 'opts'`; sửa `schema.opts` thành `self.root.opts`, fixed pass | Manifest giữ `historical_supported=false`: tám PASS_TO_PASS identifiers nguồn bị cắt ở khoảng trắng, không khớp tên tham số đầy đủ trong JUnit. Quan sát fail→pass là thật nhưng chưa xác nhận đủ theo matcher exact. [Base](../runs/reproduce-20261029T173656833907Z/historical-base.stdout.txt), [fixed](../runs/reproduce-20261029T173656833907Z/historical-fixed.stdout.txt) |
| chunkify #340 | Export từ chối nonregular entry `config/tags/generic.yaml` (symlink) trước build/test | Không có seed hoặc lỗi ứng dụng được xác nhận; không nới kiểm soát archive để cho case qua. [Manifest](../runs/reproduce-20261029T173729961250Z/manifest.json) |
| pydicom #1139 | Base PersonName không iterable, ba test next/iterator/contains fail; reference repair bổ sung hành vi, fixed pass | Lỗi lịch sử này khác lỗi ngày tháng do synthetic bên dưới. [Base](../runs/reproduce-20261029T173731561454Z/historical-base.stdout.txt), [fixed](../runs/reproduce-20261029T173731561454Z/historical-fixed.stdout.txt) |
| sshpilot #716 | Base bỏ sót tra cứu passphrase theo resolved identity, test thấy danh sách lookup rỗng; head test pass | Unit tests dùng stub GI/terminal upstream, chưa phải tích hợp desktop SSH thật. [Base](../runs/reproduce-20261029T173823606271Z/historical-base.stdout.txt), [fixed](../runs/reproduce-20261029T173823606271Z/historical-fixed.stdout.txt) |
| pydicom #1256 | Base không truyền bulk-data handler vào sequence lồng, giá trị expected `b'xyzzy'` thành None; reference repair truyền handler, fixed pass | Giả thuyết local được hỗ trợ; không coi lỗi synthetic mới là lỗi PR gốc. [Base](../runs/reproduce-20261029T173859391541Z/historical-base.stdout.txt), [fixed](../runs/reproduce-20261029T173859391541Z/historical-fixed.stdout.txt) |
| pydicom #1694 | Base đọc data element ngoài try nên lỗi không được suppress; patch đưa truy cập vào try, fixed pass | Đạt matcher nguồn. Ba output synthetic đều invalid, không có candidate để xác nhận nguyên nhân mới. [Base](../runs/reproduce-20261029T173955546586Z/historical-base.stdout.txt), [fixed](../runs/reproduce-20261029T173955546586Z/historical-fixed.stdout.txt) |

Đây là local reconstruction với upstream test cố định, không phải raw CI logs lịch sử. Reference repair/test patches và source metadata giữ riêng trong cache; revision/hash trong registry/manifests. Nhãn PR-level agent không chứng minh ai gây lỗi.

## Ba candidate khác byte đạt thực thi

### P1139-A — Ba lượt 01/02/03 trùng hoàn toàn

**Kết luận:** làm hỏng hỗ trợ ngày `YYYY.MM.DD`, đạt baseline pass → ba fail ổn định → restored pass cho từng lượt. Candidate SHA-256 `d6335f8e5d8105cd94e94cea214ff5d72a1b27f325dc7454f19ef51a69b23a56`.

**Bằng chứng:** [candidate lượt 01](../runs/generate-20261029T173754950832Z/attempt-01/candidate.py), [raw proposal](../runs/generate-20261029T173754950832Z/attempt-01/proposal.json), [diff](../runs/generate-20261029T173754950832Z/attempt-01/change.diff), [verification manifest đủ ba lượt](../runs/verify-20261029T173806351343Z/manifest.json), [log rep 1](../runs/verify-20261029T173806351343Z/attempt-01/candidate-1.stdout.txt), [JUnit](../runs/verify-20261029T173806351343Z/attempt-01/candidate-1.junit.xml).

**Nguyên nhân agent đề xuất:** dòng 78 trong `pydicom/valuerep.py`, nhánh `DA.__new__`, đổi kiểm tra dấu `.` sang `-`. Chuỗi `1961.08.04` vốn được chấp nhận không đi vào nhánh chuyển đổi và gây `ValueError: Cannot convert to datetime`. `TestDateTime.test_date` là nơi phát hiện. Mỗi repetition có một failure, 40 test pass; cơ chế được code và log hỗ trợ với độ chắc chắn cao. Generator tự gắn `syntax`; code đã chạy nên nhãn đó không được evidence hỗ trợ. Mô tả nhãn tạm thời: logic/điều kiện nhận dạng định dạng sai.

**Đánh giá sử dụng:** một edit nhỏ, không đổi tests/API/dependencies; không thêm comment chỉ ý đồ. Độ đại diện thực tế chưa được chứng minh. Giữ một candidate đại diện cùng liên kết ba lượt trùng, không nhân ba số mẫu độc lập; raw của cả ba lượt vẫn giữ. Chưa phải training-approved hoặc gold-labeled.

**Người dùng cần quyết định:** review lời giải thích và kiến nghị giữ một đại diện làm ứng viên development. Nhãn taxonomy/vị trí chính thức và training vẫn pending.

### P1256-A — Lượt 01 và 03 trùng hoàn toàn

**Kết luận:** thay sai phân biệt hoa/thường của key JSON, làm dữ liệu hợp lệ bị từ chối. Candidate SHA-256 `0f15de3d28ead93252a6bbc28fdd19b6ad1fb86ab0662f2b6e5662998a0ebf80`; cả hai lượt đạt kiểm chứng thực thi.

**Bằng chứng:** [candidate 01](../runs/generate-20261029T173924603722Z/attempt-01/candidate.py), [proposal](../runs/generate-20261029T173924603722Z/attempt-01/proposal.json), [diff](../runs/generate-20261029T173924603722Z/attempt-01/change.diff), [manifest đủ ba lượt](../runs/verify-20261029T173935725566Z/manifest.json), [log rep 1](../runs/verify-20261029T173935725566Z/attempt-01/candidate-1.stdout.txt), [JUnit](../runs/verify-20261029T173935725566Z/attempt-01/candidate-1.junit.xml).

**Nguyên nhân agent đề xuất:** dòng 210 trong `pydicom/jsonrep.py`, hàm `get_sequence_item`, đổi `'vr' not in val` thành `'VR' not in val`. Input chứa `vr` đúng quy ước nhưng không chứa `VR`; điều kiện mới bật nhánh raise ở dòng 212. Log có KeyError nói thiếu `vr` dù dict đang chứa `vr`. Mỗi repetition có bốn failure, 19 pass. Độ chắc chắn cao từ biểu thức, dict trong trace và repetition signatures. Nhãn tạm thời: logic/validation key sai; generator `syntax` không phù hợp.

**Đánh giá sử dụng:** regression nhỏ có cơ chế rõ, không sửa test hoặc thêm comment chỉ lỗi. Kiến nghị giữ một đại diện, liên kết lượt 01/03 là duplicate; chưa duyệt tính đại diện, nhãn gold hoặc training.

**Người dùng cần quyết định:** review giải thích điều kiện phân biệt hoa/thường và kiến nghị giữ ứng viên. Chưa cần phê duyệt train.

### P1256-B — Lượt 02

**Kết luận:** đảo điều kiện kiểm tra kiểu trong giải mã PersonName, trả dict thay vì chuỗi đã chuẩn hóa. Candidate SHA-256 `972bc7ba518606aea50aca13a37906477991a5249cd4408b7297c998321d4cd1`; đạt kiểm chứng thực thi.

**Bằng chứng:** [candidate 02](../runs/generate-20261029T173924603722Z/attempt-02/candidate.py), [proposal](../runs/generate-20261029T173924603722Z/attempt-02/proposal.json), [diff](../runs/generate-20261029T173924603722Z/attempt-02/change.diff), [log rep 1](../runs/verify-20261029T173935725566Z/attempt-02/candidate-1.stdout.txt), [JUnit](../runs/verify-20261029T173935725566Z/attempt-02/candidate-1.junit.xml).

**Nguyên nhân agent đề xuất:** dòng 251, `get_pn_element_value`, đổi `if not isinstance(value, dict)` thành `if isinstance(value, dict)`. Dict hợp lệ đi vào nhánh warning và `return value` ở dòng 259 thay vì được ghép các thành phần thành string ở dòng 273. Downstream gặp AttributeError về `append`/`split` rồi bọc thành ValueError ở `pydicom/dataelem.py:279`. Đó là nơi lỗi lộ ra sau đó, không phải edit gây lỗi. Mỗi repetition có sáu failure, 17 pass. Nhãn tạm thời logic/đảo type guard dẫn tới giá trị sai kiểu, độ chắc chắn cao; không phải SyntaxError như generator tự khai.

**Đánh giá sử dụng:** cơ chế khác P1256-A dù cùng case/file; cần cùng repo/development group khi chia tập sau. Không thêm comment chỉ ý đồ, nhưng mức thực tế vẫn cần rà. Kiến nghị giữ candidate riêng làm ứng viên development, training pending.

**Người dùng cần quyết định:** review chuỗi đảo điều kiện → trả dict → lỗi downstream và kiến nghị giữ. Các trường xác nhận chính thức tiếp tục pending.

## Năm lượt có candidate nhưng không tạo failure

| Nhóm | Kết luận / bằng chứng | Giải thích agent và kiến nghị |
|---|---|---|
| marshmallow #1343, 02/03 | Hai candidate trùng hash `2a21776c5e5672f5a7a02b68a1b7805ff720706cf47940540ce26b979214982b`; mỗi repetition 25 pass. [Diff](../runs/generate-20261029T173541374859Z/attempt-02/change.diff), [log](../runs/verify-20261029T173556500724Z/attempt-02/candidate-1.stdout.txt) | Dòng 950 thay fallback `utils.if_none(...)` trong schema processor; test mục tiêu không phát hiện regression. Chưa có coverage chứng minh đường thay đổi có chạy. Generator gọi syntax không có căn cứ. Loại khỏi tập synthetic-failure hiện tại, giữ failed-generation evidence; không tự xác nhận code đúng mọi tình huống |
| TCM #364, 02 | Hash `7f36fd6ed263d85851003c2b04e0802d09139f1500b1bcffc87d2978ecc43854`; một test pass ở cả ba repetition. [Candidate](../runs/generate-20261029T173641181162Z/attempt-02/candidate.py), [log](../runs/verify-20261029T173652371964Z/attempt-02/candidate-1.stdout.txt) | Dòng 187 đổi escaping trong nhánh `if os_name == 'nt'`; Docker chạy Linux nên nhánh đó không phải đường kiểm chứng hiện tại. Cảnh báo escape không phải SyntaxError. Không có lỗi được thực thi chứng minh; loại khỏi tập mẫu lỗi hiện tại, chưa suy làm negative sample |
| marshmallow #1359, 01/02 | Hai candidate trùng hash `584a530d8b41b9aae4aea6a5a4d43b045f14b4cab66c1bfb5b4661feb237a321`; 77 test pass ở mỗi repetition. [Diff](../runs/generate-20261029T173710990536Z/attempt-01/change.diff), [log](../runs/verify-20261029T173720986776Z/attempt-01/candidate-1.stdout.txt) | Dòng 1115 thêm một `self.format or` trước biểu thức vốn đã bắt đầu bằng `self.format or`; dư thừa trong trường hợp attribute thông thường. Không có thay đổi import hoặc failure hỗ trợ nhãn `import` của generator. Loại khỏi tập mẫu lỗi hiện tại; không kết luận tương đương trong mọi subclass có side effect |

Độ chắc chắn cao về kết quả test đã quan sát; suy luận về nhánh/logic chỉ có phạm vi như mô tả. Người dùng chỉ cần review kiến nghị loại khỏi tập failure hiện tại, không phải tự phân tích lại code/log hoặc duyệt nhãn pass.

## Mười output không hợp lệ

| Case / lượt | Điều quan sát | Kiến nghị |
|---|---|---|
| marshmallow #1343 / 01 | `before` không khớp đúng một lần; proposal không tạo candidate. [Proposal](../runs/generate-20261029T173541374859Z/attempt-01/proposal.json) | Giữ invalid_output, không có vị trí lỗi thực thi hay gold label |
| TCM #364 / 01,03 | `before == after`, model nói không cần đổi. [01](../runs/generate-20261029T173641181162Z/attempt-01/proposal.json), [03](../runs/generate-20261029T173641181162Z/attempt-03/proposal.json) | Không đạt yêu cầu tạo regression; không tự sửa output |
| marshmallow #1359 / 03 | `before` không khớp, lời giải thích hướng sửa default. [Proposal](../runs/generate-20261029T173710990536Z/attempt-03/proposal.json) | Không có candidate thực thi, không nhận nhãn import làm nguyên nhân |
| sshpilot #716 / 01,02,03 | Các điều kiện `if requires_force:`/`if not passphrase_available:` không khớp đúng một lần trong source nguyên trạng. [Manifest](../runs/generate-20261029T173843891949Z/manifest.json) | Giữ ba invalid_output, không nới matching hoặc chỉnh output cho qua |
| pydicom #1694 / 01,02,03 | 01/03 before không khớp; 02 before/after không đổi. [Manifest](../runs/generate-20261029T174020789887Z/manifest.json) | Không có candidate để chẩn đoán lỗi mới; giữ cả ba lượt trong mẫu số |

Đây là lỗi giao thức sinh/không tạo candidate, không phải bằng chứng lỗi syntax/import của repo. Độ chắc chắn cao về lý do validation từ raw output và source đã hash; không suy nhãn lỗi thực thi khi chưa chạy candidate. Không cần người dùng gán lỗi cho output invalid.

## Prompt, input và quyết định còn lại

- Sáu candidate khác byte hợp lệ chỉ thay một biểu thức/điều kiện; không thêm comment cố ý tiết lộ lỗi. Comment tự nhiên có sẵn vẫn giữ nguyên. Stack trace/file/dòng là evidence hợp lệ.
- Nhiều proposal giải thích theo hướng sửa code hoặc nói không cần sửa, dù prompt yêu cầu cài regression; nhãn self-label không đáng tin trong đợt này. Đây là vấn đề chất lượng generator, không được chữa bằng sửa output cũ.
- Chưa đóng gói input cho 3B hoặc train. Theo contract, reference patch, proposed_label/explanation và nhận định agent nằm riêng; khi đóng gói code/log phải rà leakage trên input thực tế.
- Các diff v2 đã lưu có xuống dòng thừa khi đọc trên Windows do newline translation. Candidate/source bytes và hashes vẫn khớp; review dựa thêm vào before/after và candidate đầy đủ. Đã sửa writer cho các run sau, không sửa diff raw của đợt này.
- Người dùng review ba kiến nghị giữ candidate khác byte và kiến nghị loại các lượt không tạo failure. Nhãn taxonomy, vị trí chính thức, tính đại diện và training eligibility tiếp tục pending. Chưa có bất kỳ phê duyệt mới nào trong đợt này.
