# Phân tích lỗi và hiệu quả synthetic — evaluation v1

Đây là bản phân tích kỹ thuật của kết quả đã khóa, chưa phải slide/báo cáo bảo vệ giữa kỳ. [Bảng điểm](evaluation-results.md), [validation](evaluation-validation.md), [protocol](evaluation-protocol-v1.md). M1-P2 dùng prompt mới; raw responses và nhãn không bị chỉnh sửa.

## Quan sát và giới hạn diễn giải

**Kết quả chính:** M5 đúng loại lỗi 24/38 so với M2 22/38 (+5,26 điểm phần trăm), Macro-F1 0,3375 so với 0,3132. Định vị hàm tăng từ 6/38 lên 7/38, nhưng định vị file giảm từ 18/38 xuống 16/38; joint cùng 4/38. Theo từng mẫu: phân loại M5 thắng 4/thua 2, hàm thắng 2/thua 1, joint thắng 1/thua 1. Không có cải thiện đồng đều trên mọi nhiệm vụ.

Mức tăng phân loại tập trung ở Pylint: M2 10/19, M5 12/19; Flask cùng 2/3 và Pytest cùng 10/16. Trên Pytest, joint M5 giảm từ 3/16 xuống 2/16; trên Pylint tăng từ 0/19 lên 1/19. Đây là quan sát của một seed và ba repo, chưa phải chứng cứ thống kê hoặc kết luận nhân quả về synthetic.

Hai lớp train đều thiếu dependency/configuration và syntax. Cả M2/M5 không nhận đúng trường hợp nào trong 8 test dependency/configuration; syntax không có support test. M5 tăng recall logic/value từ 15/21 lên 18/21 nhưng giảm API/type từ 7/9 xuống 6/9. Không thể dùng accuracy tổng để che khoảng trống lớp này.

**Format, retrieval và nhãn:** M1-P2 có 8/38 output invalid, đều có Markdown fence; không mẫu nào trong tám mẫu chạm trần 384 token. Giữ nguyên strict parser. Reference hàm vắng khỏi context ở 26/38 mẫu; mỗi SFT có 3 prediction trùng cặp reference trực tiếp nhưng không được scorer hiện hành tính credit vì cổng visibility. Đây là giới hạn của toàn pipeline/chấm điểm, không được tự chuyển thành lỗi suy luận. Với nhãn silver, các bất đồng taxonomy hoặc causal absence vẫn cần rà ở phiên bản dữ liệu tương lai, không sửa nhãn sau test.

**Chi phí:** parent + continuation của M2 là 4.387 giây (73,12 phút), M5 là 6.324 giây (105,40 phút). Chi phí này gồm phần học tiếp đến 10 epoch dù adapter được chọn vẫn là parent104. Bốn phase suy luận mới dùng 1.339,69 giây inference; thời gian evaluation tính theo hợp các operation là 1.445/7.200 giây. [Bảng chi phí](evaluation-results.md#chi-phí-thực-đo) tách M1 cũ, M1-P2 mới, train và test; không suy ra chi phí tiền hoặc thời gian GPU từ wall time.

Đã đối chiếu từng38mẫu với prediction, reference và retrieved locations; kiểm tra hash log/manifest/patch và đọc source bằng text/AST. Không chạy candidate, Docker hoặc model để sửa thiếu sót. Chi tiết38mẫu nằm tronganalysisJSON của run; cơ chế silver có sẵn được ghi nguồn, không coi là phê duyệt chuyên gia mới.

- Nhóm format/schema, abstention, bất đồng với silver và reference không có trong context có thể chồng nhau. Một tỷ lệ thấp chưa đủ quy toàn bộ lỗi cho model.
- Nhãn có giới hạn/diễn giải thay thế được giữ nguyên và pending. Đã có các ghi chú từ trước test: ví dụ config-path có thể được mô tả ở mức logic/API, missing-method không phải dòng code đang tồn tại. Không sửa đáp án sau khi nhìn prediction.
- M2/M5 đã tiêu ngân sách10epoch nhưng checkpoint được chọn đều104, tương ứng4,73/2,99epoch. Vì vậy đây là so sánh adapter được chọn theo validation dưới ngân sách continuation, không phải test hai adapter cuối epoch10.
- Train real có134logic/value/41API/type; synthetic95logic/value/6API/type. Mixed tăng tỷ trọnglogic/value từ76,57% lên82,97%, không bổ sung syntax/dependency-config. Đây là yếu tố phân bố cần cân nhắc, không chứng minh nguyên nhân cải thiện hoặc suy giảm.

## Mẫu bất đồng M2/M5

| Case | Silver | M2 loại/hàm/joint | M5 loại/hàm/joint | Cơ chế theo assessment đã lưu |
|---|---|---|---|---|
| pylint-dev__pylint-4175 | logic/value | sai/sai/sai | đúng/sai/sai | check_parallel first lets map/reduce checkers update linter.stats, then overwrites those reducer-produced statistics by merging only worker stats. Including the existing linter.stats in the merge preserves reducer messages and restores single-process/parallel equivalence. |
| pylint-dev__pylint-4492 | dependency/configuration | sai/sai/sai | sai/đúng/sai | The reporter loader treats a comma-separated multi-format setting with an output path as one reporter identifier. It then tries to resolve that entire value and raises InvalidReporterError. Parsing the individual reporter specifications and composing reporters allows the saved multi-format test to pass. |
| pylint-dev__pylint-5743 | API/type | đúng/sai/sai | sai/sai/sai | Unexpected AST-building exceptions are caught and converted directly to an astroid-error message inside get_ast. That consumes the exception before the caller can generate its fatal-error issue template. Reraising a chained AstroidBuildingError routes it through the callers intended error protocol. |
| pylint-dev__pylint-6506 | logic/value | sai/sai/sai | đúng/sai/sai | The unknown-option branch emits a linter message and raises an internal _UnrecognizedOptionError instead of routing the invalid option through argparse error handling. The parser error path supplies the expected user-facing error and exit behavior. |
| pylint-dev__pylint-7228 | API/type | sai/sai/sai | đúng/sai/sai | The comma-separated regex transformer calls re.compile directly without translating re.error into argparse.ArgumentTypeError. An invalid pattern therefore escapes as a regex exception rather than the CLI input-error protocol. The new wrapper performs that translation; the plain-regexp registry is also routed through it. |
| pylint-dev__pylint-7993 | logic/value | đúng/sai/sai | đúng/đúng/đúng | The message-template field regex accepts arbitrary characters between braces, so literal escaped JSON braces are consumed as an unsupported field. The subsequent cleanup deletes valid template text and leaves a malformed report. Restricting the captured field name to word characters keeps the literal header while substituting category. |
| pytest-dev__pytest-7499 | logic/value | đúng/đúng/đúng | đúng/sai/sai | The mismatch diagnostic still uses the old Pattern ... does not match text and lacks the revised punctuation/escaping hint. Saved assertions require the Regex pattern ... message and fail on the difference. Building the required diagnostic in this method restores the contract. |
| pytest-dev__pytest-7500 | logic/value | sai/sai/sai | đúng/sai/sai | The lock-eligibility check uses exists rather than checking a usable lock file with guarded is_file. In the saved inaccessible-lock simulation it proceeds to remove the lock and returns True when eligibility must be False. Guarding is_file errors preserves the conservative no-delete decision. |
| pytest-dev__pytest-9279 | API/type | đúng/sai/sai | sai/sai/sai | The cooperative constructor forwards name and parent as keywords to an Item/File multiple-inheritance chain whose legacy file constructor expects the first value positionally. Path propagation is lost and the saved stack reaches _imply_path with both path and fspath None. Positional forwarding preserves that compatibility contract. |

Không gọi mẫu M5đúng/M2sai là bằng chứng nhân quả của một synthetic cụ thể: chưa có ablation hoặc can thiệp theo từng mẫu train. Điểm và số thắng/thua là quan sát, không phải kết luận tổng quát.

## Tám chuỗi bằng chứng đã đọc chi tiết

### pallets__flask-4160

**Quan sát và cơ chế:** Decimal đi vào encoder không có nhánh chuyển đổi → fallback standard JSON encoder → TypeError Object of type Decimal is not JSON serializable. Patch thêm Decimal vào nhánh UUID trả str. Lỗi được phát hiện trong stdlib nhưng causal function là JSONEncoder.default của Flask.

**Bằng chứng:** [log lỗi local](../runs/reproduce-20261111T233102382247Z/historical-base.stdout.txt); [log fixed pass](../runs/reproduce-20261111T233102382247Z/historical-fixed.stdout.txt); [repair patch](../.cache/dataset-v1-source/cases/pallets__flask-4160-ds1-extra/repair.patch); [assessment silver](../.cache/dataset-v1/records-retrieval-v2/pallets__flask-4160/assessment.json).

- [src/flask/json/__init__.py](../.cache/case-contexts/pallets__flask-4160-ds1-extra/5ebc497be74fb60a/reproduce-20261111T233102382247Z/base/src/flask/json/__init__.py) — JSONEncoder.default, line 42, status `definition_present`, source hash verified=True.

**Prediction và điểm theo protocol:**

| Model | Loại | Vị trí | Loại/hàm/joint |
|---|---|---|---|
| M1-P2 | API/type | flask/json/__init__.py::JSONEncoder.default; flask/json/__init__.py::dumps | đúng/sai/sai; [raw](../runs/evaluation-20261112T210848574175Z/test-M1-P2/213b93c8c73da270e210/result.json) |
| M2 | API/type | src/flask/json/__init__.py::JSONEncoder.default | đúng/đúng/đúng; [raw](../runs/evaluation-20261112T210848574175Z/test-M2/213b93c8c73da270e210/result.json) |
| M5 | API/type | src/flask/json/__init__.py::JSONEncoder.default | đúng/đúng/đúng; [raw](../runs/evaluation-20261112T210848574175Z/test-M5/213b93c8c73da270e210/result.json) |

**Nhận định kỹ thuật:** M1-P2 nêu được vấn đề Decimal nhưng trả đường dẫn flask/json/... thiếu src/. M2 trỏ đúng src/flask/json/__init__.py::JSONEncoder.default. Cần tách convention đường dẫn và mức hiểu cơ chế, không tự chuẩn hóa đường dẫn sau test.

**Phần chưa xác nhận:** đây là phân tích evidence và bất đồng với silver; không đổi nhãn, không tự phê duyệt gold hoặc training eligibility. Nếu cần đổi taxonomy/vị trí trong tương lai, phải tạo phiên bản dataset riêng và không dùng điểm test này để chọn lại model.

### pylint-dev__pylint-4812

**Quan sát và cơ chế:** read_config_file chỉ expanduser → giữ nguyên ${tmp_path_env} → exists kiểm tra literal và phát sinh OSError. Patch gọi expandvars trước kiểm tra tồn tại. Đây là defect xử lý cấu hình trong sản phẩm, không phải thiếu pytest hoặc Docker setup.

**Bằng chứng:** [log lỗi local](../runs/reproduce-20261111T202555799166Z/historical-base.stdout.txt); [log fixed pass](../runs/reproduce-20261111T202555799166Z/historical-fixed.stdout.txt); [repair patch](../.cache/dataset-v1-source/cases/pylint-dev__pylint-4812-ds1/repair.patch); [assessment silver](../.cache/dataset-v1/records-retrieval-v2/pylint-dev__pylint-4812/assessment.json).

- [pylint/config/option_manager_mixin.py](../.cache/case-contexts/pylint-dev__pylint-4812-ds1-env2/339c3d089aef6981/reproduce-20261111T202555799166Z/base/pylint/config/option_manager_mixin.py) — OptionsManagerMixIn.read_config_file, line 238, status `definition_present`, source hash verified=True.

**Prediction và điểm theo protocol:**

| Model | Loại | Vị trí | Loại/hàm/joint |
|---|---|---|---|
| M1-P2 | invalid | — | sai/sai/sai; [raw](../runs/evaluation-20261112T210848574175Z/test-M1-P2/0b20cb82300554723bcc/result.json) |
| M2 | API/type | pylint/config/option_manager_mixin.py::OptionsManagerMixIn.read_config_file | sai/đúng/sai; [raw](../runs/evaluation-20261112T210848574175Z/test-M2/0b20cb82300554723bcc/result.json) |
| M5 | logic/value | pylint/config/option_manager_mixin.py::OptionsManagerMixIn.read_config_file | sai/đúng/sai; [raw](../runs/evaluation-20261112T210848574175Z/test-M5/0b20cb82300554723bcc/result.json) |

**Nhận định kỹ thuật:** Nhãn dependency/configuration là silver; API/type hoặc logic là cách nhìn khác ở mức thô đã được assessment ghi nhận. M1-P2 bị strictparse do Markdown; không bỏ fence để thay điểm. M2 trỏ đúng hàm nhưng nhãn API/type khác reference và thêm chi tiết trailing slash không được patch/log hỗ trợ.

**Phần chưa xác nhận:** đây là phân tích evidence và bất đồng với silver; không đổi nhãn, không tự phê duyệt gold hoặc training eligibility. Nếu cần đổi taxonomy/vị trí trong tương lai, phải tạo phiên bản dataset riêng và không dùng điểm test này để chọn lại model.

### pylint-dev__pylint-6059

**Quan sát và cơ chế:** Hai checker có cùng dữ liệu vẫn so sánh không bằng vì base không có __eq__ theo giá trị. Assertion fake_checker_1 == fake_checker_2 fail; patch thêm __eq__ so tên/messages. __gt__ và thay ngoặc không phải nguyên nhân được assertion equality chứng minh.

**Bằng chứng:** [log lỗi local](../runs/reproduce-20261111T203516841649Z/historical-base.stdout.txt); [log fixed pass](../runs/reproduce-20261111T203516841649Z/historical-fixed.stdout.txt); [repair patch](../.cache/dataset-v1-source/cases/pylint-dev__pylint-6059-ds1/repair.patch); [assessment silver](../.cache/dataset-v1/records-retrieval-v2/pylint-dev__pylint-6059/assessment.json).

- [pylint/checkers/base_checker.py](../.cache/case-contexts/pylint-dev__pylint-6059-ds1-env2/e433fb8dd3468cc4/reproduce-20261111T203516841649Z/base/pylint/checkers/base_checker.py) — BaseChecker.__eq__, line không có definition trong base, status `definition_absent_in_base_requires_patch_context`, source hash verified=True.

**Prediction và điểm theo protocol:**

| Model | Loại | Vị trí | Loại/hàm/joint |
|---|---|---|---|
| M1-P2 | logic/value | pylint/checkers/base_checker.py::BaseChecker.__gt__; pylint/extensions/comparison_placement.py::&lt;module&gt;; pylint/message/message.py::Message.format; pylint/checkers/refactoring/refactoring_checker.py::ConsiderUsingWithStack.clear_all | đúng/sai/sai; [raw](../runs/evaluation-20261112T210848574175Z/test-M1-P2/3467276d99991b79d265/result.json) |
| M2 | logic/value | pylint/checkers/base_checker.py::BaseChecker.__eq__ | đúng/sai/sai; [raw](../runs/evaluation-20261112T210848574175Z/test-M2/3467276d99991b79d265/result.json) |
| M5 | logic/value | pylint/checkers/base_checker.py::BaseChecker.__eq__ | đúng/sai/sai; [raw](../runs/evaluation-20261112T210848574175Z/test-M5/3467276d99991b79d265/result.json) |

**Nhận định kỹ thuật:** Reference BaseChecker.__eq__ là causal absence được contract cho phép. Scorer hiện vẫn yêu cầu reference xuất hiện trong retrieved context, nên có thể từ chối credit dù prediction nêu đúng cặp đó. M2 nêu đúng cặp nhưng giải thích như thể __eq__ đã tồn tại và sai class identity; M1-P2 lại đổ lỗi cho test dùng ==. Đúng tên vị trí không chứng minh đúng giải thích. Gold/location confirmation vẫn pending.

**Phần chưa xác nhận:** đây là phân tích evidence và bất đồng với silver; không đổi nhãn, không tự phê duyệt gold hoặc training eligibility. Nếu cần đổi taxonomy/vị trí trong tương lai, phải tạo phiên bản dataset riêng và không dùng điểm test này để chọn lại model.

### pylint-dev__pylint-6357

**Quan sát và cơ chế:** Checker bỏ các dòng disabled trước khi parse intermediate source → có thể mất toàn bộ suite sau def → AstroidSyntaxError. Patch giữ source gốc cho parse và áp filter sau. Source ban đầu hợp lệ; lỗi cú pháp là triệu chứng downstream của logic preprocessing.

**Bằng chứng:** [log lỗi local](../runs/reproduce-20261111T234743009042Z/historical-base.stdout.txt); [log fixed pass](../runs/reproduce-20261111T234743009042Z/historical-fixed.stdout.txt); [repair patch](../.cache/dataset-v1-source/cases/pylint-dev__pylint-6357-ds1/repair.patch); [assessment silver](../.cache/dataset-v1/records-retrieval-v2/pylint-dev__pylint-6357/assessment.json).

- [pylint/checkers/similar.py](../.cache/case-contexts/pylint-dev__pylint-6357-ds1-env2/a8c802669926fbed/reproduce-20261111T234743009042Z/base/pylint/checkers/similar.py) — Similar.append_stream, line 359, status `definition_present`, source hash verified=True.

**Prediction và điểm theo protocol:**

| Model | Loại | Vị trí | Loại/hàm/joint |
|---|---|---|---|
| M1-P2 | syntax | raw_strings_disable_scope_second_function/first.py::Class.method | sai/sai/sai; [raw](../runs/evaluation-20261112T210848574175Z/test-M1-P2/fd95119b8c6499055eac/result.json) |
| M2 | logic/value | pylint/checkers/similar.py::LineSet.__init__ | đúng/sai/sai; [raw](../runs/evaluation-20261112T210848574175Z/test-M2/fd95119b8c6499055eac/result.json) |
| M5 | logic/value | pylint/checkers/similar.py::stripped_lines | đúng/sai/sai; [raw](../runs/evaluation-20261112T210848574175Z/test-M5/fd95119b8c6499055eac/result.json) |

**Nhận định kỹ thuật:** M1-P2 dự đoán syntax và vị trí trong fixture input; đó là nơi có symptom, không phải nơi gây lỗi trong checker. M2 dự đoán logic/value nhưng trỏ LineSet.__init__ và giải thích raw-string delimiter, chưa khớp cơ chế append_stream đã được patch/log hỗ trợ.

**Phần chưa xác nhận:** đây là phân tích evidence và bất đồng với silver; không đổi nhãn, không tự phê duyệt gold hoặc training eligibility. Nếu cần đổi taxonomy/vị trí trong tương lai, phải tạo phiên bản dataset riêng và không dùng điểm test này để chọn lại model.

### pytest-dev__pytest-8422

**Quan sát và cơ chế:** Factory _approx_scalar tạo ApproxScalar chung cho Decimal trong list/dict → tolerance nhân float với Decimal → TypeError. Patch dispatch sang ApproxDecimal. Tolerance là nơi phát hiện lỗi, factory mới là causal site.

**Bằng chứng:** [log lỗi local](../runs/reproduce-20261112T012306727341Z/historical-base.stdout.txt); [log fixed pass](../runs/reproduce-20261112T012306727341Z/historical-fixed.stdout.txt); [repair patch](../.cache/dataset-v1-source/cases/pytest-dev__pytest-8422-ds1-eval/repair.patch); [assessment silver](../.cache/dataset-v1/records-retrieval-v2/pytest-dev__pytest-8422/assessment.json).

- [src/_pytest/python_api.py](../.cache/case-contexts/pytest-dev__pytest-8422-ds1-eval-scm1/97be6155f9a498bb/reproduce-20261112T012306727341Z/base/src/_pytest/python_api.py) — ApproxBase._approx_scalar, line 74, status `definition_present`, source hash verified=True.

**Prediction và điểm theo protocol:**

| Model | Loại | Vị trí | Loại/hàm/joint |
|---|---|---|---|
| M1-P2 | API/type | _pytest/python_api.py::ApproxScalar.tolerance; _pytest/python_api.py::__eq__; _pytest/python_api.py::__eq__; _pytest/python_api.py::__eq__; _pytest/python_api.py::__eq__ | đúng/sai/sai; [raw](../runs/evaluation-20261112T210848574175Z/test-M1-P2/75e0af1a8d0878da28fc/result.json) |
| M2 | API/type | src/_pytest/python_api.py::ApproxScalar.tolerance | đúng/sai/sai; [raw](../runs/evaluation-20261112T210848574175Z/test-M2/75e0af1a8d0878da28fc/result.json) |
| M5 | API/type | _pytest/python_api.py::ApproxScalar.tolerance | đúng/sai/sai; [raw](../runs/evaluation-20261112T210848574175Z/test-M5/75e0af1a8d0878da28fc/result.json) |

**Nhận định kỹ thuật:** Cả ba model cùng nghiêng về ApproxScalar.tolerance. M1-P2 và M5 còn thiếu src/ ở đường dẫn. Dù nhận diện đúng API/type, vị trí chưa phải factory mà repair xác nhận. M2 đề nghị float(Decimal), một phương án chưa được evidence kiểm chứng; không coi là gold chỉ vì hợp lý bề ngoài.

**Phần chưa xác nhận:** đây là phân tích evidence và bất đồng với silver; không đổi nhãn, không tự phê duyệt gold hoặc training eligibility. Nếu cần đổi taxonomy/vị trí trong tương lai, phải tạo phiên bản dataset riêng và không dùng điểm test này để chọn lại model.

### pylint-dev__pylint-4492

**Quan sát và cơ chế:** Chuỗi cấu hình json:<output>,text,... được coi như một tên reporter duy nhất → resolver tìm module json:/tmp/... → ImportError rồi InvalidReporterError. Repair tách dấu phẩy, tách tên/output tại dấu hai chấm và ghép MultiReporter. Hàm cũ PyLinter._load_reporter là causal site dù repair thay tên/sắp xếp lại nhiều hàm.

**Bằng chứng:** [log lỗi local](../runs/reproduce-20261112T001215506951Z/historical-base.stdout.txt); [log fixed pass](../runs/reproduce-20261112T001215506951Z/historical-fixed.stdout.txt); [repair patch](../.cache/dataset-v1-source/cases/pylint-dev__pylint-4492-ds1-extra/repair.patch); [assessment silver](../.cache/dataset-v1/records-retrieval-v2/pylint-dev__pylint-4492/assessment.json).

- [pylint/lint/pylinter.py](../.cache/case-contexts/pylint-dev__pylint-4492-ds1-extra/34ad160613dbdf87/reproduce-20261112T001215506951Z/base/pylint/lint/pylinter.py) — PyLinter._load_reporter, line 530, status `definition_present`, source hash verified=True.

**Prediction và điểm theo protocol:**

| Model | Loại | Vị trí | Loại/hàm/joint |
|---|---|---|---|
| M1-P2 | logic/value | pylint/lint/pylinter.py::_load_reporter; pylint/lint/pylinter.py::_load_reporter_class; pylint/lint/pylinter.py::load_default_plugins; pylint/__pkginfo__.py::&lt;module&gt;; pylint/lint/pylinter.py::_get_file_descr_from_stdin | sai/sai/sai; [raw](../runs/evaluation-20261112T210848574175Z/test-M1-P2/0016caf3b847746095a8/result.json) |
| M2 | API/type | pylint/lint/reporters/json.py::JSONReporter.__init__ | sai/sai/sai; [raw](../runs/evaluation-20261112T210848574175Z/test-M2/0016caf3b847746095a8/result.json) |
| M5 | logic/value | pylint/lint/pylinter.py::PyLinter._load_reporter | sai/đúng/sai; [raw](../runs/evaluation-20261112T210848574175Z/test-M5/0016caf3b847746095a8/result.json) |

**Nhận định kỹ thuật:** M5 định vị đúng _load_reporter, M2 đưa đường dẫn pylint/lint/reporters/json.py và constructor không phải causal site. Tuy vậy M5 tự thêm so sánh nopreport/json và lỗi extension separator không được patch/log hỗ trợ. Hai model đều khác nhãn silver dependency/configuration. Đây là thắng về vị trí của M5, không phải joint hoặc một lời giải thích hoàn chỉnh.

**Phần chưa xác nhận:** đây là phân tích evidence và bất đồng với silver; không đổi nhãn, không tự phê duyệt gold hoặc training eligibility. Nếu cần đổi taxonomy/vị trí trong tương lai, phải tạo phiên bản dataset riêng và không dùng điểm test này để chọn lại model.

### pylint-dev__pylint-7993

**Quan sát và cơ chế:** Regex \{(.+?)(:.*)?\} trong TextReporter.on_set_current_module nhận cả đoạn literal JSON trong template {{ "Category": "{category}" }} như field không hỗ trợ → nhánh cleanup xóa phần hợp lệ → log chỉ còn '" }' thay vì category convention. Repair giới hạn tên field bằng \w+?.

**Bằng chứng:** [log lỗi local](../runs/reproduce-20261111T201220091415Z/historical-base.stdout.txt); [log fixed pass](../runs/reproduce-20261111T201220091415Z/historical-fixed.stdout.txt); [repair patch](../.cache/dataset-v1-source/cases/pylint-dev__pylint-7993-ds1/repair.patch); [assessment silver](../.cache/dataset-v1/records-retrieval-v2/pylint-dev__pylint-7993/assessment.json).

- [pylint/reporters/text.py](../.cache/case-contexts/pylint-dev__pylint-7993-ds1-env2/c695ecab03375841/reproduce-20261111T201220091415Z/base/pylint/reporters/text.py) — TextReporter.on_set_current_module, line 166, status `definition_present`, source hash verified=True.

**Prediction và điểm theo protocol:**

| Model | Loại | Vị trí | Loại/hàm/joint |
|---|---|---|---|
| M1-P2 | logic/value | pylint/reporters/text.py::TextReporter.on_set_current_module; pylint/reporters/text.py::ParseableTextReporter.__init__; pylint/reporters/text.py::colorize_ansi; pylint/reporters/text.py::register; pylint/reporters/text.py::colorize_ansi | đúng/đúng/đúng; [raw](../runs/evaluation-20261112T210848574175Z/test-M1-P2/5365b7d34c04f7a11f79/result.json) |
| M2 | logic/value | pylint/reporters/text.py::TextReporter.on_message | đúng/sai/sai; [raw](../runs/evaluation-20261112T210848574175Z/test-M2/5365b7d34c04f7a11f79/result.json) |
| M5 | logic/value | pylint/reporters/text.py::TextReporter.on_set_current_module | đúng/đúng/đúng; [raw](../runs/evaluation-20261112T210848574175Z/test-M5/5365b7d34c04f7a11f79/result.json) |

**Nhận định kỹ thuật:** M5 trỏ đúng hàm parser và mô tả template tạo output sai, đạt joint; giải thích còn chưa nêu chính xác regex/cleanup. M2 trỏ TextReporter.on_message và đề xuất escape template, không khớp causal site. Đây là một trong hai mẫu joint khác nhau, không đủ suy ra synthetic nào đã dạy model xử lý regex.

**Phần chưa xác nhận:** đây là phân tích evidence và bất đồng với silver; không đổi nhãn, không tự phê duyệt gold hoặc training eligibility. Nếu cần đổi taxonomy/vị trí trong tương lai, phải tạo phiên bản dataset riêng và không dùng điểm test này để chọn lại model.

### pytest-dev__pytest-7499

**Quan sát và cơ chế:** ExceptionInfo.match dùng re.search đúng hợp đồng nhưng phát thông báo cũ Pattern ... does not match, thiếu tiền tố Regex, dấu chấm và gợi ý re.escape khi pattern bằng message. Các assertion so diagnostic string thất bại. Repair đổi nội dung thông báo và thêm hint, không thay regex engine.

**Bằng chứng:** [log lỗi local](../runs/reproduce-20261112T012540779445Z/historical-base.stdout.txt); [log fixed pass](../runs/reproduce-20261112T012540779445Z/historical-fixed.stdout.txt); [repair patch](../.cache/dataset-v1-source/cases/pytest-dev__pytest-7499-ds1-eval/repair.patch); [assessment silver](../.cache/dataset-v1/records-retrieval-v2/pytest-dev__pytest-7499/assessment.json).

- [src/_pytest/_code/code.py](../.cache/case-contexts/pytest-dev__pytest-7499-ds1-eval-scm1/18a294319786b4a3/reproduce-20261112T012540779445Z/base/src/_pytest/_code/code.py) — ExceptionInfo.match, line 605, status `definition_present`, source hash verified=True.

**Prediction và điểm theo protocol:**

| Model | Loại | Vị trí | Loại/hàm/joint |
|---|---|---|---|
| M1-P2 | logic/value | _pytest/_code/code.py::ExceptionInfo.match; _pytest/_code/code.py::&lt;module&gt; | đúng/sai/sai; [raw](../runs/evaluation-20261112T210848574175Z/test-M1-P2/9453d767dd026ec8f2e0/result.json) |
| M2 | logic/value | src/_pytest/_code/code.py::ExceptionInfo.match | đúng/đúng/đúng; [raw](../runs/evaluation-20261112T210848574175Z/test-M2/9453d767dd026ec8f2e0/result.json) |
| M5 | logic/value | src/_pytest/python_api.py::RaisesContext.excinfo.match | đúng/sai/sai; [raw](../runs/evaluation-20261112T210848574175Z/test-M5/9453d767dd026ec8f2e0/result.json) |

**Nhận định kỹ thuật:** M2 đúng loại/vị trí nên đạt joint, nhưng giải thích single regex atom/normalized repr chưa phản ánh thay đổi thông báo được patch chứng minh. M5 trỏ RaisesContext.excinfo.match trong python_api.py và bịa khác biệt re.match/re.search; vị trí/explanation không khớp. Đây là trường hợp M5 thua M2; điểm joint không tự chấm độ đúng của explanation.

**Phần chưa xác nhận:** đây là phân tích evidence và bất đồng với silver; không đổi nhãn, không tự phê duyệt gold hoặc training eligibility. Nếu cần đổi taxonomy/vị trí trong tương lai, phải tạo phiên bản dataset riêng và không dùng điểm test này để chọn lại model.

## Việc còn mở sau phân tích

- Giữ kết luận trong paired counts, ba repo và một seed; không dùng test này để chỉnh prompt, retrieval hoặc tăng epoch rồi chấm lại.
- Nếu mở dataset v2: rà chất lượng/độ nhất quán taxonomy trên development; bổ sung class support và định nghĩa cách chấm causal absence/path convention trước một test mới.
- Nghiên cứu parser/format và retrieval là các nhánh tương lai, không sửa điểm chính trong đợt đã khóa.
- Slide/báo cáo bảo vệ giữa kỳ sẽ bàn riêng sau ba đầu việc này.
