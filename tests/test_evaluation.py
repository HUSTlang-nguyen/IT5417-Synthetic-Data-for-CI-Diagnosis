"""Frozen evaluation checks use text/tokenizer fixtures, never research inference."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from contextlib import nullcontext
from unittest.mock import Mock, patch

from ci_demo.common import read_json, write_json, sha256
from ci_demo.evaluation import M1_P2, SYSTEM, EvaluationRequests, cached_phase, frozen_rows, gpu_ready
from ci_demo.batch import BudgetStop
from ci_demo.ml import prepare_input
from tests.test_ml import WordTokenizer


class EvaluationTests(unittest.TestCase):
    def test_trial_lock_precedes_test_and_resume_reuses_finished_phases(self):
        from ci_demo.evaluation import run
        from ci_demo.experiment import Experiment
        from transformers import AutoTokenizer
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cache=root/'.cache';study=root/'study';trial=root/'evaluation-fixture'
            write_json(study/'manifest.json',{'kind':'dataset_sft_experiment','status':'running','mode':'manual_learning_v1.2','deadline':None,
                'stage_limits_seconds':{'evaluation':7200},'stage_budget_modes':{'evaluation':'operation_union'},'request_limits':{'diagnoser_3b_inference':1500},'operations':{}})
            write_json(study/'diagnoser-model.json',{'local_dir':'inert-fixture'});write_json(study/'diagnoser-file-sha256.json',{})
            spec={'run_ids':['m0','old-m1'],'experiment_run_id':'study','trained_model_lock':{'fixture':True}}
            path=root/'spec.json';write_json(path,spec)
            called=[];fail_once=[True]
            def fake_phase(experiment,spec,folder,role,name,rows,info):
                phase=folder/(role+'-'+name)
                if (phase/'completed.json').exists():return read_json(phase/'completed.json')['metrics']
                if role=='test':
                    self.assertTrue((folder/'final-test-lock.json').exists());self.assertTrue((study/'final-config-lock.json').exists())
                if name=='M2' and fail_once[0]:fail_once[0]=False;raise RuntimeError('inert load interruption before inference')
                called.append((role,name));write_json(phase/'completed.json',{'metrics':{'fixture':True},'files':{}})
                return {'fixture':True}
            def fake_rows(spec,tokenizer,role):
                return [{'sample_id':str(i),'input_sha256':'input','user_message_sha256':'user',
                         'prepared':{'prompt_sha256':'old'},'prepared_p2':{'prompt_sha256':'new'}} for i in range(37 if role=='validation' else 38)]
            def create(kind):trial.mkdir();return trial
            with patch('ci_demo.evaluation.ROOT',root),patch('ci_demo.evaluation.CACHE',cache), \
                 patch('ci_demo.experiment.CACHE',cache),patch('ci_demo.experiment.run_path',return_value=study), \
                 patch('ci_demo.evaluation.verify_spec',return_value=spec),patch('ci_demo.evaluation.gpu_ready',return_value={}), \
                 patch('ci_demo.evaluation.verify_checkpoint'),patch('ci_demo.evaluation.frozen_rows',side_effect=fake_rows), \
                 patch('ci_demo.evaluation.model_phase',side_effect=fake_phase),patch('ci_demo.evaluation.new_run',side_effect=create), \
                 patch('ci_demo.evaluation.run_path',return_value=trial),patch.object(AutoTokenizer,'from_pretrained',return_value=None):
                with self.assertRaisesRegex(RuntimeError,'inert load'):run(path)
                self.assertEqual(read_json(trial/'manifest.json')['status'],'evaluation_failed')
                result=run(path,resume=trial.name)
                self.assertEqual(result['status'],'evaluation_finished')
                again=run(path,resume=trial.name);self.assertEqual(again,result)
                with self.assertRaises(ValueError):run(path)
            self.assertEqual(called,[('validation','M1-P2'),('test','M0'),('test','M1-P2'),('test','M2'),('test','M5')])

    def test_optional_messages_leave_original_tokenization_unchanged(self):
        t=WordTokenizer();data={'execution_log':'begin '+'log '*1000+'failure','code':[]}
        original=prepare_input(data,t);with_messages=prepare_input(data,t,include_messages=True)
        messages=with_messages.pop('messages')
        self.assertEqual(original,with_messages);self.assertEqual(messages[0]['content'],SYSTEM)
        self.assertIn('failure',messages[1]['content']);self.assertNotEqual(M1_P2,SYSTEM)
        self.assertIn('No ``` fences:',M1_P2)

    def test_frozen_variant_preserves_user_and_retrieval_and_checks_old_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);tokenizer=WordTokenizer();records=[];rows=[];cached=[]
            for i in range(37):
                sid='fixture'+str(i);directory=root/sid
                data={'execution_log':'failure '+str(i),'code':[]};write_json(directory/'input.json',data)
                prepared=prepare_input(data,tokenizer)
                records.append({'sample_id':sid,'directory':sid})
                rows.append({'sample_id':sid,'role':'validation','input_sha256':sha256(directory/'input.json'),'prepared':prepared})
                cached.append({'sample_id':sid,'role':'validation','prepared':prepared})
            dataset=root/'lock.json';write_json(dataset,{'records':records});old=root/'old';write_json(old/'prepared-inputs.json',cached)
            cohort=[{k:r[k] for k in ['sample_id','input_sha256']}|{'prompt_sha256':r['prepared']['prompt_sha256']} for r in rows]
            spec={'dataset_path':'lock.json','run_ids':['m0','old'],'cohorts':{'validation':cohort}}
            with patch('ci_demo.evaluation.ROOT',root),patch('ci_demo.evaluation.run_path',return_value=old),patch('ci_demo.evaluation.load_locked_dataset',return_value=(rows,None)):
                result=frozen_rows(spec,tokenizer,'validation')
                self.assertEqual(result[0]['prepared']['code_retention'],result[0]['prepared_p2']['code_retention'])
                self.assertNotEqual(result[0]['prepared']['prompt_sha256'],result[0]['prepared_p2']['prompt_sha256'])
                cached[0]['prepared']={**cached[0]['prepared'],'prompt_sha256':'changed'};write_json(old/'prepared-inputs.json',cached)
                with self.assertRaises(ValueError):frozen_rows(spec,tokenizer,'validation')

    def test_request_cap_counts_failed_and_unknown_but_allows_existing_reservation(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest=Path(tmp)/'manifest.json';write_json(manifest,{'operations':{
                'trial-'+str(i):{'request_role':'diagnoser_3b_inference','status':'unknown'} for i in range(151)}})
            exp=Mock(manifest=manifest);wrapped=EvaluationRequests(exp,'trial')
            with self.assertRaises(BudgetStop):wrapped.reserve('trial-new','evaluation',request_role='diagnoser_3b_inference')
            exp.reserve.assert_not_called()
            wrapped.reserve('trial-0','evaluation',request_role='diagnoser_3b_inference')
            exp.reserve.assert_called_once()

    def test_cached_phase_refuses_modified_predictions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);write_json(root/'predictions.json',{'fixture':None})
            write_json(root/'completed.json',{'metrics':{'fixture':True},'files':{'predictions.json':sha256(root/'predictions.json')}})
            with patch('ci_demo.evaluation.ROOT',root):
                self.assertEqual(cached_phase(root),{'fixture':True})
                write_json(root/'predictions.json',{'changed':None})
                with self.assertRaises(ValueError):cached_phase(root)

    def test_gpu_guard_does_not_clear_or_interrupt_busy_gpu(self):
        with patch('ci_demo.evaluation.shutil.disk_usage',return_value=Mock(free=30*1024**3)),patch('ci_demo.evaluation.subprocess.run',return_value=Mock(stdout='1000, 99')):
            with self.assertRaises(BudgetStop):gpu_ready()


if __name__=='__main__':unittest.main()
