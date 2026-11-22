"""Byte-preserving portable dataset exports; no source execution or model loading."""
import argparse
from collections import Counter
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile

from .common import read_json, sha256, write_json

FILES = ('input.json', 'reference.json', 'assessment.json', 'manifest.json')


def checked_file(root, relative):
    path = PurePosixPath(relative)
    if path.is_absolute() or '..' in path.parts or '\\' in relative or ':' in relative:
        raise ValueError('Unsafe package path')
    target = root.joinpath(*path.parts)
    if not target.resolve().is_relative_to(root.resolve()) or any(p.is_symlink() for p in [target, *target.parents]):
        raise ValueError('Package path escapes or uses symlink')
    if not target.is_file():
        raise ValueError('Missing package file: ' + relative)
    return target


def verify(folder):
    folder = Path(folder).resolve()
    package = read_json(folder / 'package.json')
    if package.get('schema') != 'ci-diagnosis-portable-v1':
        raise ValueError('Unknown portable schema')
    ids, counts, expected = set(), Counter(), {'package.json'}
    for row in package['records']:
        identity = row['sample_id']
        if not re.fullmatch(r'[A-Za-z0-9_.-]+', identity) or identity in ids:
            raise ValueError('Invalid or duplicate sample ID')
        ids.add(identity)
        if row['role'] not in {'train', 'validation', 'test'}:
            raise ValueError('Unknown split')
        if set(row['files']) != set(FILES):
            raise ValueError('Incomplete record')
        for name, digest in row['files'].items():
            relative = 'records/' + identity + '/' + name
            p = checked_file(folder, relative)
            if p.stat().st_size > 10 * 1024**2 or sha256(p) != digest:
                raise ValueError('Changed or oversized record: ' + identity)
            expected.add(relative)
        base = folder / 'records' / identity
        meta, reference = read_json(base / 'manifest.json'), read_json(base / 'reference.json')
        if meta['sample_id'] != identity or reference['sample_id'] != identity or meta['role'] != row['role']:
            raise ValueError('Record identity or split mismatch')
        for kind in ('input', 'reference', 'assessment'):
            if meta[kind + '_sha256'] != row['files'][kind + '.json']:
                raise ValueError('Source record hash mismatch')
        if set(read_json(base / 'input.json')) != {'execution_log', 'code'}:
            raise ValueError('Input/reference boundary mismatch')
        if reference['quality'] != 'silver':
            raise ValueError('Unexpected label quality')
        counts[row['role'] + '/' + meta['origin']] += 1
    actual = {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}
    for relative, digest in package.get('attachments', {}).items():
        if relative in expected:
            raise ValueError('Attachment collides with record or package manifest')
        p = checked_file(folder, relative)
        if p.stat().st_size > 10 * 1024**2 or sha256(p) != digest:
            raise ValueError('Changed or oversized attachment')
        expected.add(relative)
    if actual != expected or sum((folder / p).stat().st_size for p in actual) > 100 * 1024**2:
        raise ValueError('Unexpected package files or oversized package')
    if dict(counts) != package['counts']:
        raise ValueError('Package denominator mismatch')
    return {'records': len(ids), 'counts': dict(counts), 'source_lock_sha256': package['source_lock_sha256'],
            'publication': package['publication']}


def export(source_lock, destination):
    source_lock, destination = Path(source_lock), Path(destination)
    lock = read_json(source_lock)
    if lock.get('status') != 'locked' or lock.get('protocol') != 'v1.1':
        raise ValueError('Expected immutable v1.1 lock')
    if destination.exists():
        raise ValueError('Destination exists; never overwrite a snapshot')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as tmp:
        staging = Path(tmp) / 'package'
        staging.mkdir()
        records, counts = [], Counter()
        for row in lock['records']:
            identity = row['sample_id']
            if not re.fullmatch(r'[A-Za-z0-9_.-]+', identity):
                raise ValueError('Unsafe sample ID')
            source = Path(row['directory'])
            if sha256(source / 'manifest.json') != row['manifest_sha256']:
                raise ValueError('Changed source metadata')
            target = staging / 'records' / identity
            target.mkdir(parents=True)
            for name in FILES:
                shutil.copyfile(source / name, target / name)
            meta = read_json(source / 'manifest.json')
            details = meta.get('injected_by', {}).get('model_info', {}).get('details', {})
            transformations = []
            if 'modelfile' in details:
                # Ollama's build description embeds local paths; it is not diagnosis input.
                del details['modelfile']
                transformations = ['omit injected_by.model_info.details.modelfile from portable metadata']
                write_json(target / 'manifest.json', meta)
            counts[row['role'] + '/' + meta['origin']] += 1
            records.append({'sample_id': identity, 'role': row['role'], 'group_id': row['group_id'],
                            'source_manifest_sha256': row['manifest_sha256'], 'transformations': transformations,
                            'files': {name: sha256(target / name) for name in FILES}})
        write_json(staging / 'package.json', {'schema': 'ci-diagnosis-portable-v1',
            'source_protocol': 'v1.1', 'source_lock_sha256': sha256(source_lock),
            'publication': 'pending_license_attribution_privacy_audit',
            'records': records, 'counts': dict(counts)})
        result = verify(staging)
        staging.rename(destination)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', type=Path)
    parser.add_argument('--source-lock', type=Path)
    parser.add_argument('--destination', type=Path)
    args = parser.parse_args()
    if args.check and not (args.source_lock or args.destination):
        print(verify(args.check))
    elif args.source_lock and args.destination and not args.check:
        print(export(args.source_lock, args.destination))
    else:
        parser.error('Use --check PACKAGE or --source-lock LOCK --destination NEW_PACKAGE')


if __name__ == '__main__':
    main()
