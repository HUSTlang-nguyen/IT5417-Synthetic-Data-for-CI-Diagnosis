# Dung lượng, trạng thái và phiên bản dữ liệu

Cập nhật12/11/2026, Asia/Bangkok. [Số đo chỉ đọc](evidence/dataset-v1-progress/storage-inventory-20261112.json); chưa xóa cache, image, source hoặc evidence.

## Nơi đang chiếm dung lượng

Đơn vịGiB =1024³byte; số đo thư mục là tổng byte logic, không đi theo junction/symlink. Docker nằm trong file đĩa ảo nên không cộng các image/build cache thêm lần nữa.

| Vị trí | GiB | Nội dung |
|---|---:|---|
| `C:/Users/neikh/AppData/Local/Docker/wsl/disk/docker_data.vhdx` | 81.160 | Đĩa ảo Docker, số byte cấp phát cũng81.160GiB |
| Worktree hiện hành: `.cache/case-contexts/` | 19.842 | Source/tests base và fixed, build contexts theo case/revision; khoảng1,39triệu file |
| Worktree: `.cache/ml-v1/` | 7.771 | Môi trường Python/ML, gồm thư viện CUDA |
| Worktree: `.cache/models/` | 5.759 | Checkpoint3B ghim revision |
| Checkout gốc: `.cache/models/` | 5.280 | Model Ollama đang dùng cho generator |
| Checkout gốc: `.cache/tools/` | 3.587 | Công cụ runtime đã tải |
| Worktree: `runs/` | 0.692 | Raw logs, manifest, model outputs và evidence |
| Worktree: `.cache/dataset-v1-source/` | 0.534 | Metadata/test patch/repair patch nguồn đã ghim |
| Worktree: `.cache/dataset-v1/` | 0.012 | Các bản xuất input/reference/assessment cho chẩn đoán |

Worktree là`C:/Users/neikh/.codex/worktrees/a4f5/IT5417-Synthetic-Data-for-CI-Diagnosis`; checkout gốc là`C:/Users/neikh/Documents/GitHub/IT5417-Synthetic-Data-for-CI-Diagnosis`.

Tổng`.cache`worktree34.960GiB; `.cache`checkout gốc8.867GiB. ỔC có475.957GiB tổng, còn khoảng46.453GiB tại thời điểm đo. Đây không là kiểm kê toàn bộ các ứng dụng trên ổC.

Docker báo469images/37.34GB và38.91GBbuildcache; reclaimable tương ứng33.85GB và21.11GB. Đơn vịGB của Docker khácGiB trong bảng. “Reclaimable” chỉ nghĩa Docker xem là không được dùng; không chứng minh dữ liệu không còn cần cho nghiên cứu. Các lớp dùng chung khiến không thể cộng số đó thành lượng chắc chắn thu hồi. Việc xóa nội dung Docker cũng không bảo đảm fileVHDX giảm ngay.

## Khi train, validation và test cần gì

Chẩn đoán3B dùng input gồm log/code đã đóng gói. Train có target silver; validation/test chỉ đưa input cho model, rồi bộ chấm đối chiếu nhãn/vị trí riêng. Đây không là bài toán sinh patch sửa lỗi, nên không cần dựng Docker lại cho từng dự đoán hoặc từng model.

Docker/source/test environments cần khi tái hiện, kiểm chứng candidate hoặc kiểm tra lại nguồn evidence. Validator hiện hành còn đọc inventory trong`case-contexts`; xóa chúng lúc audit đang chạy sẽ làm kiểm tra thất bại. Nhãn riêng lẻ không thay được input hoặc bằng chứng nguồn.

| Thành phần | Quy tắc giữ/xóa |
|---|---|
| Raw logs/manifests/candidate/test patches/assessments và dataset versions | Giữ hoặc sao lưu có hash và kiểm tra phục hồi; chưa xóa |
| Build cache và image của các profile lỗi/không được chọn | Có thể dọn sau khi inventory/evidence đã lưu và không còn tiến trình dùng; chưa thực hiện |
| Image được dùng trong evidence | Không bắt buộc cho SFT text-only; muốn replay đúng image phải giữ image hoặc archive. Dựng lại từ recipe không bảo đảm cùng image ID |
| Source contexts của case được chọn | Giữ tới khi audit xong và có bản lưu có thể phục hồi; chuyển đi phải giữ provenance/path mapping |
| Model/thư viện tải lại được | Có thể tái tạo theo revision/dependency đã ghim; xóa sẽ phát sinh thời gian tải/cài lại |

## Đọc tiến độ mà không audit lại

1. [dataset-v1-status.json](../data-manifests/dataset-v1-status.json): snapshot nhỏ hiện hành, có timestamp, số lượng, gate và việc còn thiếu. Cập nhật tại milestone; không gọi model/Docker/hash toàn bộ để trả lời trạng thái.
2. [dataset card](dataset-card.md): cách chia tập, nhãn, bảngrepo và hạn chế.
3. [real selection](../data-manifests/dataset-v1-real-selection.json):250ID được chọn, role, hash và lý do các bản ghi ngoài lựa chọn.
4. `runs/<experiment>/real-reproduction-summary.json` và các manifest: trạng thái tự ghi của worker, chỉ dùng khi cần kiểm tra thay đổi sau snapshot hoặc phục hồi gián đoạn.

Full audit là công việc nghiệm thu riêng. Một checkpoint không được cập nhật không chứng minh worker còn chạy hoặc đã thành công; khi gián đoạn cần kiểm tra trạng thái thực tế và ghi mốc mới.

## DVC và Google Drive — đề xuất, chưa triển khai

Git giữ code, recipe, manifest, status và metadataDVC; DVC quản lý các dataset versions cùng evidence đã đóng gói; Google Drive có thể làm remote chứa byte dữ liệu. DVC chính thức hỗ trợ`gdrive://`, kiểm tra hash khi tải và có hướng dẫn xác thực/quota riêng: [Google Drive remote](https://dvc.org/doc/user-guide/data-management/remote-storage/google-drive).

Ưu tiên version hóa input/reference/assessment và manifest đã khóa, sau đó archive evidence bất biến liên quan; không đẩy toàn bộ build cache, virtualenv hoặc mọi Docker image lênDrive. Chỉ dọn local sau khi upload và phục hồi thử thành công. DVC không thay file trạng thái và không tự giảm dung lượng cache; cần chọn cache/link strategy phù hợpWindows và chỗ lưu.

Chưa càiDVC, tạo remote, yêu cầu credential hoặc uploadDrive trong lượt này. Không chuyển protocol/data version chỉ để khớp số lượng còn thiếu.
