"""Inert fixture backends exercise manual startup/resume; no research model or GPU runs."""
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch
import importlib.util

from ci_demo.common import read_json, sha256, write_json
from ci_demo.dataset import selection_hash
from ci_demo.experiment import manual_learning_experiment
from ci_demo.learning import lock_reviewed_pilot
from ci_demo.sft import CHECKPOINT_FILES, train_sft
from ci_demo.synthetic_experiment import gpu_trace


class ManualTrainingTests(unittest.TestCase):
    def test_check_command_never_starts_study_or_loads_model(self):
        from ci_demo.sft import main
        with patch('sys.argv',['sft','--manual','--check']), \
             patch('ci_demo.learning.check_prepared_pilot',return_value={'status':'fixture_ready'}) as check, \
             patch('ci_demo.sft.manual_learning_experiment') as start, \
             patch('ci_demo.sft.load_model') as load:
            main()
        check.assert_called_once();start.assert_not_called();load.assert_not_called()

    def test_resume_rejects_wrong_identity_before_model_operation(self):
        from ci_demo.sft import _run_learning
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);dataset=root/'dataset.json';write_json(dataset,{'status':'locked'})
            study=root/'study';study.mkdir();write_json(study/'diagnoser-model.json',{'repo_id':'fixture','revision':'fixture'})
            write_json(study/'diagnoser-file-sha256.json',{'fixture':True});write_json(study/'manifest.json',{'operations':{}})
            run=root/'wrong-run';run.mkdir();write_json(run/'manifest.json',{'kind':'diagnosis_learning','config':{'model':'M5'}})
            exp=Mock(folder=study,manifest=study/'manifest.json')
            with patch('ci_demo.sft.run_path',return_value=run),patch('ci_demo.sft.load_model') as load:
                with self.assertRaisesRegex(ValueError,'identity mismatch'):
                    _run_learning(dataset,'M2',context=2048,resume=run.name,experiment=exp,smoke=False)
            load.assert_not_called();exp.reserve.assert_not_called()

    def test_reviewed_lock_reuses_exact_parent_subset_and_rejects_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cache=root/'.cache';folder=cache/'dataset-v1/fixture';folder.mkdir(parents=True)
            for name in ['input','reference','assessment']:write_json(folder/(name+'.json'),{'fixture':name})
            meta={name+'_sha256':sha256(folder/(name+'.json')) for name in ['input','reference','assessment']}
            write_json(folder/'manifest.json',meta)
            record={'sample_id':'fixture','directory':str(folder.resolve()),'manifest_sha256':sha256(folder/'manifest.json'),'group_id':'train'}
            parent={'status':'evidence_checked_group_review_pending','records':[record],
                    'cross_split_groups':[],'exact_source_duplicate_families':[],'exact_candidate_duplicate_families':[],'lexical_edit_suggestions':[]}
            audit=root/'audit.json';write_json(audit,parent)
            review=root/'review.json';write_json(review,{'status':'completed','selection_sha256':selection_hash([record]),
                'reviewed_sample_ids':['fixture'],'semantic_review':'Inert fixture review, not experimental evidence','lexical_family_decisions':[]})
            selection=root/'selection.json';write_json(selection,{'full_audit':{'path':'audit.json','sha256':sha256(audit)},
                'group_review':{'path':'review.json','sha256':sha256(review)},
                'records':[{**record,'directory':folder.relative_to(root).as_posix()}]})
            with patch('ci_demo.learning.ROOT',root),patch('ci_demo.learning.CACHE',cache),patch('ci_demo.learning.check_learning_gate',return_value={'fixture_gate':True}):
                lock=lock_reviewed_pilot(selection,root/'lock.json');self.assertEqual(lock['protocol'],'v1.1')
                self.assertEqual(lock_reviewed_pilot(selection,root/'lock.json'),lock)
                (folder/'reference.json').write_text('changed fixture')
                with self.assertRaises(ValueError):lock_reviewed_pilot(selection,root/'other-lock.json')

    def test_manual_study_starts_once_and_preserves_collection_and_cumulative_caps(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cache=root/'.cache';source=root/'collection';source.mkdir();study=root/'manual-study-fixture';study.mkdir()
            original={'kind':'fixture_collection','deadline':'historical-fixed-deadline'};write_json(source/'manifest.json',original)
            for name in ['diagnoser-model.json','diagnoser-file-sha256.json']:write_json(source/name,{'fixture':name})
            dataset=root/'dataset.json';write_json(dataset,{'status':'locked','protocol':'v1.1','fixture':True})
            spec=root/'data-manifests/training-v1.1.json';write_json(spec,{'protocol':'v1.1','dataset_sha256':sha256(dataset),
                'source_experiment_run_id':'collection','model_metadata_sha256':{name:sha256(source/name) for name in ['diagnoser-model.json','diagnoser-file-sha256.json']}})
            resolver=lambda name: source if name=='collection' else study
            with patch('ci_demo.experiment.ROOT',root),patch('ci_demo.experiment.CACHE',cache),patch('ci_demo.experiment.run_path',side_effect=resolver),patch('ci_demo.experiment.new_run',return_value=study) as create:
                first=manual_learning_experiment(dataset);first.reserve('fixture','training_M2');first.finish('fixture','failed',error='inert fixture')
                again=manual_learning_experiment(dataset);self.assertEqual(first.folder,again.folder);create.assert_called_once()
                state=read_json(again.manifest);self.assertEqual(state['operations']['fixture']['status'],'failed')
                self.assertEqual(state['stage_limits_seconds']['training_M2'],7200);self.assertIsNone(state['deadline'])
                self.assertEqual(read_json(source/'manifest.json'),original)
                changed=read_json(spec);changed['extra']='changed policy';write_json(spec,changed)
                with self.assertRaises(ValueError):manual_learning_experiment(dataset)

    def test_gpu_monitor_collects_details_and_cleans_child_on_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            child=Mock();child.poll.return_value=None
            with patch('ci_demo.synthetic_experiment.subprocess.Popen',return_value=child) as launch:
                with self.assertRaisesRegex(RuntimeError,'fixture-stop'):
                    with gpu_trace(Path(tmp),detailed=True):raise RuntimeError('fixture-stop')
            self.assertIn('temperature.gpu',launch.call_args.args[0][1])
            child.terminate.assert_called_once();child.wait.assert_called_once()

    @unittest.skipUnless(importlib.util.find_spec('peft'), 'Run inert backend integration in isolated ML environment')
    def test_sft_resumes_trainer_state_without_repeating_completed_validation(self):
        import torch
        import transformers, peft
        _ = transformers.Trainer, transformers.TrainingArguments, transformers.TrainerCallback
        calls=[];validations=[];weights={'fixture':torch.tensor([1.0])}
        class Model:
            config=SimpleNamespace(use_cache=True)
            def eval(self):return self
            def train(self):return self
        class Arguments:
            def __init__(self,**kwargs):self.__dict__.update(kwargs)
            def to_dict(self):return self.__dict__
        class Trainer:
            def __init__(self,model,args,train_dataset,data_collator,callbacks):self.args=args;self.callbacks=callbacks
            def train(self,resume_from_checkpoint=None):
                calls.append(resume_from_checkpoint)
                step=104 if resume_from_checkpoint else 52
                state=SimpleNamespace(global_step=step,epoch=1.0);control=SimpleNamespace(should_save=False)
                checkpoint=Path(self.args.output_dir)/('checkpoint-'+str(step));checkpoint.mkdir(parents=True)
                for name in CHECKPOINT_FILES:
                    if name not in {'experiment-config.json','exposures.json'}:write_json(checkpoint/name,{'fixture':name})
                write_json(checkpoint/'trainer_state.json',{'global_step':step})
                for cb in self.callbacks:
                    cb.on_train_begin(self.args,state,control);cb.on_step_begin(self.args,state,control)
                    cb.on_step_end(self.args,state,control);cb.on_log(self.args,state,control,logs={'loss':1.0})
                    cb.on_save(self.args,state,control)
                if resume_from_checkpoint is None:raise KeyboardInterrupt('inert interruption after checkpoint52')
                return SimpleNamespace(metrics={'fixture':True})
            def save_state(self):pass
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);folder=root/'run';folder.mkdir();exp=Mock()
            rows=[{'role':'train'}]*276;train=[{'sample_id':'fixture','origin':'real_local_reconstruction'}]
            def predict(experiment,model,tokenizer,validation,path,**kwargs):
                validations.append(path.name);write_json(path/'metrics.json',{'joint_top1':0.5});return {'joint_top1':0.5}
            with patch('ci_demo.sft.ROOT',root),patch('ci_demo.sft.training_example',return_value={'input_ids':[1],'labels':[1]}), \
                 patch('ci_demo.sft.load_model',side_effect=lambda _: (Model(),None)), \
                 patch('transformers.Trainer',Trainer),patch('transformers.TrainingArguments',Arguments), \
                 patch('peft.prepare_model_for_kbit_training',side_effect=lambda model,**kwargs:model), \
                 patch('peft.get_peft_model',side_effect=lambda model,*args:model), \
                 patch('peft.set_peft_model_state_dict') as restore, \
                 patch('peft.PeftModel.from_pretrained',return_value=Model()), \
                 patch('peft.get_peft_model_state_dict',return_value=weights), \
                 patch('safetensors.torch.load_file',return_value=weights), \
                 patch('ci_demo.sft.predict_rows',side_effect=predict), \
                 patch('torch.cuda.reset_peak_memory_stats'),patch('torch.cuda.max_memory_allocated',return_value=0), \
                 patch('torch.cuda.max_memory_reserved',return_value=0),patch('torch.cuda.empty_cache'):
                with self.assertRaises(KeyboardInterrupt):train_sft(exp,{'local_dir':'fixture'},None,rows,train,[],folder,'training_M2',{'model':'M2'})
                result=train_sft(exp,{'local_dir':'fixture'},None,rows,train,[],folder,'training_M2',{'model':'M2'},resume=True,invocation='fixture-resume')
            self.assertEqual(calls[0],None);self.assertTrue(calls[1].endswith('checkpoint-52'))
            self.assertEqual(validations,['validation-step-52','validation-step-104']);restore.assert_called_once()
            self.assertEqual(result['updates'],104);self.assertTrue(result['reload_verified'])
            self.assertTrue((folder/'checkpoints/checkpoint-52/checkpoint-evidence.json').is_file())


if __name__=='__main__':unittest.main()
