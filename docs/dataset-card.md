# Dataset v1 — bản đang xây dựng


<!-- dataset-v1-current:start -->
## Checkpoint hiện hành

2026-11-12T18:43:27+07:00: 471 profiles/449 sources đã thử; 285 strict-supported/333 seed pass. Đã xuất 265 real silver {'train': 181, 'test': 41, 'validation': 43}, 105 synthetic silver trước final selection; 20 real quarantine/92 synthetic loại sau review. 372 request7B đã reserve/197 đạt runner. Software106:105pass/1skip. Dataset chưa khóa; M0/M1/M2/M5 chưa chạy nghiên cứu.

Đã chọn250real(175train/37validation/38test) theo stable-ID; chưa là dataset lock. Có105synthetic export,102trong final class/quality scope: thiếu73/175. Source queue đã xong13:39. Generator mới bị gián đoạn, không còn worker;372lời gọi đã hoàn tất, một verification unknown24455. Stage sinh đã hết ngân sách gồm thời gian in-flight bị gián đoạn; không reset/replay/gọi mới. Đang audit352records lựa chọn; M0/M1/M2/M5 vẫn gated.

[Checkpoint](../runs/experiment-20261111T192045721211Z/curation-checkpoint-2026-11-12T184327_0700.json). Token-only audit276:0target overflow/context2048-response384; chưa phải suy luận3B. Silver không là expert gold, raw evidence bất biến. Group/selection lock vẫn bắt buộc trước research fit. [Bằng chứng tiến độ trong project](evidence/dataset-v1-progress/README.md).
<!-- dataset-v1-current:end -->
Cập nhật 12/11/2026, Asia/Bangkok. Đây là manifest/card thăm dò đang xây dựng; chưa khóa dataset huấn luyện hoặc có kết quả SFT.

## Mục đích và đơn vị

Một mẫu là một tình huống lỗi có provenance, code/log tái hiện đúng revision và phân tích nguyên nhân/vị trí. Source case, environment profile, testcase và model call là các đơn vị khác nhau. Mục tiêu vẫn 250 real độc lập và synthetic đạt chất lượng bằng số real train; chưa đạt mục tiêu.

## Nguồn và vai trò

Lựa chọn hiện hành có [250 real với hash và lý do các mẫu ngoài lựa chọn](../data-manifests/dataset-v1-real-selection.json), từ plan SCM-ready525case. Có9repo: train gồm SymPy/pydicom/pvlib/astroid/marshmallow, validation Sphinx, test Pylint/Flask/pytest. Train được chọn có134logic/value và41API/type; các lớp thưa giữ nguyên evidence ngoài train, không lọc lớp heldout. Đây là protocol tự chia, chưa là benchmark chính thức hoặc dataset đã khóa. Các plan443/468 dưới đây là checkpoint lịch sử.

| Repository | Vai trò | Real được chọn | Synthetic trong phạm vi lựa chọn |
|---|---|---:|---:|
| SymPy | train | 158 | 89 |
| pvlib | train | 6 | 4 |
| astroid | train | 5 | 3 |
| pydicom | train | 4 | 3 |
| marshmallow | train | 2 | 3 |
| Sphinx | validation | 37 | 0 |
| Pylint | test | 19 | 0 |
| pytest | test | 16 | 0 |
| Flask | test | 3 | 0 |
| **Tổng** | | **250** | **102** |

Các số synthetic trên chưa thay thế final group audit hoặc learning lock. Lựa chọn lệch mạnh về SymPy;102synthetic gồm96logic/value và6API/type, khác phân bố real train134/41. Không tự cân bằng lại hoặc suy lợi ích SFT từ số lượng này. Dataset v1 hiện dùng nguồn SWE-bench đã ghim; AIDev và các pilot/expansion cũ tiếp tục nằm ở phần development lịch sử.

- SWE-bench revision `e48e2bd1e9fecd5bbd641e9414ac59da9f2e69f6`; metadata từ train/dev/test nguồn được sàng lọc cho protocol chẩn đoán tự chia. Không công bố điểm benchmark SWE-bench chính thức. Các bản nguồn thiếu test patch/F2P không đủ điều kiện.
- [Plan ban đầu](../data-manifests/dataset-v1-plan.json): 443 ứng viên, gồm 300 train/100 validation/43 test. Train: SymPy, pydicom, pvlib, astroid, marshmallow; validation: Sphinx; test: Pylint. Repo đã phơi lộ trong phát triển trước đây không làm held-out mới. Không khẳng định repo chưa xuất hiện khi model nền pretrain.
- [Recipe correction env2](../data-manifests/dataset-v1-plan-env2.json): cùng 443 tình huống nguồn, 42 profile Pylint mới bổ sung appdirs/tomlkit sau khi đọc lỗi môi trường. Vai trò repo/commit/source/test/repair patch giữ nguyên; raw profile lỗi và quan hệ lần trước được giữ. Đây không phải 42 mẫu real bổ sung.
- Cần hoàn thiện duplicate/shared-family audit trước khóa tập. Tỷ lệ 70/15/15 là mục tiêu theo nhóm, không ép dịch chuyển repo vì kết quả. W1 và hai expansion cũ tiếp tục là evidence development lịch sử.

## Frontier dữ liệu ban đầu — lịch sử

Frontier đầu tiên gồm 15 case nguồn (5 mỗi vai trò): 7 tái hiện nghiêm ngặt, 9 seed pass. Tái hiện nghiêm ngặt yêu cầu F2P/P2P giải được và đúng trên base/fixed cùng frozen harness. Head pass riêng không đủ làm mẫu real. Các lượt tiếp theo được checkpoint trong `runs/experiment-20261111T192045721211Z/real-reproduction-summary.json`; không suy tổng hiện tại từ frontier này.

Đã đóng gói sơ bộ 7 tình huống silver khác nhau theo cùng retrieval v2: 3 train, 3 validation, 1 test. Input/reference và assessment gắn hash tách riêng dưới `.cache/dataset-v1/records-retrieval-v2/`. Hai prototype retrieval v1 được giữ nguyên trong thư mục cũ, không cộng thành hai tình huống mới. Audit local `real-dataset-audit-v2.json` xác minh hash, source identity và repo/shared-commit groups, nhưng còn thiếu quy mô, support lớp và near-duplicate review nên chưa khóa final dataset. Chưa có synthetic mới trong vòng này hoặc đủ gate SFT.

## Nhãn và input

Nhãn silver gồm nguyên nhân kỹ thuật, file/hàm và giải thích có evidence; không phải expert gold. Taxonomy: syntax, dependency/configuration, API/type, logic/value; thiếu bằng chứng để unknown/quarantine. Nhãn generator, nhận định có evidence và xác nhận người dùng tách riêng. Actor real mặc định unknown. Quyền dùng silver cho thực nghiệm từ goal không phải phê duyệt expert gold.

Input chỉ có log quan sát và code truy xuất không dùng đáp án. Gold repair/test patch, cơ chế tham chiếu, selected edit site và label không được đưa vào input. Các trường hợp registry module hoặc thiếu phương thức phải ghi rõ phạm vi vị trí, không bịa dòng/hàm có sẵn. Giữ riêng độ bao phủ truy xuất và lỗi chẩn đoán; retrieval bỏ sót vẫn tính trượt toàn pipeline.

## Giới hạn và cổng sử dụng

Chưa xác minh đủ chất lượng nhãn, nhóm trùng, phân bố lớp hoặc tính đại diện. Các recipe là tái dựng local có giới hạn, không phải log CI lịch sử. License được đối chiếu marker/file hash tại source ghim; đây không phải thẩm định pháp lý. Nguồn và license phải đi kèm từng record.

Chỉ chạy hai SFT khi đủ 250 real, mỗi split tối thiểu 25, train có ít nhất hai lớp với 10 mẫu/lớp, đồng nhất input và matched synthetic. Chưa đáp ứng thì giữ trạng thái chưa hoàn thành. Không dùng frontier nhỏ hoặc phép đo 3B runtime thay cho đánh giá nghiên cứu.


## Checkpoint lịch sử sau hiệu chỉnh môi trường và usage-limit resume

Pool tại checkpoint này có 468 source identities trong [env-ready plan](../data-manifests/dataset-v1-plan-env-ready.json), 300 train/100 validation/68 test. Thêm 11 Flask/14 Pylint source task trong cùng dataset revision; không đổi vai trò các repo cũ và không dựa trên điểm model. Các profile hiệu chỉnh chỉ thay environment/runner, không phải source fault mới. Profile lỗi và manifest cũ giữ nguyên; checkpoint đầu tài liệu phản ánh pool/kết quả mới hơn.

Có 11 export silver cùng retrieval v2 (4 train/4 validation/3 test) và một class-attribute quarantine chưa export. Audit 11 mẫu vẫn là draft và thiếu số lượng/support/final near-duplicate review. Các đoạn phía trên về frontier/bảy export là mốc lịch sử, không cộng dồn thành dataset mới. Một Sphinx thiếu method và một SymPy registry ngoài hàm trong prototype còn cần kiểm tra lại điều kiện scope khi khóa dataset.

Pydicom scratch-file case đã strict-supported sau khi dùng /work tmpfs mode 1777, còn source/test chỉ đọc. Sphinx dependency bổ sung được đối chiếu pyproject của revision nguồn. Trường hợp pvlib head pass nhưng base không khớp F2P vẫn chỉ là seed, không đổi thành real verified. Source counts cập nhật trong summary experiment local; counts chưa có gold approval.

Code học/đánh giá đã có nhưng chưa chạy research fit, SFT hoặc test. Cần hoàn tất orchestration và dữ liệu trước khi mở các bước này. Mọi thời gian usage-limit vẫn nằm trong deadline 24 giờ; stage real/synthetic tính hợp thời gian operation đã ghi, không xóa ngân sách đã tiêu.


### Final selection policy — 12 November, before research prediction

[data-manifests/dataset-v1-selection-policy.json](../data-manifests/dataset-v1-selection-policy.json) applies the existing minimum10 real train examples per learned class: sparse train classes retain their reviewed labels/evidence but are outside the final selection. Validation/test are not filtered for unseen classes; their support and all errors remain reportable. At the12:36checkpoint, train had128logic/value,40API/type,1configuration,1syntax; this is a class-coverage limitation, not permission to relabel. Real role targets175/37/38 and matched synthetic remain mandatory; deficits leave SFT gated. Stable IDs order selection after quality/dedup, never retrieval coverage or model performance. A bound final ledger/audit is still pending.


[Final-selection exclusions](../data-manifests/dataset-v1-selection-exclusions.json) retain two sparse-class real train records and three exploratory synthetic records outside the final training selection. Two Set+integer synthetic perturbations had only qualified realism and are not counted toward the matched target; their previous silver assessments/raw remain unchanged. The third synthetic is outside the learned real-train class scope. This is not a gold-label change or five new samples.


### Input coverage limitation from the276-record token preflight

The fixed retrieval-v2 input includes at least one reference function after tokenization for54/170real train,8/43validation,13/41test and9/22synthetic train records. This is a reference-aware data preflight, not a3B prediction score or final dataset metric. It is not used to tune retrieval/prompt or select/exclude records. Maximum prepared input1636tokens and target127tokens fit the2048/384budget. All retrieval misses remain errors in subsequent end-to-end metrics; report this bottleneck separately from generation quality. Final model test predictions remain unopened.
