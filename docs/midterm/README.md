# Bộ tài liệu bảo vệ giữa kỳ — 13/11/2026

Nội dung tiếng Việt, 20 phút trình bày. Các tệp sử dụng trực tiếp nằm tại [output/midterm](../../output/midterm/).

| Tệp | Mục đích |
|---|---|
| `hust-midterm.pptx` | 24 slide chính +4 dự phòng ẩn; bảng/sơ đồ và ghi chú thuyết trình chỉnh sửa được |
| `hust-midterm.pdf` | Bản đọc/chiếu gồm cả 28 slide, không phụ thuộc font máy chiếu |
| `bao-cao-giua-ky.pdf` | 11 trang nội dung; tổng 14 trang gồm bìa, mục lục và tham khảo |
| `cheatsheet-a4.pdf` | Một mặt A4 dọc để in; in 100%, không ghép nhiều trang |
| `ghi-chu-on-tap.pdf` | Sáu trang học/ôn, tách khỏi tờ tra nhanh |
| `loi-thuyet-trinh.pdf` | Lời đọc đầy đủ theo 24 slide, có mốc 20 phút; 4 phần dự phòng nằm riêng |
| `loi-thuyet-trinh.md` | Bản lời đọc để sửa theo cách nói của người trình bày |
| `latex-source.zip` | Source LaTeX, bảng/sơ đồ dùng chung, snapshot số liệu và hai ví dụ có provenance |

Báo cáo PDF đã điền **Nguyễn Hoàng Kiên — 20250735E** và bỏ dòng ngày cập nhật số liệu ở bìa/header. Bìa slide vẫn để trống họ tên/MSSV theo phiên bản trước. Thông tin GVHD lấy từ tài liệu định hướng trong repo; ngày bảo vệ chưa được xác nhận.

Báo cáo dùng tên hiển thị **M1** cho baseline prompt-only trong phần mô tả và bảng kết quả. Tên run, cấu hình và truy vết trong snapshot/evidence giữ nguyên; các đầu ra khác chưa đổi cách gọi. Macro `\baselineModelName` chỉ đổi nhãn hiển thị của hai bảng khi biên dịch báo cáo.

## Đọc và tập trình bày

Mở cheatsheet để nắm kiến trúc/model/metric, sau đó đọc ghi chú ôn tập. [Ghi chú theo từng slide](speaker-notes.md) có thời lượng dự kiến tổng 1200 giây, không tính hỏi đáp và 4 slide dự phòng. Đây là phân bổ thời gian, chưa phải một lần nói thử đã đo. PPTX có speaker notes tương ứng; khi cần dự phòng, chọn trực tiếp slide 25–28 trong PowerPoint.

[Lời đọc đầy đủ](talk-script.md) khác với ghi chú tóm tắt trong PPTX: văn phong ngôi “em”, có câu chuyển ý, chỉ dẫn trong ngoặc vuông và mốc bắt đầu/kết thúc từng slide. PDF gồm 14 trang, mỗi trang hai slide: 12 trang chính và 2 trang dự phòng. Chỉ đọc các đoạn văn, không đọc phần nhắc thao tác. Bản đầu khoảng 3.500 đơn vị cách trắng, cần nói thử để căn tốc độ và khoảng dừng. Chỉnh `talk-script.md`, chạy `python build_talk_script.py`, rồi biên dịch `talk-script.tex` bằng XeLaTeX hoặc Tectonic để xuất lại; số liệu và bộ slide giữ nguyên.

Template gốc là `HUST PPT Template 2021 ( Red 3X4).pptx`, thực tế 4:3. Nền/logo/master giữ từ bản người dùng cung cấp; slide nội dung dùng bố cục đỏ đơn giản. Tiêu đề giữ family Lato, chữ nội dung dùng Calibri. PDF slide dùng trang render ở kích thước gốc của template để giữ đúng khoảng trắng và logo; không chọn/copy chữ trong PDF này. Dùng PPTX khi cần sửa/copy nội dung hoặc chiếu ở độ phân giải cao. Nếu PowerPoint thay Lato trên máy chưa cài, có thể dùng PDF hoặc cài Lato từ Google Fonts. Báo cáo, cheatsheet và ghi chú vẫn là PDF văn bản từ LaTeX.

## Biên dịch LaTeX

Trong Overleaf: tải source zip, chọn `report.tex` làm Main document và compiler **XeLaTeX**. Đổi Main document thành `cheatsheet.tex` hoặc `study-notes.tex` để xuất hai bản tương ứng. Times New Roman/Arial/Consolas dùng khi có; máy khác dùng TeX Gyre Termes/Heros/Latin Modern Mono, có thể khác ngắt dòng nhẹ.

Với máy đã có XeLaTeX, chạy trong thư mục source:

```powershell
xelatex report.tex
xelatex report.tex
xelatex cheatsheet.tex
xelatex study-notes.tex
```

Trong worktree đã chuẩn bị, dùng compiler portable riêng, không cài thêm vào `.cache/ml-v1`:

```powershell
Set-Location 'C:\Users\neikh\.codex\worktrees\a4f5\IT5417-Synthetic-Data-for-CI-Diagnosis\docs\midterm'
..\..\.cache\midterm\tectonic\tectonic.exe --outdir ..\..\output\midterm report.tex
..\..\.cache\midterm\tectonic\tectonic.exe --outdir ..\..\output\midterm cheatsheet.tex
..\..\.cache\midterm\tectonic\tectonic.exe --outdir ..\..\output\midterm study-notes.tex
```

Tectonic 0.17.0 tải từ release chính thức; thư viện TeX/font được cache, lần biên dịch đầu có thể cần mạng. Các lệnh chỉ biên dịch tài liệu, không gọi model/Docker/pipeline. Tên PDF compiler tạo là `report.pdf`, `cheatsheet.pdf`, `study-notes.pdf`; tệp bàn giao được đổi tên như bảng trên.

`build_support.py` sinh bảng và sơ đồ từ `facts.json` bằng standard library; không cần dataset/model để biên dịch source đã đóng gói. Nguồn dựng PPTX `build_slides.mjs` nằm trong repo, dùng runtime authoring riêng và template gốc; không thuộc dependency pipeline ML. PPTX có thể chỉnh trực tiếp mà không chạy builder. Builder bảo vệ bản final đã tồn tại, nên lần dựng mới phải dùng tên output mới hoặc di chuyển bản đã có vào nơi lưu phiên bản trước.

## Nguồn và ranh giới số liệu

Snapshot `facts.json` lấy từ dataset lock v1.1, bảng evaluation v1 và hai mẫu train đã ghim. Chỉ giữ snippet code/log để trình bày cùng hash/provenance; không đóng gói full raw dataset hoặc weights. [Validation](../evaluation-validation.md), [test/cost](../evaluation-results.md), [phân tích lỗi](../evaluation-error-analysis.md) là nguồn diễn giải đầy đủ.

- AIDev thuộc development; tập 250 real SFT từ SWE-bench, log là tái hiện local.
- M1-P2 prompt mới, M2/M5 prompt cũ; adapter được chọn là parent104, không phải epoch10.
- Nhãn silver, M3/M4 chưa chạy; chưa có gold hoặc kết luận lợi ích synthetic tổng quát.
- Không train/generate/chấm test lại, không chỉnh raw/model/parser hoặc commit/push khi soạn tài liệu.
