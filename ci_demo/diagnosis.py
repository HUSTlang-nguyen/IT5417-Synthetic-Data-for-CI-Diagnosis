"""Reference-free source retrieval and explicit-denominator diagnosis metrics."""
from __future__ import annotations

import ast
from collections import Counter
import re
from pathlib import Path

from .multicase import is_test, safe_relative

LABELS = ("syntax", "dependency/configuration", "API/type", "logic/value")


def failure_log(log):
    """Drop pytest progress chatter; retain the observed failure and traceback verbatim."""
    sections = re.split(r"={3,}\s+(?:FAILURES|ERRORS)\s+={3,}", log, maxsplit=1)
    if len(sections) == 2:
        return re.split(r"={3,}\s+short test summary info\s+={3,}", sections[1], maxsplit=1)[0].strip()
    return log


def functions(text):
    """Read source as text/AST only; never import target repositories."""
    tree = ast.parse(text)
    result = []

    def visit(nodes, parent=""):
        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = parent + node.name
                if not isinstance(node, ast.ClassDef):
                    result.append((name, node.lineno, node.end_lineno))
                visit(node.body, name + ".")
    visit(tree.body)
    return result


def retrieve(tree, log, *, max_functions=5, max_chars=6000, source_overrides=None):
    """Rank using observable stack paths/lines and lexical symbols, never labels/patches."""
    if not 1 <= max_functions <= 5 or max_chars < 100:
        raise ValueError("Invalid retrieval bounds")
    root = Path(tree).resolve()
    if not root.is_dir():
        raise ValueError("Source root missing")
    source_overrides = {} if source_overrides is None else source_overrides
    if not isinstance(source_overrides, dict):
        raise ValueError("Source overrides must map existing paths to source text")
    for name, value in source_overrides.items():
        path = root / safe_relative(name)
        if not isinstance(value, str) or not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError("Invalid candidate repository overlay")
    log = failure_log(log)
    query = set(re.findall(r"[A-Za-z_][A-Za-z_0-9]{2,}", log))
    observed_test_modules = set(re.findall(r"\btest_([A-Za-z_0-9]+)\.py\b", log))
    # Python tracebacks and pytest's path:line summaries both describe observed input.
    trace = [(p.replace("\\", "/"), int(n)) for p, n in
             re.findall(r'File ["\']([^"\']+\.py)["\'], line (\d+)', log)]
    trace += [(p.replace("\\", "/"), int(n)) for p, n in
              re.findall(r'(?:^|\s)([^\s:"\']+\.py):(\d+)', log)]
    ranked = []
    scanned = 0
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root).as_posix()
        if any(part in {".git", ".venv", "__pycache__", "build", "dist"} for part in path.relative_to(root).parts):
            continue
        if is_test(relative) or path.is_symlink() or not path.resolve().is_relative_to(root):
            continue
        if path.stat().st_size > 250_000:
            continue
        scanned += 1
        text = source_overrides[relative] if relative in source_overrides else path.read_text(encoding="utf-8", errors="replace")
        try:
            entities = functions(text)
            parsed = ast.parse(text)
        except (SyntaxError, ValueError):
            entities = []
            parsed = None
        lines = text.splitlines()
        if not entities:
            entities = [("<module>", 1, len(lines))]
        elif parsed:
            module_nodes = [node for node in parsed.body if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
            if module_nodes:
                entities.append(("<module>", min(n.lineno for n in module_nodes), max(n.end_lineno for n in module_nodes)))
        trace_lines = [n for p, n in trace if p == relative or p.endswith("/" + relative)]
        for name, start, end in entities:
            content = "\n".join(lines[start - 1:end])
            terms = set(re.findall(r"[A-Za-z_][A-Za-z_0-9]{2,}", content))
            lexical = len(query & terms) / max(1, len(terms)) ** 0.5
            symbol_match = bool(set(name.split(".")) & query) if name != "<module>" else False
            score = (1000 * any(start <= n <= end for n in trace_lines) + 100 * bool(trace_lines)
                     + 30 * symbol_match + 20 * (path.stem in observed_test_modules) + lexical)
            if score:
                ranked.append((score, relative, name, start, end, content))
    ranked.sort(key=lambda row: (-row[0], row[1], row[3], row[2]))
    snippets = []
    remaining = max_chars
    for score, path, name, start, end, content in ranked[:max_functions]:
        header = f"{path}::{name} lines {start}-{end}\n"
        excerpt = (header + content)[:remaining]
        if len(excerpt) <= len(header):
            break
        snippets.append({"file": path, "function": name, "start_line": start, "end_line": end,
                         "score": round(score, 6), "text": excerpt,
                         "truncated": len(excerpt) < len(header) + len(content)})
        remaining -= len(excerpt)
    return {"snippets": snippets, "production_files_scanned": scanned,
            "ranked_function_count": len(ranked), "characters": max_chars - remaining,
            "method": "failure_stack_symbols_and_module_names_v2"}


def locations(value, limit=5):
    if not isinstance(value, list):
        return []
    output = []
    for item in value[:limit] if limit is not None else value:
        if not isinstance(item, dict):
            continue
        path, function = item.get("file"), item.get("function")
        if not isinstance(path, str) or not isinstance(function, str) or not function:
            continue
        try:
            safe_relative(path)
        except ValueError:
            continue
        pair = (path, function)
        if pair not in output:
            output.append(pair)
    return output


def evaluate(references, predictions):
    """Missing/invalid predictions and retrieval misses remain failures, not filtered rows."""
    ids = [r["sample_id"] for r in references]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate reference sample ID")
    if set(predictions) - set(ids):
        raise ValueError("Predictions contain unknown sample IDs")
    confusion = {label: Counter() for label in LABELS}
    counts = Counter(total=len(references))
    for ref in references:
        pred = predictions.get(ref["sample_id"])
        valid = (isinstance(pred, dict) and pred.get("cause_type") in (*LABELS, "unknown")
                 and isinstance(pred.get("locations"), list)
                 and len(pred["locations"]) <= 5
                 and all(isinstance(item, dict) and set(item) == {"file", "function"}
                         and len(locations([item])) == 1 for item in pred["locations"])
                 and isinstance(pred.get("explanation"), str))
        counts["invalid_output"] += not valid
        proposal = pred if valid else {}
        guessed = proposal.get("cause_type", "<invalid>")
        counts["unknown_output"] += guessed == "unknown"
        actual = ref.get("cause_type")
        expected = locations(ref.get("locations"), limit=None)
        observed = locations(proposal.get("locations"))
        retrieved = locations(ref.get("retrieved_locations"))
        class_ok = actual in LABELS
        counts["classification_missing_reference"] += not class_ok
        counts["localization_missing_reference"] += not bool(expected)
        if class_ok:
            counts["classification_eligible"] += 1
            confusion[actual][guessed] += 1
            counts["classification_correct"] += guessed == actual
        if expected:
            counts["localization_eligible"] += 1
            expected_files = {p for p, _ in expected}
            visible_files = expected_files & {p for p, _ in retrieved}
            visible_functions = set(expected) & set(retrieved)
            files = list(dict.fromkeys(p for p, _ in observed))
            for k in (1, 5):
                counts[f"file_top{k}_correct"] += bool(visible_files & set(files[:k]))
                counts[f"function_top{k}_correct"] += bool(visible_functions & set(observed[:k]))
                counts[f"file_recall{k}_sum"] += len(visible_files & set(files[:k])) / len(expected_files)
                counts[f"function_recall{k}_sum"] += len(visible_functions & set(observed[:k])) / len(set(expected))
            if class_ok:
                counts["joint_eligible"] += 1
                counts["joint_top1_correct"] += guessed == actual and bool(visible_functions & set(observed[:1]))
        # Retrieval is scored after prediction, using pre-frozen references, not used by retrieve().
        if expected:
            counts["retrieval_function_covered"] += bool(set(expected) & set(retrieved))
            counts["retrieval_file_covered"] += bool({p for p, _ in expected} & {p for p, _ in retrieved})
    per_class = {}
    for label in LABELS:
        tp = confusion[label][label]
        support = sum(confusion[label].values())
        fp = sum(row[label] for other, row in confusion.items() if other != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / support if support else 0.0
        per_class[label] = {"support": support, "precision": precision, "recall": recall,
                            "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0}
    def rate(key, denominator):
        return counts[key] / counts[denominator] if counts[denominator] else None
    return {"counts": dict(counts), "macro_f1": sum(v["f1"] for v in per_class.values()) / len(LABELS) if counts["classification_eligible"] else None,
            "classification_accuracy": rate("classification_correct", "classification_eligible"),
            "per_class": per_class, "confusion": {k: dict(v) for k, v in confusion.items()},
            **{f"{level}_top{k}": rate(f"{level}_top{k}_correct", "localization_eligible")
               for level in ("file", "function") for k in (1, 5)},
            **{f"{level}_recall_at{k}": rate(f"{level}_recall{k}_sum", "localization_eligible")
               for level in ("file", "function") for k in (1, 5)},
            "joint_top1": rate("joint_top1_correct", "joint_eligible"),
            "retrieval_function_coverage": rate("retrieval_function_covered", "localization_eligible"),
            "retrieval_file_coverage": rate("retrieval_file_covered", "localization_eligible"),
            "label_order": list(LABELS), "reference_quality": "silver_not_expert_gold"}
