# Evidence đợt development 01

- [summary.json](summary.json): số liệu phái sinh từ artifact thực, links/run IDs, trạng thái pending và hash/byte-integrity checks.
- [software-tests.txt](software-tests.txt): output thật của host unit suite cuối; fixture phần mềm được tách khỏi dữ liệu nghiên cứu.
- [Tổng kết](../../development-summary.md#expansion-01), [review](../../data-review.md#expansion-01), [registry](../../../data-manifests/expansion-01.json).

Raw run root trên máy hiện tại là `runs/batch-20261029T173420443187Z/` cùng các stage được manifest liên kết. Raw snapshots/patches/setup/license metadata ở `.cache/expansion/records/`; nguồn đầy đủ ở `.cache/case-contexts/`. Đây là artifact local bị ignore, không có trong Git clone.

Archive local: `.cache/archives/expansion-01-20261030.zip`. Nó chứa raw runs mới, record/patch metadata đã dùng, actual validation summaries và code hashes của lúc chạy; không chứa model weights, image tar hoặc toàn bộ source checkout. Hash archive nằm trong `.cache/archives/expansion-01-20261030.zip.sha256`. Khi cần restore, kiểm tra hash, giải nén vào artifact root mới rồi đối chiếu manifests; không ghi đè evidence đã có và không tự chạy lại pilot để bù artifact thiếu.

Các con số execution_verified không phải gold labels, training-approved samples hoặc accuracy của model chẩn đoán. Giữ raw review.json pending và các trường xác nhận riêng cho người dùng.
