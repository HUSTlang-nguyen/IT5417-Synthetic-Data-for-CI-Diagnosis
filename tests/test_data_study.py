from datetime import datetime
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock, MagicMock
from contextlib import nullcontext
from ci_demo.common import read_json, write_json, sha256
from ci_demo.data_study import DataStudy, elapsed, tree_bytes
from ci_demo.batch import BudgetStop


class StudyTests(unittest.TestCase):
    def test_collection_waits_for_metadata_scan_without_changing_learning_default(self):
        from ci_demo.experiment import Experiment
        for cls, seconds in [(Experiment, 30), (DataStudy, 120)]:
            study = object.__new__(cls)
            study.lock, study.manifest = Path('fixture.lock'), Path('fixture.json')
            study._check = Mock(return_value=(None, 5))
            with patch('ci_demo.experiment.batch_lock', return_value=nullcontext()) as lock, patch('ci_demo.experiment.read_json', return_value={}):
                self.assertEqual(study.check('metadata'), 5)
                lock.assert_called_once_with(study.lock, wait_seconds=seconds)

    def test_storage_scan_handles_temporary_disappearance_but_not_permission_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            present = root / 'present'
            present.write_bytes(b'1234567')
            gone_file = Mock()
            gone_file.stat.side_effect = FileNotFoundError
            stable_file = Mock()
            stable_file.stat.return_value = present.stat()
            gone_dir = Mock(path=str(root / 'gone'))
            gone_dir.stat.return_value = root.stat()
            scan = MagicMock()
            scan.__enter__.return_value = scan
            scan.__iter__.return_value = iter([gone_file, stable_file, gone_dir])
            with patch('ci_demo.data_study.os.scandir', side_effect=[scan, FileNotFoundError]):
                self.assertEqual(tree_bytes(root), 7)
            denied = Mock()
            denied.stat.side_effect = PermissionError
            scan = MagicMock()
            scan.__enter__.return_value = scan
            scan.__iter__.return_value = iter([denied])
            with patch('ci_demo.data_study.os.scandir', return_value=scan):
                with self.assertRaises(PermissionError):
                    tree_bytes(root)

    def test_union_and_unfinished_intervals_charge_without_budget_reset(self):
        state={'preledger_charge_seconds':300,'operations':{
            'a':{'reserved_at':'2026-01-01T00:00:00+00:00','finished_at':'2026-01-01T00:00:10+00:00'},
            'b':{'reserved_at':'2026-01-01T00:00:05+00:00','finished_at':'2026-01-01T00:00:15+00:00'},
            'c':{'reserved_at':'2026-01-01T00:00:20+00:00'}}}
        self.assertEqual(elapsed(state,datetime.fromisoformat('2026-01-01T00:00:30+00:00')),325)
        self.assertEqual(elapsed(state,datetime.fromisoformat('2026-01-01T00:00:40+00:00')),335)

    def test_reservations_resume_caps_and_guards(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);spec=root/'data-manifests/dataset-v2.json'
            write_json(spec,{'limits':{'execution_seconds':1000,'new_generator_requests':1,'new_source_cases':1,
                'minimum_free_bytes':0,'maximum_artifact_growth_bytes':1000000}})
            data=root/'artifacts';data.mkdir()
            state={'kind':'dataset_collection_v2','specification_sha256':sha256(spec),'status':'running',
                'execution_limit_seconds':1000,'preledger_charge_seconds':300,'operations':{},
                'request_limits':{'generator_7b':1,'diagnoser_3b':0},'execution_enabled':True,'pending_gates':[],
                'artifact_baseline':[{'path':str(data),'bytes':0}]}
            file=root/'runs/fixture/manifest.json';write_json(file,state)
            with patch('ci_demo.data_study.ROOT',root),patch('ci_demo.data_study.CACHE',root/'.cache'):
                study=DataStudy('fixture')
                first=study.reserve('call','synthetic',request_role='generator_7b',timeout=1)
                with self.assertRaises(RuntimeError):study.reserve('call','synthetic',request_role='generator_7b')
                study.finish('call','finished',result={'fixture':True})
                resumed=DataStudy('fixture')
                self.assertEqual(resumed.reserve('call','synthetic')['status'],'finished')
                with self.assertRaises(BudgetStop):resumed.reserve('second','synthetic',request_role='generator_7b')
                with self.assertRaises(ValueError):resumed.reserve('train','training')
                resumed.reserve('real-one','real_reproduction');resumed.finish('real-one','failed')
                self.assertGreater(resumed.check('real_reproduction'),0)
                with self.assertRaises(BudgetStop):resumed.reserve('real-two','real_reproduction')
                state=read_json(file);state['execution_enabled']=False;write_json(file,state)
                with self.assertRaises(BudgetStop):resumed.check('synthetic')
                state['preledger_charge_seconds']=1001;write_json(file,state)
                with self.assertRaises(BudgetStop):resumed.check('audit')
                state['preledger_charge_seconds']=300;write_json(file,state)
                (data/'oversized').write_bytes(b'x'*1000000)
                with self.assertRaises(BudgetStop):resumed.check('audit')
                self.assertEqual(tree_bytes(data),1000000)
                state['specification_sha256']='wrong';write_json(file,state)
                with self.assertRaises(ValueError):resumed.check('audit')

    def test_preparation_subcommands_keep_time_free_space_and_admission_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);spec=root/'data-manifests/dataset-v2.json';data=root/'artifacts';data.mkdir()
            limits={'execution_seconds':1000,'new_generator_requests':1,'new_source_cases':2,
                    'minimum_free_bytes':1,'maximum_artifact_growth_bytes':100}
            write_json(spec,{'limits':limits})
            state={'kind':'dataset_collection_v2','specification_sha256':sha256(spec),'status':'running',
                'execution_limit_seconds':1000,'preledger_charge_seconds':300,'operations':{},
                'request_limits':{'generator_7b':1,'diagnoser_3b':0},'execution_enabled':True,'pending_gates':[],
                'artifact_baseline':[{'path':str(data),'bytes':0}]}
            file=root/'runs/fixture/manifest.json';write_json(file,state)
            with patch('ci_demo.data_study.ROOT',root),patch('ci_demo.data_study.CACHE',root/'.cache'):
                study=DataStudy('fixture')
                with self.assertRaisesRegex(ValueError,'admitted'):study.check_prepare_step()
                study.reserve('real-one','real_reproduction')
                (data/'growth').write_bytes(b'x'*100)
                with patch('ci_demo.data_study.tree_bytes',side_effect=AssertionError('No repeat tree scan within preparation')):
                    self.assertGreater(study.check_prepare_step(timeout=1),0)
                with self.assertRaises(BudgetStop):study.check('real_reproduction')
                with self.assertRaises(BudgetStop):study.reserve('real-two','real_reproduction')
                with patch('ci_demo.data_study.shutil.disk_usage') as usage:
                    usage.return_value.free=0
                    with self.assertRaises(BudgetStop):study.check_prepare_step()
                current=read_json(file);current['execution_enabled']=False;write_json(file,current)
                with self.assertRaises(BudgetStop):study.check_prepare_step()
                current['execution_enabled']=True;current['preledger_charge_seconds']=1001;write_json(file,current)
                with self.assertRaises(BudgetStop):study.check_prepare_step()
