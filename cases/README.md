# Danh mục case

Mỗi thư mục con chứa `case.json`: cấu hình/provenance nhỏ được version hóa. Repo nguồn đầy đủ, model và raw runs không nằm trong thư mục này.

| Case | Nguồn | Trạng thái đợt 01 |
|---|---|---|
| [properr-6](properr-6/case.json) | AIDev | W1 đã thực hiện; xem [review](../docs/pilot-review.md) |
| [esaul314__chunkify-340](esaul314__chunkify-340/case.json) | aidev | Đã thử tái hiện |
| [marshmallow-code__marshmallow-1343](marshmallow-code__marshmallow-1343/case.json) | swebench | Đã thử tái hiện |
| [marshmallow-code__marshmallow-1359](marshmallow-code__marshmallow-1359/case.json) | swebench | Đã thử tái hiện |
| [mfat__sshpilot-716](mfat__sshpilot-716/case.json) | aidev | Đã thử tái hiện |
| [pydicom__pydicom-1139](pydicom__pydicom-1139/case.json) | swebench | Đã thử tái hiện |
| [pydicom__pydicom-1256](pydicom__pydicom-1256/case.json) | swebench | Đã thử tái hiện |
| [pydicom__pydicom-1694](pydicom__pydicom-1694/case.json) | swebench | Đã thử tái hiện |
| [PyLabRobot__pylabrobot-527](PyLabRobot__pylabrobot-527/case.json) | aidev | Đã thử tái hiện |
| [sqlfluff__sqlfluff-1517](sqlfluff__sqlfluff-1517/case.json) | swebench | Có cấu hình, chưa chọn chạy |
| [sqlfluff__sqlfluff-1625](sqlfluff__sqlfluff-1625/case.json) | swebench | Có cấu hình, chưa chọn chạy |
| [sqlfluff__sqlfluff-1733](sqlfluff__sqlfluff-1733/case.json) | swebench | Có cấu hình, chưa chọn chạy |
| [sqlfluff__sqlfluff-1763](sqlfluff__sqlfluff-1763/case.json) | swebench | Có cấu hình, chưa chọn chạy |
| [sqlfluff__sqlfluff-2419](sqlfluff__sqlfluff-2419/case.json) | swebench | Có cấu hình, chưa chọn chạy |
| [tyighter__tcm-364](tyighter__tcm-364/case.json) | aidev | Đã thử tái hiện |

14 cấu hình mở rộng không có nghĩa 14 case đã chạy: đợt 01 chọn 9 case, năm cấu hình SWE còn lại chưa được chạy. [Kết quả thực đo](../docs/expansion-01-summary.md). Registry/chọn nhóm nằm ở [data-manifests](../data-manifests/expansion-01.json).

Loader ưu tiên `cases/<id>/case.json`; đường dẫn cũ `data-manifests/cases/<id>.json` chỉ còn được đọc làm fallback để hỗ trợ artifact/checkout cũ. Không tạo cấu hình mới ở đường dẫn cũ.
