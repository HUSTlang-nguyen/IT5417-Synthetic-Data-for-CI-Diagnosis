# Dataset portable

## v1.1 — pilot giữa kỳ

[Gói v1.1](v1.1/README.md) có351mẫu silver:175real train,37real validation,38real test và101synthetic train. Input/reference/assessment giữ nguyên bytes từ lock nguồn; metadata portable bỏ riêng Modelfile chứa đường dẫn máy cá nhân và ghi hash/biến đổi. Giấy phép nguồn, notices, attribution và các thay đổi synthetic được lưu cùng gói, không áp giấy phép chung thay giấy phép từng nguồn.

```powershell
python -m ci_demo.portable_dataset --check research-data/v1.1
```

Lệnh chỉ đọc/kiểm tra file, không cần raw runs, model hoặc Docker. Git bảo toàn bytes của research-data qua.gitattributes. Không đưa reference/assessment/provenance patch vào input model. Nhãn không phải expert gold; gói không thay dataset lock/checkpoint lineage v1 và không đủ để resume checkpoint chỉ bằng clone.

## v2 — đang xây

[Kế hoạch](../docs/dataset-v2-plan.md), [trạng thái](../data-manifests/dataset-v2-status.json). Chưa có dataset v2 khóa hoàn chỉnh; không cộng các ứng viên hoặc kết quả tái hiện vào số mẫu train đã duyệt.

Full source checkouts, raw datasets/runs, Docker/cache/model/checkpoints ngoài Git; liên kết raw evidence cần archive riêng để truy vết đầy đủ.
