# Dataset v1 — bằng chứng tiến độ

2026-11-12T18:43:27+07:00: 471 profiles/449 sources đã thử; 285 strict-supported/333 seed pass. Đã xuất 265 real silver {'train': 181, 'test': 41, 'validation': 43}, 105 synthetic silver trước final selection; 20 real quarantine/92 synthetic loại sau review. 372 request7B đã reserve/197 đạt runner. Software106:105pass/1skip. Dataset chưa khóa; M0/M1/M2/M5 chưa chạy nghiên cứu.

Đã chọn250real(175train/37validation/38test) theo stable-ID; chưa là dataset lock. Có105synthetic export,102trong final class/quality scope: thiếu73/175. Source queue đã xong13:39. Generator mới bị gián đoạn, không còn worker;372lời gọi đã hoàn tất, một verification unknown24455. Stage sinh đã hết ngân sách gồm thời gian in-flight bị gián đoạn; không reset/replay/gọi mới. Đang audit352records lựa chọn; M0/M1/M2/M5 vẫn gated.

[Checkpoint mới](checkpoint-20261112T1842.json), [checkpoint13:16](checkpoint-20261112T1317.json), [log106kiểm thử](software-tests-106.txt), [danh sách250real](../../../data-manifests/dataset-v1-real-selection.json). Audit352 đang chạy; dữ liệu chưa khóa, gold pending, chưa SFT. Raw/model/cache giữ local và ngoài Git.
