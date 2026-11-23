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
