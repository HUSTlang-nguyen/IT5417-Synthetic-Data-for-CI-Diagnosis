# Tổng kết đợt development 01

Ngày 30/10/2026. [Batch HTML](../runs/batch-20261029T173420443187Z/report.html), [manifest](../runs/batch-20261029T173420443187Z/manifest.json), [registry](../data-manifests/expansion-01.json), [review để người dùng đọc](expansion-01-review.md), [số liệu tổng hợp](evidence/expansion-01/summary.json).

## Kết quả thật

| Chỉ số | AIDev | SWE-bench Lite dev | Tổng |
|---|---:|---:|---:|
| Case sàng lọc | 10 | 10 | 20 |
| Case đã thử tái hiện | 4 | 5 | 9 |
| Giả thuyết local đạt đối chiếu nghiêm ngặt | 2 | 4 | 6 |
| Case có fixed seed pass | 2 | 5 | 7 |
| Lượt 7B đã gọi | 6 | 15 | 21 |
| Lượt đạt thực thi | 0 | 6 | 6 |

Chín case đã thử thuộc **6 repo**. Giới hạn ban đầu là 10 case/30 lượt; không bù case thiếu điều kiện ở nguồn này bằng nguồn khác. Sáu AIDev bị loại ở sàng lọc do giấy phép tại revision ghim chưa rõ hoặc xung đột proprietary; còn bốn case đủ điều kiện thử. Năm case SWE còn lại không được chọn do quota năm/nguồn, không phải kết luận chúng không tái hiện được.

Mẫu số được giữ rõ: **27 lượt yêu cầu** cho chín case đã chọn; 21 lượt thực hiện và sáu lượt chưa thực hiện vì hai case không có seed pass. Kết quả trên các lượt đã gọi: **6/21 đạt thực thi**, **10 invalid_output**, **5 không làm test fail**. Trên toàn số lượt yêu cầu là **6/27**; còn ba slot tới capacity 30 chưa có case nguồn được chọn.

Sáu lượt đạt chỉ gồm **3 candidate khác byte**, đều thuộc hai case pydicom. Có tổng cộng 11 candidate hợp lệ, gồm sáu hash khác nhau. Đây không phải sáu mẫu độc lập, sáu nhãn gold hoặc kết quả chẩn đoán 3B.

## Thời gian và tài nguyên

Batch chạy từ **00:34:20 đến 00:40:31 +07**, ngày 30/10/2026. Active time batch ghi nhận **456,233 giây**, gồm **85,124 giây discovery đã đo** và khoảng 371,109 giây xử lý batch; thời gian viết code nằm ngoài. Tổng thời gian các lời gọi sinh là **76,484 giây**, bao gồm load/runtime, không phải tốc độ steady-state.

Kiểm tra inventory image sau batch mất thêm **3,937 giây**. Tổng hai khoản active đã đo là **460,170 giây**, thấp hơn ngân sách 6 giờ. Đây là các khoản được ghi nhận, không phải đo toàn bộ thời gian tác giả thao tác; một số metadata follow-up nhỏ không có timer riêng. Không dùng thời gian làm việc trong chat để suy throughput.

Doctor xác nhận Docker Linux, RTX 4070 SUPER và Ollama local hoạt động. Dung lượng trống trước batch được đo 163,49 GiB sau khi người dùng giải phóng storage. Không đo peak VRAM hoặc suy bộ nhớ model từ snapshot; không tải/chạy 3B hay model phụ. Không tự prune Docker.

## Các điểm không đạt và giới hạn

- PyLabRobot: upstream fixture cần ghi `test_logs`, bị chặn bởi read-only filesystem; không có seed pass.
- chunkify: source archive chứa symlink, bị từ chối trước build; không có test/model run cho case đó.
- marshmallow #1359: có base failure và fixed pass, nhưng tám identifier PASS_TO_PASS nguồn bị cắt tại khoảng trắng. Matcher exact giữ `historical_supported=false`; không sửa manifest để nâng số thành công.
- Generator hay trả before không khớp, edit không đổi hoặc lời giải thích hướng sửa lỗi; mười output bị giữ invalid. Năm candidate thực thi được nhưng không làm test fail. Không retry hoặc sửa tay output để tăng yield.
- Nhãn generator của cả sáu lượt đạt là syntax, trong khi evidence là lỗi logic/validation gây ValueError/KeyError. Nhãn nguồn, đề xuất agent và phê duyệt người dùng được tách riêng.
- Các case/SWE split được dùng cho development có chủ đích, không đại diện hai dataset. Test mục tiêu và recipe local không đồng nghĩa toàn bộ harness chuẩn SWE-bench. Các case đã xem không làm test độc lập cuối cùng.
- Diff raw v2 trên Windows có newline translation thừa; before/after và candidate đầy đủ vẫn khớp hash. Đã sửa writer cho run sau, không thay artifact cũ.

## Kiểm tra và bàn giao

Đã đối chiếu **78 JUnit / 2.580 testcase records có lặp**, 11 candidate hashes/phép edit, host inventories của tám environment và tracked source/test bytes trong cả hai role của tám image. Sau test-freeze, mỗi cặp base/fixed chỉ khác đúng file sản phẩm đã đăng ký; không có khác biệt conftest/fixture ẩn. **202 file W1 được bảo vệ và 968 file raw mới được ghi inventory giữ nguyên hash.**

Kiểm thử phần mềm cuối: **49 discovered, 48 pass, một legacy Docker test opt-in skip**. Các Docker build/test thật của batch là bằng chứng tích hợp riêng; không gọi skip đó là đã chạy. [Log phần mềm](evidence/expansion-01/software-tests.txt). Kiểm tra bao gồm case/gate tách biệt, edit duy nhất, source patch vào đúng export, timeout/error giữ mẫu số, không đưa reference fields vào prompt, tamper refusal, resume không gọi lại generation chưa rõ kết quả, OS lock và HTML escaping.

Raw artifacts ở `runs/` và `.cache/expansion/`, không đi theo Git clone. Snapshot/patch/setup/license evidence được giữ local; registry và summary nhỏ có thể version hóa. Archive khôi phục của đợt được ghi ở [evidence README](evidence/expansion-01/README.md).

W2-01/02 đủ dùng cho development, W2-03 có registry và pilot nhiều repo thực tế. Bước tiếp theo là **W2-04: hoàn thiện grouping/near-duplicate và vai trò split trước vòng train**. Bản review mới sẵn sàng để người dùng đọc; gold labels/training eligibility vẫn pending. Chưa bắt đầu SFT, benchmark cuối hoặc 3B inference.
