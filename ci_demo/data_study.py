"""Persistent v2 collection guards, reusing the existing reservation/finish protocol."""
from datetime import datetime
import math
import os
from pathlib import Path
import shutil
import stat

from .batch import BudgetStop, batch_lock
from .common import CACHE, ROOT, now, read_json, sha256
from .experiment import Experiment


def tree_bytes(path):
    path = Path(path)
    if not path.exists():
        return 0
    if path.is_symlink():
        raise ValueError('Artifact root must not be a symlink')
    if path.is_file():
        return path.stat().st_size
    total, pending = 0, [path]
    while pending:
        try:
            entries = os.scandir(pending.pop())
        except FileNotFoundError:
            continue
        with entries:
            for entry in entries:
                try:
                    info = entry.stat(follow_symlinks=False)
                except FileNotFoundError:
                    continue
                if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0) & 0x400:
                    continue
                if stat.S_ISDIR(info.st_mode):
                    pending.append(entry.path)
                else:
                    total += info.st_size
    return total


def elapsed(state, timestamp):
    intervals = sorted((datetime.fromisoformat(r['reserved_at']),
                        datetime.fromisoformat(r['finished_at']) if r.get('finished_at') else timestamp)
                       for r in state['operations'].values())
    used, end = float(state['preledger_charge_seconds']), None
    for left, right in intervals:
        if right < left:
            raise ValueError('Operation timestamps reversed')
        left = max(left, end) if end else left
        used += max(0, (right-left).total_seconds())
        end = max(end, right) if end else right
    return used


class DataStudy(Experiment):
    metadata_lock_wait_seconds = 120

    def __init__(self, run_id):
        self.folder = ROOT/'runs'/run_id
        if not self.folder.resolve().is_relative_to((ROOT/'runs').resolve()):
            raise ValueError('Study path escape')
        self.manifest = self.folder/'manifest.json'
        state = read_json(self.manifest)
        if state.get('kind') != 'dataset_collection_v2':
            raise ValueError('Expected v2 collection study')
        self.lock = CACHE/'experiment-locks'/(run_id+'.lock')
        self.spec_path = ROOT/'data-manifests/dataset-v2.json'

    def reserve(self, operation, stage, *, request_role=None, timeout=0):
        if request_role == 'generator_7b' and (stage != 'synthetic' or timeout > read_json(self.spec_path)['limits'].get('model_seconds',180)):
            raise ValueError('Generator stage/timeout differs from protocol')
        return super().reserve(operation,stage,request_role=request_role,timeout=timeout)

    def before_reservation(self, state, stage):
        if stage == 'real_reproduction' and sum(r['stage']==stage for r in state['operations'].values()) >= read_json(self.spec_path)['limits']['new_source_cases']:
            raise BudgetStop('New source-case limit reached')

    def check_prepare_step(self, *, timeout=180):
        """Preparation was admitted by reserve(); still check time/free space per command."""
        with batch_lock(self.lock, wait_seconds=self.metadata_lock_wait_seconds):
            state = read_json(self.manifest)
            if not any(row['stage'] == 'real_reproduction' and row['status'] == 'reserved'
                       for row in state['operations'].values()):
                raise ValueError('Preparation requires an admitted real-case operation')
            return self._check(state, 'real_reproduction', timeout, scan_artifacts=False)[1]

    def _check(self, state, stage, timeout, *, scan_artifacts=True):
        if isinstance(timeout, bool) or not isinstance(timeout, (float,int)) or not math.isfinite(timeout) or timeout < 0:
            raise ValueError('Invalid timeout')
        if stage not in {'audit','metadata','real_reproduction','synthetic'}:
            raise ValueError('Stage not authorized for collection')
        if state['specification_sha256'] != sha256(self.spec_path):
            raise ValueError('Collection spec changed')
        spec = read_json(self.spec_path)
        limits = spec['limits']
        if state['execution_limit_seconds'] != limits['execution_seconds'] or state['request_limits'] != {
                'generator_7b':limits['new_generator_requests'],'diagnoser_3b':0}:
            raise ValueError('Study budgets differ from locked spec')
        timestamp = datetime.fromisoformat(now())
        remaining = limits['execution_seconds'] - elapsed(state,timestamp)
        if state['status'] not in {'preflight','running'} or remaining <= timeout:
            raise BudgetStop('Collection time exhausted or study terminal')
        if stage in {'real_reproduction','synthetic'} and (not state['execution_enabled'] or state.get('pending_gates')):
            raise BudgetStop('Collection preflight gates incomplete')
        storage = state.get('artifact_baseline')
        if not storage:
            raise BudgetStop('Artifact storage baseline missing')
        growth = 0
        for entry in storage:
            path = Path(entry['path'])
            volume = path.anchor
            if shutil.disk_usage(volume).free < limits['minimum_free_bytes']:
                raise BudgetStop('Artifact/Docker volume free-space gate')
            if scan_artifacts:
                growth += max(0,tree_bytes(path)-entry['bytes'])
        if growth >= limits['maximum_artifact_growth_bytes']:
            raise BudgetStop('Artifact growth limit reached')
        return timestamp,remaining


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true',required=True)
    args=parser.parse_args()
    study=DataStudy(read_json(CACHE/'dataset-v2-active.json')['run_id'])
    print({'run_id':study.folder.name,'audit_remaining_seconds':study.check('audit'),
           'execution_enabled':read_json(study.manifest)['execution_enabled']})
