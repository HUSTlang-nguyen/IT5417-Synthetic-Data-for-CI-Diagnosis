"""Mocked software tests only; never load models or execute candidate code."""
from contextlib import ExitStack, redirect_stdout, redirect_stderr
from io import StringIO
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from ci_demo import cli, ollama, pipeline, session
from ci_demo.common import read_json, write_json
from ci_demo.report import render
from scripts import demo


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.workspace = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.root = self.workspace / 'runs'
        self.root.mkdir()
        self.stack.enter_context(patch('ci_demo.common.RUNS', self.root))
        self.stack.enter_context(patch.object(demo, 'ROOT', self.workspace))
        self.stack.enter_context(redirect_stdout(StringIO()))
        self.stack.enter_context(redirect_stderr(StringIO()))

    def make_run(self, *, status='verification_finished', statuses=None, measured=True, run_id='fixture-generation'):
        folder = self.root / run_id
        folder.mkdir()
        statuses = ['invalid_output'] * 3 if statuses is None else statuses
        attempts = [{'index': i + 1, 'status': value, **({'generation_seconds': 0.2} if measured else {})}
                    for i, value in enumerate(statuses)]
        write_json(folder / 'manifest.json', {'kind': 'synthetic_generation', 'run_id': run_id,
                   'model': ollama.GENERATOR_MODEL, 'status': status, 'attempt_count': 3, 'attempts': attempts})
        (folder / 'report.html').write_text('software fixture report', encoding='utf-8')
        return run_id

    def new_session(self):
        folder = self.root / 'fixture-session'
        folder.mkdir()
        return folder

    def test_initial_session_preserves_denominator_and_unknown_timing(self):
        folder = self.new_session()
        manifest = session.save_session(folder)
        self.assertEqual(manifest['status'], 'running')
        self.assertEqual(manifest['generator']['requested'], 3)
        self.assertEqual(manifest['generator']['unexecuted'], 3)
        self.assertIsNone(manifest['generator']['generation_seconds'])
        self.assertEqual(manifest['diagnoser']['model'], ollama.DIAGNOSTIC_MODEL)
        self.assertEqual(manifest['diagnoser']['status'], 'not_implemented')
        html = (folder / 'report.html').read_text(encoding='utf-8')
        self.assertIn('0/3', html)
        self.assertIn('chưa đo', html)

    def test_zero_accepted_is_complete_and_raw_source_is_unchanged(self):
        run = self.make_run()
        raw = (self.root / run / 'manifest.json').read_bytes()
        folder = self.new_session()
        session.save_session(folder, generation_run=run)
        result = session.save_session(folder, finished=True)
        self.assertEqual(result['status'], 'demo_finished')
        self.assertEqual(result['generator']['execution_verified'], 0)
        self.assertEqual(result['generator']['generation_seconds'], 0.6)
        self.assertEqual(result['generator']['status_counts'], {'invalid_output': 3})
        self.assertEqual(raw, (self.root / run / 'manifest.json').read_bytes())
        self.assertIn('../' + run + '/report.html', (folder / 'report.html').read_text(encoding='utf-8'))
        with self.assertRaises(ValueError):
            session.save_session(folder)

    def test_partial_environment_failure_has_unexecuted_not_successful_attempts(self):
        run = self.make_run(status='environment_error', statuses=['generation_error'], measured=False)
        result = session.save_session(self.new_session(), generation_run=run, finished=True)
        self.assertEqual(result['status'], 'demo_incomplete')
        self.assertEqual(result['generator']['unexecuted'], 2)
        self.assertEqual(result['generator']['execution_verified'], 0)
        self.assertIsNone(result['generator']['generation_seconds'])

    def test_mixed_terminal_results_complete_but_pending_results_do_not(self):
        run = self.make_run(statuses=['execution_verified', 'verification_failed', 'generation_error'])
        result, complete = session.generation_summary(run)
        self.assertTrue(complete)
        self.assertEqual(result['execution_verified'], 1)
        path = self.root / run / 'manifest.json'
        manifest = read_json(path)
        manifest['attempts'][2]['status'] = 'awaiting_verification'
        write_json(path, manifest)
        self.assertFalse(session.generation_summary(run)[1])

    def test_invalid_source_kind_model_and_indices_are_rejected(self):
        run = self.make_run()
        path = self.root / run / 'manifest.json'
        original = read_json(path)
        for key, value in (('kind', 'historical_reproduction'), ('model', ollama.DIAGNOSTIC_MODEL), ('attempt_count', 2)):
            with self.subTest(key=key):
                write_json(path, {**original, key: value})
                with self.assertRaises(ValueError):
                    session.generation_summary(run)
        original['attempts'][2]['index'] = 1
        write_json(path, original)
        with self.assertRaises(ValueError):
            session.generation_summary(run)

    def test_error_text_is_escaped_and_doctor_link_is_saved(self):
        folder = self.new_session()
        write_json(self.root / 'fixture-doctor' / 'manifest.json', {'kind': 'doctor'})
        session.save_session(folder, doctor_run='fixture-doctor')
        result = session.save_session(folder, error='<script>fixture</script>', finished=True)
        html = (folder / 'report.html').read_text(encoding='utf-8')
        self.assertEqual(result['doctor_run'], 'fixture-doctor')
        self.assertIn('../fixture-doctor/manifest.json', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('<script>', html)

    def test_historical_reports_render_without_current_generation_configuration(self):
        manifest = {'kind': 'pilot_comparison', 'run_id': 'archived-fixture', 'status': 'comparison_finished',
                    'protocol_compatible': True, 'models': [
                        {'model': 'archived-generator', 'run_id': 'archived-run', 'status': 'verification_finished',
                         'execution_verified': 1, 'requested': 3, 'unexecuted': 0, 'status_counts': {},
                         'generation_seconds': None, 'measured_generation_attempts': 0}]}
        html = render(self.root, manifest)
        self.assertIn('1/3', html)
        self.assertIn('archived-generator', html)
        self.assertIn('../archived-run/report.html', html)

    def checks(self, ready=True):
        return {'run_id': 'fixture-doctor', 'target_gpu_matches': True,
                'checks': {'docker': {'exit_code': 0 if ready else 1, 'timed_out': False,
                                     'server_os': 'linux' if ready else None}, 'ollama': {'ok': ready}}}

    def demo_manifest(self):
        return read_json(next(self.root.glob('demo-*')) / 'manifest.json')

    def test_preflight_is_checkpointed_before_doctor_and_failure_stops_calls(self):
        def doctor(endpoint):
            current = self.demo_manifest()
            self.assertEqual(current['status'], 'running')
            self.assertEqual(current['generator']['unexecuted'], 3)
            return self.checks(False)
        with patch('sys.argv', ['demo.py']), patch.object(demo, 'doctor', side_effect=doctor), \
                patch.object(demo, 'cli') as stage, patch.object(demo.subprocess, 'run') as process:
            with self.assertRaises(RuntimeError):
                demo.main()
        self.assertEqual(stage.call_args.args, ('report', '--run', 'fixture-doctor'))
        process.assert_not_called()
        manifest = self.demo_manifest()
        self.assertEqual(manifest['status'], 'demo_incomplete')
        self.assertEqual(manifest['generator']['unexecuted'], 3)
        self.assertIn('Docker', manifest['error'])
        self.assertIn('Ollama', manifest['error'])

    def test_demo_pulls_and_generates_only_7b_and_preserves_stage_links(self):
        run = self.make_run(status='generation_finished')
        def stage(*args):
            if args[0] == 'reproduce':
                return 'fixture-reproduction'
            if args[0] == 'generate':
                return run
            if args[0] == 'verify':
                self.assertEqual(self.demo_manifest()['generator']['run_id'], run)
                path = self.root / run / 'manifest.json'
                m = read_json(path)
                m['status'] = 'verification_finished'
                write_json(path, m)
                return run
        with patch('sys.argv', ['demo.py', '--pull-models']), \
                patch.object(demo, 'doctor', return_value=self.checks()), \
                patch.object(demo, 'cli', side_effect=stage) as calls, patch.object(demo.subprocess, 'run') as process:
            demo.main()
        process.assert_called_once_with(['ollama', 'pull', ollama.GENERATOR_MODEL], check=True)
        self.assertEqual([c.args for c in calls.call_args_list], [
            ('report', '--run', 'fixture-doctor'), ('reproduce', '--case', 'properr-6'),
            ('generate', '--model', ollama.GENERATOR_MODEL, '--attempts', '3'), ('verify', '--run', run)])
        result = self.demo_manifest()
        self.assertEqual(result['status'], 'demo_finished')
        self.assertEqual(result['reproduction_run'], 'fixture-reproduction')
        self.assertEqual(result['generator']['requested'], 3)

    def test_stage_failure_keeps_generation_id_and_never_retries(self):
        for failing in ('generate', 'verify'):
            with self.subTest(stage=failing):
                run = self.make_run(status='environment_error', statuses=['generation_error'],
                                    measured=False, run_id='fixture-' + failing)
                def stage(*args):
                    if args[0] == failing:
                        raise demo.StageError(args, run)
                    return run if args[0] == 'generate' else None
                with patch('sys.argv', ['demo.py', '--skip-reproduce']), \
                        patch.object(demo, 'doctor', return_value=self.checks()), \
                        patch.object(demo, 'cli', side_effect=stage) as calls:
                    with self.assertRaises(RuntimeError):
                        demo.main()
                manifests = [read_json(p / 'manifest.json') for p in self.root.glob('demo-*')]
                result = next(m for m in manifests if m['generator']['run_id'] == run)
                self.assertEqual(result['status'], 'demo_incomplete')
                self.assertEqual(result['generator']['unexecuted'], 2)
                self.assertEqual(sum(c.args[0] == 'generate' for c in calls.call_args_list), 1)
                self.assertEqual(sum(c.args[0] == 'verify' for c in calls.call_args_list), int(failing == 'verify'))

    def test_download_failure_stops_before_generation_and_keeps_denominator(self):
        with patch('sys.argv', ['demo.py', '--pull-models']), \
                patch.object(demo, 'doctor', return_value=self.checks()), patch.object(demo, 'cli') as stage, \
                patch.object(demo.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, ['ollama', 'pull'])):
            with self.assertRaises(RuntimeError):
                demo.main()
        self.assertEqual(stage.call_count, 1)
        self.assertEqual(self.demo_manifest()['generator']['unexecuted'], 3)

    def test_cli_stage_error_retains_run_id(self):
        response = subprocess.CompletedProcess([], 1, stdout='run: fixture-run\n', stderr='fixture error')
        with patch.object(demo.subprocess, 'run', return_value=response):
            with self.assertRaises(demo.StageError) as caught:
                demo.cli('generate', '--model', ollama.GENERATOR_MODEL)
        self.assertEqual(caught.exception.run_id, 'fixture-run')

    def test_other_models_are_rejected_before_any_pipeline_or_http_work(self):
        for model in ('qwen2.5-coder:1.5b-instruct', ollama.DIAGNOSTIC_MODEL, 'qwen2.5-coder:3b-instruct'):
            with self.subTest(model=model), patch('ci_demo.pipeline.passing_seed') as seed, \
                    patch('ci_demo.ollama.request') as request:
                with self.assertRaises(ValueError):
                    pipeline.generate_run(model, 3, 'http://127.0.0.1:11434')
                with self.assertRaises(ValueError):
                    ollama.generate('http://127.0.0.1:11434', model, 'fixture', 0)
                with self.assertRaises(SystemExit) as caught:
                    cli.main(['generate', '--model', model])
                self.assertEqual(caught.exception.code, 2)
                seed.assert_not_called()
                request.assert_not_called()

    def test_compare_command_is_not_offered(self):
        with self.assertRaises(SystemExit) as caught:
            cli.main(['compare', '--runs', 'fixture-a', 'fixture-b'])
        self.assertEqual(caught.exception.code, 2)

    def test_verification_refuses_other_model_before_runner_or_evidence_changes(self):
        run = self.make_run(status='generation_finished', statuses=['awaiting_verification'] * 3)
        path = self.root / run / 'manifest.json'
        manifest = read_json(path)
        manifest['model'] = 'unsupported-generator'
        write_json(path, manifest)
        before = path.read_bytes()
        with patch('ci_demo.pipeline.image_identity') as image, patch('ci_demo.runner.execute') as execute:
            with self.assertRaises(ValueError):
                pipeline.verify_run(run)
            image.assert_not_called()
            execute.assert_not_called()
        self.assertEqual(before, path.read_bytes())

    def test_missing_generation_id_and_reproduction_error_are_saved(self):
        for stage_name in ('generate', 'reproduce'):
            with self.subTest(stage=stage_name):
                def stage(*args):
                    if args[0] == 'reproduce':
                        raise demo.StageError(args, 'fixture-failed-reproduction')
                    return None
                argv = ['demo.py', '--skip-reproduce'] if stage_name == 'generate' else ['demo.py']
                with patch('sys.argv', argv), patch.object(demo, 'doctor', return_value=self.checks()), \
                        patch.object(demo, 'cli', side_effect=stage):
                    with self.assertRaises(RuntimeError):
                        demo.main()
        manifests = [read_json(p / 'manifest.json') for p in self.root.glob('demo-*')]
        self.assertEqual(len(manifests), 2)
        self.assertTrue(all(m['status'] == 'demo_incomplete' and m['generator']['unexecuted'] == 3 for m in manifests))
        self.assertTrue(any(m['reproduction_run'] == 'fixture-failed-reproduction' for m in manifests))

    def test_existing_non_session_artifact_cannot_be_overwritten(self):
        folder = self.new_session()
        write_json(folder / 'manifest.json', {'kind': 'historical_reproduction'})
        before = (folder / 'manifest.json').read_bytes()
        with self.assertRaises(ValueError):
            session.save_session(folder)
        self.assertEqual(before, (folder / 'manifest.json').read_bytes())

    def test_7b_transport_preserves_prompt_options_and_seed(self):
        with patch('ci_demo.ollama.request', return_value='{}') as request:
            payload, raw, elapsed = ollama.generate('http://127.0.0.1:11434', ollama.GENERATOR_MODEL, 'fixture prompt', 1)
        self.assertEqual(raw, '{}')
        self.assertGreaterEqual(elapsed, 0)
        self.assertEqual(payload['options'], {'temperature': 0.2, 'seed': 5418, 'num_ctx': 4096, 'num_predict': 1536})
        self.assertEqual(payload['messages'], [{'role': 'user', 'content': 'fixture prompt'}])
        self.assertFalse(payload['stream'])
        self.assertEqual(payload['keep_alive'], 0)
        request.assert_called_once_with('http://127.0.0.1:11434', '/api/chat', payload)


if __name__ == '__main__':
    unittest.main()
