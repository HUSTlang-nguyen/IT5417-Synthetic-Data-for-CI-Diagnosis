"""Read-only scoring audit and paired error analysis of one completed evaluation."""
from collections import Counter
from datetime import datetime
from pathlib import Path
import argparse
import json

from .common import ROOT, read_json, write_json, sha256, run_path, now
from .diagnosis import evaluate, locations, functions


def flags(reference, prediction):
    counts = evaluate([reference], {reference['sample_id']: prediction})['counts']
    visible = bool(set(locations(reference.get('locations'), limit=None)) & set(locations(reference.get('retrieved_locations'))))
    direct_match = (not counts['invalid_output'] and isinstance(prediction, dict)
                    and bool(set(locations(reference.get('locations'), limit=None)) & set(locations(prediction.get('locations'))[:1])))
    groups = []
    if counts['invalid_output']:groups.append('format_or_schema_failure')
    if counts['unknown_output']:groups.append('abstention')
    if not visible:groups.append('reference_function_absent_from_retrieved_context')
    if not counts['invalid_output'] and not counts['classification_correct']:groups.append('classification_disagreement_with_silver')
    if direct_match and not counts['function_top1_correct']:groups.append('reference_match_not_counted_due_to_visibility_gate')
    if visible and not counts['invalid_output'] and not counts['function_top1_correct'] and not direct_match:groups.append('localization_mismatch_with_visible_reference')
    return {'classification_correct': bool(counts['classification_correct']),
            'file_top1_correct': bool(counts['file_top1_correct']),
            'function_top1_correct': bool(counts['function_top1_correct']),
            'joint_top1_correct': bool(counts['joint_top1_correct']),
            'invalid': bool(counts['invalid_output']), 'unknown': bool(counts['unknown_output']),
            'reference_function_visible': visible, 'direct_reference_pair_match_for_diagnosis_only': direct_match, 'diagnostic_groups': groups,
            'predicted_type': prediction.get('cause_type') if isinstance(prediction, dict) else None,
            'predicted_locations': prediction.get('locations') if isinstance(prediction, dict) else None}


def paired(cases, field):
    counts = Counter({'both_correct': 0, 'm2_only': 0, 'm5_only': 0, 'both_wrong': 0})
    for row in cases:
        left, right = row['models']['M2'][field], row['models']['M5'][field]
        counts['both_correct' if left and right else 'm2_only' if left else 'm5_only' if right else 'both_wrong'] += 1
    return dict(counts)


def costs(root, spec):
    result = {}
    for name, record in spec['trained_model_lock']['models'].items():
        manifest = read_json(run_path(record['run_id'])/'manifest.json')
        wall = (datetime.fromisoformat(manifest['finished_at'])-datetime.fromisoformat(manifest['created_at'])).total_seconds()
        result[name] = {'source_run_id':record['run_id'],'source_wall_seconds':wall,
                        'cost_lineage':manifest.get('cost_lineage'),
                        'training_input_tokens':manifest.get('training',{}).get('input_tokens'),
                        'training_target_tokens':manifest.get('training',{}).get('target_tokens'),
                        'training_example_exposures':manifest.get('training',{}).get('examples')}
    phases = {}
    for folder in root.iterdir():
        if not folder.is_dir() or not folder.name.startswith(('test-','validation-')):continue
        values = [read_json(p) for p in folder.glob('*/result.json')]
        phases[folder.name] = {'returned_requests':len(values),
            'inference_seconds':sum(v['seconds'] for v in values),
            'input_tokens':sum(v['input_tokens'] for v in values),
            'output_tokens':sum(v['output_tokens'] for v in values),
            'peak_allocated_bytes':max((v['peak_allocated_bytes'] for v in values),default=None),
            'peak_reserved_bytes':max((v['peak_reserved_bytes'] for v in values),default=None),
            'phase_runtime':read_json(folder/'runtime.json') if (folder/'runtime.json').exists() else None}
    return {'sources':result,'new_evaluation_phases':phases,
        'qualification':'Training sources include parent and continuation via cost_lineage; never add nested validation time twice. Inference sums exclude load; phase wall includes load. CUDA reserved is not physical VRAM. No monetary cost invented.'}


def reference_evidence(meta, reference, export):
    """Inspect source and saved local logs, never run candidate/source code."""
    rep = run_path(meta['run_id'])
    missing, changed, checked = [], [], []
    for name, expected in meta['evidence_hashes'].items():
        path = rep / name
        if not path.is_file(): missing.append(str(path))
        elif sha256(path) != expected: changed.append(str(path))
        else: checked.append(str(path.relative_to(ROOT)))
    raw = read_json(rep / 'manifest.json')
    source = raw['source']; patches = []
    for key in ['repair_patch', 'test_patch']:
        if key in source:
            path = ROOT / source[key]
            if not path.is_file(): missing.append(str(path))
            elif sha256(path) != source[key + '_sha256']: changed.append(str(path))
            else: patches.append(str(path.relative_to(ROOT)))
    inventory = raw['environment'].get('inventories', {}).get('base', {})
    context = Path(raw['environment']['context']) / 'base'
    cause_sources = []
    for location in reference['locations']:
        path = context / location['file']
        info = {'file': location['file'], 'function': location['function'], 'path': str(path), 'line': None}
        if not path.is_file() or not path.resolve().is_relative_to(context.resolve()):
            missing.append(str(path));info['status'] = 'source_missing'
        else:
            expected = inventory.get(location['file'])
            info['hash_verified'] = isinstance(expected, str) and sha256(path) == expected
            if expected and isinstance(expected, str) and sha256(path) != expected:
                changed.append(str(path))
            text = path.read_text(encoding='utf-8', errors='replace')
            try: spans = functions(text)
            except (SyntaxError, ValueError): spans = []
            found = next((r for r in spans if r[0] == location['function']), None)
            info.update(line=found[1] if found else 1 if location['function']=='<module>' else None,
                        status='definition_present' if found else 'module_cause' if location['function']=='<module>' else 'definition_absent_in_base_requires_patch_context')
        cause_sources.append(info)
    return {'export': str(export), 'reproduction_run': rep.name, 'source_commit': meta['source_commit'],
            'checked_artifacts': checked, 'checked_patches': patches, 'cause_sources': cause_sources,
            'missing': missing, 'changed': changed,
            'qualification': 'Saved local reproduction, not historical CI telemetry. Hash matches do not certify silver labels.'}


def report(run_id):
    root = run_path(run_id); state = read_json(root / 'manifest.json')
    if state['status'] != 'evaluation_finished':
        raise ValueError('Report only after all frozen phases finish')
    for relative, expected in state['phase_commitments'].items():
        path = ROOT / relative
        if sha256(path) != expected: raise ValueError('Evaluation phase commitment changed')
        for name, value in read_json(path)['files'].items():
            if sha256(ROOT / name) != value: raise ValueError('Evaluation raw/metric artifact changed')
    lock = read_json(root / 'final-test-lock.json')
    spec = read_json(ROOT / 'data-manifests/evaluation-v1.json')
    if sha256(ROOT/'data-manifests/evaluation-v1.json') != state['specification_sha256']:
        raise ValueError('Evaluation spec changed')
    records = read_json(ROOT / spec['dataset_path'])['records']
    exports = {r['sample_id']: Path(r['directory']) for r in records if r['role']=='test'}
    cached = {r['sample_id']: r['prepared'] for r in read_json(run_path(spec['run_ids'][0])/'prepared-inputs.json') if r['role']=='test'}
    predictions = {name: read_json(root/('test-'+name)/'predictions.json') for name in ['M0','M1-P2','M2','M5']}
    references, cases = [], []
    for item in lock['test_samples']:
        sid=item['sample_id'];export=exports[sid];meta=read_json(export/'manifest.json')
        for name in ['input','reference','assessment']:
            if sha256(export/(name+'.json')) != meta[name+'_sha256']:raise ValueError('Export text changed')
        if cached[sid]['prompt_sha256'] != item['original_prompt_sha256']:raise ValueError('User context differs')
        ref={**read_json(export/'reference.json'),'retrieved_locations':cached[sid]['retrieved_locations_after_tokenization']}
        assessment=read_json(export/'assessment.json');references.append(ref)
        cases.append({'sample_id':sid,'repo':meta['repo'],'reference_type':ref['cause_type'],
            'reference_locations':ref['locations'],'causal_explanation_silver':ref['explanation'],
            'assessment_confidence':assessment.get('confidence'),'assessment_limitations':assessment.get('limitations'),
            'human_gold':ref.get('human_gold','pending'),
            'models':{name:flags(ref,values.get(sid)) for name,values in predictions.items()},
            'evidence':reference_evidence(meta,ref,export)})
    recomputed={name:evaluate(references,values) for name,values in predictions.items()}
    for name,metric in state['models'].items():
        for key in ['macro_f1','classification_accuracy'] if name=='M0' else ['macro_f1','classification_accuracy','file_top1','function_top1','joint_top1']:
            if metric[key] != recomputed[name][key]:raise ValueError('Saved test score does not recompute')
    result={'recorded_at':now(),'run_id':run_id,'test_denominator':len(cases),'test_metrics':state['models'],
            'validation_m1_p2':state['validation']['M1-P2'],
            'paired_m2_m5':{key:paired(cases,key) for key in ['classification_correct','function_top1_correct','joint_top1_correct']},
            'reference_support':dict(Counter(r['cause_type'] for r in references)),
            'by_repo':{repo:{name:evaluate([r for r in references if r['sample_id'] in {c['sample_id'] for c in cases if c['repo']==repo}],
                {sid:v for sid,v in values.items() if sid in {c['sample_id'] for c in cases if c['repo']==repo}}) for name,values in predictions.items()} for repo in sorted({c['repo'] for c in cases})},
            'diagnostic_group_counts':{name:dict(Counter(group for row in cases for group in row['models'][name]['diagnostic_groups'])) for name in ['M1-P2','M2','M5']},
            'costs':costs(root,spec),'cases':cases,'qualification':'Strict JSON; M1-P2 prompt differs from M2/M5. Fixed chosen parent104, not epoch10. Silver references; no gold approvals or statistical significance claimed.'}
    output=root/'analysis';write_json(output/'analysis.json',result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',required=True)
    args=parser.parse_args();result=report(args.run)
    print(json.dumps({'run_id':result['run_id'],'paired_m2_m5':result['paired_m2_m5'],'case_count':len(result['cases'])}))


if __name__=='__main__':main()
