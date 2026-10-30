# Review dữ liệu CI và kiến nghị sử dụng

Cập nhật tổ chức tài liệu: 30/10/2026, Asia/Bangkok. Gom nguyên phân tích đã có bằng `ci-data-review`; không review lại, không chạy model/test và không thay raw artifacts. [Tổng kết và số liệu](development-summary.md) là nơi đọc tiến độ chung.

## Bảng quyết định và trạng thái

| Phạm vi | Kiến nghị agent đã ghi nhận | Xác nhận người dùng |
|---|---|---|
| [W1: ba lượt properr](#w1) | Loại 01 khỏi synthetic-failure; giữ 02/03 làm ứng viên development có bằng chứng | Đã đồng ý kết luận/giữ-loại lúc ghi nhận 29/10/2026 23:43 +07; chưa duyệt gold/training |
| [Expansion 01](#expansion-01) | Giữ ba candidate khác byte để development review, xử lý các lượt trùng theo nhóm; các lượt invalid/pass giữ làm evidence không đạt, chưa là đối chứng pass | Chờ review kiến nghị; nhãn/vị trí chính thức và training pending |
| [Expansion 02](#expansion-02) | Giữ các ứng viên có cơ chế rõ để development review; loại astroid-1196/02 khỏi subset v3 valid-Python; xét riêng tính hợp lý của marker/constant nhân tạo | Chờ review kiến nghị; chưa tự phê duyệt bất kỳ candidate nào |

**Cách đọc:** trạng thái thực thi và hash/log là sự kiện quan sát; nhãn generator là tự đề xuất; nhãn/vị trí và kiến nghị agent là nhận định có lý do; chỉ phần xác nhận được ghi rõ mới là quyết định người dùng. Tất cả formal gold labels, confirmed locations và training eligibility vẫn pending. Raw `review.json` không thay đổi.

Người dùng review lời giải thích và kiến nghị dưới đây; không phải tự phân tích code/log từ đầu. Việc đồng ý tiếp tục công việc không tự duyệt nhãn/training. Comment/metadata chỉ gây leakage theo input chẩn đoán thực tế; stack trace/số dòng là evidence hợp lệ. Phần giả định chưa chốt tại thời điểm mỗi review được giữ nguyên, xem [task contract hiện tại](task-contract.md) cho hợp đồng development và addendum v3.

## Mục lục

- [W1 — ba lượt properr, bản rà R2](#w1)
- [W1 — xác nhận kiến nghị đã ghi nhận](#w1-xác-nhận-kiến-nghị-của-người-dùng)
- [Expansion 01 — chín case, output lỗi/pass và ba candidate khác byte](#expansion-01)
- [Expansion 02 — 15 output, syntax violation và rủi ro tính hợp lý](#expansion-02)

Các câu yêu cầu review trong từng bản ghi phản ánh thời điểm phân tích; bảng xác nhận W1 và trạng thái ở đầu tài liệu là nơi phân biệt việc đã duyệt với phần còn pending. Ngày rà, run ID, bằng chứng, nhãn đề xuất và quyết định cũ được giữ nguyên.

<a id="w1"></a>

## W1-03 — Bản rà ba lượt sinh bằng 7B

Ngày rà: 29/10/2026, Asia/Bangkok. Bản rà lại R2 áp dụng skill `ci-data-review` theo yêu cầu người dùng. Đây là phân tích của agent từ artifact đã lưu, không phải lượt chạy mới hoặc phê duyệt của người duyệt. Chỉ rà generator 7B; các artifact của pilot phụ giữ nguyên và không được rà tiếp.

Điểm sửa so với bản rà trước: không còn kiến nghị loại mẫu 02/03 khỏi mọi khả năng training chỉ vì comment. Vi phạm prompt là sự kiện đã quan sát; leakage phụ thuộc input thực tế của 3B, hiện chưa chốt. Agent chuẩn bị phân tích kỹ thuật bên dưới, người dùng review kết luận và kiến nghị thay vì phải tự tìm nguyên nhân từ đầu. Bản phân tích trước được giữ riêng tại `.cache/w1-03-prior-review.md`; raw artifacts và các trường xác nhận không đổi.

<a id="w1-nguồn-và-đối-chiếu-bất-biến"></a>

### Nguồn và đối chiếu bất biến

- Run: [generate-20261029T054921315491Z](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/manifest.json); [báo cáo đã lưu](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/report.html).
- Model: `qwen2.5-coder:7b-instruct`, digest `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`; Ollama 0.40.13.
- Head properr: `8fd30245ed66b5145d651efc9203eb9a911e95d5`. [Original](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/original.py) hash `e156afcd90644779229990c8ac5ee4495a969e0df0dfb3fa5574a8dc2c252dc9`; [tests](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/tests.py) hash `50347d9a5696d704be7236a902ec7bd232a8dd5a0df59f29f97f718deb45f4f3`.
- Đối chiếu ba candidate với hash trong manifest: khớp. Hash source/tests khớp passing seed. Đọc JUnit của ba repetitions để kiểm tra điều kiện acceptance, không chạy lại candidate.
- Prompt và options gốc giữ nguyên: temperature 0.2, context 4096, output budget 1536; seed lần lượt 5417/5418/5419. Xem [prompt](C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/generate-20261029T054921315491Z/prompt.txt).
- Raw run không nằm trong worktree hiện tại; nó còn ở checkout gốc `C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis/runs/`. Các liên kết raw bên dưới trỏ đúng vị trí máy hiện tại; khi chuyển máy cần cung cấp artifact root/archive phù hợp, không tải/chạy lại model. [Tóm tắt evidence đã commit](evidence/target-pc/validation-summary.json) giúp truy vết nhưng không thay thế raw candidate/log.
- Đã kiểm tra 15 bộ kết quả baseline/repetitions/restored: JSON từng stage khớp manifest; mỗi JUnit có hai testcase, không collection error/skipped; không timeout và container đều được cleanup. Hash candidate/source/tests và image ID khớp passing seed. Chỉ đọc/parse dữ liệu, không chạy test.

<a id="w1-kết-quả-quan-sát"></a>

### Kết quả quan sát

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

<a id="w1-7b-01--wrapper-mới-không-tác-động-test"></a>

### 7B-01 — Wrapper mới không tác động test

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

<a id="w1-7b-02--typeerror-trong-wrapper-stddev"></a>

### 7B-02 — TypeError trong wrapper stddev

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

<a id="w1-7b-03--sai-giá-trị-stddev"></a>

### 7B-03 — Sai giá trị stddev

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

<a id="w1-đánh-giá-comment-nhãn-tự-khai-và-điều-kiện-training"></a>

### Đánh giá comment, nhãn tự khai và điều kiện training

**Điều đã quan sát:** cả ba candidate có comment nói ý đồ regression, vi phạm dòng 7 của prompt gốc. Cả ba nhãn generator là `syntax`, trong khi code chạy được và các kết quả là pass, TypeError hoặc assertion failure. Metadata tự khai không thay bằng chứng.

**Điều chưa chốt:** 3B sẽ nhận log, diff/code hay phần nào của metadata. Chưa đủ thông tin để kết luận comment hiện tại làm lộ đáp án trong input thực tế.

| Điều kiện input tương lai | Nhận định |
|---|---|
| 3B được xem code/diff có comment chỉ ý đồ tạo regression | Có rủi ro gợi ý nhân tạo về vùng code/nguyên nhân; cần xét mức độ gợi ý và policy nhận mẫu |
| 3B chỉ nhận log và không thấy comment | Không có leakage qua comment ấy trong input này; vi phạm prompt generator vẫn được ghi riêng |
| proposed_label/explanation chứa đáp án được đưa vào input để 3B dự đoán cùng đáp án | Lộ đáp án trực tiếp; cần tách input, target và metadata |
| Stack trace có file/dòng hoặc diff được protocol cho phép | Evidence hợp lệ cho chẩn đoán; không tự coi đó là lộ đáp án |

**Kiến nghị tổng hợp của agent:** loại 01 khỏi tập synthetic-failure hiện tại; giữ 02/03 như hai ứng viên lỗi có bằng chứng để phát triển bộ review. Không tự coi hai ứng viên đó là hai mẫu đã đủ điều kiện training, cũng không loại khỏi mọi mục đích chỉ vì comment. Các quyết định về input/taxonomy/curation thuộc bước chốt protocol sau, không được chốt lén trong lần review này.

<a id="w1-phần-người-dùng-review-kết-luận"></a>

### Phần người dùng review kết luận

Bạn chỉ cần xem ba lời giải thích ngắn và kiến nghị ở bảng tổng hợp có thuyết phục, đúng mục tiêu hay cần agent kiểm tra thêm. Có thể đồng ý, bác bỏ hoặc để chưa xác định; không cần tự lặp lại toàn bộ phân tích code/log. Đồng ý kiến nghị giữ/loại không tự xác nhận taxonomy, mọi dòng nguyên nhân hoặc training approval.

<a id="w1-xác-nhận-kiến-nghị-của-người-dùng"></a>

### Xác nhận kiến nghị của người dùng

Ghi nhận lúc **2026-10-29 23:43 +07** (Asia/Bangkok), người dùng trong chat xác nhận: “tôi duyệt 3 cái theo ý kiến agent”. Đây là thời điểm ghi nhận, không suy đoán thời điểm gửi hoặc tên người duyệt.

| Mã | Kết luận/kiến nghị đã được đồng ý | Phạm vi quyết định |
|---|---|---|
| 7B-01 | Không tạo lỗi qua bộ test hiện có; loại khỏi tập synthetic-failure | Giữ raw artifact như lượt sinh không đạt; chưa duyệt làm đối chứng pass |
| 7B-02 | Giải thích TypeError do dùng method như số; giữ làm ứng viên có bằng chứng | Phát triển dữ liệu/review; chưa duyệt nhãn gold hoặc training |
| 7B-03 | Giải thích stddev sai do nhân 1.1; giữ làm ứng viên lỗi logic | Phát triển dữ liệu/review; chưa duyệt nhãn gold hoặc training |

W1-03 hoàn tất phần phân tích và review kết luận/kiến nghị giữ/loại. Nhãn taxonomy chính thức, vị trí xác nhận theo schema và training eligibility còn pending; cần hợp đồng input/output và tiêu chí dữ liệu ở W2 trước khi xét tiếp. Raw review.json không đổi.

<a id="w1-các-trường-xác-nhận-dữ-liệu-còn-pending"></a>

### Các trường xác nhận dữ liệu còn pending

| Mã | Người duyệt / ngày | Nhãn xác nhận | Vị trí xác nhận | Tuân thủ prompt / hợp lý | Quyết định dùng để train |
|---|---|---|---|---|---|
| 7B-01 | pending | pending | pending | pending | pending |
| 7B-02 | pending | pending | pending | pending | pending |
| 7B-03 | pending | pending | pending | pending | pending |

Các trường trên chỉ dành cho xác nhận dữ liệu chính thức và giữ pending cho tới khi người dùng xác nhận rõ phần tương ứng. Bảng quyết định ở trên ghi riêng việc đồng ý kết luận/kiến nghị, không cập nhật review.json gốc, không chuyển nhãn thành gold hoặc phê duyệt training.

<a id="expansion-01"></a>

## Rà dữ liệu đợt mở rộng 01

Ngày 30/10/2026; dùng `ci-data-review`, chỉ đọc artifact mới sau khi batch kết thúc. Không chạy lại test/model để viết review. [Tổng kết](development-summary.md#expansion-01), [batch manifest](../runs/batch-20261029T173420443187Z/manifest.json), [HTML](../runs/batch-20261029T173420443187Z/report.html).

<a id="expansion-01-kết-luận-để-người-dùng-review"></a>

### Kết luận để người dùng review

21 lượt sinh từ 7 seed pass: **10 output không hợp lệ, 5 candidate không làm test fail, 6 lượt đạt thực thi**. Sáu lượt đạt gồm **3 candidate khác byte, cùng thuộc pydicom**; không coi các output trùng là mẫu độc lập. Agent kiến nghị giữ ba candidate khác byte để phát triển/review, chưa duyệt training. Các lượt còn lại giữ làm evidence thất bại; chưa tự biến thành đối chứng pass.

Đã đối chiếu 78 JUnit với 2.580 testcase records; source/test của 8 image khớp inventory hai role, 11 candidate hợp lệ khớp hash và phép edit nguyên trạng. Con số testcase records bao gồm lặp, không phải 2.580 test độc lập. [Integrity audit](../runs/integrity-20261029T174127403846Z/manifest.json). Tất cả xác nhận người dùng, gold labels và training eligibility mới vẫn pending.

<a id="expansion-01-tình-trạng-chín-case-nguồn"></a>

### Tình trạng chín case nguồn

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

<a id="expansion-01-ba-candidate-khác-byte-đạt-thực-thi"></a>

### Ba candidate khác byte đạt thực thi

<a id="expansion-01-p1139-a--ba-lượt-010203-trùng-hoàn-toàn"></a>

#### P1139-A — Ba lượt 01/02/03 trùng hoàn toàn

**Kết luận:** làm hỏng hỗ trợ ngày `YYYY.MM.DD`, đạt baseline pass → ba fail ổn định → restored pass cho từng lượt. Candidate SHA-256 `d6335f8e5d8105cd94e94cea214ff5d72a1b27f325dc7454f19ef51a69b23a56`.

**Bằng chứng:** [candidate lượt 01](../runs/generate-20261029T173754950832Z/attempt-01/candidate.py), [raw proposal](../runs/generate-20261029T173754950832Z/attempt-01/proposal.json), [diff](../runs/generate-20261029T173754950832Z/attempt-01/change.diff), [verification manifest đủ ba lượt](../runs/verify-20261029T173806351343Z/manifest.json), [log rep 1](../runs/verify-20261029T173806351343Z/attempt-01/candidate-1.stdout.txt), [JUnit](../runs/verify-20261029T173806351343Z/attempt-01/candidate-1.junit.xml).

**Nguyên nhân agent đề xuất:** dòng 78 trong `pydicom/valuerep.py`, nhánh `DA.__new__`, đổi kiểm tra dấu `.` sang `-`. Chuỗi `1961.08.04` vốn được chấp nhận không đi vào nhánh chuyển đổi và gây `ValueError: Cannot convert to datetime`. `TestDateTime.test_date` là nơi phát hiện. Mỗi repetition có một failure, 40 test pass; cơ chế được code và log hỗ trợ với độ chắc chắn cao. Generator tự gắn `syntax`; code đã chạy nên nhãn đó không được evidence hỗ trợ. Mô tả nhãn tạm thời: logic/điều kiện nhận dạng định dạng sai.

**Đánh giá sử dụng:** một edit nhỏ, không đổi tests/API/dependencies; không thêm comment chỉ ý đồ. Độ đại diện thực tế chưa được chứng minh. Giữ một candidate đại diện cùng liên kết ba lượt trùng, không nhân ba số mẫu độc lập; raw của cả ba lượt vẫn giữ. Chưa phải training-approved hoặc gold-labeled.

**Người dùng cần quyết định:** review lời giải thích và kiến nghị giữ một đại diện làm ứng viên development. Nhãn taxonomy/vị trí chính thức và training vẫn pending.

<a id="expansion-01-p1256-a--lượt-01-và-03-trùng-hoàn-toàn"></a>

#### P1256-A — Lượt 01 và 03 trùng hoàn toàn

**Kết luận:** thay sai phân biệt hoa/thường của key JSON, làm dữ liệu hợp lệ bị từ chối. Candidate SHA-256 `0f15de3d28ead93252a6bbc28fdd19b6ad1fb86ab0662f2b6e5662998a0ebf80`; cả hai lượt đạt kiểm chứng thực thi.

**Bằng chứng:** [candidate 01](../runs/generate-20261029T173924603722Z/attempt-01/candidate.py), [proposal](../runs/generate-20261029T173924603722Z/attempt-01/proposal.json), [diff](../runs/generate-20261029T173924603722Z/attempt-01/change.diff), [manifest đủ ba lượt](../runs/verify-20261029T173935725566Z/manifest.json), [log rep 1](../runs/verify-20261029T173935725566Z/attempt-01/candidate-1.stdout.txt), [JUnit](../runs/verify-20261029T173935725566Z/attempt-01/candidate-1.junit.xml).

**Nguyên nhân agent đề xuất:** dòng 210 trong `pydicom/jsonrep.py`, hàm `get_sequence_item`, đổi `'vr' not in val` thành `'VR' not in val`. Input chứa `vr` đúng quy ước nhưng không chứa `VR`; điều kiện mới bật nhánh raise ở dòng 212. Log có KeyError nói thiếu `vr` dù dict đang chứa `vr`. Mỗi repetition có bốn failure, 19 pass. Độ chắc chắn cao từ biểu thức, dict trong trace và repetition signatures. Nhãn tạm thời: logic/validation key sai; generator `syntax` không phù hợp.

**Đánh giá sử dụng:** regression nhỏ có cơ chế rõ, không sửa test hoặc thêm comment chỉ lỗi. Kiến nghị giữ một đại diện, liên kết lượt 01/03 là duplicate; chưa duyệt tính đại diện, nhãn gold hoặc training.

**Người dùng cần quyết định:** review giải thích điều kiện phân biệt hoa/thường và kiến nghị giữ ứng viên. Chưa cần phê duyệt train.

<a id="expansion-01-p1256-b--lượt-02"></a>

#### P1256-B — Lượt 02

**Kết luận:** đảo điều kiện kiểm tra kiểu trong giải mã PersonName, trả dict thay vì chuỗi đã chuẩn hóa. Candidate SHA-256 `972bc7ba518606aea50aca13a37906477991a5249cd4408b7297c998321d4cd1`; đạt kiểm chứng thực thi.

**Bằng chứng:** [candidate 02](../runs/generate-20261029T173924603722Z/attempt-02/candidate.py), [proposal](../runs/generate-20261029T173924603722Z/attempt-02/proposal.json), [diff](../runs/generate-20261029T173924603722Z/attempt-02/change.diff), [log rep 1](../runs/verify-20261029T173935725566Z/attempt-02/candidate-1.stdout.txt), [JUnit](../runs/verify-20261029T173935725566Z/attempt-02/candidate-1.junit.xml).

**Nguyên nhân agent đề xuất:** dòng 251, `get_pn_element_value`, đổi `if not isinstance(value, dict)` thành `if isinstance(value, dict)`. Dict hợp lệ đi vào nhánh warning và `return value` ở dòng 259 thay vì được ghép các thành phần thành string ở dòng 273. Downstream gặp AttributeError về `append`/`split` rồi bọc thành ValueError ở `pydicom/dataelem.py:279`. Đó là nơi lỗi lộ ra sau đó, không phải edit gây lỗi. Mỗi repetition có sáu failure, 17 pass. Nhãn tạm thời logic/đảo type guard dẫn tới giá trị sai kiểu, độ chắc chắn cao; không phải SyntaxError như generator tự khai.

**Đánh giá sử dụng:** cơ chế khác P1256-A dù cùng case/file; cần cùng repo/development group khi chia tập sau. Không thêm comment chỉ ý đồ, nhưng mức thực tế vẫn cần rà. Kiến nghị giữ candidate riêng làm ứng viên development, training pending.

**Người dùng cần quyết định:** review chuỗi đảo điều kiện → trả dict → lỗi downstream và kiến nghị giữ. Các trường xác nhận chính thức tiếp tục pending.

<a id="expansion-01-năm-lượt-có-candidate-nhưng-không-tạo-failure"></a>

### Năm lượt có candidate nhưng không tạo failure

| Nhóm | Kết luận / bằng chứng | Giải thích agent và kiến nghị |
|---|---|---|
| marshmallow #1343, 02/03 | Hai candidate trùng hash `2a21776c5e5672f5a7a02b68a1b7805ff720706cf47940540ce26b979214982b`; mỗi repetition 25 pass. [Diff](../runs/generate-20261029T173541374859Z/attempt-02/change.diff), [log](../runs/verify-20261029T173556500724Z/attempt-02/candidate-1.stdout.txt) | Dòng 950 thay fallback `utils.if_none(...)` trong schema processor; test mục tiêu không phát hiện regression. Chưa có coverage chứng minh đường thay đổi có chạy. Generator gọi syntax không có căn cứ. Loại khỏi tập synthetic-failure hiện tại, giữ failed-generation evidence; không tự xác nhận code đúng mọi tình huống |
| TCM #364, 02 | Hash `7f36fd6ed263d85851003c2b04e0802d09139f1500b1bcffc87d2978ecc43854`; một test pass ở cả ba repetition. [Candidate](../runs/generate-20261029T173641181162Z/attempt-02/candidate.py), [log](../runs/verify-20261029T173652371964Z/attempt-02/candidate-1.stdout.txt) | Dòng 187 đổi escaping trong nhánh `if os_name == 'nt'`; Docker chạy Linux nên nhánh đó không phải đường kiểm chứng hiện tại. Cảnh báo escape không phải SyntaxError. Không có lỗi được thực thi chứng minh; loại khỏi tập mẫu lỗi hiện tại, chưa suy làm negative sample |
| marshmallow #1359, 01/02 | Hai candidate trùng hash `584a530d8b41b9aae4aea6a5a4d43b045f14b4cab66c1bfb5b4661feb237a321`; 77 test pass ở mỗi repetition. [Diff](../runs/generate-20261029T173710990536Z/attempt-01/change.diff), [log](../runs/verify-20261029T173720986776Z/attempt-01/candidate-1.stdout.txt) | Dòng 1115 thêm một `self.format or` trước biểu thức vốn đã bắt đầu bằng `self.format or`; dư thừa trong trường hợp attribute thông thường. Không có thay đổi import hoặc failure hỗ trợ nhãn `import` của generator. Loại khỏi tập mẫu lỗi hiện tại; không kết luận tương đương trong mọi subclass có side effect |

Độ chắc chắn cao về kết quả test đã quan sát; suy luận về nhánh/logic chỉ có phạm vi như mô tả. Người dùng chỉ cần review kiến nghị loại khỏi tập failure hiện tại, không phải tự phân tích lại code/log hoặc duyệt nhãn pass.

<a id="expansion-01-mười-output-không-hợp-lệ"></a>

### Mười output không hợp lệ

| Case / lượt | Điều quan sát | Kiến nghị |
|---|---|---|
| marshmallow #1343 / 01 | `before` không khớp đúng một lần; proposal không tạo candidate. [Proposal](../runs/generate-20261029T173541374859Z/attempt-01/proposal.json) | Giữ invalid_output, không có vị trí lỗi thực thi hay gold label |
| TCM #364 / 01,03 | `before == after`, model nói không cần đổi. [01](../runs/generate-20261029T173641181162Z/attempt-01/proposal.json), [03](../runs/generate-20261029T173641181162Z/attempt-03/proposal.json) | Không đạt yêu cầu tạo regression; không tự sửa output |
| marshmallow #1359 / 03 | `before` không khớp, lời giải thích hướng sửa default. [Proposal](../runs/generate-20261029T173710990536Z/attempt-03/proposal.json) | Không có candidate thực thi, không nhận nhãn import làm nguyên nhân |
| sshpilot #716 / 01,02,03 | Các điều kiện `if requires_force:`/`if not passphrase_available:` không khớp đúng một lần trong source nguyên trạng. [Manifest](../runs/generate-20261029T173843891949Z/manifest.json) | Giữ ba invalid_output, không nới matching hoặc chỉnh output cho qua |
| pydicom #1694 / 01,02,03 | 01/03 before không khớp; 02 before/after không đổi. [Manifest](../runs/generate-20261029T174020789887Z/manifest.json) | Không có candidate để chẩn đoán lỗi mới; giữ cả ba lượt trong mẫu số |

Đây là lỗi giao thức sinh/không tạo candidate, không phải bằng chứng lỗi syntax/import của repo. Độ chắc chắn cao về lý do validation từ raw output và source đã hash; không suy nhãn lỗi thực thi khi chưa chạy candidate. Không cần người dùng gán lỗi cho output invalid.

<a id="expansion-01-prompt-input-và-quyết-định-còn-lại"></a>

### Prompt, input và quyết định còn lại

- Sáu candidate khác byte hợp lệ chỉ thay một biểu thức/điều kiện; không thêm comment cố ý tiết lộ lỗi. Comment tự nhiên có sẵn vẫn giữ nguyên. Stack trace/file/dòng là evidence hợp lệ.
- Nhiều proposal giải thích theo hướng sửa code hoặc nói không cần sửa, dù prompt yêu cầu cài regression; nhãn self-label không đáng tin trong đợt này. Đây là vấn đề chất lượng generator, không được chữa bằng sửa output cũ.
- Chưa đóng gói input cho 3B hoặc train. Theo contract, reference patch, proposed_label/explanation và nhận định agent nằm riêng; khi đóng gói code/log phải rà leakage trên input thực tế.
- Các diff v2 đã lưu có xuống dòng thừa khi đọc trên Windows do newline translation. Candidate/source bytes và hashes vẫn khớp; review dựa thêm vào before/after và candidate đầy đủ. Đã sửa writer cho các run sau, không sửa diff raw của đợt này.
- Người dùng review ba kiến nghị giữ candidate khác byte và kiến nghị loại các lượt không tạo failure. Nhãn taxonomy, vị trí chính thức, tính đại diện và training eligibility tiếp tục pending. Chưa có bất kỳ phê duyệt mới nào trong đợt này.

<a id="expansion-02"></a>

## Rà dữ liệu development 02 bằng ci-data-review

Ngày 30/10/2026. Phạm vi: 15 output v3 của [đợt 02](development-summary.md#expansion-02), gồm profile FastAPI hiệu chỉnh có trace riêng. Review chỉ đọc source/candidate/diff/proposal/log/JUnit đã lưu, không gọi lại model/test và không sửa raw review stub.

<a id="expansion-02-kết-luận-để-người-dùng-review"></a>

### Kết luận để người dùng review

Runner ghi **11 execution_verified, 3 candidate không làm test fail, 1 output không đổi dòng**. Mười một candidate đạt runner đều khác byte; một candidate gây IndentationError và vi phạm yêu cầu v3 giữ syntax hợp lệ. Các marker `extra`/`X` cũng cần xem xét tính tự nhiên. Agent kiến nghị giữ candidate có cơ chế rõ cho development review, loại syntax-violation khỏi subset v3 valid-Python; chưa phê duyệt gold/training cho bất kỳ mẫu nào.

Mọi candidate hợp lệ khớp SHA-256 và replay đúng một dòng theo site catalog, 6 image khớp tracked source/test inventories. [Integrity audit](../runs/integrity-20261030T000410182947Z/manifest.json). Baseline/repetitions/restoration và source-ID mappings được giữ trong manifests. V3 không yêu cầu nhãn generator; các nhãn dưới đây là **mô tả tạm thời của agent**.

<a id="expansion-02-astroid-1196--getitem-và-bool_value"></a>

### Astroid #1196 — getitem và bool_value

[Generation](../runs/generate-20261029T235321366861Z/manifest.json), [verification đủ ba lượt](../runs/verify-20261029T235337035725Z/manifest.json). Độ chắc chắn cao về behavior quan sát; tính đại diện vẫn hạn chế trong test scope.

| Lượt | Kết luận, nguyên nhân và vị trí | Evidence và kiến nghị |
|---|---|---|
| 01 | `getitem`, `astroid/nodes/node_classes.py:2381`: `return value` → `return value + 1`. `value` là AST Const node, không phải số, nên cộng int gây TypeError. Ba test failure ổn định, baseline/restored pass | [Candidate](../runs/generate-20261029T235321366861Z/attempt-01/candidate.py), [log rep 1](../runs/verify-20261029T235337035725Z/attempt-01/candidate-1.stdout.txt). Mô tả API/type misuse. Kiến nghị giữ làm ứng viên development; nhãn/vị trí chính thức và training pending |
| 02 | Dòng 2379 đổi đầu block thành `if ...: return False` nhưng block indented phía sau vẫn còn; Python báo `IndentationError: unexpected indent` tại 2380. Dòng 2380 là nơi parser phát hiện, edit gây cấu trúc sai ở 2379 | [Candidate](../runs/generate-20261029T235321366861Z/attempt-02/candidate.py), [log](../runs/verify-20261029T235337035725Z/attempt-02/candidate-1.stdout.txt). Runner chấp nhận collection error ổn định; ba error-body hashes cũng bằng nhau. **Vi phạm prompt valid-Python**: kiến nghị loại khỏi subset v3 hợp lệ, giữ artifact cho phân tích syntax/protocol riêng; không gọi là test assertion failure |
| 03 | `bool_value`, dòng 2391: trả `bool(self.items) + 1` thay bool. Đây có khả năng làm sai semantics kiểu/truthiness nhưng test đang xét đều pass | [Candidate](../runs/generate-20261029T235321366861Z/attempt-03/candidate.py), [log](../runs/verify-20261029T235337035725Z/attempt-03/candidate-1.stdout.txt). Không có regression được thực thi chứng minh trong bộ test này; loại khỏi tập synthetic-failure hiện tại, không tự duyệt làm negative sample |

Người dùng review kiến nghị giữ 01 và xử lý 02 theo ràng buộc giao thức; không phải tự dò lại code/log hoặc xác nhận mọi dòng là gold.

<a id="expansion-02-astroid-1268--xuất-ast-thành-chuỗi"></a>

### Astroid #1268 — xuất AST thành chuỗi

[Generation](../runs/generate-20261029T235415338424Z/manifest.json), [verification](../runs/verify-20261029T235427190903Z/manifest.json). Cả ba lượt đạt runner, mỗi lượt khác site/candidate; các vị trí sau gắn đúng candidate revision.

| Lượt | Giải thích nguyên nhân | Evidence / đánh giá sử dụng |
|---|---|---|
| 01 | `astroid/nodes/as_string.py:57`, `__call__`: thay newline `\n` bằng carriage return `\r`. Chuỗi xuất khác expected; một assertion failure ổn định | [Candidate](../runs/generate-20261029T235415338424Z/attempt-01/candidate.py), [log](../runs/verify-20261029T235427190903Z/attempt-01/candidate-1.stdout.txt). Logic/string-formatting; cơ chế line ending rõ, có tính hợp lý để tiếp tục review |
| 02 | `_should_wrap`, dòng 88: `return True` → `return False`; thiếu dấu ngoặc khi in biểu thức, làm sai chuỗi/ưu tiên toán tử trong năm test | [Candidate](../runs/generate-20261029T235415338424Z/attempt-02/candidate.py), [log](../runs/verify-20261029T235427190903Z/attempt-02/candidate-1.stdout.txt). Logic/parenthesization; không suy test assertion line là causal line |
| 03 | `visit_asyncwith`, dòng 106: nối thêm `'extra'` vào chuỗi xuất, làm expected `pass` thành `passextra`; một assertion failure | [Candidate](../runs/generate-20261029T235415338424Z/attempt-03/candidate.py), [log](../runs/verify-20261029T235427190903Z/attempt-03/candidate-1.stdout.txt). Candidate Python chạy được; lỗi nằm ở chuỗi sinh ra, không phải SyntaxError của candidate. Marker tùy ý làm giảm tính tự nhiên; giữ để phân tích development, chưa kiến nghị train khi policy chưa chốt |

Độ chắc chắn cao về causal mechanism vì edit và output lệch khớp log qua ba repetition. Người dùng review cách xử lý marker nhân tạo ở 03 và kiến nghị sử dụng có điều kiện; gold/training tiếp tục pending.

<a id="expansion-02-astroid-1866--suy-luận-stringformat"></a>

### Astroid #1866 — suy luận string.format

[Generation](../runs/generate-20261029T235638993708Z/manifest.json), [verification](../runs/verify-20261029T235649711472Z/manifest.json). Fixed source pass; source historical flag vẫn false do một identifier nguồn có escaped newline chưa resolve, không được sửa tay. Synthetic acceptance là gate riêng.

| Lượt | Giải thích nguyên nhân | Evidence / kiến nghị |
|---|---|---|
| 01 | `astroid/brain/brain_builtin_inference.py:963`, `_infer_str_format_call`: nối `'X'` vào formatted_string trước const_factory. Tám test nhận chuỗi thừa X | [Candidate](../runs/generate-20261029T235638993708Z/attempt-01/candidate.py), [log](../runs/verify-20261029T235649711472Z/attempt-01/candidate-1.stdout.txt). Logic/string value, chắc chắn cao về cơ chế; marker nhân tạo cần curation riêng, không tự đủ tiêu chí training |
| 02 | `_is_str_format_call`, dòng 924: nhận `int` thay `str`. Các lời gọi format hợp lệ bị phân loại sai, 15 failure, nhiều kết quả thành chuỗi rỗng thay expected | [Candidate](../runs/generate-20261029T235638993708Z/attempt-02/candidate.py), [log](../runs/verify-20261029T235649711472Z/attempt-02/candidate-1.stdout.txt). Logic/type guard, giữ làm ứng viên có evidence |
| 03 | `_infer_str_format_call`, dòng 951: thêm `or len(inferred_keyword) == 0`; trường hợp dùng positional args/không keyword bị trả Uninferable dù hợp lệ, năm failure | [Candidate](../runs/generate-20261029T235638993708Z/attempt-03/candidate.py), [log](../runs/verify-20261029T235649711472Z/attempt-03/candidate-1.stdout.txt). Logic/edge-case guard; độ chắc chắn cao trong test scope |

Các dòng assertion về Const/chuỗi là nơi test phát hiện; các edit trong brain function mới là vị trí nguyên nhân agent đề xuất. Người dùng review giữ các ứng viên và mức chấp nhận marker; chưa duyệt nhãn gold/khả năng đại diện.

<a id="expansion-02-pvlib-1072--giá-trị-nhiệt-độ"></a>

### pvlib #1072 — giá trị nhiệt độ

[Generation](../runs/generate-20261029T235810212189Z/manifest.json), [verification](../runs/verify-20261029T235820935739Z/manifest.json). Hai candidate khác byte gây numerical assertion failures ổn định; một output không đổi.

| Lượt | Giải thích nguyên nhân | Evidence / kiến nghị |
|---|---|---|
| 01 | `pvlib/temperature.py:593`, `fuentes`: đổi mẫu số hiệu chỉnh cap từ 12 thành 13. Series tính ra lệch expected, một failure | [Candidate](../runs/generate-20261029T235810212189Z/attempt-01/candidate.py), [log](../runs/verify-20261029T235820935739Z/attempt-01/candidate-1.stdout.txt). Logic/numeric parameter, giữ làm ứng viên; không suy mô hình nhiệt vật lý được validation đầy đủ chỉ từ một test |
| 02 | Dòng 606: thêm 10 vào `temp_air + 273.15`, làm ambient temperature lệch 10 K; bốn test fail | [Candidate](../runs/generate-20261029T235810212189Z/attempt-02/candidate.py), [log](../runs/verify-20261029T235820935739Z/attempt-02/candidate-1.stdout.txt). Logic/numeric offset; cơ chế rõ nhưng hằng số tùy ý cần đánh giá tính tự nhiên |
| 03 | Đề xuất thay `if tinoct > 321.15:` bằng chính dòng đó; validator ghi Unchanged site, không có candidate | [Proposal](../runs/generate-20261029T235810212189Z/attempt-03/proposal.json). Giữ invalid_output trong mẫu số; không gán nhãn lỗi thực thi hoặc sửa output cho qua |

Độ chắc chắn cao rằng edit giải thích kết quả numerical; không có bằng chứng về mức đại diện lỗi thực tế. Người dùng review kiến nghị ứng viên và curation constants, training pending.

<a id="expansion-02-fastapi-15232-r1--api-decorator-và-websocket"></a>

### FastAPI #15232-r1 — API decorator và WebSocket

[Generation](../runs/generate-20261030T000107782911Z/manifest.json), [verification](../runs/verify-20261030T000118300588Z/manifest.json). Profile này chỉ sửa recipe pytest/plugin sau build failure, có `trial_of`; không phải case nguồn mới.

| Lượt | Kết luận và giải thích | Evidence / kiến nghị |
|---|---|---|
| 01 | `fastapi/routing.py:1487`, `add_api_websocket_route`: đổi default dependencies từ None sang list Depends. Ba HTTP mount tests vẫn pass | [Candidate](../runs/generate-20261030T000107782911Z/attempt-01/candidate.py), [log](../runs/verify-20261030T000118300588Z/attempt-01/candidate-1.stdout.txt). Không có failure được chứng minh; test scope HTTP không xác nhận mọi hành vi WebSocket đúng. Không dùng làm synthetic-failure/negative gold |
| 02 | Dòng 1568, decorator của WebSocket: `return func` → `return None`. Cùng bộ HTTP tests vẫn pass | [Candidate](../runs/generate-20261030T000107782911Z/attempt-02/candidate.py), [log](../runs/verify-20261030T000118300588Z/attempt-02/candidate-1.stdout.txt). Có khả năng vi phạm API decorator nhưng chưa có execution witness ở test scope này; giữ lượt không đạt |
| 03 | `api_route`, dòng 1479: `return decorator` → `return None`. Khi `@sub_app.get(...)` cần callable decorator, nó nhận None, gây TypeError `'NoneType' object is not callable`; ba test fail ổn định | [Candidate](../runs/generate-20261030T000107782911Z/attempt-03/candidate.py), [log](../runs/verify-20261030T000118300588Z/attempt-03/candidate-1.stdout.txt). API/return contract, nguyên nhân khác vị trí test decorator báo lỗi. Kiến nghị giữ ứng viên development, nhãn/vị trí chính thức và train pending |

<a id="expansion-02-điều-kiện-dữ-liệu-và-phần-người-dùng-quyết-định"></a>

### Điều kiện dữ liệu và phần người dùng quyết định

- Không có nhãn generator trong v3; không suy thiếu nhãn thành unknown gold. Agent chỉ nêu mô tả tạm thời từ code/log.
- Các edit không thêm comment tiết lộ ý đồ. Marker X/extra hoặc offset tùy ý là vấn đề tính tự nhiên/shortcut phân phối, không tự đồng nghĩa lộ đáp án; input 3B thực tế chưa được đóng gói. Source code/stack trace đúng contract là evidence được phép.
- Reference patch, explanations và assessment nằm ngoài input chẩn đoán. Hai cohort chỉ development; không đánh giá độc lập hoặc training eligibility tự động.
- Người dùng review các kiến nghị sử dụng, đặc biệt syntax-violation và artificial markers. Không yêu cầu tự dò lại code/log. **Mọi confirmed label/location, reviewer và training approval mới vẫn pending; raw review.json không đổi.**
