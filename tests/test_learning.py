"""Learning protocol fixtures; no upstream source, model training or GPU calls."""
import unittest
import importlib.util

from ci_demo.learning import check_group_review, check_learning_gate, fit_classifier, load_locked_dataset, select_checkpoint, training_example, update_budget
from tests.test_ml import WordTokenizer


class LearningTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec("sklearn"), "Run this compatibility fixture in the isolated ML environment")
    def test_actual_m0_vectorizer_fits_train_only(self):
        train = [{"role": "train", "origin": "real_local_reconstruction", "model_text": text,
                  "reference": {"cause_type": label}}
                 for text, label in [("wrong sum value", "logic/value"), ("invalid numerical sum", "logic/value"),
                                     ("invalid string method", "API/type"), ("wrong object type", "API/type")]]
        model = fit_classifier(train)
        model.predict(["heldout_secret_symbol"])
        self.assertNotIn("heldout_secret_symbol", model.named_steps["text"].vocabulary_)

    def test_response_only_loss_and_no_silent_target_truncation(self):
        tokenizer = WordTokenizer()
        tokenizer.eos_token_id = -1
        row = {"sample_id": "fixture", "prepared": {"input_ids": [11, 12, 13], "max_new_tokens": 384},
               "reference": {"cause_type": "logic/value", "locations": [{"file": "a.py", "function": "f"}], "explanation": "reason"}}
        result = training_example(row, tokenizer)
        self.assertEqual(result["labels"][:3], [-100] * 3)
        self.assertEqual(result["labels"][3:], result["input_ids"][3:])
        self.assertEqual(result["labels"][-1], -1)
        row["reference"]["explanation"] = "long explanation " * 400
        with self.assertRaises(ValueError):
            training_example(row, tokenizer)

    def test_joint_checkpoint_selection_ties_choose_earlier_not_class_accuracy(self):
        checkpoints = [{"step": 10, "joint_top1": .2, "accuracy": 1}, {"step": 20, "joint_top1": .3},
                       {"step": 30, "joint_top1": .3}]
        self.assertEqual(select_checkpoint(checkpoints)["step"], 20)
        with self.assertRaises(ValueError):
            select_checkpoint([{"step": 1, "joint_top1": None}])
        self.assertEqual(update_budget([{"role": "train"}] * 350), 132)

    def test_small_dataset_and_heldout_classifier_fit_are_blocked_before_ml_import(self):
        with self.assertRaises(ValueError):
            check_learning_gate([])
        with self.assertRaises(ValueError):
            fit_classifier([{"role": "test", "origin": "real_local_reconstruction"}])

    def test_group_review_is_bound_to_records_not_just_a_completed_flag(self):
        from ci_demo.dataset import selection_hash
        records=[{'sample_id':'fixture','group_id':'repo:example/train','manifest_sha256':'fixture-hash'}]
        review={'status':'completed','selection_sha256':selection_hash(records),
                'reviewed_sample_ids':['fixture'],'semantic_review':'inert fixture review'}
        check_group_review(review,records)
        with self.assertRaises(ValueError):check_group_review({'status':'completed'},records)
        with self.assertRaises(ValueError):check_group_review(review,[{**records[0],'group_id':'changed'}])
        with self.assertRaises(ValueError):check_group_review({**review,'reviewed_sample_ids':[]},records)

    def test_full_size_gate_still_rejects_unmatched_synthetic_or_related_split_leakage(self):
        rows=[]
        for role,count in [('train',175),('validation',37),('test',38)]:
            for index in range(count):
                rows.append({'sample_id':f'{role}-{index}','origin':'real_local_reconstruction',
                    'role':role,'quality':'silver','group_id':role,'repo':'https://github.com/example/'+role,
                    'reference':{'cause_type':'API/type' if index%2 else 'logic/value',
                    'locations':[{'file':'a.py','function':'cause'}]}})
        rows += [{**r,'sample_id':'synthetic-'+r['sample_id'],'origin':'controlled_synthetic'} for r in rows[:175]]
        self.assertEqual(check_learning_gate(rows)['real'],250)
        with self.assertRaises(ValueError):check_learning_gate(rows[:-1])
        rows[175]['group_id']='train'
        with self.assertRaises(ValueError):check_learning_gate(rows)

    def test_v11_explicit_ratio_preserves_legacy_gate_and_model_dependencies(self):
        rows=[{'sample_id':f'{role}-{i}','origin':'real_local_reconstruction','role':role,
               'quality':'silver','group_id':role,'repo':'https://github.com/fixture/'+role,
               'reference':{'cause_type':'API/type' if i%2 else 'logic/value',
                            'locations':[{'file':'fixture.py','function':'cause'}]}}
              for role,n in [('train',175),('validation',37),('test',38)] for i in range(n)]
        for model in ['M0','M1','M2']:
            self.assertEqual(check_learning_gate(rows,protocol='v1.1',model=model)['real'],250)
        with self.assertRaises(ValueError):check_learning_gate(rows,protocol='v1.1',model='M5')
        mixed=rows+[{**r,'sample_id':'synthetic-'+r['sample_id'],'origin':'controlled_synthetic'} for r in rows[:101]]
        self.assertEqual(check_learning_gate(mixed,protocol='v1.1')['synthetic'],101)
        self.assertEqual(update_budget(mixed),104)
        with self.assertRaises(ValueError):check_learning_gate(mixed)
        with self.assertRaises(ValueError):check_learning_gate(mixed[:-1],protocol='v1.1')
        with self.assertRaises(ValueError):check_learning_gate(mixed,protocol='unapproved')
        leaked=[*mixed[:-1],{**mixed[-1],'role':'test'}]
        with self.assertRaises(ValueError):check_learning_gate(leaked,protocol='v1.1',model='M0')


if __name__ == "__main__":
    unittest.main()
