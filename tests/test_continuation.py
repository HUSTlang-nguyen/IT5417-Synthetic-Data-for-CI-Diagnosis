"""Numeric CPU fixtures only: no diagnoser weights, GPU, Docker or inference."""
from collections import Counter
from pathlib import Path
import importlib.util
import tempfile
import unittest
from unittest.mock import patch

from ci_demo.common import read_json, sha256, write_json
from ci_demo.continuation import ContinuationTrainerMixin, checked_checkpoint, training_plan


class ContinuationTests(unittest.TestCase):
    def lineage_fixture(self,root):
        from ci_demo.sft import CHECKPOINT_FILES,seal_checkpoint
        from ci_demo.continuation import expected_exposures
        from ci_demo.ml import SYSTEM
        dataset=root/'dataset.json';write_json(dataset,{'status':'locked','protocol':'v1.1'})
        parents={}
        base={'base_model':'fixture','base_revision':'fixture','context':2048,'seed':5417,
              'checkpoint_inventory_sha256':'fixture','system_prompt':SYSTEM,'dataset_sha256':sha256(dataset)}
        fields={'max_steps':104,'learning_rate':1e-4,'lora_rank':16,'lora_alpha':32,'lora_dropout':.05,
                'target_modules':'all-linear','batch_size':1,'gradient_accumulation_steps':8,'seed':5417,'context':2048}
        for name in ['M0','M1','M2','M5']:
            folder=root/'runs'/('parent-'+name);config={**base,'model':name}
            manifest={'kind':'diagnosis_learning','config':config,'status':'training_finished' if name in ['M2','M5'] else 'validation_finished','reload_verified':True}
            if name=='M0':
                write_json(folder/'classifier.joblib',{'inert':True});manifest['classifier_sha256']=sha256(folder/'classifier.joblib')
            write_json(folder/'manifest.json',manifest)
            if name in ['M2','M5']:
                plan=training_plan(name);ids=list(map(str,range(plan['train_examples'])))
                write_json(folder/'training-config.json',fields);write_json(folder/'training-sample-ids.json',ids)
                choices=[]
                for step in [52,104]:
                    p=folder/'checkpoints'/('checkpoint-'+str(step))
                    for f in CHECKPOINT_FILES:write_json(p/f,{'inert':f})
                    write_json(p/'trainer_state.json',{'global_step':step})
                    write_json(p/'experiment-config.json',fields)
                    write_json(p/'exposures.json',{'exposures':expected_exposures(ids,step,plan)})
                    seal_checkpoint(p)
                    metric=folder/('validation-'+str(step)+'.json');write_json(metric,{'joint_top1':.1})
                    choices.append({'step':step,'joint_top1':.1,'checkpoint':str(p.relative_to(root)),
                        'metrics_path':str(metric.relative_to(root)),'metrics_sha256':sha256(metric)})
                write_json(folder/'checkpoint-selection.json',{'candidates':choices,'selected':choices[0]})
            parents[name]={'run_id':folder.name,'files':{str(p.relative_to(root)):sha256(p) for p in folder.rglob('*') if p.is_file()}}
        spec={'protocol':'v1.2','dataset_sha256':sha256(dataset),'parents':parents,
              'plans':{n:training_plan(n) for n in ['M2','M5']},
              'stage_limits_seconds':{'training_each':10800,'training_M2':10800,'training_M5':10800,'evaluation':7200}}
        path=root/'data-manifests/training-v1.2.json';write_json(path,spec)
        runs=['parent-M0','parent-M1']
        for name in ['M2','M5']:
            folder=root/'runs'/('child-'+name);parent=root/'runs'/('parent-'+name)
            cfg={**base,'model':name,'training_protocol':'v1.2','continuation':training_plan(name),
                 'parent_run_id':parent.name,'specification_sha256':sha256(path)}
            chosen=read_json(parent/'checkpoint-selection.json')['selected']
            checkpoint=root/chosen['checkpoint'];plan=training_plan(name)
            write_json(folder/'checkpoint-selection.json',{'selected':chosen})
            write_json(folder/'training-config.json',{**fields,**cfg,'max_steps':plan['max_steps'],'learning_rate':2e-5})
            write_json(folder/'manifest.json',{'kind':'diagnosis_learning','config':cfg,'status':'training_finished',
                'reload_verified':True,'selected_checkpoint':str(checkpoint.relative_to(root)),
                'updates':plan['max_steps'],'training':{'examples':plan['train_examples']*10}})
            runs.append(folder.name)
        return dataset,spec,runs

    @unittest.skipUnless(importlib.util.find_spec('torch'), 'Requires isolated ML environment')
    def test_final_lock_accepts_pinned_parent_selection_with_different_update_counts(self):
        from ci_demo.sft import final_model_lock
        from ci_demo.continuation import load_spec
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);dataset,spec,runs=self.lineage_fixture(root)
            with patch('ci_demo.continuation.ROOT',root),patch('ci_demo.sft.ROOT',root), \
                 patch('ci_demo.sft.run_path',side_effect=lambda name:root/'runs'/name):
                self.assertEqual(load_spec(dataset)['protocol'],'v1.2')
                locked=final_model_lock(dataset,runs)
                self.assertEqual(locked['models']['M2']['selected_step'],52)
                child=root/'runs/child-M5/manifest.json';m=read_json(child)
                m['config']['training_protocol']='v1.1';write_json(child,m)
                with self.assertRaises(ValueError):final_model_lock(dataset,runs)
                m['config']['training_protocol']='v1.2';m['updates']=104;write_json(child,m)
                with self.assertRaises(ValueError):final_model_lock(dataset,runs)
                parent=root/'runs/parent-M2/checkpoints/checkpoint-104/optimizer.pt'
                parent.write_bytes(b'changed')
                with self.assertRaises(ValueError):load_spec(dataset)

    def test_exact_plan_and_supported_models(self):
        for name, count, total, remaining, validation in [
            ('M2',175,220,116,[132,176,220]), ('M5',276,350,246,[210,280,350])]:
            p=training_plan(name)
            self.assertEqual((p['train_examples'],p['max_steps'],p['remaining_updates'],p['validation_steps']),
                             (count,total,remaining,validation))
        for name in ['M0','M1','other']:
            with self.assertRaises(ValueError):training_plan(name)

    def test_v12_check_cannot_start_study_or_model(self):
        from ci_demo.sft import main
        with patch('sys.argv',['sft','--manual','--protocol','v1.2','--check']), \
             patch('ci_demo.continuation.check_ready',return_value={'fixture':True}), \
             patch('ci_demo.sft.manual_learning_experiment') as start,patch('ci_demo.sft.load_model') as model:
            main()
        start.assert_not_called();model.assert_not_called()

    def test_v12_rejects_legacy_models_smoke_and_context_before_study(self):
        from ci_demo.sft import main
        for arguments in [['--model','M0'],['--model','M1'],['--model','M2','--smoke'],['--model','M2','--context','1024']]:
            with patch('sys.argv',['sft','--manual','--protocol','v1.2']+arguments),patch('ci_demo.sft.manual_learning_experiment') as start:
                with self.assertRaises(SystemExit):main()
                start.assert_not_called()

    def test_parent_checkpoint_rejects_tampered_or_missing_state(self):
        from ci_demo.sft import CHECKPOINT_FILES,seal_checkpoint
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            for name in CHECKPOINT_FILES:write_json(p/name,{'inert':name})
            seal_checkpoint(p);checked_checkpoint(p)
            (p/'optimizer.pt').write_bytes(b'changed')
            with self.assertRaises(ValueError):checked_checkpoint(p)
            (p/'scheduler.pt').unlink()
            with self.assertRaises((ValueError,FileNotFoundError)):checked_checkpoint(p)

    @unittest.skipUnless(importlib.util.find_spec('transformers'), 'Requires isolated ML environment')
    def test_real_cpu_trainer_preserves_optimizer_rng_data_and_scheduler_across_two_resumes(self):
        import torch
        from transformers import Trainer,TrainingArguments,TrainerCallback

        class NumericModel(torch.nn.Module):
            def __init__(self):
                super().__init__();self.weight=torch.nn.Parameter(torch.tensor([0.4]))
            def forward(self,input_ids,labels=None):
                return {'loss':(self.weight * input_ids.float()/1000).square().mean()+torch.rand(())*0.001}

        class CounterTrainer(ContinuationTrainerMixin,Trainer):
            def compute_loss(self,model,inputs,return_outputs=False,**kwargs):
                ids=inputs.pop('sample_ids').tolist();self.seen.update(ids)
                return super().compute_loss(model,inputs,return_outputs=return_outputs,**kwargs)
            def _load_optimizer_and_scheduler(self,checkpoint):
                super()._load_optimizer_and_scheduler(checkpoint)
                if checkpoint is None:return
                saved=torch.load(Path(checkpoint)/'optimizer.pt',map_location='cpu',weights_only=True)
                actual=next(iter(self.optimizer.state.values()));expected=next(iter(saved['state'].values()))
                for key in ['step','exp_avg','exp_avg_sq']:
                    torch.testing.assert_close(actual[key],expected[key])
                self.restored_optimizer=True
            def _load_rng_state(self,checkpoint):
                super()._load_rng_state(checkpoint)
                saved=torch.load(Path(checkpoint)/'rng_state.pth',weights_only=False,map_location='cpu')
                assert torch.equal(torch.get_rng_state(),saved['cpu'])
                self.restored_rng=True

        class Probe(TrainerCallback):
            def on_train_begin(self,args,state,control,**kwargs):
                self.first_lr=kwargs['optimizer'].param_groups[0]['lr']
                state.save_steps=args.save_steps
            def on_step_end(self,args,state,control,**kwargs):
                if state.global_step==105:self.first_count=sum(self.seen.values())
            def on_save(self,args,state,control,**kwargs):
                if self.stop and state.global_step==self.stop:
                    raise KeyboardInterrupt('CPU fixture interruption after save')

        def arguments(output,total,save,lr):
            return TrainingArguments(output_dir=str(output),max_steps=total,learning_rate=lr,
                per_device_train_batch_size=1,gradient_accumulation_steps=8,seed=5417,data_seed=5417,
                save_strategy='steps',save_steps=save,logging_strategy='no',report_to=[],
                use_cpu=True,bf16=False,disable_tqdm=True,dataloader_num_workers=0,remove_unused_columns=False)

        with tempfile.TemporaryDirectory() as tmp:
            for name in ['M2','M5']:
                p=training_plan(name);root=Path(tmp)/name;data=[{'input_ids':[i+1],'labels':[0.0],'sample_ids':i} for i in range(p['train_examples'])]
                parent=CounterTrainer(model=NumericModel(),args=arguments(root/'parent',104,104,1e-4),train_dataset=data)
                parent.seen=Counter();parent.train();source=root/'parent/checkpoint-104'
                old_hashes={f.name:sha256(f) for f in source.iterdir() if f.is_file()}
                parent_seen=parent.seen.copy();self.assertEqual(sum(parent_seen.values()),828 if name=='M2' else 824)
                probe=Probe();probe.stop=p['steps_per_epoch']*6;probe.seen=parent_seen.copy()
                child=CounterTrainer(model=NumericModel(),args=arguments(root/'child',p['max_steps'],p['steps_per_epoch'],2e-5),train_dataset=data,callbacks=[probe])
                child.seen=probe.seen;child.continuation_plan=p;child.continuation_bootstrap=True;child.continuation_folder=root/'child'
                with self.assertRaises(KeyboardInterrupt):child.train(resume_from_checkpoint=str(source))
                self.assertAlmostEqual(probe.first_lr,2e-5)
                self.assertEqual(probe.first_count-sum(parent_seen.values()),8 if name=='M2' else 4)
                self.assertTrue(child.restored_optimizer and child.restored_rng)
                checkpoint=root/'child'/('checkpoint-'+str(probe.stop))
                probe2=Probe();probe2.stop=None;probe2.seen=child.seen.copy()
                resumed=CounterTrainer(model=NumericModel(),args=arguments(root/'resumed',p['max_steps'],p['steps_per_epoch'],2e-5),train_dataset=data,callbacks=[probe2])
                resumed.seen=probe2.seen;resumed.continuation_plan=p;resumed.continuation_bootstrap=False
                resumed.train(resume_from_checkpoint=str(checkpoint))
                self.assertAlmostEqual(probe2.first_lr,2e-5*(1-(probe.stop-104)/p['remaining_updates']))
                self.assertTrue(resumed.restored_optimizer and resumed.restored_rng)
                self.assertEqual(resumed.state.global_step,p['max_steps']);self.assertEqual(resumed.state.epoch,10)
                self.assertEqual(set(resumed.seen.values()),{10});self.assertEqual(sum(resumed.seen.values()),p['train_examples']*10)
                self.assertAlmostEqual(resumed.optimizer.param_groups[0]['lr'],0)
                self.assertEqual({f.name:sha256(f) for f in source.iterdir() if f.is_file()},old_hashes)


if __name__=='__main__':unittest.main()
