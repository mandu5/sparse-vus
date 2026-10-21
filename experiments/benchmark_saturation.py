"""Frozen, paired full-call development study of exact active-prefix VUS.

Development data was used in earlier research. This is not unseen-domain
confirmation. Run records are append-only; source/input drift fails closed.
"""
from __future__ import annotations

import os
for _name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
              'VECLIB_MAXIMUM_THREADS', 'NUMBA_NUM_THREADS'):
    os.environ[_name] = '1'

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'experiments'))
sys.path.insert(0, str(ROOT / 'src'))
METHOD_IDS = ('saturation', 'active_full', 'last_positive', 'radix',
              'dense_radix', 'klein', 'sparse_comparison', 'dense_direct',
              'dense_direct_radix')
SEED = 2026102113


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def sources():
    paths = sorted((ROOT / 'src/sparse_vus').glob('*.py'))
    paths += [ROOT / 'experiments' / name for name in (
        'benchmark_saturation.py', 'benchmark_advancement.py',
        'advancement_data_gate.py', 'fast_vus_adapter.py')]
    paths += [ROOT / '.cache/fast_vus/fast_vus.py']
    return {str(p.relative_to(ROOT)): digest(p) for p in paths}


def case_input(row, score_hash):
    """Bind input identity only; historical benchmark outcomes are not inputs."""
    result = {key:row[key] for key in ('series','family','model','n','positive_points',
                                     'max_buffer','label_member_sha256')}
    result['score_member_sha256'] = score_hash
    result['case_id'] = f"{row['series']}|{row['model']}|{row['max_buffer']}"
    return result


def freeze(output, phase='development'):
    from advancement_data_gate import released_metadata
    from benchmark_advancement import corpus_rows
    bindings = {}
    if phase == 'development':
        _, models, score_hashes, _, _, _ = released_metadata(ROOT)
        rows = corpus_rows('certified')
        inputs = [case_input(row, score_hashes[row['series'], row['model']])
                  for row in sorted(rows,key=lambda r:(r['max_buffer'],r['series'],r['model']))]
        assert len(inputs) == 378 and len({r['series'] for r in inputs}) == 42
        history = 'Original42series development partition, previously studied. No unseen-data claim. New algorithm derived without these runtime outcomes.'
    elif phase == 'external':
        manifest_path = ROOT/'artifacts/saturation/external-inputs/manifest.json'
        manifest = json.loads(manifest_path.read_text())
        assert manifest['status'] == 'INPUTS_VERIFIED_NO_METRIC_OUTCOMES'
        assert manifest['metric_outcomes_computed'] is False
        models = manifest['models']
        inputs = []
        for item in manifest['series']:
            path = ROOT/item['npz_path']
            if digest(path) != item['npz_sha256']:
                raise ValueError('External NPZ identity mismatch')
            with np.load(path,allow_pickle=False) as arrays:
                positives = int(arrays['labels'].sum())
            for width in (30,100,300):
                for model in models:
                    row = {'series':item['series'],'family':item['family'],'model':model,
                           'n':item['n'],'positive_points':positives,'max_buffer':width,
                           'label_member_sha256':item['array_sha256']['labels']}
                    inputs.append({**case_input(row,item['array_sha256'][model]),
                                   'npz_path':item['npz_path'],'npz_sha256':item['npz_sha256']})
        inputs.sort(key=lambda r:(r['max_buffer'],r['series'],r['model']))
        assert len(inputs)==144 and len({r['family'] for r in inputs})==9
        bindings = {str(manifest_path.relative_to(ROOT)):digest(manifest_path),
                    'artifacts/saturation/external-inputs/selection.json':manifest['selection_sha256'],
                    'experiments/fetch_saturation_external.py':digest(ROOT/'experiments/fetch_saturation_external.py')}
        history = 'Metadata-only selection of12series from9source families absent from the previous23family corpus. Four newly generated CPU score vectors per series; no detector-quality claim. Labels/scores prepared before any new metric outcome; source-family novelty is not proof of independent real-world domains.'
    else:
        raise ValueError('Unknown phase')
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / 'inputs.json', inputs)
    protocol = {
        'version':1, 'created_utc':datetime.now(timezone.utc).isoformat(),
        'phase':phase, 'cases':len(inputs), 'series':len({r['series'] for r in inputs}),
        'families':sorted({r['family'] for r in inputs}), 'models':models,
        'widths':[30,100,300], 'primary_width':30, 'repetitions':3, 'seed':SEED,
        'method_ids':list(METHOD_IDS), 'parity_atol':1e-11,
        'inputs_sha256':digest(output / 'inputs.json'), 'source_sha256':sources(),
        'external_input_bindings':bindings,
        'source_commit':subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
        'timing':'Complete scalar PR public calls, including validation and preparation. Three seeded randomized serial repeats per case. One compute thread, warmed JIT. Input I/O and diagnostic profiling outside timing.',
        'ablation':'active_full disables saturation; last_positive stops after all original positives; both retain identical activation/DSU preparation. Radix and nearest dense radix are unchanged v0.3 code. Klein is actual pinned PR-only implementation with all n thresholds.',
        'decision':'Parity on every case; at L=30 geometric and aggregate ratio lower95% family-cluster bootstrap bounds above1 against every eight comparator methods. This is a scoped empirical criterion, not a global firstness or acceptance determination.',
        'bootstrap':{'unit':'family','repetitions':2000,'seed':SEED+1,'confidence':.95},
        'history':history,
        'uncertainty':'Family-cluster intervals describe observed family/case variation, not timing-repeat or machine-population uncertainty. Individual ratios pair medians within this run.',
    }
    write_json(output / 'protocol.json', protocol)
    return {'protocol_sha256':digest(output / 'protocol.json'), 'cases':len(inputs)}


class ExternalCorpus:
    def __init__(self):
        self.key = None

    def load(self, row):
        from fetch_saturation_external import array_sha
        if row['series'] != self.key:
            path = ROOT/row['npz_path']
            if digest(path) != row['npz_sha256']:
                raise ValueError('External NPZ changed after freeze')
            with np.load(path,allow_pickle=False) as arrays:
                self.arrays = {k:arrays[k] for k in arrays.files}
            self.key = row['series']
        y, scores = self.arrays['labels'], self.arrays[row['model']]
        if array_sha(y)!=row['label_member_sha256'] or array_sha(scores)!=row['score_member_sha256']:
            raise ValueError('External array identity mismatch')
        if len(y)!=row['n'] or int(y.sum())!=row['positive_points']:
            raise ValueError('External metadata mismatch')
        return y,scores


def methods():
    from sparse_vus.saturation import sparse_pr_saturation_jit
    from sparse_vus.radix import sparse_pr_radix_jit
    from sparse_vus.dense_radix import dense_pr_nearest_radix_jit, dense_pr_direct_radix_jit
    from sparse_vus.pr_compiled import sparse_pr_jit, dense_pr_direct_jit
    from fast_vus_adapter import fast_vus_pr
    return {
        'saturation':sparse_pr_saturation_jit,
        'active_full':lambda y,s,w:sparse_pr_saturation_jit(y,s,w,stop=False),
        'last_positive':lambda y,s,w:sparse_pr_saturation_jit(y,s,w,stop='last_positive'),
        'radix':sparse_pr_radix_jit,
        'dense_radix':dense_pr_nearest_radix_jit,
        'klein':lambda y,s,w:fast_vus_pr(y,s,w,len(s)),
        'sparse_comparison':sparse_pr_jit,
        'dense_direct':dense_pr_direct_jit,
        'dense_direct_radix':dense_pr_direct_radix_jit,
    }


def environment():
    import numba
    from threadpoolctl import threadpool_info
    if sys.platform=='darwin':
        cpu = subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string'],text=True).strip()
    elif Path('/proc/cpuinfo').exists():
        cpu = next((line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines()
                    if line.startswith('model name')), 'not captured')
    else:
        cpu = platform.processor()
    return {'utc':datetime.now(timezone.utc).isoformat(),
            'python':sys.version, 'platform':platform.platform(),
            'numpy':np.__version__, 'numba':numba.__version__,
            'cpu_count':os.cpu_count(), 'numba_threads':numba.get_num_threads(),
            'cpu_model':cpu, 'threadpools':threadpool_info(),
            'process_snapshot':subprocess.check_output(
                ['ps','-axo','pid,pcpu,comm'], text=True).splitlines(),
            'scope':'Local host, not a dedicated isolated benchmark machine. Snapshot is not a continuous load trace.'}


def run(output, expected_hash):
    from benchmark_advancement import Corpus
    from sparse_vus.saturation import profile_saturation
    from threadpoolctl import threadpool_limits
    limits = threadpool_limits(limits=1)
    protocol = json.loads((output / 'protocol.json').read_text())
    if digest(output / 'protocol.json') != expected_hash:
        raise ValueError('Frozen protocol hash mismatch')
    if digest(output / 'inputs.json') != protocol['inputs_sha256'] or sources() != protocol['source_sha256']:
        raise ValueError('Frozen input/source drift')
    for name, expected in protocol['external_input_bindings'].items():
        if digest(ROOT/name) != expected:
            raise ValueError('External input binding drift')
    if any((output / name).exists() for name in ('environment.json','measurements.jsonl','report.json')):
        raise ValueError('Run already started; use a new frozen output, never append a replay')
    inputs = json.loads((output / 'inputs.json').read_text())
    evaluators = methods()
    assert list(evaluators) == protocol['method_ids']
    warm_y = np.array([0,1,0,0,1,0], dtype=np.int8)
    warm_s = np.array([0.,4.,3.,2.,1.,0.])
    for fn in evaluators.values():
        fn(warm_y,warm_s,6)
    for stop in (True,False,'last_positive'):
        profile_saturation(warm_y,warm_s,6,stop=stop)
    write_json(output / 'environment.json', environment())
    write_json(output / 'run-start.json', {'protocol_sha256':expected_hash,
               'source_sha256':sources(),'utc':datetime.now(timezone.utc).isoformat()})
    corpus = Corpus() if protocol['phase']=='development' else ExternalCorpus()
    rng = random.Random(protocol['seed'])
    with (output / 'measurements.jsonl').open('x') as stream:
        for i, item in enumerate(inputs):
            y, scores = corpus.load(item)
            if protocol['phase']=='development' and corpus.hashes[item['model']][item['series']] != item['score_member_sha256']:
                raise ValueError('Score manifest mismatch')
            measured = {name:{'seconds':[], 'values':[]} for name in evaluators}
            orders = []
            for _ in range(protocol['repetitions']):
                order = list(evaluators)
                rng.shuffle(order)
                orders.append(order)
                for name in order:
                    start = time.perf_counter_ns()
                    value = evaluators[name](y,scores,item['max_buffer'])
                    elapsed = (time.perf_counter_ns()-start) / 1e9
                    measured[name]['seconds'].append(elapsed)
                    measured[name]['values'].append(float(value))
            profiles = {name:profile_saturation(y,scores,item['max_buffer'],stop=stop)
                        for name,stop in [('saturation',True),('active_full',False),
                                          ('last_positive','last_positive')]}
            record = {**item, 'methods':measured, 'orders':orders, 'profiles':profiles}
            stream.write(json.dumps(record,allow_nan=False)+'\n')
            stream.flush()
            if (i+1)%12 == 0 or i+1 == len(inputs):
                print(json.dumps({'completed':i+1,'total':len(inputs),'width':item['max_buffer']}),flush=True)
    write_json(output / 'environment-end.json', environment())
    if sources() != protocol['source_sha256']:
        raise ValueError('Source drifted during run; recorded measurements remain but are invalid')
    write_json(output/'completion.json', {'status':'COMPLETED',
               'utc':datetime.now(timezone.utc).isoformat(),
               'protocol_sha256':expected_hash,'source_sha256':sources(),
               'measurements_sha256':digest(output/'measurements.jsonl'),
               'cases':len(inputs)})
    return report(output)


def summarize(rows, bootstrap_repetitions=2000):
    ids = [r['case_id'] for r in rows]
    if not rows or len(ids) != len(set(ids)):
        raise ValueError('Duplicate or empty cases')
    method_ids = list(rows[0]['methods'])
    if 'saturation' not in method_ids:
        raise ValueError('Missing saturation method')
    maximum_error = 0.
    medians = []
    for row in rows:
        if set(row['methods']) != set(method_ids):
            raise ValueError('Inconsistent method coverage')
        med = {}
        reference = row['methods']['saturation']['values'][0]
        for name in method_ids:
            times = row['methods'][name]['seconds']
            values = row['methods'][name]['values']
            if len(times) != 3 or len(values) != 3 or not all(math.isfinite(x) and x>0 for x in times):
                raise ValueError('Invalid timing repetitions')
            if not all(math.isfinite(x) for x in values):
                raise ValueError('Nonfinite metric')
            maximum_error = max(maximum_error, *(abs(x-reference) for x in values))
            med[name] = statistics.median(times)
        medians.append(med)
    widths = {}
    rng = np.random.default_rng(SEED+1)
    for width in sorted({r['max_buffer'] for r in rows}):
        selected = [i for i,r in enumerate(rows) if r['max_buffer']==width]
        families = sorted({rows[i]['family'] for i in selected})
        clusters = [np.array([j for j,i in enumerate(selected) if rows[i]['family']==f]) for f in families]
        candidate = np.array([medians[i]['saturation'] for i in selected])
        draws = rng.integers(0,len(clusters),size=(bootstrap_repetitions,len(clusters)))
        comparisons = {}
        for method in method_ids:
            if method == 'saturation':
                continue
            baseline = np.array([medians[i][method] for i in selected])
            ratios = baseline / candidate
            geos, aggregates = [], []
            for draw in draws:
                ix = np.concatenate([clusters[d] for d in draw])
                geos.append(float(np.exp(np.mean(np.log(ratios[ix])))))
                aggregates.append(float(baseline[ix].sum()/candidate[ix].sum()))
            comparisons[method] = {
                'median_ratio':float(np.median(ratios)),
                'geomean_ratio':float(np.exp(np.mean(np.log(ratios)))),
                'aggregate_ratio':float(baseline.sum()/candidate.sum()),
                'geomean_ci95':np.quantile(geos,[.025,.975]).tolist(),
                'aggregate_ci95':np.quantile(aggregates,[.025,.975]).tolist(),
                'wins':int((ratios>1).sum()), 'losses':int((ratios<1).sum()),
                'ties':int((ratios==1).sum()), 'minimum_ratio':float(ratios.min()),
                'candidate_seconds_sum':float(candidate.sum()),
                'reference_seconds_sum':float(baseline.sum()),
            }
        widths[str(width)] = {'cases':len(selected),'families':families,
                              'comparisons':comparisons}
    parity = maximum_error <= 1e-11
    primary = widths.get('30',{}).get('comparisons',{})
    return {'cases':len(rows),'parity_pass':parity,'max_absolute_error':maximum_error,
            'widths':widths,'primary_decision':bool(parity and primary and all(
                c['geomean_ci95'][0]>1 and c['aggregate_ci95'][0]>1 for c in primary.values())),
            'scope':'Paired development measurements; all losses retained. No global SOTA or independent confirmation claim.'}


def report(output):
    protocol = json.loads((output/'protocol.json').read_text())
    start = json.loads((output/'run-start.json').read_text())
    completed = json.loads((output/'completion.json').read_text())
    if (protocol['version']!=1 or protocol['repetitions']!=3
            or protocol['primary_width']!=30 or protocol['parity_atol']!=1e-11
            or protocol['bootstrap']['seed']!=SEED+1
            or protocol['method_ids']!=list(METHOD_IDS)):
        raise ValueError('Unsupported frozen protocol contract')
    if (digest(output/'inputs.json')!=protocol['inputs_sha256']
            or completed['status']!='COMPLETED'
            or completed['protocol_sha256']!=digest(output/'protocol.json')
            or start['protocol_sha256']!=completed['protocol_sha256']
            or start['source_sha256']!=protocol['source_sha256']
            or completed['source_sha256']!=protocol['source_sha256']):
        raise ValueError('Run completion, source or input binding mismatch')
    inputs = json.loads((output/'inputs.json').read_text())
    raw = output/'measurements.jsonl'
    if digest(raw)!=completed['measurements_sha256']:
        raise ValueError('Raw measurement digest mismatch')
    rows = [json.loads(line) for line in raw.read_text().splitlines()]
    if len(rows) != protocol['cases'] or [r['case_id'] for r in rows] != [r['case_id'] for r in inputs]:
        raise ValueError('Incomplete or reordered case coverage')
    for row,item in zip(rows,inputs):
        if any(row.get(k)!=v for k,v in item.items()) or list(row['methods']) != protocol['method_ids']:
            raise ValueError('Input identity or method binding mismatch')
        if set(row['profiles'])!={'saturation','active_full','last_positive'}:
            raise ValueError('Incomplete work-profile modes')
        for profile in row['profiles'].values():
            if (len(profile['visited']) != row['max_buffer']+1
                    or len(profile['active']) != row['max_buffer']+1) or any(
                    type(v) is not int or type(a) is not int or not 0 < v <= a <= profile['Q']
                    for v,a in zip(profile['visited'],profile['active'])):
                raise ValueError('Invalid work profile')
            if abs(profile['values']['pr']-row['methods']['saturation']['values'][0])>protocol['parity_atol']:
                raise ValueError('Profile semantic mismatch')
        profiles=row['profiles']
        if profiles['active_full']['visited']!=profiles['active_full']['active']:
            raise ValueError('Full scan did not visit all active positions')
        if not all(a<=b<=c for a,b,c in zip(profiles['saturation']['visited'],
                                          profiles['last_positive']['visited'],
                                          profiles['active_full']['visited'])):
            raise ValueError('Saturation work exceeds last-positive or full-scan work')
    result = summarize(rows,protocol['bootstrap']['repetitions'])
    result.update(protocol_sha256=digest(output/'protocol.json'),
                  measurements_sha256=digest(raw), inputs_sha256=digest(output/'inputs.json'))
    result['phase'] = protocol['phase']
    result['scope'] = protocol['history']
    write_json(output/'report.json',result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action',choices=['freeze','run','report'])
    parser.add_argument('output',type=Path)
    parser.add_argument('--protocol-sha256')
    parser.add_argument('--phase',choices=['development','external'],default='development')
    args = parser.parse_args()
    if args.action=='freeze':
        result=freeze(args.output,args.phase)
    elif args.action=='run':
        result=run(args.output,args.protocol_sha256)
    else:
        result=report(args.output)
    print(json.dumps(result,indent=2,allow_nan=False))
