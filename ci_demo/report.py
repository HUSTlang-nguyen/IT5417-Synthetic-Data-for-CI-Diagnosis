"""Offline HTML report. Every model/source string is escaped."""
from __future__ import annotations
from html import escape
import json
from pathlib import Path
from urllib.parse import quote
from .common import read_json, run_path

def esc(value):
    return escape(str(value), quote=True)

def link(path, text=None):
    return '<a href="' + quote(path, safe="/.-") + '">' + esc(text or path) + '</a>'

def stage(folder, result, prefix=""):
    if not result: return "<p>Chưa chạy.</p>"
    detail = "timeout" if result.get("timed_out") else "exit " + str(result.get("exit_code"))
    files = [link(prefix + result[k]) for k in ("stdout", "stderr", "junit") if k in result]
    return "<p>" + esc(detail) + " · " + esc(result.get("duration_seconds")) + "s · " + " · ".join(files) + "</p>"

def render(folder, manifest):
    source = manifest.get("source", {})
    body = ['<h1>Demo dữ liệu lỗi CI có kiểm chứng</h1>',
            '<p class="notice">BÁO CÁO ARTIFACT ĐÃ LƯU — mở trang này không gọi LLM hoặc chạy test mới.</p>',
            '<p>Run: <code>' + esc(manifest["run_id"]) + '</code> · ' + esc(manifest.get("created_at")) + '</p>',
            '<p>Trạng thái: <strong>' + esc(manifest["status"]) + '</strong></p>']
    if manifest.get("error"):
        body.append('<p class="error">' + esc(manifest["error"]) + '</p>')
    body.append('<p>' + link("manifest.json", "Manifest đầy đủ") + '</p>')
    if source:
        body.append('<h2>Nguồn và workflow</h2><p>' + esc(source["dataset"]) + " " + esc(source["revision"])
                    + " · " + esc(source["table"]) + " · record " + esc(source["record_id"]) + '</p>')
        body.append('<p>Base: <code>' + esc(source["base"]) + '</code><br>Head: <code>'
                    + esc(source.get("head", "base + pinned repair patch")) + '</code></p>')
        body.append('<p>Dataset → repo/commit → môi trường → LLM sinh ứng viên → test độc lập → người rà nhãn.</p>')
        body.append('<p>Nhãn agent ở PR không chứng minh actor gây lỗi. Log ở đây là log tái hiện local, không phải CI lịch sử.</p>')
    if manifest["kind"] == "historical_reproduction":
        body.append('<h2>Kiểm tra giả thuyết lịch sử</h2><p>' + esc(source["historical_hypothesis"]) + '</p>')
        body.append('<h3>Base</h3>' + stage(folder, manifest.get("base")))
        body.append('<h3>Head</h3>' + stage(folder, manifest.get("head")))
        body.append('<p>Bản head pass là điều kiện chọn seed. Không suy gold label hoặc tác giả gây lỗi từ kết quả này.</p>')
        if manifest.get("build"):
            body.append('<h3>Dựng môi trường</h3>' + stage(folder, manifest["build"]))
    elif manifest["kind"] == "synthetic_generation" and manifest.get("schema_version", 1) == 1:
        attempts = manifest.get("attempts", [])
        denominator = manifest["attempt_count"]
        executed = sum(x["status"] == "execution_verified" for x in attempts)
        body.append('<h2>Thí nghiệm synthetic có kiểm soát</h2><p>Model: <strong>' + esc(manifest["model"]) + '</strong></p>')
        body.append('<p>Đạt kiểm tra thực thi: ' + str(executed) + "/" + str(denominator)
                    + '. Mẫu số gồm cả lượt lỗi/không hợp lệ; không phải tỷ lệ nhãn gold hay hiệu quả huấn luyện.</p>')
        body.append('<p>Rà nhãn: <strong>chờ người duyệt</strong>. Đây là lỗi mới sinh, không phải lỗi lịch sử AIDev.</p>')
        body.append('<p>' + link("prompt.txt") + ' · ' + link("original.py") + ' · ' + link("tests.py") + '</p>')
        for item in attempts:
            prefix = item["directory"] + "/"
            body.append('<section><h3>Lượt ' + str(item["index"]) + ' — ' + esc(item["status"]) + '</h3>')
            body.append('<p>Thời gian sinh: ' + esc(item.get("generation_seconds", "chưa đo")) + 's</p>')
            if item.get("error"): body.append('<p class="error">' + esc(item["error"]) + '</p>')
            if item.get("rejection_reason"):
                body.append('<p>Lý do không đạt: ' + esc(item["rejection_reason"]) + '</p>')
            for filename in ("request.json", "response.raw.json", "proposal.json", "review.json"):
                if (folder / prefix / filename).is_file():
                    body.append('<p>' + link(prefix + filename) + '</p>')
            patch = folder / prefix / "change.diff"
            if patch.is_file():
                body.append('<h4>Diff từ output LLM</h4><pre>' + esc(patch.read_text(encoding="utf-8")) + '</pre>')
            if "baseline" in item:
                body.append('<h4>Baseline</h4>' + stage(folder, item["baseline"], prefix))
                for i, result in enumerate(item["repetitions"], 1):
                    body.append('<h4>Ứng viên / lần ' + str(i) + '</h4>' + stage(folder, result, prefix))
                body.append('<h4>Hoàn tác</h4>' + stage(folder, item["restored"], prefix))
            body.append('</section>')
        if len(attempts) < denominator:
            body.append('<p class="error">Có lượt chưa thực hiện; không coi chúng là thành công.</p>')
    elif manifest["kind"] == "case_reproduction":
        body.append('<h2>Tái hiện local với upstream tests cố định</h2>')
        body.append('<p>' + esc(manifest.get("qualification")) + '</p>')
        body.append('<p>Giả thuyết được hỗ trợ: ' + esc(manifest.get("historical_supported", "chưa biết"))
                    + ' · Seed fixed pass: ' + esc(manifest.get("head_passed", "chưa biết")) + '</p>')
        body.append('<h3>Base</h3>' + stage(folder, manifest.get("base")))
        body.append('<h3>Fixed</h3>' + stage(folder, manifest.get("head")))
        if manifest.get("environment"):
            body.append('<h3>Build</h3>' + stage(folder, manifest["environment"].get("build")))
            body.append('<p>' + link('environment.json') + ' · ' + link('base-source.json') + ' · ' + link('head-source.json') + '</p>')
    elif manifest["kind"] in {"synthetic_generation", "synthetic_verification"}:
        generated = manifest["kind"] == "synthetic_generation"
        attempts = manifest.get("attempts", [])
        body.append('<h2>' + ('Sinh bằng 7B — ' + esc(manifest.get('protocol', 'single-file-exact-edit-v2')) if generated
                             else 'Kiểm chứng candidate trong Docker') + '</h2>')
        body.append('<p>Đã ghi nhận ' + str(len(attempts)) + '/' + str(manifest["attempt_count"]) + ' lượt; đạt thực thi: '
                    + ("xem verification run" if generated else str(sum(x["status"] == "execution_verified" for x in attempts))) + '</p>')
        if generated:
            files = [link(p) for p in ('prompt.txt', 'original.py', 'tests.json') if (folder / p).is_file()]
            body.append('<p>' + ' · '.join(files) + '</p>')
        else:
            body.append('<p>' + link('../' + manifest['generation_run'] + '/report.html', 'Raw generation được giữ nguyên') + '</p>')
        body.append('<p>Development; nhãn gold và training eligibility pending.</p>')
        for item in attempts:
            prefix = item["directory"] + '/'
            body.append('<section><h3>Lượt ' + str(item["index"]) + ' — ' + esc(item["status"]) + '</h3>')
            body.append('<p>' + esc(item.get('error') or item.get('rejection_reason') or '') + '</p>')
            for filename in ('request.json', 'response.raw.json', 'proposal.json', 'change.diff', 'candidate.py', 'review.json'):
                if (folder / prefix / filename).is_file(): body.append('<p>' + link(prefix + filename) + '</p>')
            if item.get('baseline'):
                body.append('<h4>Baseline</h4>' + stage(folder, item['baseline'], prefix))
                for rep in item.get('repetitions', []): body.append('<h4>Candidate</h4>' + stage(folder, rep, prefix))
                body.append('<h4>Restored</h4>' + stage(folder, item.get('restored'), prefix))
            body.append('</section>')
    elif manifest["kind"] == "development_batch":
        summary = manifest.get('summary', {})
        body.append('<h2>Đợt phát triển nhiều repo</h2><p>Ngân sách: 6 giờ active runtime; tối thiểu 20 GiB trống.</p>')
        body.append('<p>Đã đo: ' + esc(manifest.get('active_seconds')) + 's · Cận thời gian mất do gián đoạn: '
                    + esc(manifest.get('unaccounted_time_bound_seconds', 0)) + 's</p>')
        body.append('<pre>' + esc(json.dumps(summary, ensure_ascii=False, indent=2)) + '</pre>')
        if manifest.get('stop_reason'): body.append('<p>' + esc(manifest['stop_reason']) + '</p>')
        body.append('<table><tr><th>Case / nguồn</th><th>Trạng thái</th><th>Evidence</th></tr>')
        for item in manifest['cases']:
            links = [link('../' + value['run_id'] + ('/report.html' if (folder.parent / value['run_id'] / 'report.html').is_file()
                           else '/manifest.json'), name) for name, value in item['stages'].items()]
            body.append('<tr><td>' + esc(item['case_id']) + '<br>' + esc(item['source_kind']) + '</td><td>'
                        + esc(item['status']) + '<br>' + esc(item.get('error', '')) + '</td><td>' + ' · '.join(links) + '</td></tr>')
        body.append('</table><p>Giữ toàn bộ lỗi và lượt chưa chạy. Execution acceptance chưa là gold/training approval.</p>')
    elif manifest["kind"] == "generation_demo":
        generator = manifest["generator"]
        body.append('<h2>Phiên sinh dữ liệu bằng 7B</h2><p>Generator: <strong>' + esc(generator["model"]) + '</strong></p>')
        body.append('<p>Trạng thái sinh/kiểm chứng: ' + esc(generator["status"]) + '</p>')
        body.append('<p>Đạt kiểm chứng thực thi: ' + str(generator["execution_verified"]) + '/' + str(generator["requested"])
                    + ' · Lượt chưa thực hiện: ' + str(generator["unexecuted"]) + '</p>')
        measured = generator["generation_seconds"]
        timing = ('chưa đo' if measured is None else str(measured) + 's / '
                  + str(generator["measured_generation_attempts"]) + ' lượt có số đo')
        body.append('<p>Thời gian gọi sinh đã đo: ' + esc(timing) + '. Có thể gồm loading; không phải tổng thời gian demo hoặc peak VRAM.</p>')
        body.append('<p>Trạng thái các lượt: ' + esc(json.dumps(generator["status_counts"])) + '</p>')
        if generator.get("error"):
            body.append('<p class="error">' + esc(generator["error"]) + '</p>')
        for run_id, label in ((manifest.get("doctor_run"), 'Kiểm tra môi trường'),
                              (manifest.get("reproduction_run"), 'Tái hiện properr'),
                              (generator["run_id"], 'Evidence sinh và kiểm chứng')):
            if run_id:
                # A failing stage can save its manifest before its HTML is built.
                filename = 'report.html' if (folder.parent / run_id / 'report.html').is_file() else 'manifest.json'
                body.append('<p>' + link('../' + run_id + '/' + filename, label) + '</p>')
        body.append('<p>Rà nhãn: <strong>chờ người duyệt</strong>. Đạt thực thi chưa là phê duyệt dùng để train.</p>')
        body.append('<p>Model chẩn đoán chính: ' + esc(manifest["diagnoser"]["model"])
                    + ' — chưa triển khai, chưa chạy trong phiên sinh dữ liệu.</p>')
    elif manifest["kind"] == "pilot_comparison":
        body.append('<h2>So sánh pilot hai model sinh</h2>')
        body.append('<p>Nhãn chờ người duyệt. Một seed không đủ kết luận tổng quát hoặc hiệu quả huấn luyện.</p>')
        body.append('<p>Tương thích giao thức: ' + esc(manifest["protocol_compatible"]) + '</p>')
        for issue in manifest.get("comparison_issues", []):
            body.append('<p class="error">' + esc(issue) + '</p>')
        if manifest.get("doctor_run"):
            body.append('<p>' + link('../' + manifest["doctor_run"] + '/report.html', 'Kiểm tra môi trường') + '</p>')
        body.append('<table><tr><th>Model</th><th>Trạng thái</th><th>Đạt/tổng lượt</th>'
                    '<th>Chưa thực hiện</th><th>Thời gian sinh đã đo</th><th>Evidence</th></tr>')
        for model in manifest["models"]:
            measured = model["generation_seconds"]
            timing = ('chưa đo' if measured is None else str(measured) + 's / '
                      + str(model["measured_generation_attempts"]) + ' lượt có số đo')
            evidence = (link('../' + model["run_id"] + '/report.html', 'Artifact đã lưu')
                        if model["run_id"] else 'Chưa có run')
            body.append('<tr><td>' + esc(model["model"]) + '</td><td>' + esc(model["status"])
                        + '</td><td>' + str(model["execution_verified"]) + '/' + str(model["requested"])
                        + '</td><td>' + str(model["unexecuted"]) + '</td><td>' + esc(timing)
                        + '</td><td>' + evidence + '</td></tr>')
        body.append('</table><p>Mẫu số giữ cả lượt lỗi và lượt chưa thực hiện. Thời gian trên chỉ cộng các lượt có số đo; không phải tổng thời gian chạy.</p>')
        for model in manifest["models"]:
            body.append('<p>' + esc(model["model"]) + ': ' + esc(json.dumps(model["status_counts"])) + '</p>')
            if model.get("error"):
                body.append('<p class="error">' + esc(model["error"]) + '</p>')
    else:
        body.append('<pre>' + esc(json.dumps(manifest, ensure_ascii=False, indent=2)) + '</pre>')
    return """<!doctype html><html lang="vi"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>CI demo — artifact report</title>
<style>body{max-width:1080px;margin:40px auto;padding:0 24px;background:#f2f0e9;color:#151610;font:17px/1.7 system-ui}
h1{line-height:1.3}h2{margin-top:2em}a{color:#193b74}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#e6e3d9;padding:20px}
code{overflow-wrap:anywhere}section{border-top:1px solid #aaa;padding:20px 0}.notice{border:1px solid #888;padding:12px}.error{color:#8c1a10}
table{width:100%;border-collapse:collapse;font-size:15px}th,td{border:1px solid #aaa;padding:10px;text-align:left;overflow-wrap:anywhere}</style>""" + "\n".join(body) + "</html>"

def report_run(run_id):
    folder = run_path(run_id)
    manifest = read_json(folder / "manifest.json")
    path = folder / "report.html"
    path.write_text(render(folder, manifest), encoding="utf-8")
    return path
