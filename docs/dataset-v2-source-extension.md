# Bổ sung nguồn train và test upstream

Nhóm metadata ban đầu có trần lý thuyết **626 real train** sau khi áp giới hạn 140 mẫu/repo, đã bao gồm các ID train v1 có thể tái sử dụng. Vì vậy cần bổ sung nguồn để đạt 700, không cộng lại v1 hoặc giảm mục tiêu. [Đối chiếu dung lượng nguồn](../data-manifests/dataset-v2-source-capacity.json).

## Bản ghi thiếu test patch của SWE-bench train

Đã kiểm tra hai bản ghi bằng commit Git upstream. Patch sản phẩm gốc được áp lên đúng base trong Git index riêng; blob sản phẩm sau sửa khớp byte với upstream head. Case youtube-dl-23199 có thêm hai assertion về ngày mang hậu tố `rd` trong test upstream. Case FastAPI-493 không có test delta, nên chưa được nhận qua luồng này. [Probe ban đầu](../data-manifests/dataset-v2-upstream-test-probes-2.json), [kiểm tra blob](../data-manifests/dataset-v2-upstream-test-blob-verification-2.json). So sánh diff dạng text ban đầu khác phần tên hàm ở hunk header; bản kiểm tra blob bổ sung bằng chứng mạnh hơn, không sửa receipt cũ.

Các trường `FAIL_TO_PASS` và `PASS_TO_PASS` của nguồn vẫn không có giá trị tham chiếu cho hai bản ghi này. Không điền kết quả suy đoán vào các trường ấy.

## Cổng riêng `upstream_pr_recovered_v1`

`ci_demo/upstream_tests.py` kiểm tra nguồn/revision, base/head, repo, SHA của record, metadata PR và hai patch. Test patch chỉ được chứa test upstream đã khai báo; code sau sửa phải khớp blob upstream trước khi build. Chính sách mới chỉ áp dụng cho nguồn train v2 được khai báo rõ; nguồn có sẵn F2P/P2P tiếp tục dùng cổng cũ.

- `fail_to_pass`/`pass_to_pass`: giữ trống khi nguồn không cung cấp.
- `local_expected_failures`/`local_expected_passes`: các node test upstream chọn trước khi chạy để kiểm chứng local. Không phải nhãn benchmark hoặc gold.
- Manifest lưu `local_test_resolution` và `test_reference_origin`, tách khỏi `source_test_resolution` của nguồn có tham chiếu.
- Cần regression đã chọn fail trên base và pass trên fixed; lỗi ở test khác không thay thế được. Control test phải pass ở cả hai khi được khai báo.
- Vai trò repo mới nằm trong supplement chỉ ghi thêm. Cổng từ chối đổi vai trò cũ, source/commit không khớp, shared commit qua split hoặc repo fork/canonical chưa rõ. [Supplement youtube-dl](../data-manifests/dataset-v2-source-supplement-youtube.json).

Case đầu chọn `TestUtil.test_unified_dates` và `test_unified_timestamps` từ file upstream, không sửa test và không cần dịch vụ mạng. Nhãn nguyên nhân/vị trí vẫn chỉ được đề xuất sau khi đọc bằng chứng thực thi. Source/repair/issue/provenance luôn nằm ngoài input chẩn đoán.

## Lỗi môi trường trước build

Lượt đầu bị cổng byte chặn: Git áp patch thành 5.599 dòng CRLF, trong khi upstream là LF; nội dung sau chuẩn hóa kết thúc dòng hoàn toàn giống nhau. Thiết lập Git toàn cục là `core.autocrlf=true`. [Bằng chứng](evidence/dataset-v2-upstream-first-preflight-failure.json).

Bản sửa đầu cố định `core.autocrlf=false` riêng cho lệnh áp patch; không sửa cấu hình Git toàn máy hoặc byte source của lượt lỗi. Tạo profile `-r1` riêng, giữ nguyên source/test/repair và các node test; đây là lần hiệu chỉnh môi trường duy nhất cho case này. Cổng byte vẫn phải đạt trước Docker. [Plan hiệu chỉnh](../data-manifests/dataset-v2-upstream-first-recipe-r1.json). Không sửa raw run cũ hoặc tự thử profile thứ ba.

Case nguồn, profile môi trường, seed pass và ứng viên silver là các số khác nhau. Mọi kết quả ở đây là tái dựng local; chưa phải log CI lịch sử, nhãn gold, training approval hoặc kết quả model chẩn đoán.

## Kết quả hiệu chỉnh thực tế

Profile youtube-dl `-r1` cũng dừng trước Docker vì Git archive vẫn xuất CRLF. Đã cố định LF cho cả archive và apply, kiểm tra bằng fixture Git thực dưới cấu hình autocrlf=true. Hai raw run giữ nguyên; không chạy profile thứ ba cho case này. Chưa có mẫu mới được nhận từ cohort youtube-dl.

Requests6028 có lỗi ánh xạ ID tham số: nguồn dùng quy tắc tách whitespace và rút absolute-path parameter về basename của [parser SWE-bench đã ghim](https://github.com/SWE-bench/SWE-bench/blob/726c5461e2ef52d83cf1ea2107870a8bb3328d57/swebench/harness/log_parsers/python.py). Chế độ riêng giữ nguyên ID nguồn và yêu cầu mọi node thuộc cùng nhóm có đúng trạng thái; nhóm mixed bị từ chối. [Đối chiếu log cũ](evidence/dataset-v2-requests-source-id-check.json). Profile hiệu chỉnh duy nhất `psf__requests-6028-ds2-heldout2-r1`, run `reproduce-20261123T110438250093Z`, đạt kiểm chứng local; không sửa verdict raw cũ hoặc test.

## Repo bổ sung đầu tiên tái hiện đạt: GitPython

`gitpython-developers__GitPython-946` có product blob khớp upstream head và test pickle nguyên gốc được khôi phục; nguồn vẫn thiếu F2P/P2P tham chiếu. [Proof](../data-manifests/dataset-v2-gitpython-product-blob-verification.json). Harness dùng bare Git fixture chứa đúng base commit, không host alternates và chỉ đọc trong Docker; hai upstream unit methods được chọn trước khi chạy.

Lượt đầu dừng trước build do giới hạn đường dẫn Windows, [receipt](evidence/dataset-v2-git-fixture-first-preflight-failure.json). Chỉ một profile hiệu chỉnh: Git longpaths riêng lệnh, Git directory tương đối trong context kiểm soát; không đổi cấu hình toàn máy, commit, test hoặc dependency. Run `reproduce-20261123T112846407762Z` đạt base fail/fixed pass cho pickle, control dashify pass ở cả hai. Không thử profile thứ ba. Đây là tái dựng local qua hai unit methods, chưa chứng minh toàn bộ chương trình multiprocessing của issue. Silver review/selection riêng, không tự thành gold hoặc training approval.
