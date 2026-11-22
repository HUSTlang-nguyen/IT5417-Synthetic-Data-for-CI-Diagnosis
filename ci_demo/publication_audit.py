"""Prepare pinned license attribution and privacy findings; never claim legal approval."""
import argparse
from pathlib import Path
import re
import shutil
import tempfile

from .common import ROOT, read_json, sha256, write_json, now
from .portable_dataset import checked_file, verify


def audit(package, destination):
    package, destination = Path(package), Path(destination)
    verify(package)
    if destination.exists():
        raise ValueError('Audit destination already exists')
    destination.mkdir(parents=True)
    report = {'created_at': now(), 'package_sha256': sha256(package/'package.json'),
              'status': 'attribution_prepared_review_pending', 'records': [], 'privacy_findings': []}
    secret = re.compile(rb'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|AKIA[0-9A-Z]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')
    for row in read_json(package/'package.json')['records']:
        folder = package/'records'/row['sample_id']
        meta = read_json(folder/'manifest.json')
        if meta['origin'] == 'controlled_synthetic':
            generated = read_json(ROOT/'runs'/meta['generation_run']/'manifest.json')
            run_id = generated['reproduction_run']
        else:
            run_id = meta['run_id']
        run = ROOT/'runs'/run_id
        raw, license = read_json(run/'manifest.json'), read_json(run/'license-evidence.json')
        context = Path(raw['environment']['context'])/'base'
        source = checked_file(context, license['path'])
        if sha256(source) != license['sha256']:
            raise ValueError('Pinned license changed: ' + row['sample_id'])
        name = license['sha256'] + '.txt'
        (destination/name).write_bytes(source.read_bytes())
        report['records'].append({'sample_id': row['sample_id'], 'repo': meta['repo'],
            'source_commit': meta['source_commit'], 'base_commit': raw['source']['base'],
            'origin': meta['origin'], 'license': license['declared_license'],
            'license_file': name, 'license_sha256': license['sha256'],
            'source_license_path': license['path'], 'reproduction_run': run_id,
            'notice_review': 'pending_source_file_headers_and_additional_notices'})
        for file in folder.iterdir():
            data = file.read_bytes()
            if secret.search(data):
                report['privacy_findings'].append({'sample_id':row['sample_id'],'file':file.name,'kind':'credential_pattern'})
            if re.search(rb'[A-Za-z]:\\+Users\\+|/home/[^/\s]+/', data):
                report['privacy_findings'].append({'sample_id':row['sample_id'],'file':file.name,'kind':'local_home_path_review'})
    report['license_variants'] = len({r['license_sha256'] for r in report['records']})
    report['repositories'] = len({r['repo'] for r in report['records']})
    write_json(destination/'audit.json', report)
    return {k:v for k,v in report.items() if k not in {'records','privacy_findings'}} | {'privacy_findings':len(report['privacy_findings'])}


def publish_v1(package, audit_directory, destination):
    package, audit_directory, destination = map(Path,(package,audit_directory,destination))
    checked = verify(package)
    expected = {'train/real_local_reconstruction':175,'validation/real_local_reconstruction':37,
                'test/real_local_reconstruction':38,'train/controlled_synthetic':101}
    if checked['counts'] != expected or checked['source_lock_sha256'] != read_json(ROOT/'data-manifests/training-v1.1.json')['dataset_sha256']:
        raise ValueError('Publication must match the original v1.1 cohort and lock')
    report = read_json(audit_directory/'audit.json')
    if report['package_sha256'] != sha256(package/'package.json'):
        raise ValueError('Publication audit belongs to another package')
    for finding in report['privacy_findings']:
        if (finding['sample_id'],finding['file'],finding['kind']) != ('pytest-dev__pytest-9064','input.json','local_home_path_review'):
            raise ValueError('Unresolved privacy finding')
    if destination.exists():raise ValueError('Never overwrite a publication')
    destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as tmp:
        staging=Path(tmp)/'package';shutil.copytree(package,staging)
        attribution=[]
        for entry in report['records']:
            item=dict(entry);run=ROOT/'runs'/entry['reproduction_run'];raw=read_json(run/'manifest.json')
            meta=read_json(staging/'records'/entry['sample_id']/'manifest.json')
            context=Path(raw['environment']['context'])/('head' if entry['origin']=='controlled_synthetic' else 'base')
            notices=[]
            license=checked_file(audit_directory,entry['license_file'])
            if sha256(license)!=entry['license_sha256']:raise ValueError('Audit license changed')
            license_target=staging/'LICENSES'/entry['license_file'];license_target.parent.mkdir(exist_ok=True);shutil.copyfile(license,license_target)
            for file in sorted(context.iterdir()):
                if file.is_file() and not file.is_symlink() and file.name.upper().startswith(('LICENSE','COPYING','COPYRIGHT','NOTICE','AUTHORS')):
                    digest=sha256(file);target=staging/'NOTICES'/(digest+'.txt');target.parent.mkdir(exist_ok=True)
                    shutil.copyfile(file,target);notices.append({'source_path':file.name,'file':target.relative_to(staging).as_posix(),'sha256':digest})
            headers=[]
            for snippet in read_json(staging/'records'/entry['sample_id']/'input.json')['code']:
                file=snippet['file'];source=checked_file(context,file);text=source.read_text(encoding='utf-8-sig')
                header='\n'.join(text.splitlines()[:100])+'\n';digest=__import__('hashlib').sha256(header.encode()).hexdigest()
                target=staging/'NOTICES'/(digest+'.txt');target.parent.mkdir(exist_ok=True);target.write_text(header,encoding='utf-8',newline='\n')
                headers.append({'source_path':file,'source_sha256':sha256(source),'header_file':target.relative_to(staging).as_posix(),
                    'upstream_base_url':entry['repo']+'/blob/'+entry['base_commit']+'/'+file})
            changes=[]
            if entry['origin']=='controlled_synthetic':
                generated=ROOT/'runs'/meta['generation_run'];candidate=generated/('attempt-'+str(meta['attempt_index']).zfill(2))
                for name,source in [('candidate.diff',candidate/'change.diff'),('repair.patch',ROOT/raw['source']['repair_patch'])]:
                    target=staging/'provenance'/entry['sample_id']/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
                    changes.append(target.relative_to(staging).as_posix())
            item.update(notice_review='pinned_root_notices_and_source_headers_retained',notices=notices,source_headers=headers,synthetic_changes=changes)
            attribution.append(item)
        write_json(staging/'attribution.json',{'records':attribution,'qualification':'Original source licenses apply per record/file; no blanket relicensing. Source excerpts, pinned notices and synthetic changes supplied as source, not binaries.'})
        (staging/'README.md').write_text('# CI diagnosis pilot v1.1 portable\n\n351marked-silver records:175real train,37validation,38test,101synthetic train.\n\nInput and reference/assessment are separate. Never supply held-out references, assessments or provenance repair patches to retrieval/model prompts. Labels are not expert gold. This derived snapshot does not replace the original training lock or enable checkpoint resume on another machine.\n\nRun `python -m ci_demo.portable_dataset --check research-data/v1.1`. No raw runs, Docker or model required.\n\nSee attribution.json and LICENSES/NOTICES for original licenses, copyright notices, source revisions and synthetic changes. Generic /home/user/root_dir strings in pytest9064 are upstream expected diagnostic fixtures, retained verbatim; local Ollama Modelfile paths were omitted only from derived metadata with original hashes preserved. Raw evidence remains in external archives and is not reproduced by this package.\n',encoding='utf-8')
        manifest=read_json(staging/'package.json');manifest['publication']='attribution_and_privacy_checked_source_licenses_retained'
        manifest['attachments']={p.relative_to(staging).as_posix():sha256(p) for p in staging.rglob('*') if p.is_file() and p.relative_to(staging).parts[0]!='records' and p.name!='package.json'}
        write_json(staging/'package.json',manifest);verify(staging);staging.rename(destination)
    return verify(destination)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package',type=Path,required=True)
    parser.add_argument('--destination',type=Path,required=True)
    args=parser.parse_args()
    print(audit(args.package,args.destination))
