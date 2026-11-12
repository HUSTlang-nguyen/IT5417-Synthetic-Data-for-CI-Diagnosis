# Dataset v1 — bằng chứng tiến độ

2026-11-12T19:30:07+07:00: chọn250real silver(175train/37validation/38test) từ265real đã rà;105synthetic export,101sau loại trừ cuối, thiếu74/175. Tổng372lời gọi7B/197lượt đạt runner. Software106:105pass/1skip. M0/M1/M2/M5 nghiên cứu chưa chạy; data gate chưa đạt.

Audit352 hoàn tất19:22:53:hash/source/test/lineage đạt, không cross-split hoặc trùng byte. Loại thêm một semantic duplicate constant-printer, giữ351bản ghi với group review/selectionhash và retained-export hashes khớp. Đây là partial dataset, chưa là learning lock. Stage sinh đã hết budget; không replay unknown24455/resetcap/gọi mới.

[Trạng thái hiện hành](../../../data-manifests/dataset-v1-status.json), [audit lựa chọn](selection-audit-20261112.json), [log106kiểm thử](software-tests-106.txt), [kết quả](../../results.md).

Checkpoint lịch sử: [13:16](checkpoint-20261112T1317.json), [18:43](checkpoint-20261112T1842.json). Raw code/data/models giữ local và ngoài Git; không có nhãn gold hoặc kết quả SFT.
