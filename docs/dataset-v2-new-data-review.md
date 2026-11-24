# Rà dữ liệu mới của v2

Đây là nhận định kỹ thuật từ source/diff và log thực thi đã lưu. Các nhãn là **silver đề xuất**; xác nhận người dùng, gold và training eligibility còn pending. Không chạy lại thí nghiệm để viết review. Các bản export hiện là prototype, chưa thuộc bộ v2 đã khóa.

## Pvlib — wave 1

Cả bốn case có base fail, fixed pass trên cùng harness; đã đối chiếu hash patch, toàn bộ inventory source/test và F2P/P2P bằng `real_evidence`. [Chi tiết, run IDs và hash](evidence/dataset-v2-pvlib-wave1-review.json). Mỗi mẫu là một lỗi nguồn; không lấy số assertion hoặc số hunk làm số mẫu.

| Case | Quan sát và nguyên nhân đề xuất | Nhãn / vị trí | Kiến nghị |
|---|---|---|---|
| pvlib-python-1072 | `np.diff(index).astype(float)` gặp `Timedelta` từ timestamp có timezone và báo TypeError tại temperature.py:602. Patch lấy số giây qua `Series.diff().dt.total_seconds()` rồi đổi sang giờ. Đây là giả định không đúng về biểu diễn/API thời gian; không có bằng chứng thiếu dependency. | API/type; `pvlib/temperature.py::fuentes`, dòng base 602–603 | Giữ ứng viên silver; chắc chắn cao trong môi trường đã ghim. |
| pvlib-python-1854 | Truyền một `Array` vào `PVSystem` đi tới `len(arrays)` và báo không có len tại pvsystem.py:223. Patch nhận diện Array đơn và bọc tuple một phần tử. Patch cũng mở rộng mô tả input được hỗ trợ. | API/type; `pvlib/pvsystem.py::PVSystem.__init__`, dòng base 223–230 | Giữ ứng viên silver cho tương thích Array đơn; không khái quát mọi iterable. |
| pvlib-python-1707 | Với `n=1, L=0`, test mong IAM bằng 0 tại 90/100 độ nhưng base trả NaN. Công thức có mẫu số bằng 0 và thiếu xử lý ranh giới ánh sáng từ phía sau; patch bổ sung ranh giới này và xử lý cảnh báo số học. | logic/value; `pvlib/iam.py::physical`, dòng base 166–218 | Giữ ứng viên silver. NaN/cảnh báo không tự trở thành lỗi API/type. |
| pvlib-python-1606 | Tối ưu golden-section ném `Iterations exceeded maximum` tại tools.py:383. Trần vòng lặp ước lượng riêng dừng trước khi thỏa hội tụ trong case đã lưu. Patch bỏ trần này, dùng độ rộng khoảng và trả ước lượng midpoint. | logic/value; `pvlib/tools.py::_golden_sect_DataFrame`, dòng base 351–393 | Giữ ứng viên silver; patch có nhiều thay đổi liên quan, log chứng minh trực tiếp lỗi dừng sớm, không chứng minh từng hunk là lỗi độc lập. |

**Đánh giá sử dụng:** test chỉ là nơi phát hiện; target trỏ hàm sản phẩm gây lỗi. Input chẩn đoán chỉ có log và code truy xuất từ bản lỗi, không có repair patch, assessment hay nhãn. Không phát hiện lý do loại chỉ vì comment upstream. Chưa chốt retrieval v2 cuối nên chưa kết luận coverage/leakage cho input cuối; bản prototype dùng retrieval hiện hành của pilot.

**Phần người dùng review:** có thể xem xét bốn lập luận và kiến nghị giữ ở trên; chưa yêu cầu tự dò code/log. Việc tiếp tục thu thập không tự xác nhận nhãn hoặc phê duyệt dùng để train.

## Sphinx và pytest — wave 1

Bốn case tiếp theo cũng đã qua đối chiếu source/test inventory, patch, F2P/P2P và log fixed pass. [Chi tiết và hash](evidence/dataset-v2-sphinx-pytest-wave1-review.json). Cả bốn nhãn đề xuất là logic/value; không lấy tên exception hoặc chữ “config” làm nhãn tự động.

| Case | Chuỗi nguyên nhân và bằng chứng | Vị trí đề xuất / độ chắc chắn | Kiến nghị và giới hạn |
|---|---|---|---|
| sphinx-7910 | `_skip_member` tra class qua globals của wrapper đã decorate. Lookup sai bị bắt exception, dẫn đến không nhận diện class sở hữu method. Test nhận None thay vì False. Patch unwrap trước lookup. | `sphinx/ext/napoleon/__init__.py::_skip_member`, base:441; vừa | Giữ ứng viên silver. Exception trung gian bị nuốt nên cơ chế namespace là suy luận từ code/patch, không có trace riêng. |
| sphinx-11192 | `index_page` nằm trong `write_doc`, pha ghi song song. Test search index chỉ có `index`, thiếu `nosearch` và `tocitem`. Patch chuyển cập nhật index sang pha serialized. | `sphinx/builders/html/__init__.py::StandaloneHTMLBuilder.write_doc` và `write_doc_serialized`; vừa | Giữ ứng viên silver. Log chứng minh mất mục index; trạng thái riêng của worker là giải thích từ cấu trúc code/patch, không phải phép đo bộ nhớ bổ sung. |
| pytest-10051 | `caplog.clear()` gọi reset để gán một list mới, nhưng stash của pha call vẫn trỏ list cũ. `get_records('call')` còn LogRecord cũ thay vì rỗng. Patch xóa list tại chỗ. Base:399/699 thể hiện đọc/lưu reference vào stash. | `src/_pytest/logging.py::LogCaptureHandler.reset` và `LogCaptureFixture.clear`; cao | Giữ ứng viên silver. Đây là code sản phẩm pytest; tên `_pytest` không khiến nó thành file test. |
| pytest-11044 | `testpaths` không khớp file, code chuyển sang tìm từ invocation directory nhưng thiếu cảnh báo cấu hình. Test không tìm thấy `No files were found in testpaths`; patch thêm cảnh báo và giữ fallback. | `src/_pytest/config/__init__.py::Config.parse`, base:1382–1387; vừa | Giữ ứng viên silver, nhãn tạm logic/value cho thiếu hành vi cảnh báo. Trigger là cấu hình nhưng chưa có bằng chứng dependency hoặc môi trường bị hỏng. |

Input prototype vẫn chỉ gồm log và failing code truy xuất không dùng reference. Target/repair/assessment nằm riêng. Nhận định, kiến nghị giữ, xác nhận người dùng và gold là các phần khác nhau; tất cả xác nhận của người dùng cho nhóm mới này còn pending. Không biến các trường hợp chắc chắn vừa thành nhãn gold.

## Hai case held-out đầu tiên

Rà nguyên nhân sau khi [input protocol v3](../data-manifests/dataset-v2-input-protocol.json) đã khóa, không dùng các mẫu này để chỉnh retrieval. [Receipt và hash](evidence/dataset-v2-first-heldout-review.json).

| Case / role | Kết luận và bằng chứng | Nhận định / kiến nghị |
|---|---|---|
| seaborn-3276 / validation | Base/fixed đạt strict gate. `norm=None` có mặt trong dictionary nên điều kiện `"norm" not in kws` bỏ qua vmin/vmax, làm màu khác với khi không truyền norm. JUnit báo khác RGBA; issue cũng mô tả mất vmin/vmax. Patch kiểm tra giá trị None ở `seaborn/matrix.py:301`. | logic/value tại `_HeatMapper.plot`, chắc chắn cao. Giữ ứng viên silver; target/repair/issue nằm ngoài input chẩn đoán. Đã xuất theo v3, vẫn pending final curation và xác nhận. |
| xarray-3812 / test | Base/fixed đạt strict gate: OPTIONS display_style từ text sang html, test mới đòi html. Issue “Turn on _repr_html_ by default?” hỏi thay đổi một mặc định đã có lựa chọn khác, không nêu defect hiện hữu. | Loại khỏi cohort real-fault v2 vì thay đổi tính năng/mặc định. Không ép nhãn logic/value chỉ do assertion fail. Giữ lượt thử, strict result, log/hash và lý do loại; không xuất mẫu này vào dataset. |

Số tái hiện đạt có thể lớn hơn số ứng viên được giữ. Không mô tả log tái dựng local là log CI lịch sử; không suy actor từ tác giả PR. Người dùng chưa xác nhận các kiến nghị mới hoặc nhãn gold.

## Bốn mẫu đầu được rà ở wave 2

[Receipt, source/patch/log hashes và bản xuất v3](evidence/dataset-v2-wave2-first4-review.json). Cả bốn có base fail, fixed pass và F2P/P2P khớp; issue nguồn xác nhận đây là hành vi lỗi hiện hữu. Các kiến nghị sau còn chờ người dùng xác nhận.

| Case | Nguyên nhân và bằng chứng | Nhãn / vị trí đề xuất | Kiến nghị |
|---|---|---|---|
| marshmallow-1359 | DateTime lồng trong List/Tuple nhận container làm đối số schema, nhưng đọc `schema.opts` như một Schema. Log báo List không có opts tại fields.py:1117. Patch lấy opts từ root Schema. | API/type; `src/marshmallow/fields.py::DateTime._bind_to_schema` | Giữ ứng viên silver; chắc chắn cao. Đây là regression được issue mô tả, không phải thiếu dependency. |
| astroid-1268 | Visitor dispatch gọi `visit_unknown` chưa được triển khai. Log báo AsStringVisitor không có method đó; patch bổ sung method trả representation của Unknown. | API/type; `astroid/nodes/as_string.py::AsStringVisitor.visit_unknown` | Giữ ứng viên silver; ghi rõ causal absence, không bịa dòng method trong bản lỗi. NodeNG.accept là nơi phát hiện. |
| pytest-11160 | `WarningsRecorder.pop` lấy subclass đầu tiên, bỏ qua exact match hoặc lớp phù hợp hơn ở phía sau. Hai assertion nhận Child/ChildOfChild thay vì Parent/Child. | logic/value; `src/_pytest/recwarn.py::WarningsRecorder.pop` | Giữ ứng viên silver; lỗi chọn phần tử theo thứ tự, không phải warning class không hợp lệ. |
| sphinx-7350 | Khi phát sinh directive attribute/method, Napoleon không truyền tiếp noindex đã có trong options. Test thấy thiếu hai dòng `:noindex:`. | logic/value; `sphinx/ext/napoleon/docstring.py::GoogleDocstring._parse_attributes_section` và `_parse_methods_section` | Giữ ứng viên silver; đây là bỏ sót option đã tồn tại. Issue yêu cầu sửa việc option bị bỏ qua. |

Đã xuất cả bốn bằng input v3 đã khóa; reference, issue và assessment vẫn ở ngoài input. Chưa có nhãn gold hoặc training approval. Các mẫu không thấy causal function trong retrieved code vẫn giữ nguyên trạng thái coverage, không thêm reference vào truy xuất.

## Hai mẫu train tiếp theo ở wave 2

[Receipt và hash nguồn/log](evidence/dataset-v2-wave2-next2-review.json). Cả hai qua full real_evidence và xuất input v3 cố định; chưa có xác nhận người dùng, gold hoặc training approval.

| Case | Quan sát và giải thích | Nhãn/vị trí đề xuất; kiến nghị |
|---|---|---|
| sympy-24102 | Hai test parser báo SyntaxError ở mathematica.py:909, fixed pass. Biểu thức tokenizer tại dòng657 áp regex định hướng ASCII lên cả ký tự Hy Lạp, làm mất toán hạng; patch giữ nguyên toán hạng non-ASCII. | logic/value, MathematicaParser._from_mathematica_to_tokens; cao. Python không sai grammar: đây là exception do thư viện báo khi xử lý input hợp lệ. Giữ ứng viên silver. |
| marshmallow-1343 | Dữ liệu nested sai kiểu trả None; validator vẫn subscript như mapping và chỉ bắt KeyError. JUnit báo NoneType not subscriptable tại schema.py:894, fixed pass sau khi bắt thêm TypeError. | API/type, BaseSchema._invoke_field_validators; vừa. Mô tả việc dùng interface mapping trên None, đồng thời ghi ranh giới taxonomy với logic/error-path guarding. Giữ ứng viên silver. |

Log là tái dựng local; exception name không tự quyết định nhãn. Input chỉ có failing code/log, không chứa repair/issue/assessment. Người dùng review kết luận, không phải tự dò lại code/log.

## Bốn mẫu heldout tiếp theo

[Receipt, hash và xuất v3](evidence/dataset-v2-heldout-wave2-four-review.json). Đã rà sau khi input protocol khóa; không chỉnh retrieval từ heldout.

| Case / role | Quan sát → nguyên nhân đề xuất | Nhãn / vị trí và kiến nghị |
|---|---|---|
| seaborn-3407 / validation | MultiIndex tuple bị chuyển thành ndarray; pandas nhận thành nhiều key, báo KeyError [1] not in index. Giữ list tránh làm mất biểu diễn tuple. Fixed pass. | logic/value, PairGrid.map_diag tại seaborn/axisgrid.py:1475; giữ silver. Lỗi ở pandas là điểm phát hiện, không tự thành lỗi dependency. |
| xarray-3677 / test | Dataset.merge đưa DataArray vào nhánh cần interface items(), không đổi sang Dataset. Log báo thiếu DataArray.items; fixed pass. | API/type, Dataset.merge tại xarray/core/dataset.py:3607; giữ silver. common.py.__getattr__ là nơi phát hiện. |
| xarray-4629 / test | merge_attrs trả dictionary attrs đầu vào theo reference. Sửa attrs ở kết quả làm nguồn đổi x từ0 thành2. Fixed pass sau shallow copy. | logic/value, merge_attrs tại xarray/core/merge.py:504; giữ silver. Không khẳng định deep-copy mọi giá trị lồng nhau. |
| requests-6028 / test | Ghép lại URL bằng netloc nhưng bỏ phần auth được parse riêng, mất user/password trong hai test utility. Fixed pass. | logic/value, prepend_scheme_if_needed tại requests/utils.py:966–982; giữ silver. Không gọi proxy/network, không coi HTTP407 trong issue là kết quả local. |

Cả bốn đã đối chiếu full inventory, patch/log/JUnit và source F2P/P2P; Requests dùng profile hiệu chỉnh ID đã khai báo. Silver, xác nhận người dùng/gold/training vẫn pending. xarray4098 chưa được gán nhãn/chọn: issue chỉ nói groupby nên hỗ trợ name=None, còn cần phân biệt sửa lỗi với mở rộng điều kiện API.

## Bốn mẫu train: GitPython và wave 2

[Receipt, full inventory/log/patch hashes và bản xuất v3](evidence/dataset-v2-train-plus-gitpython-four-review.json). Nhãn đề xuất dưới đây còn pending xác nhận/gold/training.

| Case | Chuỗi nguyên nhân và phạm vi chứng minh | Nhãn / vị trí đề xuất |
|---|---|---|
| GitPython-946 | Constructor tzoffset cần offset, nhưng pickle mặc định không cung cấp đối số khi dựng lại object. Test pickle.loads báo thiếu secs_west_of_utc; sửa __reduce__ cung cấp constructor/offset/name và test pass. Control dashify pass hai phía. | API/type; tzoffset.__reduce__ (causal absence) và tzoffset.__init__, git/objects/util.py. Giữ silver; không bịa dòng method chưa có hoặc khẳng định đã chạy chương trình multiprocessing trong issue. |
| pytest-7571 | set_level đổi cả logger và handler, nhưng state/finalizer chỉ lưu/khôi phục logger. Handler level rò sang test kế tiếp; test nested nhận2fail thay vì3pass. Fixed pass. | logic/value; LogCaptureFixture._finalize, set_level và __init__, src/_pytest/logging.py. Giữ silver; chỉ xác nhận chuỗi test đã lưu, không mọi cách gọi set_level lặp lại. |
| SymPy-20916 | Regex module chỉ nhận chữ/digit ASCII, nên split_super_sub không tách Unicode letter/digit thành subscript. Assertion nhận tên chưa tách và list subscript rỗng; fixed pass. | logic/value; <module> (regex _name_with_digits_p) và split_super_sub, sympy/printing/conventions.py. Giữ silver. Ký tự Unicode ngoài BMP bị JUnit hiển thị #x...; source test thực có Unicode, không phải chuỗi literal #x. |
| astroid-1196 | Dict.getitem gọi .getitem lên AST Name của biểu thức unpack, chưa infer thành Dict. Hai test báo Name thiếu getitem tại node_classes.py:2364; fixed pass khi infer/check type trước. | API/type; Dict.getitem, astroid/nodes/node_classes.py. Giữ silver; TODO về overriding là giới hạn riêng, không coi mọi pattern unpack đều đã kiểm chứng. |

GitPython dùng upstream recovered local expectations, không phải F2P/P2P có sẵn từ nguồn. Cả bốn input chỉ là log/failing code theo v3 khóa; reference, patch, issue và nhận định ở ngoài input.

## AIDev: một lỗi cú pháp được kiểm chứng local

[Review/hash](evidence/dataset-v2-aidev-first-compilation-review.json), [coverage input](evidence/dataset-v2-aidev-compilation-input-coverage.json), run `reproduce-20261123T120616750003Z`. Case `aidev-3232895285`, repo tinystork/zeanalyser, [PR52](https://github.com/tinystork/zeanalyser/pull/52). Nguồn ghim từ AIDev; base/head là hai commit thật, không phải candidate synthetic.

- **Kết luận:** base không biên dịch được với Python3.11; head biên dịch pass bằng cùng owned harness. Đây là kiểm tra cú pháp local, chưa chạy GUI, dependency hay test pytest của repo; không phải log CI lịch sử.
- **Bằng chứng/cơ chế:** block sau `if processed_count > 0` dùng17dấu cách từ dòng3180, rồi lùi về16ở dòng3185; mức16không có trong stack indentation. Log báo IndentationError tại3185. Patch sửa block về16dấu cách; source blobs, full inventories và harness đều khớp hash.
- **Vị trí đề xuất:** syntax / `analyse_gui.py::AstroImageAnalyzerGUI.finalize_analysis`, chắc chắn cao. Header3117 và toàn bộ prefix trước nó không đổi so với fixed. Đây là hàm hiện hữu trong file lỗi cú pháp, không phải causal absence; dùng trường unparseable_definitions riêng. Dòng Python phát hiện lỗi và đầu block gây lỗi được phân biệt.
- **Kiến nghị:** giữ ứng viên silver cho chẩn đoán; không dùng làm seed sinh vì chỉ có compile check. AIDev metadata cho biết tác giả PR sửa lỗi, không chứng minh ai đưa lỗi vào code. Input giữ source/log, repair/PR/nhận định ở ngoài.
- **Giới hạn input/người dùng review:** v3 lấy được file lỗi nhưng không có tên finalize_analysis trong input đã xuất; không coi đây là mẫu đã đủ evidence để model trả đúng hàm. Giữ kết quả coverage thay vì thêm đáp án vào input hoặc loại âm thầm. Gold và training eligibility vẫn pending. Người dùng review các kết luận/kiến nghị này; không phải tự phân tích lại log.

## Sáu lượt AIDev từ đợt sàng lọc 20

[Receipt, run IDs, hash và nhận định](evidence/dataset-v2-aidev-screen20-compilation-review.json). Cả sáu giữ vai trò repo đã ghim trước kết quả. Chỉ kiểm chứng biên dịch Python3.11 bằng owned harness; không gọi là test chức năng hoặc CI lịch sử. Không có generator tự gán nhãn cho các case thật này.

| Case / role | Code → hành vi → log | Kiến nghị |
|---|---|---|
| 3194109543 / train | `Gallery_tab.add_tag_changes`: `last_tag` dòng718 ngang mức `if`716 nên block chỉ có comment, không có statement. Log báo expected an indented block, fixed pass khi indent assignment. Header507 không đổi. | syntax, chắc chắn cao; giữ ứng viên silver, đã export v4. |
| 3245143429 / validation | `_determine_bpjs_field_name`: sau docstring, assignment161 thụt thêm mức dù không mở block. Log unexpected indent, fixed pass. Repair còn sửa các nhánh khác; không coi từng lỗi tiềm ẩn là một lượt đã thực thi riêng. | syntax, chắc chắn cao; giữ ứng viên silver, đã export v4. |
| 3263598324 / validation | `AutoML.py`: khai báo class ở8932 bị đưa ra module, trong khi class tiếp theo tại8958 vẫn indent4; parser không có mức4 để quay về. Log phát hiện tại8958, repair đổi khai báo8932. | syntax, `<module>` vì nguyên nhân nằm ở khai báo class; giữ silver. Retrieval v4 chưa trả vị trí tham chiếu module: ghi miss, không sửa protocol từ heldout. |
| 3137319809 / train | `resolve` được chuyển từ module vào `AttackAction`, nhưng base và fixed đều compile pass. Thay đổi ownership có thể ảnh hưởng hành vi; compile-only không kiểm chứng được điều đó. | Loại khỏi subset lỗi cú pháp của harness này; không kết luận repo không có lỗi, không gán syntax theo tiêu đề. |
| 3136962971 / test | Đổi nesting của các thao tác reproject/combine; base và fixed đều compile pass. | Không xuất mẫu lỗi từ kết quả này; không suy nhãn từ thay đổi indentation, không tự retry test khác. |
| 3226294394 / train | Docstring tại6 không indent sau `def print_message`5; log expected an indented block, fixed pass. Repair còn thêm import/fallback và đổi annotation header. | Đề xuất syntax / `print_message`, nhưng giữ pending binding, chưa export: validator hiện yêu cầu prefix/header không đổi. Không ép sang module hoặc causal absence để vượt gate. |

GPL3 của case3226294394 được đọc từ LICENSE của đúng base; API hiện tại gợi ý MIT không thay giấy phép nguồn đã ghim. Lần chuẩn bị thất bại trước đó vẫn lưu; đây là lượt tái hiện đầu tiên, không phải retry môi trường.

Tất cả source/log/patch giữ nguyên. Input chỉ có failing source và log, không chứa repair, PR body hay assessment. Comment tự nhiên và stack trace không tự bị coi là lộ đáp án. Các nhãn/vị trí trên là nhận định kỹ thuật; người dùng review kết luận/kiến nghị, không phải tự dò lại log. Xác nhận người dùng, gold và training eligibility vẫn pending.

## Export v4, giữ lịch sử v3

[Kiểm tra chuyển27mẫu](evidence/dataset-v2-uniform-v4-export-27.json), [calibration train51](evidence/dataset-v2-retrieval-v4-train-calibration-51-r2.json), [protocol](../data-manifests/dataset-v2-input-protocol-v4.json). Cùng27danh tính, không cộng thêm27mẫu:26input không đổi; chỉ case3232895285 bổ sung được header hàm từ source quan sát. Nhãn/vị trí nguyên nhân và assessment không đổi, v3/raw giữ nguyên. Phần coverage v3 ở mục cũ là kết quả lịch sử, không bị viết lại.

Sau ba export mới, hiện có30ứng viên silver khác danh tính; chưa có final selection v2. Calibration16/51→17/51 là độ hiện diện header sau crop, không phải độ chính xác model. Với các mẫu mới, trường reference_location_retrieved trong receipt chỉ đo metadata retrieval trước token crop; không suy thành điểm hàm hay chẩn đoán.

## Rà13case tồn sau tái hiện

[Receipt, code/log hashes và assessment từng mẫu](evidence/dataset-v2-backlog13-data-review.json). Đã kiểm tra lại toàn bộ inventory source/test, patch và JUnit bằng `real_evidence`; xuất theo input v4 đã khóa. Không chạy lại source/model cho review.

| Case | Code → hành vi → log | Nhãn/vị trí đề xuất; kiến nghị |
|---|---|---|
| pydicom-1562 | So string PatientName trực tiếp với key Tag/int thay vì chuẩn hóa; trả False dù annotation/API cho phép keyword. Fixed chuẩn hóa Tag. | API/type; `dictionary_has_tag`; giữ silver, cao. Lỗi quan sát là boolean sai, không phải TypeError. |
| marshmallow-1229 | List/Mapping không nhận/truyền only/exclude đến Nested khi khởi tạo và bind; tám assertion về lựa chọn field sai, fixed pass. | logic/value; `List.__init__`, `List._bind_to_schema`, `Mapping.__init__`, `Mapping._bind_to_schema`; giữ, cao. |
| sphinx-9281 | Enum rơi vào repr chung, trả `<MyEnum.FOO: 1>` thay vì `MyEnum.FOO`; fixed xử lý Enum riêng. | logic/value; `object_description`; giữ, cao; lỗi biểu diễn có phạm vi hẹp. |
| pytest-9681 | Tạo module placeholder dù package thật có thể import; placeholder che package và làm import tests.subpath báo không phải package. | logic/value; `insert_missing_modules`; giữ, cao. Không phải thiếu dependency bên ngoài. |
| sympy-11787 | Bỏ mẫu số trước tìm nghiệm đưa nghiệm đã bị khử trở lại; test nhận -2 thay vì -1 cho biểu thức đã lưu. | logic/value; `nsolve`; giữ, cao. Không dùng ví dụ khác trong issue như một run đã đo. |
| seaborn-3216 | Figure do người dùng cấp bị đặt layout engine=None dù không yêu cầu đổi; test nhận NoneType thay MockEngine. | logic/value; `Plotter._finalize_figure`; giữ, cao; chưa đo lại ảnh/title. |
| seaborn-3217 | Đổi width riêng sang data space rồi căn giữa tuyến tính gây sai mép bar trên log scale; hai mép lẽ ra trùng lại khác nhau. | logic/value; `Plotter._unscale_coords` và `BarBase._make_patches`; giữ, cao. |
| seaborn-3394 | pd.NA còn trong suy kiểu nên dữ liệu số thành categorical; đường coordinate giữ nullable Int64 thay float. | logic/value; `_core.rules.variable_type`, `_oldcore.VectorPlotter.comp_data`; giữ, cao. |
| xarray-4098 | GroupBy chặn tên None bằng ValueError thay vì dùng tên mặc định; fixed pass. | logic/value; `GroupBy.__init__`; giữ đề xuất silver, vừa. Issue rất ngắn; ranh giới sửa restriction hay mở rộng API cần giữ trong curation. |
| xarray-5131 | Chuỗi repr có một space ngay trước newline, làm nhiều assertion biểu diễn fail; fixed bỏ space. | logic/value; `GroupBy.__repr__`; giữ, cao. Không gọi là lỗi cấu hình flake8 hay CI lịch sử đã đo. |
| sphinx-8951 | Thêm toán tử spaceship của C++20 vào grammar parser; log DefinitionError trên cú pháp C++ mới được hỗ trợ. | Kiến nghị loại khỏi subset lỗi hiện hữu vì là mở rộng tính năng; Python source không sai syntax. |
| pvlib-1653 | Issue có lỗi mô hình thật, nhưng patch đồng thời thêm string_factor trước angle_of_repose. Test mới gọi10đối số hoặc bị bind đối số thứ9 sang angle cũ. | Quarantine: lỗi giao diện mới và sai số mô hình bị trộn trong log, chưa xuất một nhãn đơn để train. Không sửa test hoặc chạy lại ngầm. |
| pvlib-1737 | Test mới truyền encoding, base chỉ báo unexpected keyword; patch còn đổi đọc thời gian/file. | Quarantine: failure này chưa tách riêng lỗi file/phút ban đầu. Giữ evidence, chưa xuất làm lỗi gốc được chứng minh. |

Mười bản export mới là ứng viên, không phải mười mẫu đã duyệt huấn luyện. Tổng hiện40danh tính silver v4; toàn bộ human confirmation, gold và training eligibility còn pending. Các comment/source/log trong input đã xác định, repair/issue/assessment ở ngoài. Các kiến nghị trên là phần để người dùng review, không phải yêu cầu người dùng tự phân tích code/log lại.

## Tám case wave3 và pip

[Receipt/hash/assessment](evidence/dataset-v2-wave3-plus-pip-review.json): sáu export silver, hai yêu cầu mở rộng tính năng được kiến nghị loại. Hai profile hiệu chỉnh vẫn là hai danh tính nguồn cũ, không tạo thêm case mới.

| Case | Quan sát → nguyên nhân đề xuất | Kiến nghị |
|---|---|---|
| xarray-2905 | `getattr(data, values, data)` bóc `.values` của object bất kỳ, làm đổi shape/kiểu trước dựng Variable. Log ValueError về dimensions/ndim; fixed giới hạn bóc giá trị cho đối tượng pandas. | API/type; `as_compatible_data`; giữ, cao. Profile r1 bổ sung bottleneck/sparse để toàn bộ P2P hết skip; test/source không sửa. |
| xarray-4419 | Dict kết quả chèn biến merge trước các biến concat, không tái lập đúng thứ tự ban đầu; assertion nhận x thay time. | logic/value; `_dataset_concat`; giữ, cao. Hunk ghi tên helper ensure_common_dims nhưng dòng sửa nằm ngoài helper. |
| xarray-3156 | Thiếu kiểm tra group rỗng ở constructor; test mong ValueError nhưng không raise. | logic/value; `GroupBy.__init__`; giữ, cao. StopIteration là mô tả issue, không phải exception đã thấy trong run này. |
| xarray-4802 | `np.ndim > 0` không đảm bảo có `.item()`; list một phần tử gây AttributeError. | API/type; `CFScaleOffsetCoder.decode`; giữ, cao; fixed chuyển sang ndarray trước lấy scalar. |
| xarray-3406 | Nhãn nhóm NaN và dữ liệu không được lọc đồng bộ; index10 vượt size9. | logic/value; `GroupBy.__init__`; giữ, cao; không chạy lại ví dụ ngẫu nhiên trong issue. |
| pip-10079 | So Link/URL nguyên trạng làm fragment egg dư thừa bị xem khác package; drop-egg assertion fail trên base, fixed pass; control khác hash pass cả hai. | logic/value; `links_equivalent`; giữ, cao. Unit offline, không phải full pip install hay log CI lịch sử; nguồn train không cung cấp F2P/P2P. |
| xarray-4248 | Issue yêu cầu hiển thị đơn vị trong overview; patch thêm hook biểu diễn inline. | Loại feature extension khỏi subset lỗi hiện hữu, không ép nhãn theo assertion mới. |
| xarray-3364 | Yêu cầu concat linh hoạt hơn khi thiếu biến; code cũ chủ động từ chối, patch đổi chính sách. | Loại feature extension; ValueError không tự chứng minh lỗi gốc. |

Nguồn pip đã đối chiếu original repair với blob upstream, giấy phép MIT tại base và hai node unit chọn trước chạy. Profile đầu lỗi do hai ghim setuptools/wheel của recipe mâu thuẫn bootstrap runner; chỉ r1 loại hai ghim trùng, raw thất bại vẫn giữ. Không tự thêm lần thử thứ ba.

## AIDev projected groups: load_icon

[Receipt](evidence/dataset-v2-aidev3857454812-review.json), run `reproduce-20261123T201622155100Z`, case3857454812 / validation. Source được lấy từ projection metadata tại revision ghim, không tạo body thay thế; Git blobs/API merge/license tại base được kiểm tra riêng.

Trong `19build_updated_v6.py`, try308 indent8 nhưng assignment309 vẫn indent8 nên try không có body. Log phát hiện309; repair một dòng dedent try về4. Fixed compile pass; header `load_icon`287 và prefix không đổi. Kiến nghị syntax / load_icon, chắc chắn cao cho lỗi grammar đã đo. Chưa import Tk/Pillow, chưa chạy GUI/icon và không dùng compile-only làm seed sinh. Input v4 lấy được vị trí hàm trước crop; không suy thành điểm chẩn đoán.

Ứng viên LSB-Helsinki không được thử vì chưa thấy giấy phép ở đúng base, dù API hiện tại gợi ý MIT. Metadata/title discovery không được cộng thành mẫu đạt. Sau đợt này47prototype khác danh tính; human/gold/training eligibility vẫn pending, final v2 selection vẫn0.

## Sàng lọc dependency/configuration sau khi hoàn tất lô nguồn

[Sàng lọc20case](../data-manifests/dataset-v2-aidev-dependency-screen-results20.json) có18case cần điều tra tiếp,1patch lớn và1HTTPerror. Đây là metadata, không phải18mẫu lỗi được chứng minh. [Triage4 chỉ đọc diff](evidence/dataset-v2-dependency-static-triage4.json) giữ hash và phần chưa biết:

| Case | Quan sát từ diff | Kiến nghị tiếp theo |
|---|---|---|
| Open-ipa-Library4023568668 | Thêm project root vào sys.path trước import src.orchestrator | Điều tra cách gọi chương trình và package resolution; chưa kết luận thiếu thư viện ngoài |
| Monkey-Head-Project3122497433 | Thêm pyyaml vào install_requires | Kiểm tra import thực tế và môi trường sạch; dependency bắc cầu có thể che lỗi |
| capsule-mcp3126899461 | Thêm fastapi trong pyproject | Kiểm tra fastmcp có cung cấp fastapi bắc cầu hay không, chưa có log fail/pass |
| pyics4005390637 | Diff thể hiện lặp bảng project.scripts/tool.setuptools ở base và sửa nhiều phần packaging | Ưu tiên xác minh file/license ở commit ghim; cần policy kiểm tra TOML và input cấu hình rõ ràng trước chạy/export |

Chưa có log thực thi cho bốn case này, chưa gán nhãn silver hoặc vị trí được xác nhận. Không có generator tham gia; gold/human/training vẫn pending. Không đưa patch sửa hoặc nhận định ở đây vào input chẩn đoán. 44case strict mới còn chờ phân tích nhân quả; tổng prototype vẫn47.


## Lô đã hoàn tất: năm case đầu

[Receipt và hash evidence](evidence/dataset-v2-completed-wave-first5-review.json). Cả năm đáp ứng kiểm chứng base/fixed với cùng test patch; không chạy lại để review. Các vị trí dưới đây là nguyên nhân đề xuất ở source base, khác dòng test phát hiện lỗi.

| Case | Quan sát và nguyên nhân | Kiến nghị |
|---|---|---|
| xarray4075, test | Weighted._sum_of_weights dòng145 dùng phép giảm boolean nên tổng hai trọng số thành1; mean thành2thay vì1. Fixed chuyển trọng số sang int. | Silver logic/value, chắc chắn cao |
| xarray3905, test | short_data_repr dòng450 trả repr trực tiếp; log ghi601dòng, yêu cầu<50. Fixed giới hạn độ dài nhánh này. | Silver logic/value, chắc chắn cao; không phải hỏng dữ liệu số |
| astroid1978, train | InspectBuilder.imported_member dòng474 gọi getattr không giữ/định tuyến stdout/stderr; test caplog thiếu chuỗi INFO mong đợi. Fixed ghi lại qua logger. | Silver logic/value, chắc chắn vừa: test mô phỏng hook, chưa chứng minh mọi FutureWarning từ numpy được xử lý |
| pytest8022, train | Session.collect dòng772–775 áp đặc lệ __init__.py cho cả DoctestModule và chỉ yield phần tử đầu; log1test thay vì2. Fixed chỉ áp cho Package. | Silver logic/value, chắc chắn cao |
| xarray4966, test | Bốn test yêu cầu giải mã unsigned thành signed với _Unsigned=false thất bại ở base, fixed pass. Issue mô tả quy ước trước đó chưa được hỗ trợ. | Quarantine ranh giới bug/feature; chưa gán taxonomy hoặc export |

Repair/issue/assessment nằm riêng khỏi input v4, không có nhãn generator cho các lỗi nguồn này. Kiến nghị giữ bốn prototype để tuyển chọn tiếp; người dùng chưa xác nhận nhãn, gold và training eligibility vẫn pending. Tổng51prototype (syntax5/API-type12/logic-value34/dependency0), finalselected0. Đếm đầy đủ theo run ID sửa backlog trước rà từ44thành45, còn40sau năm case này.


## Lô đã hoàn tất: năm case tiếp theo

[Receipt đầy đủ](evidence/dataset-v2-completed-wave-next5-review.json); cùng test patch trên base/fixed, inventory và log/reference hash đã kiểm tra. Đây là năm đề xuất silver, không phải gold hoặc duyệt training.

| Case train | Code → hành vi → log | Nhãn/vị trí đề xuất và giới hạn |
|---|---|---|
| Sphinx9711 | So sánh chuỗi3.9>3.10 làm từ chối phiên bản đủ mới; saved test báo VersionRequirementError, fixed pass | logic/value / verify_needs_extensions; không phải dependency chưa cài |
| Sympy21259 | Range.as_relational thiếu ràng buộc modulo bước nhảy; Range.size loại biểu thức symbolic trước rút gọn | logic/value / Range.as_relational, Range.size; mức vừa, repair hai cơ chế. So sánh biểu thức step1 đơn thuần chưa chứng minh lỗi ngữ nghĩa; step2 và cardinality hỗ trợ kết luận |
| Pytest11178 | _repr_compare trừ None và float khi tạo chi tiết assertion; outer test nhận2dòng thay6, traceback có TypeError tại269 | API/type / ApproxMapping._repr_compare; lỗi tạo báo cáo, không phải phép so sánh ban đầu đáng ra phải pass;16skip giữ nguyên |
| Sphinx8435 | Hai documenter không truyền autodoc_type_aliases vào get_type_hints; in int thay vì myint | logic/value / DataDocumenter.add_directive_header, AttributeDocumenter.add_directive_header; cấu hình hợp lệ bị bỏ qua |
| Sympy15225 | _finger tính trọng số cả lần xuất hiện phủ định gây trùng fingerprint; bool_map trả mapping cho XOR/XNOR | logic/value / _finger; repair cũng sửa đường trả no-match trong bool_map, test không tách tác động từng edit |

Tổng56prototype:syntax5/API-type13/logic-value38/dependency0. Còn35saved strict outcomes chưa rà; finalselected0. Repair, issue và nhận định không vào input v4; không có generator label cho các case thật này. Người dùng cần review kết luận/kiến nghị khi bàn giao, không cần tự lần lại log từ đầu.


## Lô đã hoàn tất: năm case thứ ba và hai GitPython mới

[Review5](evidence/dataset-v2-completed-wave-third5-review.json) / [GitPython2](evidence/dataset-v2-gitpython-two-review.json): inventory, hash patch/log và test IDs đã đối chiếu, không chạy lại để phân tích.

| Case | Code → hành vi → log | Kiến nghị |
|---|---|---|
| pvlib1213 | _compute_wavelet bắt đầu bằng tín hiệu đã lấy trung bình, thiếu detail scale nhỏ nhất và lệch crop/alignment. Saved test có12scale thay13; kiểm tra tổng wavelet sai3/10000phần tử, sai số lớn nhất0,1. Fixed13test pass. | logic/value / _compute_wavelet, cao; nhiều edit liên quan, không tách hiệu quả từng edit |
| Sphinx10427 | update_defvalue gán __signature__ trực tiếp cho bound classmethod, lỗi bị catch; default hiển thị giá trị đã evaluate thay tên biểu thức. Fixed xử lý storage và cls. | API/type / update_defvalue, cao; log là assertion về text, không có uncaught AttributeError |
| Sympy23191 | Chèn tên vector tại dấu ngoặc phải đầu tiên bên trong biểu thức thay vì ngoặc ngoài cùng; i_C lọt giữa sin/cos trong saved diff. Fixed4test pass. | logic/value / PrettyPrinter._print_BasisDependent, cao; lỗi biểu diễn, không phải tính vector sai |
| pvlib1616 | Hai base failures dùng keyword n_ar mới; source issue yêu cầu thêm mô hình AR coating | Loại khỏi subset lỗi hiện có: feature extension, không ép thành API/type |
| Sympy13852 | Base giữ polylog(2,2) unevaluated; test mới đòi closed form. Patch cũng sửa nhánh s=1 nhưng các test được chọn chưa chứng minh lỗi nhánh đó. | Loại evidence bổ sung phép evaluate; chưa gán lỗi số học từ biểu thức chưa rút gọn |
| GitPython1314 | Actor._main_actor gọi default() khi tạo argument cho get_value, dù config đã có name/email. Mock getpass bị gọi, assertion True is not false. Fixed2node pass. | logic/value / Actor._main_actor, cao; Actor là tên class, không phải nhãn người/agent gây lỗi |
| GitPython1547 | Hai hàm đổi múi giờ coi HHMM là giờ thập phân: +0001 ra-36thay-60giây; chiều ngược ra+0550thay+0530. Fixed3node pass. | logic/value / utctz_to_altz, altz_to_utctz_str, cao |

GitPython dùng test upstream gốc được phục hồi, có local expectations riêng; nguồn SWEtrain không cung cấp F2P/P2P. Lần đầu cả hai case dừng vì thiếu plugin do pyproject yêu cầu; đúng một profile hiệu chỉnh khai báo plugin đã đạt, không sửa test/source. Đây là tái hiện local, không phải log CI lịch sử.

Tổng61prototype (syntax5/API-type14/logic-value42/dependency0), còn30saved strict outcomes chưa rà; human/gold/training vẫn pending, finalselected0. Các nhận định/repair nằm ngoài input v4. Kiến nghị giữ năm prototype mới để tuyển chọn tiếp, không tự phê duyệt huấn luyện.


## Lô đã hoàn tất: mười review tiếp và pip4430

[Review4th5](evidence/dataset-v2-completed-wave-fourth5-review.json) / [review5th5](evidence/dataset-v2-completed-wave-fifth5-review.json) / [pip4430](evidence/dataset-v2-pip4430-review.json). Tất cả kết luận dựa trên source/diff/test/JUnit đã lưu, kiểm tra inventory/hash/reference; không chạy lại để rà dữ liệu.

| Case | Bằng chứng và nguyên nhân đề xuất | Kiến nghị |
|---|---|---|
| pydicom944 | convert_single_string chỉ bỏ một space; log còn2space từ3padding. Fixed loop bỏ padding; test còn kiểm tra NUL và multivalue. | logic/value, cao. Base dừng ở assert đầu; chưa chứng minh độc lập lỗi MultiString hoặc charset KeyError lịch sử |
| astroid2240 | Arguments.arguments chỉ gom positional nodes; test nhận fruit thay fruit,args,b,c,kwargs. Fixed bổ sung aggregation/variadic nodes. | logic/value, vừa; repair nhiều phần và phạm vi API all-arguments cần người dùng review.187test tổng,9skip,0fail ởfixed |
| pvlib1589 | _ground_angle/masking_angle tính1/gcr vớigcr0, haiZeroDivisionError; công thức fixed loại trung gian chia0. | logic/value, cao; kiểm chứng haihelper, chưa thêm thí nghiệm hệPV |
| pydicom965 | Empty SQ sauwrite/read thànhNone thay[]; empty_value_for_VR thiếu nhánhSQ đầu tiên. | API/type, cao về representation contract; local làassert None!=[], không phải loglen(None) lịch sử |
| pytest9646 | Item.__init_subclass__ phátwarning khi định nghĩa class; testwarnings-as-errors fail trước giai đoạn tạo node. Fixed dời việc check và chỉwarning một lần/class. | logic/value, cao; cấu hình hợp lệ làm lộ sai lifecycle, không phải cấu hình người dùng hỏng |
| pip4430 | auto_decode truyềnNone từlocale.getpreferredencoding vào bytes.decode; TypeError tạiencoding.py31. Fixedfallbackdefaultencoding và cả2node pass. | API/type, cao; localeNone do test upstream mock, không phải đo locale thật của host |

Năm case còn lại (Sphinx8273/10325/11109,Sympy20049,pvlib1764) bị loại khỏi subset lỗi hiện có: lần lượt thêm thư mục section manpage, danh sách inherited classes, tùy chọn Literal ngắn, tự suy vận tốc và method_kwargs solver. Test mới yêu cầu tính năng chưa tồn tại; không ép thành nhãn lỗi vì base fail/fixed pass.

Lô pip4 được báo riêng trong [audit thực thi](evidence/dataset-v2-pip-four-execution-summary.json):9569pass cảhairole dưới UTF8 nên khôngxácnhận;4982bị chặn bởi conftest.get_marker củapytestcũ trước khi đo subprocess.9050lầnđầu vướngimport-order distutils; một r1tườngminh vượt lỗi đó nhưng thiếu helper csv23, không thử profile thứba. Các lỗi harness này không được gán thành dependency/configuration cho sản phẩm. Bốn recipe chuẩn bị bị thừa lineage của template đã được phát hiện và thay trước chạy; lịch sử/hash giữ riêng, không cộng vào profile đã thực thi.

Tổng67prototype:syntax5/API-type16/logic-value46/dependency0; còn20strict chưareview, finalselected0. Human/gold/training eligibility tiếp tục pending; sourceissue/repair/assessment nằm ngoài inputv4. Giữ sáu prototype mới để tuyển chọn tiếp; user review kết luận còn quan trọng, không phải tự dò lại log.
