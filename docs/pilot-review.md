# W1-03 — Bản rà ba lượt sinh bằng 7B

Ngày rà: 29/10/2026, Asia/Bangkok. Bản rà lại R2 áp dụng skill `ci-data-review` theo yêu cầu người dùng. Đây là phân tích của agent từ artifact đã lưu, không phải lượt chạy mới hoặc phê duyệt của người duyệt. Chỉ rà generator 7B; các artifact của pilot phụ giữ nguyên và không được rà tiếp.

Điểm sửa so với bản rà trước: không còn kiến nghị loại mẫu 02/03 khỏi mọi khả năng training chỉ vì comment. Vi phạm prompt là sự kiện đã quan sát; leakage phụ thuộc input thực tế của 3B, hiện chưa chốt. Agent chuẩn bị phân tích kỹ thuật bên dưới, người dùng review kết luận và kiến nghị thay vì phải tự tìm nguyên nhân từ đầu. Bản phân tích trước được giữ riêng tại `.cache/w1-03-prior-review.md`; raw artifacts và các trường xác nhận không đổi.

## Nguồn và đối chiếu bất biến

- Run: [generate-20261029T054921315491Z](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/manifest.json); [báo cáo đã lưu](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/report.html).
- Model: `qwen2.5-coder:7b-instruct`, digest `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`; Ollama 0.40.13.
- Head properr: `8fd30245ed66b5145d651efc9203eb9a911e95d5`. [Original](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/original.py) hash `e156afcd90644779229990c8ac5ee4495a969e0df0dfb3fa5574a8dc2c252dc9`; [tests](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/tests.py) hash `50347d9a5696d704be7236a902ec7bd232a8dd5a0df59f29f97f718deb45f4f3`.
- Đối chiếu ba candidate với hash trong manifest: khớp. Hash source/tests khớp passing seed. Đọc JUnit của ba repetitions để kiểm tra điều kiện acceptance, không chạy lại candidate.
- Prompt và options gốc giữ nguyên: temperature 0.2, context 4096, output budget 1536; seed lần lượt 5417/5418/5419. Xem [prompt](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/prompt.txt).
- Raw run không nằm trong worktree hiện tại; nó còn ở checkout gốc `C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/`. Các liên kết raw bên dưới trỏ đúng vị trí máy hiện tại; khi chuyển máy cần cung cấp artifact root/archive phù hợp, không tải/chạy lại model. [Tóm tắt evidence đã commit](evidence/target-pc/validation-summary.json) giúp truy vết nhưng không thay thế raw candidate/log.
- Đã kiểm tra 15 bộ kết quả baseline/repetitions/restored: JSON từng stage khớp manifest; mỗi JUnit có hai testcase, không collection error/skipped; không timeout và container đều được cleanup. Hash candidate/source/tests và image ID khớp passing seed. Chỉ đọc/parse dữ liệu, không chạy test.

## Kết quả quan sát

Mã thoát 0 là pass; mã 1 trong các lượt này có test failure thực tế. Cả ba baseline và restoration đều pass; không có timeout. Tất cả `review.json` gốc vẫn pending, reviewer và confirmed_label đều null.

| Mã | Trạng thái gốc | Baseline → ba repetitions → restored | Nhãn model đề xuất | Nhận xét của agent, chưa xác nhận | Vị trí trong candidate |
|---|---|---|---|---|---|
| 7B-01 | verification_failed; does_not_fail_consistently | 0 → 0/0/0 → 0 | syntax | Không quan sát được lỗi test; thêm wrapper nhưng API đang được test vẫn trỏ bản gốc | Thay đổi ở properr/__init__.py:14–20; chưa có vị trí lỗi thực thi được chứng minh |
| 7B-02 | execution_verified | 0 → 1/1/1 → 0 | syntax | API/type misuse gây TypeError; không có bằng chứng là lỗi cú pháp | properr/__init__.py:16, hàm stddev |
| 7B-03 | execution_verified | 0 → 1/1/1 → 0 | syntax | Thay đổi logic số học của stddev gây assertion failure | properr/__init__.py:15, hàm stddev |

Nhãn `syntax` ở cả ba lượt được đọc nguyên trạng từ proposal, không dùng làm gold. Hai lượt đạt acceptance của runner chỉ xác nhận chuỗi thực thi, không tự xác nhận nguyên nhân, vị trí hoặc quyền dùng để train.

| Mã | Kết luận kỹ thuật của agent | Độ chắc chắn và lý do | Kiến nghị để người dùng review |
|---|---|---|---|
| 7B-01 | Không tạo regression mà test hiện tại phát hiện | Cao trong phạm vi hai test: cả ba repetitions pass, các alias được test không đổi. Không suy code đúng trong mọi tình huống | Loại khỏi tập synthetic-failure hiện tại; giữ artifact như một lượt sinh không đạt |
| 7B-02 | Lỗi dùng phương thức như số, gây TypeError ở dòng 16 | Cao: biểu thức khớp stack trace và cả ba lần lỗi; nguồn Rust đã pin cũng khai báo stddev là method | Giữ làm ứng viên lỗi API/type có bằng chứng; chờ tiêu chí chất lượng và input trước khi quyết định training |
| 7B-03 | Lỗi logic nhân sai hệ số, gây sai số ở dòng 15 | Cao: hệ số trong code giải thích hai giá trị observed/expected và chữ ký lỗi ổn định | Giữ làm ứng viên lỗi logic có bằng chứng; chờ tiêu chí chất lượng và input trước khi quyết định training |

## 7B-01 — Wrapper mới không tác động test

**Kết luận ngắn:** lượt này chưa đạt mục tiêu sinh một ca lỗi được kiểm chứng. Test vẫn pass; đây không phải một lỗi syntax đã được xác nhận.

Evidence: [request](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-01/request.json), [raw response](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-01/response.raw.json), [proposal](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-01/proposal.json), [candidate](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-01/candidate.py), [diff](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-01/change.diff).

Candidate SHA-256: `bc63093b730e58bd1eb5aeedc47ef8338ec8aa4869382f24e4e5e98dd0a484a4`.

- Thêm `nominal_with_regression` và `stddev_with_regression`, mở rộng `__all__`; các alias `nominal`/`stddev` được test không đổi. Ba repetitions vẫn pass, nên không có vị trí lỗi đã được thực thi chứng minh.
- Cơ chế: test gọi `properr.nominal(...)` và `properr.stddev(...)`, còn hai hàm mới dùng tên khác nên không thay thế những lời gọi ấy. Alias gốc ở dòng 9/10 vẫn trỏ Rust. Giải thích của generator nói có regression factor, nhưng không chứng minh factor đã tác động đường chạy của hai test. [Stdout lần 1](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-01/candidate-1.stdout.txt), dòng 11, ghi `2 passed`.
- Prompt compliance: không đạt mục tiêu tạo regression bị test phát hiện; dòng 13 ghi trực tiếp ý đồ regression, tên wrapper cũng tiết lộ ý đồ.
- Tính hợp lý: có thay đổi code nhưng không tạo ca lỗi cho bộ test hiện tại; không suy diễn rằng mọi tình huống sử dụng khác đều pass.
- Kiến nghị của agent: loại khỏi tập synthetic-failure hiện tại; giữ như evidence lượt sinh không đạt. Người dùng đã đồng ý kiến nghị loại khỏi tập synthetic-failure; xem bảng xác nhận phạm vi ở cuối tài liệu.
- Người dùng cần review: có đồng ý đây là lượt không tạo lỗi cho bộ test hiện tại và loại khỏi tập mẫu lỗi hay không? Không cần tự gán một nhãn lỗi khi chưa quan sát lỗi. Không tự chuyển nó thành mẫu đối chứng pass đã được duyệt.
- Log: [baseline](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-01/baseline.json), [rep 1](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-01/candidate-1.json), [rep 2](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-01/candidate-2.json), [rep 3](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-01/candidate-3.json), [restored](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-01/restored.json).

## 7B-02 — TypeError trong wrapper stddev

**Kết luận ngắn:** đây là ca lỗi runtime do dùng API sai, có bằng chứng thực thi ổn định; vị trí nguyên nhân đề xuất là `properr/__init__.py:16`, không phải dòng assertion trong test.

Evidence: [request](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-02/request.json), [raw response](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-02/response.raw.json), [proposal](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-02/proposal.json), [candidate](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-02/candidate.py), [diff](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-02/change.diff).

Candidate SHA-256: `0be77d2c2a556e960aaee7e39186e276e504ea66237bc3f76582b52e74667d33`.

- Dòng 16 nhân `value.stddev` với 1.1. Log báo `TypeError: unsupported operand type(s) for *: 'builtin_function_or_method' and 'float'` ở cả hai test `test_uncertain_arithmetic` và `test_uncertain_multiplication`, với chữ ký lỗi giống nhau trong ba repetitions.
- Hiểu đơn giản: `value.stddev` ở đây là phương thức, chưa phải kết quả số. Code lấy phương thức đó nhân với một số nên Python không thực hiện được phép nhân. Nguồn Rust đúng head có `fn stddev(&self) -> f64` ở `src/lib.rs:103`; hash file này khớp inventory source đã lưu. Stack trace đi từ test dòng 13/25 tới wrapper dòng 16, phù hợp cơ chế trên.
- Đối chiếu bổ sung: [khai báo method trong source Rust](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/.cache/exports/8fd30245ed66b5145d651efc9203eb9a911e95d5/src/lib.rs) và [inventory head đã commit](evidence/target-pc/historical/head-source.json). [Stdout lần 1](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-02/candidate-1.stdout.txt), dòng 31/54, báo TypeError với method object. Các chữ ký JUnit của ba repetitions giống nhau; đây không phải AttributeError hoặc SyntaxError.
- Chỉ thêm dấu gọi `()` chưa đồng nghĩa sửa toàn bộ hành vi, vì hệ số `* 1.1` vẫn còn. Đây là lưu ý từ phân tích code, chưa chạy thử một bản sửa và không tạo output đã sửa.
- Nhãn/vị trí agent đề xuất: API/type misuse, wrapper `stddev`, dòng 16. Đây là đề xuất từ code và log, không phải taxonomy đã duyệt; nhãn model `syntax` không khớp loại lỗi quan sát.
- Prompt compliance: thay đổi trong file cho phép, giữ API nhưng comment dòng 13 và cuối dòng 16 tiết lộ mục đích gây lỗi.
- Tính hợp lý: có lỗi dùng API và hoàn tác phục hồi pass; cơ chế thực tế là TypeError, không phải phép nhân số trả sai như ý đồ có thể gợi ra.
- Đánh giá sử dụng: lỗi dùng API là một cơ chế có thể giải thích rõ, nhưng hệ số nhân còn lại là dấu hiệu cần lưu ý nếu mục tiêu đòi một nguyên nhân thuần nhất. Vi phạm prompt về comment đã rõ; leakage vào 3B chưa được chứng minh vì input chưa chốt.
- Kiến nghị của agent: giữ nguyên artifact làm ứng viên lỗi API/type để rà nhãn và thiết kế dữ liệu; chưa duyệt training. Nếu policy sau này yêu cầu nghiêm ngặt không có comment chỉ ý đồ hoặc một cơ chế lỗi duy nhất thì xét theo policy đó, không tự sửa output cũ cho đạt.
- Người dùng cần review: có đồng ý lời giải thích “dùng phương thức như số gây TypeError” và giữ mẫu này như ứng viên có bằng chứng không? Nhãn taxonomy chính thức, hợp đồng input và training approval vẫn pending.
- Log: [baseline](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-02/baseline.json), [rep 1](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-02/candidate-1.json), [rep 2](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-02/candidate-2.json), [rep 3](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-02/candidate-3.json), [restored](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-02/restored.json), [JUnit rep 1](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-02/candidate-1.junit.xml).

## 7B-03 — Sai giá trị stddev

**Kết luận ngắn:** ca lỗi logic số học có bằng chứng ổn định; vị trí nguyên nhân đề xuất là `properr/__init__.py:15`. Log phát hiện lỗi tại test, nhưng nguyên nhân nằm trong wrapper vừa thay đổi.

Evidence: [request](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-03/request.json), [raw response](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-03/response.raw.json), [proposal](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-03/proposal.json), [candidate](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-03/candidate.py), [diff](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-03/change.diff).

Candidate SHA-256: `dc4f3a5c8ee60adc3fd7d2892806c84fa612c63d50cae2813baf9d0a8256dfaf`.

- Dòng 15 trả `_rust.stddev(value) * 1.1`. Hai test thất bại ổn định: giá trị 1.5556349186104048 thay vì 1.4142135623730951; 15.556349186104047 thay vì 14.142135623730951, theo expected tolerance của pytest.
- Cơ chế: hàm Rust vẫn được gọi để lấy số, sau đó wrapper tăng kết quả 10%. Hai giá trị sai trong log phù hợp hệ số này. Vì Python vẫn tính ra số rồi test so sánh thất bại, nhãn lỗi quan sát là logic/sai giá trị số học, không phải SyntaxError. `tests/test_import.py:13` và `:25` là nơi phát hiện; dòng 15 của candidate là vị trí nguyên nhân agent đề xuất. [Stdout lần 1](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-03/candidate-1.stdout.txt), dòng 25/26 và 43/44, có các cặp Obtained/Expected.
- Nhãn/vị trí agent đề xuất: logic/sai giá trị số học, hàm `stddev`, dòng 15; không có bằng chứng SyntaxError. Cùng test identity, failure kind và assertion message trong cả ba repetitions.
- Prompt compliance: thay đổi nhỏ trong file cho phép và giữ API; comment dòng 13 vẫn công khai ý đồ regression, vi phạm yêu cầu không tiết lộ lỗi trong code.
- Tính hợp lý: cơ chế nhân sai hệ số phù hợp một regression hành vi; mức độ đại diện thực tế và nhãn/vị trí cần người duyệt xác nhận.
- Đánh giá sử dụng: đây là ứng viên rõ nhất trong ba lượt cho regression logic của wrapper. Kết luận “phù hợp về cơ chế lỗi” có độ chắc chắn cao; kết luận “đại diện lỗi thực tế” vẫn hạn chế vì chỉ một repo và hai test. Comment vi phạm prompt, nhưng leakage chưa thể kết luận độc lập với input 3B.
- Kiến nghị của agent: giữ artifact làm ứng viên lỗi logic có bằng chứng; chờ policy/input và người duyệt trước khi xét training. Nếu cần biến thể sạch comment, phải là giao thức/run mới hoặc dữ liệu phái sinh được truy vết riêng; không sửa raw rồi coi là output gốc.
- Người dùng cần review: có đồng ý giải thích “nhân thêm 1.1 làm stddev sai” và giữ mẫu này như ứng viên lỗi logic không? Chưa cần xác nhận training khi input/tiêu chí chưa chốt.
- Log: [baseline](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-03/baseline.json), [rep 1](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-03/candidate-1.json), [rep 2](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-03/candidate-2.json), [rep 3](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-03/candidate-3.json), [restored](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-03/restored.json), [JUnit rep 1](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/attempt-03/candidate-1.junit.xml).

## Đánh giá comment, nhãn tự khai và điều kiện training

**Điều đã quan sát:** cả ba candidate có comment nói ý đồ regression, vi phạm dòng 7 của prompt gốc. Cả ba nhãn generator là `syntax`, trong khi code chạy được và các kết quả là pass, TypeError hoặc assertion failure. Metadata tự khai không thay bằng chứng.

**Điều chưa chốt:** 3B sẽ nhận log, diff/code hay phần nào của metadata. Chưa đủ thông tin để kết luận comment hiện tại làm lộ đáp án trong input thực tế.

| Điều kiện input tương lai | Nhận định |
|---|---|
| 3B được xem code/diff có comment chỉ ý đồ tạo regression | Có rủi ro gợi ý nhân tạo về vùng code/nguyên nhân; cần xét mức độ gợi ý và policy nhận mẫu |
| 3B chỉ nhận log và không thấy comment | Không có leakage qua comment ấy trong input này; vi phạm prompt generator vẫn được ghi riêng |
| proposed_label/explanation chứa đáp án được đưa vào input để 3B dự đoán cùng đáp án | Lộ đáp án trực tiếp; cần tách input, target và metadata |
| Stack trace có file/dòng hoặc diff được protocol cho phép | Evidence hợp lệ cho chẩn đoán; không tự coi đó là lộ đáp án |

**Kiến nghị tổng hợp của agent:** loại 01 khỏi tập synthetic-failure hiện tại; giữ 02/03 như hai ứng viên lỗi có bằng chứng để phát triển bộ review. Không tự coi hai ứng viên đó là hai mẫu đã đủ điều kiện training, cũng không loại khỏi mọi mục đích chỉ vì comment. Các quyết định về input/taxonomy/curation thuộc bước chốt protocol sau, không được chốt lén trong lần review này.

## Phần người dùng review kết luận

Bạn chỉ cần xem ba lời giải thích ngắn và kiến nghị ở bảng tổng hợp có thuyết phục, đúng mục tiêu hay cần agent kiểm tra thêm. Có thể đồng ý, bác bỏ hoặc để chưa xác định; không cần tự lặp lại toàn bộ phân tích code/log. Đồng ý kiến nghị giữ/loại không tự xác nhận taxonomy, mọi dòng nguyên nhân hoặc training approval.

## Xác nhận kiến nghị của người dùng

Ghi nhận lúc **2026-10-29 23:43 +07** (Asia/Bangkok), người dùng trong chat xác nhận: “tôi duyệt 3 cái theo ý kiến agent”. Đây là thời điểm ghi nhận, không suy đoán thời điểm gửi hoặc tên người duyệt.

| Mã | Kết luận/kiến nghị đã được đồng ý | Phạm vi quyết định |
|---|---|---|
| 7B-01 | Không tạo lỗi qua bộ test hiện có; loại khỏi tập synthetic-failure | Giữ raw artifact như lượt sinh không đạt; chưa duyệt làm đối chứng pass |
| 7B-02 | Giải thích TypeError do dùng method như số; giữ làm ứng viên có bằng chứng | Phát triển dữ liệu/review; chưa duyệt nhãn gold hoặc training |
| 7B-03 | Giải thích stddev sai do nhân 1.1; giữ làm ứng viên lỗi logic | Phát triển dữ liệu/review; chưa duyệt nhãn gold hoặc training |

W1-03 hoàn tất phần phân tích và review kết luận/kiến nghị giữ/loại. Nhãn taxonomy chính thức, vị trí xác nhận theo schema và training eligibility còn pending; cần hợp đồng input/output và tiêu chí dữ liệu ở W2 trước khi xét tiếp. Raw review.json không đổi.

## Các trường xác nhận dữ liệu còn pending

| Mã | Người duyệt / ngày | Nhãn xác nhận | Vị trí xác nhận | Tuân thủ prompt / hợp lý | Quyết định dùng để train |
|---|---|---|---|---|---|
| 7B-01 | pending | pending | pending | pending | pending |
| 7B-02 | pending | pending | pending | pending | pending |
| 7B-03 | pending | pending | pending | pending | pending |

Các trường trên chỉ dành cho xác nhận dữ liệu chính thức và giữ pending cho tới khi người dùng xác nhận rõ phần tương ứng. Bảng quyết định ở trên ghi riêng việc đồng ý kết luận/kiến nghị, không cập nhật review.json gốc, không chuyển nhãn thành gold hoặc phê duyệt training.
