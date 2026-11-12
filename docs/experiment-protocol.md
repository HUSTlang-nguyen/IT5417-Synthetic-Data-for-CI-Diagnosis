# Protocol dataset v1 và SFT thăm dò

Phiên bản 1.0, khóa trước lời gọi model mới ngày 12/11/2026, Asia/Bangkok. Người dùng đã cho phép thực thi goal 24 giờ, dùng silver có đánh dấu, giữ riêng repo và giữ cổng chất lượng. Nghiên cứu phân loại nguyên nhân và khoanh vùng file/hàm với hai nhiệm vụ chính; không coi kết quả thăm dò là expert-gold benchmark.

## Mục tiêu và thời gian

- 250 tình huống real khác nhau sau kiểm tra evidence/nhãn/trùng lặp; khoảng 70/15/15 theo repo và nhóm liên quan. Synthetic train đạt chất lượng bằng số real train thực tế, dự kiến 175. Thiếu mục tiêu không tự đổi định nghĩa hoàn tất.
- Phiên local bắt đầu 12/11/2026 02:19:29 +07; hạn tuyệt đối 13/11/2026 02:19:29 +07, bao gồm lập trình/setup. Không bắt đầu operation không đủ thời gian hoặc dưới 20 GiB trống; không xóa cache/images cũ.
- Trần 600 request generator 7B; 1.500 request suy luận diagnoser 3B (không tính optimizer updates). Request timeout 180s; Docker build 1200s/test 300s. Các trần không có nghĩa đủ thời gian thực hiện tất cả. Stage tối đa discovery 2h, real reproduction 8h, synthetic 6h, ML setup 2h, mỗi SFT 2h, evaluation 2h; deadline toàn phiên luôn ưu tiên.
- Stage/request được reserve trước side effect, checkpoint sau kết quả; công việc hoàn tất không chạy lại. Operation gián đoạn không rõ kết quả phải giữ unknown và liên kết lần trước, không tự gửi lại.

## Đơn vị dữ liệu và cổng chất lượng

- Real là tình huống lỗi từ code/lịch sử dự án nguồn, tái hiện local có log, đúng revision và test. PR metadata, head pass hoặc số testcase thất bại không tự thành mẫu real. Mỗi nhóm một cơ chế, không tách repetition/output log thành mẫu mới.
- Reproduction cần base fail/fixed pass trong cùng harness bất biến, kiểm tra inventory/hash, repair/test patch provenance và test IDs. Lỗi setup không được gán thành nguyên nhân ứng dụng. Source FAIL_TO_PASS/PASS_TO_PASS unresolved giữ qualification, chưa đạt real gate nghiêm ngặt.
- Silver do phân tích evidence theo ci-data-review, ghi nguồn nhãn, cơ chế, reference file/hàm, độ chắc chắn và lý do sử dụng. Nhãn generator và confirmed human gold là các trường khác. Thiếu evidence giữ unknown/quarantine; không ép lớp theo exception hoặc để đủ quota.
- Synthetic chỉ từ train seed pass: giữ baseline pass → ba failure có signature ổn định → restored pass, nguyên candidate/tests. Loại byte trùng, instruction violation và các mẫu đã bị giới hạn analysis-only. Sửa một dòng không tự xác nhận causal function, nhãn hoặc tính tự nhiên.
- Real phải đạt 250 và đủ các split theo repo trước hai lượt đối chứng SFT; mỗi split có tối thiểu 25 real, train tối thiểu hai lớp và 10 mẫu/lớp trong các lớp được học. Mixed chỉ chạy khi số synthetic hợp lệ bằng real train. Thiếu cổng: vẫn xây phần mềm/artifact, có thể báo prompt-only hợp lệ, không ép SFT hoặc tuyên bố đủ nghiên cứu.

## Nhóm và chống leakage

- Mọi repo/group đã xem trong development-groups-v1, properr và ví dụ astropy trước đây chỉ ở train/development. Validation/test là repo mới đối với dự án; không khẳng định model nền chưa thấy repo khi pretraining.
- Ghim source revision và role của repo bằng metadata trước test/model. Chọn task Python có test rõ, license xác minh, ưu tiên ít dependency; trong các recipe đã hỗ trợ, xếp theo số file sản phẩm, số byte patch sản phẩm và instance ID. Không đổi role vì nhãn hoặc kết quả model; không tự bù trường hợp thiếu bằng di chuyển train sang test.
- Shared commits/forks/duplicate family không qua split; hash chuẩn hóa/edit gần trùng cần audit và quyết định trước khóa dataset. Tất cả source cũ và synthetic cũ vẫn có provenance development, không tự đổi thành test.

## Ghim nguồn trước tái hiện dataset v1

- Nguồn SWE-bench revision e48e2bd1e9fecd5bbd641e9414ac59da9f2e69f6; sàng lọc 21.527 metadata rows từ các split nguồn. Nhiều bản train nguồn không có test patch/FAIL_TO_PASS nên không đủ điều kiện. Có sử dụng bản test của nguồn làm nguồn task cho protocol chẩn đoán tự chia này; không báo điểm benchmark SWE-bench chính thức.
- data-manifests/dataset-v1-plan.json ghim 443 ứng viên, chưa phải 443 mẫu đạt: train 300 (SymPy/pydicom/pvlib/astroid/marshmallow), validation 100 (Sphinx), test 43 (Pylint). Vai trò đã chọn trước thực thi; repo đánh giá chưa dùng để phát triển prompt/model trong dự án. Chỉ metadata môi trường và harness được xử lý khi dựng môi trường; không sử dụng phản hồi dự đoán test.
- Loại source instance từng chạy, không dùng profile mới để tăng mẫu số. Bản source-plan-lock.json trong experiment ghim hash manifest/case/repair/test patch trước lần Docker đầu tiên. Hash license tại commit được lưu riêng; không tuyên bố kiểm tra pháp lý chuyên sâu.
- SymPy có test ID nguồn dạng tên hàm: ánh xạ chính xác sang một hàm test duy nhất trong frozen harness, từ chối thiếu/trùng; không suy test bằng gần giống tên. Mọi failure/timeout giữ artifact và mẫu số; không tự retry môi trường lỗi.

## Input và target

- Model chỉ thấy log execution đã chuẩn hóa bảo toàn triệu chứng và code truy xuất tại đúng revision. Không đưa problem statement có lời giải, gold repair/test patch, proposal/explanation, allowed_file/focus_line/site catalog hoặc assessment vào input. Test patch là harness tham chiếu, không là query truy xuất.
- Truy xuất code bằng đường dẫn production trong stack trace và lexical search từ failure message/symbol trên inventory Python source. Xếp hạng cố định trước chấm; kèm ngữ cảnh hàm có line numbers và tối đa năm hàm/file theo ngân sách token. Không dùng reference để chọn excerpt. Nếu chỉ có một ứng viên vì log, ghi rõ candidate count; không gọi đó là tìm kiếm toàn repo không điều kiện.
- Input serialized và reference tách riêng. Context tổng 2.048 token bao gồm đáp án; giữ tối đa 384 token output, instruction/log có ngân sách cố định và cắt code có thống kê. Reference locations không được dùng để sửa query/truncation. Báo retrieval coverage trước/sau tokenization.
- Target JSON: cause_type, ranked locations (tối đa năm cặp file/qualified function), explanation ngắn. Enum syntax, dependency/configuration, API/type, logic/value, unknown. Actor metadata mặc định unknown trừ provenance trực tiếp; không là task chính.

## Mô hình và đối chứng

- M0: TF-IDF + Logistic Regression, fit chỉ real train, cùng text input; chỉ so nhiệm vụ phân loại. M1: Qwen2.5-Coder-3B-Instruct prompt-only. M2 và M5: hai fresh adapters độc lập từ cùng HF base revision/chat template, không nối từ adapter pilot hoặc từ nhau.
- SFT QLoRA: NF4/double quant, LoRA r16/alpha32/dropout0.05 all-linear, lr1e-4, batch1/accumulation8, seed5417, response-only loss. Hai run có cùng số update: ceil(3 * mixed_train_size / 8), tối đa 180; shuffle/cycle real-only để khớp updates. Lưu số lần thấy từng mẫu, token input/target và compute thực, không tuyên bố tách hoàn toàn ảnh hưởng số lượng/compute khi token khác.
- Train/eval dùng HF checkpoint duy nhất với revision ghim trước download. Ghim optional ML environment sau compatibility check; core pipeline vẫn standard library. Candidate code không import/execute trên host; training chỉ xử lý code dưới dạng text.
- Nếu OOM, giữ log lỗi và tạo config run mới context1024 áp cùng M1/M2/M5, tối đa một corrective retry. Không thay model bằng model phụ, không silently drop dữ liệu hoặc baseline để có điểm.
- Validation giữa và cuối: chọn joint Top-1 success (đúng class và function), hòa chọn checkpoint sớm. Test giữ kín dự đoán/metric tới khi config/checkpoint tất cả model khóa; sau đó chấm một lần. Không sửa prompt/filter từ phản hồi test.

## Metric và logging

- Báo Macro-F1, precision/recall/F1/support từng lớp; file/function Top-1/Top-5; joint class+function Top-1; retrieval coverage, invalid/unknown output, missing-reference counts. Không gộp các nhiệm vụ thành một con số che lỗi khoanh vùng.
- Eligibility/reference set khóa trước dự đoán. Mẫu đã đủ reference nhưng retrieval bỏ sót, trả sai format hoặc không trả vị trí tính trượt end-to-end. Multiple valid locations chấp nhận ít nhất một đúng và báo Recall@k khi có nhiều vị trí đủ reference. Nhãn không chắc ghi riêng, không loại sau khi thấy model sai.
- Lưu dataset version/hash, split/sample/group IDs, source/ref/proposal separation, label provenance, code/log/inventory hashes; model/tokenizer/config/packages/seed; loss/lr/grad norm/updates/epochs/tokens; validation/checkpoint selection; từng raw prediction và parsed output; metric/confusion matrix; timing setup/load/train/eval và GPU memory thực đo.
- Checkpoint gồm adapter và trainer/optimizer/scheduler/RNG state khi hỗ trợ; reload verification. Raw evidence/model/data/checkpoints bị ignore; chỉ code, config nhỏ, summaries và textual evidence phù hợp trong Git. Không push/merge main.

## Bàn giao

Dataset manifest/card, protocol, code/tests; kết quả M0/M1/M2/M5 hoặc trạng thái chưa thực hiện với nguyên nhân; báo mẫu số/chi phí/giới hạn silver và held-out repo. Roadmap chỉ done theo gate có evidence; thiếu 250 real, synthetic hoặc bất kỳ thí nghiệm bắt buộc nào thì goal chưa hoàn tất. Hết ngân sách lưu trạng thái và bàn giao thật, không sửa mục tiêu để nhận hoàn tất.

## Chi tiết triển khai khóa trước các lượt học/held-out prediction

- M0 dùng cùng text đã qua chat-template/token budget như 3B: TF-IDF word 1–2 gram, tối đa 20.000 features; LogisticRegression C=1, class_weight=balanced, max_iter=1000, random_state=5417. Chỉ fit real train; localization của classifier là không áp dụng.
- M2/M5 cùng 132 updates nếu mixed có 350 mẫu theo công thức đã ghi; không coi đây là số update thực đạt trước khi chạy. AdamW torch, linear scheduler, warmup=0, bf16, gradient checkpointing non-reentrant. Loss chỉ trên đáp án; target quá 384 token bị từ chối, không cắt ngầm. Lưu cả config JSON đầy đủ của Trainer và exposures/token thực tại từng checkpoint.
- Hai SFT có đồng hồ/cap riêng, gồm cả validation của run đó. Evaluation dùng hợp các khoảng operation đã ghi để không tính hai lần request nằm trong parent và không tính khoảng nghỉ giữa M1 và hai SFT. Real reproduction/synthetic cũng chuyển sang cách tính operation này khi tiếp tục sau usage-limit; không xóa phần đã tiêu, không tăng trần, deadline 13/11 02:19:29 +07 vẫn tính toàn bộ thời gian nghỉ.
- Sau frontier môi trường, thêm 25 source task (11 Flask/14 Pylint) trong cùng revision dữ liệu, thành 468 ứng viên; Flask được gán test trước thực thi. Không chuyển repo cũ sang vai trò khác hoặc dựa vào điểm model để chọn case. Các repair mới có tối đa năm file Python sản phẩm, vẫn giữ frozen tests và source F2P/P2P.
- Profile môi trường mới chỉ sửa khai báo runtime/test: cwd `/work` cho scratch file pydicom, pytest-mock cho pvlib, Git/importlib-metadata và test dependencies khai báo của Sphinx. Một trial pydicom `-r1` sửa lỗi mode tmpfs của runner có liên kết hai profile thất bại trước; không sửa test/source/output. Profile không làm tăng số tình huống real.


## Addendum triển khai trước held-out prediction — 12/11/2026

- Một lần calibration trên train được phép trước dataset gate để đo runtime; không dùng làm điểm M1 chính. Raw output có Markdown và bị parser JSON nghiêm ngặt từ chối được giữ nguyên. Không sửa output thành hợp lệ.
- Retrieval v1 bộc lộ nhiễu từ pytest progress trong calibration train. Retrieval v2 dùng failure section, stack, symbol và tên module quan sát được, thêm module-level context; không nhận gold location. Bản xuất đầu tiên vẫn giữ nguyên, final dataset cần một phiên bản input thống nhất và hash mới. Chưa dự đoán validation/test hoặc tune từ điểm test.
- Vị trí cấp module dùng marker <module>; phương thức còn thiếu phải có assessment nêu causal absence và được đối chiếu với định nghĩa trong repair, không giả có dòng đó trên base. Report cần nêu những trường hợp này, không gọi mọi vị trí là một function hiện hữu.
- Sau frontier môi trường, có đúng một profile correction env2 cho các Pylint case chưa đạt: thêm appdirs/tomlkit, cùng source/tests/patches/roles. Các profile/lỗi cũ giữ nguyên và liên kết phiên trước; không retry mù hoặc replay operation chưa rõ trạng thái. Source plan env2 được ghim riêng trước lần chạy; profile không làm tăng số real độc lập. Đây là correction có nguyên nhân từ evidence môi trường, không thay test để ép failure/pass.


## Bổ sung thu thập trước held-out prediction

Pool chuẩn bị 525 nguồn, thêm 57 pytest task được gán test trước thực thi. Ba task đầu theo thứ tự metadata được tách làm calibration môi trường có giới hạn; không là điểm model hoặc final dataset. Curation-buffer plan giữ mục tiêu cuối 250 (khoảng 175/37/38) nhưng thu thập tối đa 195/45/45 strict reproduction để bù các mẫu không đạt scope/duplicate review. Không chuyển vai trò repo và không chọn từ điểm model. Mọi quota request, stage cap và deadline ban đầu giữ nguyên.

Checkpoint metadata có thể chờ khóa tối đa 30 giây khi tiến trình khác đang ghi; worker Docker/model vẫn từ chối chạy đồng thời. Một xung đột thực tế đã được khôi phục bằng kiểm tra hash artifact có sẵn, không replay model.

## Prompt quality-r2 trước lô synthetic tiếp theo

Review chỉ trên train cho thấy marker, cộng lệch tùy ý và `and False`/`or True` có thể đạt runner nhưng không đạt tính hợp lý. Các mẫu đó giữ execution evidence và disposition riêng, không tự thành train. Prompt revision `single-line-site-v3-quality-r2` yêu cầu lỗi comparison/boundary/operator/attribute/call/guarded-return có căn cứ trong code/test, cấm các thiết bị gây lỗi tùy ý nói trên. Định dạng chỉnh một dòng v3, model/digest, options, seeds5417–5419, ba lượt/seed và ngân sách giữ nguyên; đây là thay đổi hướng dẫn sinh, không phải kết quả chất lượng đã chứng minh. Mỗi run mới ghi `prompt_revision`; run v3 cũ không có trường này vẫn giữ nguyên, không chạy lại. Không dùng dự đoán validation/test để sửa prompt.


### Final selection policy — 12 November, before research prediction

[data-manifests/dataset-v1-selection-policy.json](../data-manifests/dataset-v1-selection-policy.json) applies the existing minimum10 real train examples per learned class: sparse train classes retain their reviewed labels/evidence but are outside the final selection. Validation/test are not filtered for unseen classes; their support and all errors remain reportable. At the12:36checkpoint, train had128logic/value,40API/type,1configuration,1syntax; this is a class-coverage limitation, not permission to relabel. Real role targets175/37/38 and matched synthetic remain mandatory; deficits leave SFT gated. Stable IDs order selection after quality/dedup, never retrieval coverage or model performance. A bound final ledger/audit is still pending.


### Fresh-generation quality-r3 — before its first request

`single-line-site-v3-quality-r3` replaces the always-near-line1 site preference for fresh workers. It prefers statically test-named source functions/classes, then chooses at most18 sites by SHA256(case identity,line), with whole-file fallback. Each attempt shows its own bounded source neighborhoods. This is a diversity heuristic, not measured test coverage; no gold repair, review/reference labels or heldout model feedback enter it. Model/options/seeds5417–5419, schema,180s requests and global600 cap stay fixed. The existing40-seed quality-r2 worker continues its loaded code; raw per-attempt prompts/revision and hash-verified implementation snapshots distinguish cohorts even when its on-disk implementation hash observes the newer file. New R3 requests are not yet measured. Software105tests:104pass/1skip.


### Fresh verification timeout stop

The next quality-r3 worker stops candidate repetitions after its first timeout, still executes restoration, and records `verification_policy=stop_repetitions_after_timeout_restore_still_required_v1`. Acceptance still requires three stable test failures; a timeout can never pass. Three generation attempts remain in the denominator, with incomplete repetition count visible. The in-flight quality-r2 cohort is unchanged. The prior waiting r3 queue was cancelled before calling run_batch and replaced to load the tested verifier; no completed seed is repeated. Software106:105pass/1skip.
