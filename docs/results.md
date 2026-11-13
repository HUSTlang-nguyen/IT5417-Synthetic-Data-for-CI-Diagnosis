# Kết quả vòng dataset v1 — cập nhật 13/11/2026

## Evaluation v1 — M1-P2 và final test

[Validation đã chốt](evaluation-validation.md) dùng M1-P2 **prompt mới**, parser strict và user code/log cũ. M1-P2 accuracy29/37, Macro-F1 .3642, function6/37, joint4/37, invalid1/37; không chọn lại checkpoint M2/M5. M1 cũ giữ điểm0 do37/37 output có Markdown fence.

**Final test hoàn tất một lần trên cùng38real**, run `evaluation-20261112T210848574175Z`: M0 accuracy9/38/F1 .1106; M1-P2 16/38/.2549; M2 22/38/.3132; M5 24/38/.3375. Joint M2/M5 cùng4/38, định vị hàm6/38 so với7/38; chưa đủ kết luận synthetic có lợi tổng quát. [Bảng test, từng lớp/repo và chi phí](evaluation-results.md), [phân tích lỗi](evaluation-error-analysis.md), [manifest](../data-manifests/evaluation-v1.json), [protocol](evaluation-protocol-v1.md), [receipt hash/request](evidence/dataset-v1-progress/evaluation-integrity-20261113.json). 151request mới finished, không gọi trùng; nhãn silver và gold pending. Kiểm thử phần mềm132:131pass/1skip. Các checkpoint dưới đây là lịch sử trước khi mở test.

## Continuation v1.2 — cả hai đã học đủ tổng 10 epoch

M2 hoàn tất02:09:56, M5 hoàn tất03:38:20ngày13/11+07. Globalupdates220/350, tổngexposures1750/2760, mỗi mẫu10lượt; adapterreload/hash và các metrics hash đạt. [Evidence hoàn tất](evidence/dataset-v1-progress/continuation-validation-complete-20261113.json). Kiểm tra tương thích final-model bằng hàm đọc thuần đạt; chưa ghi finaltestlock hoặc gọi model/test.

| Model | Macro-F1 checkpoint104 | Macro-F1 epoch10 | Joint104 | Joint epoch10 | Checkpoint được chọn |
|---|---:|---:|---:|---:|---|
| M2 | 0,3515 | 0,3226 | 4/37 | 4/37 | Parent104, theo quy tắc hòa chọn sớm |
| M5 | 0,4060 | 0,3731 | 5/37 | 5/37 | Parent104, theo quy tắc hòa chọn sớm |

Định vị hàm vẫn5/37 cho cảhai ở các mốc mới. Chưa thấy lợi ích học tiếp theo metric hiện hành; không suy rằng thêm epoch sẽ khắc phục retrieval/nhãn hoặc rằng model đã hội tụ toàn cục. Điểm chính vẫn lấy checkpoint đã chọn, phân biệt với điểm epoch10. Các đoạn đề xuất176updates/fresh-base bên dưới là lịch sử trước khi người dùng chọn continuation; không được triển khai.

## Pilot v1.1 — validation hoàn tất, kiểm tra 13/11/2026 lúc 00:39 +07

Đã tính lại metric từ prediction đã lưu của cùng 37 real validation, đối chiếu input prompt hashes giống nhau giữa bốn model và reference hashes khớp. Không gọi model, chuẩn hóa output, đổi scorer hoặc mở final test. [Evidence cuối](evidence/dataset-v1-progress/validation-comparison-final-20261113.json); [snapshot lịch sử lúc M5 mới xong step52](evidence/dataset-v1-progress/validation-comparison-20261113.json) giữ nguyên.

| Model | Trạng thái/checkpoint | Accuracy phân loại | Macro-F1 | File Top-1 | Hàm Top-1 | Joint loại/hàm Top-1 | Invalid |
|---|---|---:|---:|---:|---:|---:|---:|
| M0 | Validation hoàn tất | 6/37 = 16,22% | 0,0835 | Không áp dụng | Không áp dụng | Không áp dụng | 0/37 |
| M1 | Validation hoàn tất | 0/37 | 0 | 0/37 | 0/37 | 0/37 | 37/37 |
| M2 | Hoàn tất; chọn step104 | 28/37 = 75,68% | 0,3515 | 9/37 = 24,32% | 5/37 = 13,51% | 4/37 = 10,81% | 0/37 |
| M5 | Hoàn tất; chọn step104 | 30/37 = 81,08% | 0,4060 | 9/37 = 24,32% | 5/37 = 13,51% | 5/37 = 13,51% | 1/37 |

M1 có37response lưu và hash khớp, toàn bộ bắt đầu bằng Markdown fence và parsed=null; không chạm trần384output tokens. Điểm0 là kết quả end-to-end của parser JSON nghiêm ngặt, không chứng minh mọi suy luận nguyên nhân đều sai. Chưa sửa parser hoặc tự làm sạch response để đổi điểm. Vì SFT còn học tuân thủ JSON, không quy toàn bộ chênh lệch M1–M2 cho năng lực chẩn đoán.

M5 hoàn tất00:36:59,104updates/2,9855epochs, adapter reload/hash đạt; cả M2/M5 chọn104. M5 từ52→104 giữaccuracy30/37 vàfunction5/37, Macro-F1 tăng .350806→.405956, joint3/37→5/37; có1invalid ở104. M2 từ52→104 tăng Macro-F1 .191071→.351515, joint2/37→4/37. Hai mốc chưa chứng minh hội tụ. Accuracy riêng cũng cần thận trọng: lớp logic/value chiếm29/37, dự đoán luôn lớp này cho accuracy78,38%. Macro-F1 hiện lấy trung bình cố định bốn lớp, gồm syntax không có support trong validation. Metric định vị yêu cầu vị trí reference có trong retrieved code; coverage hàm7/37 là hạn chế pipeline. M2/M5 đều không đoán đúng4mẫu dependency/configuration; train không có lớp đó. Thêm epoch trên cùng tập không bổ sung support lớp hoặc code bị thiếu. Dữ liệu silver và validation nhỏ chưa đủ kết luận tổng quát về synthetic; raw runs giữ nguyên.

**Đề xuất, chưa phê duyệt/thực thi:** thử một ngân sách mới tổng176updates cho mỗi SFT, từ cùng base3B với lịch LR tương ứng; tương đương M2≈8epochs, M5≈5,03epochs, cao hơn hiện tại khoảng3,27 và2,04epochs. Đây là phép thử hữu hạn, không phải ngưỡng hội tụ đã đo. Giữ kết quả104 và protocol/cap hiện tại; cần phiên bản cấu hình riêng trước chạy, không dùng resume để gia hạn run đã xong. M0/M1 không có đề xuất thêm epoch. Tăng số mốc validation (khoảng35updates/lần, giữ104 và mốc cuối) để quan sát xu hướng; chưa sửa code hoặc bật early stopping. Chọn theo joint với quy tắc đã chốt ở protocol mới, không dùng final test để quyết định.

## Kết quả lịch sử vòng thu thập v1.0

**Cập nhật sau bàn giao:** đã triển khai [pilot thủ công v1.1](experiment-protocol-v1.1.md) dùng 101 synthetic hiện có theo yêu cầu người dùng, với lock riêng và [lệnh chạy](training-runbook.md). Chưa train hoặc mở model test. Báo cáo dưới đây giữ nguyên đánh giá mục tiêu v1.0, không coi pilot code setup là hoàn tất thí nghiệm cũ.

**Đạt phần dữ liệu thật, chưa hoàn thành thí nghiệm SFT.** Đã chọn250real silver theo175train/37validation/38test; có101synthetic sau kiểm tra chất lượng và trùng lặp, thiếu74so với mục tiêu175. Cổng dữ liệu từ chối mở huấn luyện; không giảm mục tiêu hoặc dùng tập thiếu để báo hoàn thành.

[Trạng thái hiện hành](../data-manifests/dataset-v1-status.json), [lựa chọn351bản ghi](../data-manifests/dataset-v1-curated-selection.json), [evidence/group audit](evidence/dataset-v1-progress/selection-audit-20261112.json), [dataset card](dataset-card.md), [protocol](experiment-protocol.md).

## Các mẫu số thực đạt

| Giai đoạn | Số lượng | Ý nghĩa |
|---|---:|---|
| Nguồn trong plan đã ghim | 525 | Ứng viên, chưa phải dữ liệu đạt |
| Case nguồn đã thử | 449 | Không cộng profile sửa môi trường thành case mới |
| Profile tái hiện đã thử | 471 | Bao gồm các profile lỗi và một lượt unknown |
| Tái hiện nghiêm ngặt | 285 | Test F2P/P2P trênbase/fixed và source/test bất biến |
| Seedpass | 333 | Headpass riêng không đủ để nhận mẫu real |
| Real đã rà/đóng gói silver | 265 | 20casekhác quarantine, raw giữ nguyên |
| Real được chọn | 250 | 175train/37validation/38test |
| Lời gọi7B đã có response lưu | 372 | Trần600; không đồng nghĩa372mẫu đạt |
| Lượt đạt runner | 197 | Baselinepass →3failổn định →restorationpass |
| Verificationfailed / invalidoutput | 159 /13 | Giữ trong mẫu số |
| Attempt chờ verification bị gián đoạn | 3 | Một seedunknown; không chạy lại |
| Synthetic xuất silver | 105 | Trước các loại trừ lựa chọn cuối |
| Synthetic còn trong lựa chọn | 101 | Thiếu74/175; khác byte và đã xử lý nhóm lexical |

Ba cohort hoàn tất đầu có69+120lời gọi; cohort quality-r3 ghi183lời gọi,60verification sessions hoàn tất, một casekhông có site và một verification bị gián đoạn. Model/prompt/options/seeds và mỗi phiên bản hướng dẫn được lưu trong raw artifact; không coi các cohort khác case là đối chứng kiểm soát tác động prompt.

## Kiểm tra và curation

- Full audit352bản ghi hoàn tất19:22:53+07: kiểm tra lại source/test inventories, raw logs, candidate, manifests, assessments và hash; không có nhóm giao giữa các split, exact source duplicate hoặc exact candidate duplicate.
- Có hai nhóm lexical cần phân xử. Constant printer cùng đổi`math.pi`thành`math.pi()`ở hai revision là cùng cơ chế: giữ bản sớm, loại bản sau. Hai lỗi sentinel trong`Vector.__add__`và`Vector.__eq__`có cùng difftext nhưng khác hợp đồng toán tử/cơ chế và log; giữ như một họ train có tương quan.
- Sau loại trùng còn351bản ghi. Hash manifest/input/reference/assessment của351bản giữ lại được kiểm tra không đổi; group review gắn đúng selectionhash và parent audit. Không gọi đây là một lần deep inventory audit mới.
- Tokenizer-only preflight352:0targetoverflow trong context2048/response384; subset351giữ kết quả này. Không load model hoặc tạo dự đoán trong bước đó.
- Reference function có trong code truy xuất sau tokenization:59/175realtrain,7/37validation,12/38test,44/101synthetic. Đây là kiểm tra dữ liệu có dùng reference, không phải độ chính xác model. Không sửa retrieval hoặc lọc mẫu theo các số heldout; misses vẫn phải tính lỗi toàn pipeline.
- Software suite:106kiểm thử,105pass/1opt-inDocker skip. Đây là kết quả phần mềm, khác test trong repo nguồn. [Log](evidence/dataset-v1-progress/software-tests-106.txt).
- Kiểm tra2.504file lịch sử:0rawđổi/0missing; hai trang chỉ mục tài liệu thay đổi có chủ đích. Evidence mới, các review bị validator từ chối và erratum đều giữ riêng.

## Kết quả model

| Model | Trạng thái | Macro-F1 / file-hàmTop1/5 |
|---|---|---|
| M0 TF-IDF+LogReg | Chưa fit, data gate chưa đạt | Chưa có; localization không thuộc classifier này |
| M1 3Bprompt-only | Chưa chạy nghiên cứu | Chưa có |
| M2 3BSFTreal-only | Chưa train | Chưa có |
| M5 3BSFTreal+synthetic | Chưa train | Chưa có |

Có một runtime calibration trên train từ trước: load16.750s, inference24.515s,1.635input/199outputtokens, peakCUDAallocated2.43GiB/reserved3.01GiB. Output fencedJSON không hợp parser nghiêm ngặt. Không phải baselineM1, kết quả validation/test hay phép đo thời gian train. Không có loss/adapter/checkpoint/độ cải thiện SFT để báo cáo.

## Giới hạn và điểm dừng

- Dữ liệu hiện hành lấy từ SWE-benchrevision đã ghim theo protocol tự chia9repo; AIDev/pilot cũ giữ development lịch sử. Không phải điểm benchmarkSWE-bench chính thức hoặc bảo đảm model nền chưa từng thấy repo.
- Nhãn đều silver, actorrealunknown, goldpending. Trainreal134logic/value+41API/type; các lớp thưa giữ evidence ngoài lựa chọn, heldout không lọc lớp. SymPy chiếm158/175realtrain và88/101synthetic; synthetic95logic/value+6API/type. Không khẳng định tính đại diện hoặc độc lập giữa mọi biến thể.
- Worker sinh bị gián đoạn: last savedevent16:07:41, không còn tiến trình khi kiểm tra18:25. Nguyên nhân chưa xác định. Verification24455được đánhunknown bằng sidecar; raw giữ nguyên, không replay.
- Stage sinh đã tính22.198s so với cap21.600s, bao gồm khoảng unknownin-flight tới lúc được phát hiện. Đây là thời gian tính ngân sách có phần chưa xác định, không phải thời gian GPUactive đo được. Không đặt lại cap hoặc phát sinh thêm request sau khi xác nhận hết budget.
- Deadline24h vẫn là13/11/2026lúc02:19:29+07. Dù còn thời gian lịch, stage sinh đã hết budget và chưa đủ matchedsynthetic. Muốn tiếp tục thu phần thiếu cần quyết định ngân sách/thí nghiệm tiếp theo; không tự mở rộng trong vòng này.

Bàn giao code/protocol, manifest250real, partial selection351, reviews, hash/evidence, software tests, storage inventory và trạng thái thiếu74synthetic. Mục tiêu đầy đủ250real+175synthetic+M0/M1/M2/M5 vẫn **chưa đạt**; cổng huấn luyện và finalmodeltest chưa mở.
