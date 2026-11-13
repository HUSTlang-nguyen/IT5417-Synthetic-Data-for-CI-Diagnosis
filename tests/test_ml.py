"""CPU/string-only protocol tests; no torch, tokenizer downloads or model calls."""
import re
import unittest
from pathlib import Path
import tempfile
import importlib.util

from ci_demo.ml import prepare_input, verify_checkpoint
from ci_demo.common import sha256


class WordTokenizer:
    def __init__(self):
        self.words = []
        self.mapping = {}

    def encode(self, text, **kwargs):
        ids = []
        for word in re.findall(r"\S+|\s+", text):
            if word not in self.mapping:
                self.mapping[word] = len(self.words)
                self.words.append(word)
            ids.append(self.mapping[word])
        return ids

    def decode(self, ids, **kwargs):
        return "".join(self.words[i] for i in ids)

    def apply_chat_template(self, messages, **kwargs):
        return self.encode("\n".join(m["role"] + ": " + m["content"] for m in messages) + "\nassistant:")


class MLProtocolTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec('transformers'), 'Requires isolated ML environment')
    def test_oversized_raw_log_is_cropped_without_model_length_warning(self):
        from tokenizers import Tokenizer
        from tokenizers.models import WordLevel
        from tokenizers.pre_tokenizers import Whitespace
        from transformers import PreTrainedTokenizerFast
        backend = Tokenizer(WordLevel({'[UNK]': 0, 'log': 1, 'failure': 2}, unk_token='[UNK]'))
        backend.pre_tokenizer = Whitespace()
        tokenizer = PreTrainedTokenizerFast(tokenizer_object=backend, unk_token='[UNK]', model_max_length=32768)
        tokenizer.chat_template = "{% for m in messages %}{{ m['role'] + ': ' + m['content'] + '\\n' }}{% endfor %}assistant:"
        raw = 'log ' * 46148 + 'failure'
        logger = 'transformers.tokenization_utils_base'
        with self.assertLogs(logger, level='WARNING'):
            full_ids = tokenizer.encode(raw, add_special_tokens=False)
        self.assertEqual(len(full_ids), 46149)
        tokenizer.deprecation_warnings.clear()
        with self.assertNoLogs(logger, level='WARNING'):
            prepared = prepare_input({'execution_log': raw, 'code': []}, tokenizer)
        self.assertEqual(prepared['log_original_tokens'], 46149)
        self.assertEqual(prepared['log_retained_tokens'], 640)
        self.assertLessEqual(prepared['input_tokens'] + 384, 2048)
        self.assertIn('failure', tokenizer.decode(prepared['input_ids']))

    def test_checkpoint_inventory_detects_changed_or_omitted_weights(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.safetensors"
            path.write_bytes(b"inert software fixture")
            info = {"revision": "fixture", "local_dir": tmp, "files": {path.name: path.stat().st_size}}
            inventory = {"revision": "fixture", "files": {path.name: sha256(path)}}
            verify_checkpoint(info, inventory)
            with self.assertRaises(ValueError):
                verify_checkpoint(info, {"revision": "fixture", "files": {}})
            path.write_bytes(b"changed fixture")
            with self.assertRaises(ValueError):
                verify_checkpoint(info, inventory)

    def test_prompt_budget_keeps_retrieval_order_without_reference_oracle(self):
        model_input = {"execution_log": "start " + "log " * 2000 + "actual_failure",
                       "code": [{"file": f"p{i}.py", "function": "f", "text": f"p{i}.py::f\n" + "return x + 1\n" * 100}
                                for i in range(5)], "reference": "SECRET_REFERENCE"}
        for context in (2048, 1024):
            tokenizer = WordTokenizer()
            result = prepare_input(model_input, tokenizer, context=context)
            text = tokenizer.decode(result["input_ids"])
            self.assertLessEqual(result["input_tokens"] + 384, context)
            self.assertNotIn("SECRET_REFERENCE", text)
            self.assertIn("actual_failure", text)
            pairs = result["retrieved_locations_after_tokenization"]
            self.assertEqual([p["file"] for p in pairs], [f"p{i}.py" for i in range(len(pairs))])
            self.assertEqual(len(result["prompt_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
