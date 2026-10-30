# Evidence development 02

- [summary.json](summary.json): số liệu thực, hai batch, correction budget carry, candidate hashes, source-pair/image checks và combined metrics.
- [software-tests.txt](software-tests.txt): output software unit suite thật, giữ byte CRLF bằng `.gitattributes`; không phải log nghiên cứu giả lập.
- [Tổng kết](../../development-summary.md#expansion-02), [review kỹ thuật](../../data-review.md#expansion-02), [grouping snapshot](../../../data-manifests/development-groups-v1.json), [case index](../../../cases/README.md).

Primary run: `batch-20261029T235240554230Z`; correction run: `batch-20261029T235944990687Z`; image audit: `integrity-20261030T000410182947Z`. Source/test/model artifacts ở các run được manifest liên kết, raw metadata/patches trong `.cache/expansion-02/records/`. Chúng bị ignore và không tự có trong clone.

Archive local `.cache/archives/expansion-02-20261030.zip` chứa raw runs mới, cached records/patches, validation/code-hash snapshots và registry/case metadata liên quan; không chứa weights, image tar hoặc toàn bộ source checkout. SHA và size ghi trong summary, bản sidecar ở `.cache/archives/expansion-02-20261030.zip.sha256`. Restore vào artifact root mới, kiểm tra hash và không ghi đè run cũ. Archive là bằng chứng đã chạy, không phải lệnh yêu cầu chạy lại.

Profile `-r1` có cùng source_case_id với nguồn cũ, không tăng số case nguồn. Execution acceptance, prompt compliance, agent recommendations và human/gold/training approval là các trạng thái riêng; review mới vẫn pending.
