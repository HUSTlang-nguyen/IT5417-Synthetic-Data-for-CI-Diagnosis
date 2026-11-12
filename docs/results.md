# Kết quả vòng dataset v1 — 12/11/2026

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
