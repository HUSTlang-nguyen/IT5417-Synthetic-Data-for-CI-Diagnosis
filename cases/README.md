# Danh mục case và profile

Mỗi thư mục con chứa `case.json`; source checkout, weights và raw runs ở cache/runtime bị ignore. `-r1` là profile hiệu chỉnh của cùng case nguồn, không phải PR mới.

| Profile | Case nguồn | Cohort | Trạng thái thật |
|---|---|---|---|
| [esaul314__chunkify-340](esaul314__chunkify-340/case.json) | esaul314__chunkify-340 | expansion-01 | Chưa có fixed pass; Nonregular source archive entry: config/tags/generic.yaml |
| [fastapi__fastapi-15232](fastapi__fastapi-15232/case.json) | fastapi__fastapi-15232 | expansion-02 | Chưa có fixed pass; docker-build failed: see docker-build.stderr.txt |
| [fastapi__fastapi-15232-r1](fastapi__fastapi-15232-r1/case.json) | fastapi__fastapi-15232 | expansion-02-corrections | Fixed pass; 1/3 đạt runner |
| [marshmallow-code__marshmallow-1343](marshmallow-code__marshmallow-1343/case.json) | marshmallow-code__marshmallow-1343 | expansion-01 | Fixed pass; 0/3 đạt runner |
| [marshmallow-code__marshmallow-1359](marshmallow-code__marshmallow-1359/case.json) | marshmallow-code__marshmallow-1359 | expansion-01 | Fixed pass; 0/3 đạt runner |
| [mfat__sshpilot-716](mfat__sshpilot-716/case.json) | mfat__sshpilot-716 | expansion-01 | Fixed pass; 0/3 đạt runner |
| [properr-6](properr-6/case.json) | properr-6 | W1 | W1 đã chạy; xem review W1 |
| [pvlib__pvlib-python-1072](pvlib__pvlib-python-1072/case.json) | pvlib__pvlib-python-1072 | expansion-02 | Fixed pass; 2/3 đạt runner |
| [pvlib__pvlib-python-1154](pvlib__pvlib-python-1154/case.json) | pvlib__pvlib-python-1154 | expansion-02 | Có cấu hình, chưa được chọn chạy |
| [pvlib__pvlib-python-1606](pvlib__pvlib-python-1606/case.json) | pvlib__pvlib-python-1606 | expansion-02 | Có cấu hình, chưa được chọn chạy |
| [pvlib__pvlib-python-1707](pvlib__pvlib-python-1707/case.json) | pvlib__pvlib-python-1707 | expansion-02 | Có cấu hình, chưa được chọn chạy |
| [pvlib__pvlib-python-1854](pvlib__pvlib-python-1854/case.json) | pvlib__pvlib-python-1854 | expansion-02 | Có cấu hình, chưa được chọn chạy |
| [pydicom__pydicom-1139](pydicom__pydicom-1139/case.json) | pydicom__pydicom-1139 | expansion-01 | Fixed pass; 3/3 đạt runner |
| [pydicom__pydicom-1256](pydicom__pydicom-1256/case.json) | pydicom__pydicom-1256 | expansion-01 | Fixed pass; 3/3 đạt runner |
| [pydicom__pydicom-1694](pydicom__pydicom-1694/case.json) | pydicom__pydicom-1694 | expansion-01 | Fixed pass; 0/3 đạt runner |
| [PyLabRobot__pylabrobot-527](PyLabRobot__pylabrobot-527/case.json) | PyLabRobot__pylabrobot-527 | expansion-01 | Chưa có fixed pass |
| [PyLabRobot__pylabrobot-528](PyLabRobot__pylabrobot-528/case.json) | PyLabRobot__pylabrobot-528 | expansion-02 | Chưa có fixed pass; Frozen harness must consist of tests |
| [PyLabRobot__pylabrobot-528-r1](PyLabRobot__pylabrobot-528-r1/case.json) | PyLabRobot__pylabrobot-528 | expansion-02-corrections | Chưa có fixed pass; Undeclared test/harness difference between base and fixed: pylabrobot/tests/serializer_tests.py |
| [pylint-dev__astroid-1196](pylint-dev__astroid-1196/case.json) | pylint-dev__astroid-1196 | expansion-02 | Fixed pass; 2/3 đạt runner |
| [pylint-dev__astroid-1268](pylint-dev__astroid-1268/case.json) | pylint-dev__astroid-1268 | expansion-02 | Fixed pass; 3/3 đạt runner |
| [pylint-dev__astroid-1333](pylint-dev__astroid-1333/case.json) | pylint-dev__astroid-1333 | expansion-02 | Chưa có fixed pass |
| [pylint-dev__astroid-1866](pylint-dev__astroid-1866/case.json) | pylint-dev__astroid-1866 | expansion-02 | Fixed pass; 3/3 đạt runner |
| [pylint-dev__astroid-1978](pylint-dev__astroid-1978/case.json) | pylint-dev__astroid-1978 | expansion-02 | Có cấu hình, chưa được chọn chạy |
| [shillis13__python-33](shillis13__python-33/case.json) | shillis13__python-33 | expansion-02 | Chưa có fixed pass; Nonregular source archive entry: scripts/chatConverter.py |
| [sqlfluff__sqlfluff-1517](sqlfluff__sqlfluff-1517/case.json) | sqlfluff__sqlfluff-1517 | expansion-01 | Có cấu hình, chưa được chọn chạy |
| [sqlfluff__sqlfluff-1625](sqlfluff__sqlfluff-1625/case.json) | sqlfluff__sqlfluff-1625 | expansion-01 | Có cấu hình, chưa được chọn chạy |
| [sqlfluff__sqlfluff-1733](sqlfluff__sqlfluff-1733/case.json) | sqlfluff__sqlfluff-1733 | expansion-01 | Có cấu hình, chưa được chọn chạy |
| [sqlfluff__sqlfluff-1763](sqlfluff__sqlfluff-1763/case.json) | sqlfluff__sqlfluff-1763 | expansion-01 | Có cấu hình, chưa được chọn chạy |
| [sqlfluff__sqlfluff-2419](sqlfluff__sqlfluff-2419/case.json) | sqlfluff__sqlfluff-2419 | expansion-01 | Có cấu hình, chưa được chọn chạy |
| [tyighter__tcm-364](tyighter__tcm-364/case.json) | tyighter__tcm-364 | expansion-01 | Fixed pass; 0/3 đạt runner |

Có 30 profile folders cho 28 case nguồn đã có cấu hình (gồm properr W1). Số folder không phải số case đã tái hiện thành công. Hai đợt mở rộng đã thử 17 case nguồn trên 10 repo; hai profile hiệu chỉnh được đếm riêng.

[Đợt 01](../docs/expansion-01-summary.md) · [Đợt 02](../docs/expansion-02-summary.md) · [Grouping/duplicate](../data-manifests/development-groups-v1.json). Registry còn lưu case bị loại mà không có runnable config.

Loader ưu tiên `cases/<id>/case.json`; `data-manifests/cases/<id>.json` chỉ là fallback đọc artifact cũ. Không tạo case mới ở đường dẫn cũ.
