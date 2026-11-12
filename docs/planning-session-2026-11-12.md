# Context phiên thảo luận dữ liệu và SFT ngày 12 tháng 11 năm 2026

Ngày ghi nhận theo context người dùng: 12/11/2026, Asia/Bangkok. Đây là bản lưu thảo luận và kế hoạch dự kiến, **chưa phải protocol được duyệt hoặc kết quả thực nghiệm**. Đọc cùng [roadmap](implementation-plan.md), [architecture](architecture.md) và [review hiện có](data-review.md).

## Điểm tiếp tục và giới hạn thực thi

- Người dùng muốn đạt một mốc tương đương nửa đồ án trong 24 giờ và cân nhắc giao toàn bộ phần kỹ thuật cho hệ thống. Không có tiêu chí đã thống nhất để quy đổi thành 50%; đầu ra cần đo bằng artifact và kết quả thật.
- Goal tên chung `start goal` từng được bật rồi người dùng xóa. Sau đó người dùng yêu cầu rõ: **lên plan để duyệt trước khi thực thi**. Chưa có lệnh phê duyệt thực thi plan 24 giờ sau các lần làm rõ.
- Yêu cầu hiện tại chỉ là lưu context. Không suy việc hỏi, chọn phương án hoặc lưu context thành cho phép tải model, tạo dataset mới, chạy thí nghiệm hay SFT. Đồng hồ ngân sách 24 giờ chưa bắt đầu.
- Task kỹ thuật đang mở vẫn W2-04; W3-03 doing sau khi duyệt kiến nghị giữ/loại. Bước hội thoại kế tiếp là sửa plan theo các điểm dưới và xin người dùng duyệt bản hoàn chỉnh.
- Chưa tạo `docs/experiment-protocol.md`, dataset SFT đã export, baseline diagnosis hoặc trainer. Chưa có lượt inference 3B/SFT mới.

## Các lựa chọn người dùng đã chọn khi lập kế hoạch

**Cập nhật mới nhất — ưu tiên hơn các con số pilot bên dưới:** người dùng chuyển mục tiêu sang **250 tình huống real đủ điều kiện** ("vậy ta nên chuyển sang 250 real đi, ok không"). Mục tiêu 60 real và quy mô 30–60 cũ chỉ giữ làm lịch sử thảo luận, không còn là đích dataset hiện tại. 250 là số tình huống lỗi độc lập sau kiểm tra, không phải 250 repo, record metadata, test failures hoặc lời gọi sinh. Đây chưa phải cam kết thu đủ trong 24 giờ hoặc số mẫu đã có; việc đánh giá quy mô đủ cho kết luận nghiên cứu vẫn phụ thuộc support/nhóm và kết quả. Cần viết lại số mẫu/split/synthetic, trần request và lịch SFT trước khi duyệt thực thi; không mặc định giới hạn 120 request hay 18–36 synthetic cũ đủ cho đích mới. Các lựa chọn silver có đánh dấu, giữ riêng repo, hai nhiệm vụ chính và giữ cổng chất lượng vẫn áp dụng. Chưa chốt lại số mỗi split hoặc tỷ lệ synthetic cho mục tiêu 250.

| Nội dung | Lựa chọn đã xác nhận | Phạm vi |
|---|---|---|
| Đầu ra 24 giờ | Có thử nghiệm SFT | Ưu tiên real-only và real + synthetic nhỏ, có thể giảm thời gian thu thêm dữ liệu; đây là mong muốn, không bảo đảm kết quả |
| Nhãn thăm dò | Cho phép có đánh dấu | Có thể dùng silver cho train/đánh giá thăm dò trong kế hoạch tương lai; không gọi gold hoặc đánh giá cuối. Chưa duyệt từng nhãn hay toàn bộ plan |
| Đánh giá | Giữ riêng repository | Validation/test từ repo chưa dùng phát triển của dự án; không khẳng định checkpoint pretrained chưa từng thấy repo |

7B vẫn là generator duy nhất, 3B là diagnoser. Model phụ đã bỏ vẫn không được tải/gọi/chạy/rà tiếp. Không có đề xuất thay vai trò này.

## Lựa chọn bổ sung sau khi tiếp tục chốt kế hoạch ngày 12 tháng 11

- Người dùng chọn mục tiêu **60 real + 18–36 synthetic** để cân bằng thu thập và SFT. Đây là mục tiêu số mẫu đạt tiêu chí, chưa phải số hiện có hoặc bảo đảm thu được; phân bổ 36 train/12 validation/12 test mới là đề xuất, chưa xác nhận riêng.
- Người dùng chọn **giữ cổng dữ liệu**: thiếu dữ liệu thì báo phần thiếu, không ép chạy hai SFT trên tập quá ít. Ngưỡng tối thiểu số lượng/chất lượng cần được sửa và duyệt trong plan cuối; không tự dùng lại mốc 18/6/6 như cam kết đủ nghiên cứu.
- Người dùng muốn output loại nguyên nhân + file/hàm + giải thích, đồng thời chất vấn cách coi vị trí chỉ là chỉ số phụ vì vị trí lỗi quan trọng. Hướng sửa: **phân loại và khoanh vùng file/hàm là hai mục tiêu chính**, không thu hẹp phạm vi thành classifier-only. Dòng chính xác vẫn tùy bằng chứng.
- Giải thích của agent: đề xuất vị trí phụ trước đây do khó tạo reference location chắc chắn hơn class, không phải vì khoanh vùng kém quan trọng. Không giải quyết khó gán nhãn bằng cách âm thầm hạ vị trí thành mục tiêu phụ.
- Metric đề xuất để đưa vào plan sửa: Macro-F1 phân loại và Top-1/Top-5 file/hàm báo riêng, không lấy phân loại tốt để thay thế khoanh vùng. Đóng băng eligibility theo từng nhiệm vụ trước dự đoán; báo số mẫu có reference đủ evidence, thiếu nhãn, retrieval coverage và lỗi output. Với mẫu đã đủ nhãn, retrieval bỏ sót hoặc model không trả vị trí vẫn tính trượt end-to-end; không loại khỏi mẫu số sau khi thấy kết quả. Chưa chốt metric tổng hợp/chọn checkpoint giữa hai mục tiêu.
- Input cho khoanh vùng không được chọn bằng reference location, generator site/allowed_file hoặc gold patch. Nếu chỉ cấp một file đã biết trước là file lỗi thì file accuracy là bài toán bị điều kiện hóa/trivial; phải công bố và không dùng làm bằng chứng định vị toàn repo. Cần chốt candidate retrieval và phạm vi file/hàm trong plan cuối.
- Các lựa chọn này bổ sung, không tự thay thế việc phê duyệt toàn bộ kế hoạch. Chưa thực thi runtime/model/SFT.

## Hiện trạng và cách đọc các con số

- W1 properr báo riêng: ba lượt 7B, hai đạt thực thi. Hai expansion: 40 case sàng lọc, 17 case nguồn thử trên 10 repo, 36 lượt gọi, 17 lượt đạt runner/14 candidate khác byte. Đây không phải số mẫu đã được duyệt train.
- Kiểm tra manifest local ngày 12/11 tìm được 19 profile tái hiện trong hai expansion: 10 `hypothesis_supported_locally`, 4 `hypothesis_not_confirmed`, 5 `environment_error`. Profile hiệu chỉnh không phải case nguồn mới; không chuyển các số này thành số nhãn real đã hoàn thiện.
- 58 kiểm thử phần mềm đã lưu (57 pass/1 skip) kiểm tra code pipeline, khác với test trong các repo dùng kiểm chứng lỗi. Chưa chạy lại suite trong phiên thảo luận này.
- Kiểm tra môi trường trước khi goal bị xóa: RTX 4070 SUPER 12.282 MiB tổng/9.576 MiB free; ổ C khoảng 81 GiB free; Docker Desktop Linux pipe chưa hiện diện. Đây là snapshot lúc kiểm tra, không phải peak VRAM hay trạng thái daemon được bảo đảm hiện tại.
- Python được kiểm tra chưa có torch/transformers/peft/trl/sklearn/numpy/bitsandbytes/datasets. Có `.cache/data-tools` Python 3.11.9 riêng. Truy cập socket Ollama và truy vấn WSL bị sandbox từ chối; chưa xác minh Ollama/WSL chết. Không gọi lại thí nghiệm cũ để lấy context.

## Dự thảo 24 giờ đã trình bày và chưa được duyệt

Mục tiêu: protocol nhỏ, dataset v0.1, M0 TF-IDF + Logistic Regression, M1 3B prompt-only, M2 SFT real-only và M5 SFT real + synthetic. M0 chỉ đánh giá phân loại; M1/M2/M5 thêm file/hàm và tính hợp lệ output. Chỉ local, không cloud/API trả phí hoặc tự merge/push main.

Lịch dự kiến: 0–2h môi trường/protocol; 2–10h dữ liệu và sinh; 10–13h review/đóng gói/audit; 13–16h M0/M1 và training smoke test; 16–21h M2/M5; 21–24h chấm/diễn giải/báo cáo. Đây là phân bổ đề xuất; không phải thời gian đã đo. Không bảo đảm chạy nền liên tục nếu phiên ngắt hoặc máy ngủ.

### Dữ liệu và split dự kiến

- Mục tiêu thu 30–60 tình huống real; mốc tối thiểu đề xuất là 18 real train, 6 real validation, 6 real test và 9 synthetic train. Như vậy 39 record khác nhau; real-only học 18, mixed học cùng 18 + 9, validation/test dùng chung. Không cộng real được dùng lại hai lần.
- Người dùng đã chất vấn quy mô này quá ít; agent thừa nhận đây chỉ là ngưỡng **pilot kỹ thuật/thăm dò**, không đủ căn cứ khẳng định hiệu quả nghiên cứu. Sáu test samples khiến một dự đoán thay đổi accuracy khoảng 16,7 điểm phần trăm; cùng repo còn có tương quan. Phải sửa cách đặt mục tiêu trước khi duyệt plan.
- Con số 500 real và ví dụ 350/75/75, hoặc mixed 350+175 / 350+350, trước đây chỉ là minh họa quy hoạch, chưa chốt hay chứng minh thu được trong 24 giờ. 70/15/15 trong đề cương là tỷ lệ khởi đầu theo nhóm, không phải split hiện có hoặc split gốc của SWE-bench.
- Validation/test chính chỉ có real. Synthetic sinh từ train groups; không đưa biến thể/retry/duplicate family qua split. Nếu đã dùng phản hồi test để sửa thiết kế/dữ liệu, tập đó trở thành development, cần tập đánh giá cuối khác.
- Dự thảo sàng lọc tối đa 60 tình huống mới, ưu tiên SWE train/dev ít dependency; real cũ chỉ dùng nếu đủ evidence, không lấy head pass làm mẫu chẩn đoán real. Giữ case AIDev phù hợp, không ép quota nguồn.
- Repo đã xem, gồm mọi repo trong grouping snapshot, properr và ví dụ astropy cũ, thuộc phát triển. Đề xuất chọn ít nhất hai repo mới, một validation/một test, ghim vai trò trước chạy; sàng lọc metadata theo chi phí môi trường, số file và instance ID. Không đổi split vì điểm model. Ngưỡng sáu ứng viên/repo và số lượng cuối còn cần cân nhắc cùng cỡ mẫu nghiên cứu.
- Đề xuất train có ít nhất hai nhóm lỗi, ba tình huống real/nhóm. Không ép nhãn để đạt quota. Synthetic sau lọc từ 0,5–1 lần real train; dùng tối đa 1:1 trong mixed. Cỡ mẫu và support cuối chưa khóa.

### Giới hạn sinh và giao thức v3

- 120 lời gọi là **trần số request gửi 7B**, không phải 120 mẫu đạt. Ba request/seed tương đương tối đa 40 bộ ba nếu đều thực hiện. Phải giữ output lỗi/timeout/không gây failure trong mẫu số.
- `single-line-site-v3` đã triển khai: đọc AST seed tĩnh để lập site catalog, cung cấp ngữ cảnh code/test, nhận `path/site_id/replacement/explanation`, render đúng một dòng với indentation/newline gốc. Không yêu cầu generator tự gán nhãn diagnosis. Site/proposal không tự thành input 3B.
- Một dòng vẫn có thể sai cú pháp hoặc không gây regression. Candidate chạy baseline pass → ba failure ổn định → restored pass trong Docker cô lập. Giữ raw nguyên trạng và policy đã duyệt: syntax violation ngoài valid-Python subset, marker extra/X và +10 K chỉ phân tích development, chưa train.
- Đề xuất build 20 phút/test 5 phút/request sinh 3 phút; Docker/model tuần tự, tải metadata tối đa hai tác vụ; không stage mới dưới 20 GiB hoặc khi không đủ thời gian; không tự prune cache/images. Checkpoint/resume tránh gọi trùng stage không chắc đã hoàn tất. Các giới hạn mới chưa được kích hoạt.

## Nhãn và cấu trúc mẫu SFT đã giải thích

Một mẫu = tình huống chẩn đoán có input và đáp án tham chiếu. Nhiều test cùng một nguyên nhân hoặc ba repetitions không tự thành nhiều mẫu. Một case có thể sinh nhiều candidate, cần theo dõi nhóm và trùng lặp.

- Input dự kiến: instruction, log thực thi và code đúng phiên bản. Vòng đầu đề xuất chưa đưa diff vào input; code được chọn theo bằng chứng có tại thời điểm lỗi, không dùng gold location để chọn sẵn đoạn đúng.
- Target dự kiến: nhóm nguyên nhân + file/hàm liên quan + giải thích ngắn; dòng chính xác chỉ thêm khi đủ bằng chứng. Đây chưa phải schema đã implement/chốt.
- Metadata tách riêng: nguồn real/synthetic, repo/commit/run, hash, split/group, nguồn gán nhãn, mức evidence, trạng thái xác nhận và điều kiện sử dụng. Real/synthetic và silver/gold là hai trục khác nhau.
- AIDev/SWE cung cấp provenance; SWE có repair/test patch và FAIL_TO_PASS/PASS_TO_PASS. Không có sẵn taxonomy chẩn đoán riêng của đề tài, mọi file/hàm/dòng nguyên nhân hoặc actor gây lỗi đã xác nhận. Gold repair patch là bản sửa tham chiếu, không tự là gold cause label.
- Công cụ trích pass/fail/exception từ thực thi. Agent phải phân tích code/diff/log để đề xuất nguyên nhân, vị trí và giải thích; không áp máy móc TypeError → API/type hoặc coi mọi dòng sửa là causal line. Nhãn generator cũ vẫn chỉ tự khai.
- Taxonomy đề xuất: syntax; dependency/configuration; API/type; logic/value; unknown. Không lấy environment setup failure làm lỗi ứng dụng chỉ để tăng số mẫu.

### Silver và gold

- Chưa có dataset silver export. Hiện chỉ có evidence, bản phân tích và nhãn đề xuất. Silver là cách phân loại nguồn/chất lượng nhãn dự kiến cho dataset mới.
- Silver: tự động hoặc mô hình hỗ trợ, có kiểm tra bằng evidence nhưng có thể sai. Human acceptance of disposition không tự nâng thành gold.
- Người dùng là sinh viên, không tự nhận chuyên gia. Không gán tên reviewer từ tài khoản/máy; không coi câu duyệt chung là xác nhận chuyên môn mọi nhãn/vị trí.
- Đề xuất tạo tập tham chiếu đáng tin hơn bằng rubric, ví dụ/phản ví dụ, một phần gán độc lập trước khi xem đề xuất, đo bất đồng, phân xử và nếu có thể nhờ GVHD/người có kinh nghiệm kiểm tra subset khó. Không có reviewer độc lập thì công bố silver/reference tạm thời và giới hạn, không đổi tên thành expert gold.
- Chất lượng theo từng trường: execution_verified có thể được xác minh trong khi causal class/line vẫn pending. Quyền dùng silver cho thăm dò được chọn trong lập kế hoạch, không đồng nghĩa toàn bộ record đủ điều kiện train hoặc plan đã được phê duyệt thực thi.

### Vai trò người và agent gây lỗi

Nhiệm vụ chính được đề xuất là nguyên nhân kỹ thuật và file/hàm; actor chỉ subset có provenance. AIDev PR do agent tạo có thể đang sửa lỗi cũ; không suy agent gây lỗi ban đầu. 7B synthetic có nguồn sinh biết rõ, là cố ý tạo lỗi trong thí nghiệm, không đại diện lỗi vô tình của coding agent ngoài thực tế. Chưa có bộ đối chứng thao tác người thật được xây.

## Huấn luyện, logging và dataset v2

### Cấu hình thăm dò từng được đề xuất

- Cùng checkpoint HF Qwen2.5-Coder-3B-Instruct/revision/chat template cho prompt-only và SFT; môi trường ML tách trong cache, version lock sau compatibility smoke test.
- QLoRA NF4 double-quant, rank 16/alpha 32/dropout 0,05, lr 1e-4, microbatch 1/accumulation 8, context tổng 2048, response-only loss. Đây là khởi điểm đề xuất, chưa cài/benchmark/chạy.
- Hai adapter độc lập, seed 5417. Công thức cũ `min(60, ceil(3*(R+S)/8))` cho hai cấu hình với shuffle/cycle real-only để khớp update. Với R=18/S=9 chỉ là 11 updates; agent đã nêu rõ quá nhỏ để kết luận và cần xem lại thiết kế trước chạy. Khớp update không tự khớp token/distribution; phải báo cả hai.
- Validation giữa/cuối, chọn Macro-F1, hòa chọn checkpoint sớm; một fallback OOM 1024 token áp cùng hai cấu hình, ghi run/config khác. Đây là dự thảo, chưa phải lựa chọn đã được người dùng duyệt.
- Trần hai giờ/lượt train là **timeout**, không phải tốc độ đã đo. Cần pilot ngắn trên độ dài mẫu thật để dự báo thời gian. Chưa có training logs hoặc peak training VRAM.

### Logging cần có trước khi train

Dataset version/hash, split/sample IDs, label provenance/support; model/tokenizer revision/chat template; config/dependency versions/seed; loss/lr/grad norm/update/epoch/tokens; validation metrics/checkpoint selection; dự đoán từng mẫu, lỗi format và confusion matrix; thời gian download/load/train/eval tách riêng, GPU memory thực đo; adapter và trainer/optimizer/scheduler/RNG state để resume khi hỗ trợ. Không thay log cũ, không tự tuyên bố phần logging này đã implement.

### Dataset v2 và model choice

- Agent khuyến nghị, **người dùng chưa xác nhận thành quyết định**: khi đánh giá dataset v2, khởi tạo adapter mới từ cùng 3B Instruct gốc cho mỗi real-only/mixed run. Không pretrain từ số không. Giữ adapter v1 như pilot, tránh mang nhãn sai/lịch sử học khác nhau vào đối chứng chính.
- Dataset v2 có thể tích lũy mẫu v1 còn đạt, sửa nhãn có lineage, loại mẫu không đạt và thêm mẫu mới. Không mặc định v2 chỉ chứa dữ liệu mới hoặc phải bỏ v1.
- Phân biệt fresh SFT với continued SFT từ adapter cũ và resume checkpoint đang bị ngắt. Continued SFT là lựa chọn cho continual learning, chưa phải câu hỏi nghiên cứu chính đã chốt.
- Agent khuyến nghị GPT-6.1 Sol High cho thiết kế protocol, nhãn, leakage và phân tích khó; Medium cho script theo đặc tả, chuyển định dạng và thao tác thường lệ. Chưa có lệnh đổi model/reasoning của phiên. High/Medium không điều khiển GPU train 3B và không thay thế evidence review.

## Những việc phải làm rõ trước khi thực thi

1. Viết bản plan thay thế, phân biệt mục tiêu pilot 24 giờ với thí nghiệm chính; sửa cách gọi gold và các ngưỡng mẫu nhỏ gây hiểu lầm.
2. Khóa output/label rubric, cách xác nhận silver và cách báo chất lượng đánh giá khi chưa có expert-reviewed gold.
3. Chốt số lượng mục tiêu/minimum, split theo nhóm/repo, công thức budget huấn luyện và chế độ label review; không dựa quota nhỏ để tuyên bố hiệu quả synthetic.
4. Giữ logging đầy đủ và baseline/đối chứng cùng model nền. Chỉ bắt đầu sau khi người dùng duyệt plan; không tự tạo goal/schedule hoặc khởi động runtime vì đọc checkpoint này.

Nguồn đã tham khảo trong trao đổi: [SWE-bench schema](https://www.swebench.com/SWE-bench/guides/datasets/), [AIDev paper](https://arxiv.org/abs/2602.09185), [SWE-smith generation](https://swesmith.com/guides/create_instances/), [TRL SFT](https://huggingface.co/docs/trl/sft_trainer), [PEFT quantization](https://huggingface.co/docs/peft/developer_guides/quantization), [Trainer logging/checkpoint](https://huggingface.co/docs/transformers/main_classes/trainer), [PEFT checkpoint](https://huggingface.co/docs/peft/developer_guides/checkpoint), [OpenAI reasoning guidance](https://developers.openai.com/api/docs/guides/reasoning). Nguồn hỗ trợ phương pháp/cấu trúc; không chứng minh số lượng mẫu đủ, throughput hoặc hiệu quả trên dự án này.
