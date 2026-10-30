# Rà dữ liệu development 02 bằng ci-data-review

Ngày 30/10/2026. Phạm vi: 15 output v3 của [đợt 02](expansion-02-summary.md), gồm profile FastAPI hiệu chỉnh có trace riêng. Review chỉ đọc source/candidate/diff/proposal/log/JUnit đã lưu, không gọi lại model/test và không sửa raw review stub.

## Kết luận để người dùng review

Runner ghi **11 execution_verified, 3 candidate không làm test fail, 1 output không đổi dòng**. Mười một candidate đạt runner đều khác byte; một candidate gây IndentationError và vi phạm yêu cầu v3 giữ syntax hợp lệ. Các marker `extra`/`X` cũng cần xem xét tính tự nhiên. Agent kiến nghị giữ candidate có cơ chế rõ cho development review, loại syntax-violation khỏi subset v3 valid-Python; chưa phê duyệt gold/training cho bất kỳ mẫu nào.

Mọi candidate hợp lệ khớp SHA-256 và replay đúng một dòng theo site catalog, 6 image khớp tracked source/test inventories. [Integrity audit](../runs/integrity-20261030T000410182947Z/manifest.json). Baseline/repetitions/restoration và source-ID mappings được giữ trong manifests. V3 không yêu cầu nhãn generator; các nhãn dưới đây là **mô tả tạm thời của agent**.

## Astroid #1196 — getitem và bool_value

[Generation](../runs/generate-20261029T235321366861Z/manifest.json), [verification đủ ba lượt](../runs/verify-20261029T235337035725Z/manifest.json). Độ chắc chắn cao về behavior quan sát; tính đại diện vẫn hạn chế trong test scope.

| Lượt | Kết luận, nguyên nhân và vị trí | Evidence và kiến nghị |
|---|---|---|
| 01 | `getitem`, `astroid/nodes/node_classes.py:2381`: `return value` → `return value + 1`. `value` là AST Const node, không phải số, nên cộng int gây TypeError. Ba test failure ổn định, baseline/restored pass | [Candidate](../runs/generate-20261029T235321366861Z/attempt-01/candidate.py), [log rep 1](../runs/verify-20261029T235337035725Z/attempt-01/candidate-1.stdout.txt). Mô tả API/type misuse. Kiến nghị giữ làm ứng viên development; nhãn/vị trí chính thức và training pending |
| 02 | Dòng 2379 đổi đầu block thành `if ...: return False` nhưng block indented phía sau vẫn còn; Python báo `IndentationError: unexpected indent` tại 2380. Dòng 2380 là nơi parser phát hiện, edit gây cấu trúc sai ở 2379 | [Candidate](../runs/generate-20261029T235321366861Z/attempt-02/candidate.py), [log](../runs/verify-20261029T235337035725Z/attempt-02/candidate-1.stdout.txt). Runner chấp nhận collection error ổn định; ba error-body hashes cũng bằng nhau. **Vi phạm prompt valid-Python**: kiến nghị loại khỏi subset v3 hợp lệ, giữ artifact cho phân tích syntax/protocol riêng; không gọi là test assertion failure |
| 03 | `bool_value`, dòng 2391: trả `bool(self.items) + 1` thay bool. Đây có khả năng làm sai semantics kiểu/truthiness nhưng test đang xét đều pass | [Candidate](../runs/generate-20261029T235321366861Z/attempt-03/candidate.py), [log](../runs/verify-20261029T235337035725Z/attempt-03/candidate-1.stdout.txt). Không có regression được thực thi chứng minh trong bộ test này; loại khỏi tập synthetic-failure hiện tại, không tự duyệt làm negative sample |

Người dùng review kiến nghị giữ 01 và xử lý 02 theo ràng buộc giao thức; không phải tự dò lại code/log hoặc xác nhận mọi dòng là gold.

## Astroid #1268 — xuất AST thành chuỗi

[Generation](../runs/generate-20261029T235415338424Z/manifest.json), [verification](../runs/verify-20261029T235427190903Z/manifest.json). Cả ba lượt đạt runner, mỗi lượt khác site/candidate; các vị trí sau gắn đúng candidate revision.

| Lượt | Giải thích nguyên nhân | Evidence / đánh giá sử dụng |
|---|---|---|
| 01 | `astroid/nodes/as_string.py:57`, `__call__`: thay newline `\n` bằng carriage return `\r`. Chuỗi xuất khác expected; một assertion failure ổn định | [Candidate](../runs/generate-20261029T235415338424Z/attempt-01/candidate.py), [log](../runs/verify-20261029T235427190903Z/attempt-01/candidate-1.stdout.txt). Logic/string-formatting; cơ chế line ending rõ, có tính hợp lý để tiếp tục review |
| 02 | `_should_wrap`, dòng 88: `return True` → `return False`; thiếu dấu ngoặc khi in biểu thức, làm sai chuỗi/ưu tiên toán tử trong năm test | [Candidate](../runs/generate-20261029T235415338424Z/attempt-02/candidate.py), [log](../runs/verify-20261029T235427190903Z/attempt-02/candidate-1.stdout.txt). Logic/parenthesization; không suy test assertion line là causal line |
| 03 | `visit_asyncwith`, dòng 106: nối thêm `'extra'` vào chuỗi xuất, làm expected `pass` thành `passextra`; một assertion failure | [Candidate](../runs/generate-20261029T235415338424Z/attempt-03/candidate.py), [log](../runs/verify-20261029T235427190903Z/attempt-03/candidate-1.stdout.txt). Candidate Python chạy được; lỗi nằm ở chuỗi sinh ra, không phải SyntaxError của candidate. Marker tùy ý làm giảm tính tự nhiên; giữ để phân tích development, chưa kiến nghị train khi policy chưa chốt |

Độ chắc chắn cao về causal mechanism vì edit và output lệch khớp log qua ba repetition. Người dùng review cách xử lý marker nhân tạo ở 03 và kiến nghị sử dụng có điều kiện; gold/training tiếp tục pending.

## Astroid #1866 — suy luận string.format

[Generation](../runs/generate-20261029T235638993708Z/manifest.json), [verification](../runs/verify-20261029T235649711472Z/manifest.json). Fixed source pass; source historical flag vẫn false do một identifier nguồn có escaped newline chưa resolve, không được sửa tay. Synthetic acceptance là gate riêng.

| Lượt | Giải thích nguyên nhân | Evidence / kiến nghị |
|---|---|---|
| 01 | `astroid/brain/brain_builtin_inference.py:963`, `_infer_str_format_call`: nối `'X'` vào formatted_string trước const_factory. Tám test nhận chuỗi thừa X | [Candidate](../runs/generate-20261029T235638993708Z/attempt-01/candidate.py), [log](../runs/verify-20261029T235649711472Z/attempt-01/candidate-1.stdout.txt). Logic/string value, chắc chắn cao về cơ chế; marker nhân tạo cần curation riêng, không tự đủ tiêu chí training |
| 02 | `_is_str_format_call`, dòng 924: nhận `int` thay `str`. Các lời gọi format hợp lệ bị phân loại sai, 15 failure, nhiều kết quả thành chuỗi rỗng thay expected | [Candidate](../runs/generate-20261029T235638993708Z/attempt-02/candidate.py), [log](../runs/verify-20261029T235649711472Z/attempt-02/candidate-1.stdout.txt). Logic/type guard, giữ làm ứng viên có evidence |
| 03 | `_infer_str_format_call`, dòng 951: thêm `or len(inferred_keyword) == 0`; trường hợp dùng positional args/không keyword bị trả Uninferable dù hợp lệ, năm failure | [Candidate](../runs/generate-20261029T235638993708Z/attempt-03/candidate.py), [log](../runs/verify-20261029T235649711472Z/attempt-03/candidate-1.stdout.txt). Logic/edge-case guard; độ chắc chắn cao trong test scope |

Các dòng assertion về Const/chuỗi là nơi test phát hiện; các edit trong brain function mới là vị trí nguyên nhân agent đề xuất. Người dùng review giữ các ứng viên và mức chấp nhận marker; chưa duyệt nhãn gold/khả năng đại diện.

## pvlib #1072 — giá trị nhiệt độ

[Generation](../runs/generate-20261029T235810212189Z/manifest.json), [verification](../runs/verify-20261029T235820935739Z/manifest.json). Hai candidate khác byte gây numerical assertion failures ổn định; một output không đổi.

| Lượt | Giải thích nguyên nhân | Evidence / kiến nghị |
|---|---|---|
| 01 | `pvlib/temperature.py:593`, `fuentes`: đổi mẫu số hiệu chỉnh cap từ 12 thành 13. Series tính ra lệch expected, một failure | [Candidate](../runs/generate-20261029T235810212189Z/attempt-01/candidate.py), [log](../runs/verify-20261029T235820935739Z/attempt-01/candidate-1.stdout.txt). Logic/numeric parameter, giữ làm ứng viên; không suy mô hình nhiệt vật lý được validation đầy đủ chỉ từ một test |
| 02 | Dòng 606: thêm 10 vào `temp_air + 273.15`, làm ambient temperature lệch 10 K; bốn test fail | [Candidate](../runs/generate-20261029T235810212189Z/attempt-02/candidate.py), [log](../runs/verify-20261029T235820935739Z/attempt-02/candidate-1.stdout.txt). Logic/numeric offset; cơ chế rõ nhưng hằng số tùy ý cần đánh giá tính tự nhiên |
| 03 | Đề xuất thay `if tinoct > 321.15:` bằng chính dòng đó; validator ghi Unchanged site, không có candidate | [Proposal](../runs/generate-20261029T235810212189Z/attempt-03/proposal.json). Giữ invalid_output trong mẫu số; không gán nhãn lỗi thực thi hoặc sửa output cho qua |

Độ chắc chắn cao rằng edit giải thích kết quả numerical; không có bằng chứng về mức đại diện lỗi thực tế. Người dùng review kiến nghị ứng viên và curation constants, training pending.

## FastAPI #15232-r1 — API decorator và WebSocket

[Generation](../runs/generate-20261030T000107782911Z/manifest.json), [verification](../runs/verify-20261030T000118300588Z/manifest.json). Profile này chỉ sửa recipe pytest/plugin sau build failure, có `trial_of`; không phải case nguồn mới.

| Lượt | Kết luận và giải thích | Evidence / kiến nghị |
|---|---|---|
| 01 | `fastapi/routing.py:1487`, `add_api_websocket_route`: đổi default dependencies từ None sang list Depends. Ba HTTP mount tests vẫn pass | [Candidate](../runs/generate-20261030T000107782911Z/attempt-01/candidate.py), [log](../runs/verify-20261030T000118300588Z/attempt-01/candidate-1.stdout.txt). Không có failure được chứng minh; test scope HTTP không xác nhận mọi hành vi WebSocket đúng. Không dùng làm synthetic-failure/negative gold |
| 02 | Dòng 1568, decorator của WebSocket: `return func` → `return None`. Cùng bộ HTTP tests vẫn pass | [Candidate](../runs/generate-20261030T000107782911Z/attempt-02/candidate.py), [log](../runs/verify-20261030T000118300588Z/attempt-02/candidate-1.stdout.txt). Có khả năng vi phạm API decorator nhưng chưa có execution witness ở test scope này; giữ lượt không đạt |
| 03 | `api_route`, dòng 1479: `return decorator` → `return None`. Khi `@sub_app.get(...)` cần callable decorator, nó nhận None, gây TypeError `'NoneType' object is not callable`; ba test fail ổn định | [Candidate](../runs/generate-20261030T000107782911Z/attempt-03/candidate.py), [log](../runs/verify-20261030T000118300588Z/attempt-03/candidate-1.stdout.txt). API/return contract, nguyên nhân khác vị trí test decorator báo lỗi. Kiến nghị giữ ứng viên development, nhãn/vị trí chính thức và train pending |

## Điều kiện dữ liệu và phần người dùng quyết định

- Không có nhãn generator trong v3; không suy thiếu nhãn thành unknown gold. Agent chỉ nêu mô tả tạm thời từ code/log.
- Các edit không thêm comment tiết lộ ý đồ. Marker X/extra hoặc offset tùy ý là vấn đề tính tự nhiên/shortcut phân phối, không tự đồng nghĩa lộ đáp án; input 3B thực tế chưa được đóng gói. Source code/stack trace đúng contract là evidence được phép.
- Reference patch, explanations và assessment nằm ngoài input chẩn đoán. Hai cohort chỉ development; không đánh giá độc lập hoặc training eligibility tự động.
- Người dùng review các kiến nghị sử dụng, đặc biệt syntax-violation và artificial markers. Không yêu cầu tự dò lại code/log. **Mọi confirmed label/location, reviewer và training approval mới vẫn pending; raw review.json không đổi.**
