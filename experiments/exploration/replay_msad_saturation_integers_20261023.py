"""Independent integer saturation witnesses; no production metric imports."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from math import isqrt
from pathlib import Path
import os

os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'artifacts/msad-saturation-diagnostic-20261023'
MANIFEST = ROOT/'artifacts/msad-corpus-20261023/manifest.json'
D = 1 << 32


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def write_new(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def interval_runs(y):
    indices = np.flatnonzero(y)
    result = []
    a = b = int(indices[0])
    for raw in indices[1:]:
        i = int(raw)
        if i == b+1: b = i
        else: result.append((a, b)); a = b = i
    result.append((a, b))
    return result


def geometry(y, width, original):
    radius, n = width//2, len(y)
    # Sum actual interval ramps, then clip; weights use Python integers.
    buffer = {}
    for a, b in original:
        for distance in range(1, radius+1):
            z = (width-distance)*D*D
            low = isqrt(z//width)
            high = low if low*low*width == z else low+1
            assert low*low*width <= z <= high*high*width
            for position in (a-distance, b+distance):
                if 0 <= position < n and not y[position]:
                    old_low, old_high = buffer.get(position, (0, 0))
                    buffer[position] = (min(D, old_low+low), min(D, old_high+high))
    components = []
    for a, b in original:
        start, end = max(0, a-radius), min(n-1, b+radius)
        if components and start <= components[-1][1]:
            components[-1] = (components[-1][0], max(end, components[-1][1]))
        else: components.append((start, end))
    return buffer, components


def pair(value): return [str(value.numerator), str(value.denominator)]


def witness(count, a, lower, upper, hits, components, p0):
    rhs = 2*(p0-a)*D
    def recall(buffer):
        denominator = (2*p0*D+buffer)*components
        numerator = min(2*(a*D+buffer), 2*p0*D+buffer)*hits
        return Fraction(numerator, denominator)
    return {'predicted_count': int(count), 'original_positive_count': int(a),
        'buffer_lower_numerator': str(lower), 'buffer_upper_numerator': str(upper),
        'weight_scale': str(D), 'hit_count': int(hits), 'components': int(components),
        'saturation_buffer_threshold_numerator': str(rhs),
        'lower_mass_minus_threshold_numerator': str(lower-rhs),
        'upper_mass_minus_threshold_numerator': str(upper-rhs),
        'recall_lower_fraction': pair(recall(lower)), 'recall_upper_fraction': pair(recall(upper))}


def freeze():
    producer = read(OUT/'protocol.json')
    protocol = {'kind': 'Independent direct-ramp integer replay, after exploratory diagnostic',
        'frozen_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'All96 model records by31 widths, no production imports; raw current and previous GLOBAL distinct-score threshold witnesses',
        'producer_protocol_sha256': digest(OUT/'protocol.json'),
        'producer_records_sha256': digest(OUT/'records.jsonl'),
        'manifest_sha256': digest(MANIFEST), 'source_sha256': digest(Path(__file__)),
        'series': producer['series'], 'models': producer['models'], 'widths': list(range(31)),
        'comparison': 'Match recorded first-saturation global count; certify current recall_lower=1 and predecessor recall_upper<1 using exact Fraction arithmetic',
        'cpu_rule': 'Execute only after explicit timing-window CPU release; no runtime measurement'}
    write_new(OUT/'integer-replay-protocol.json', protocol)
    print(digest(OUT/'integer-replay-protocol.json'))


def run():
    protocol = read(OUT/'integer-replay-protocol.json')
    assert digest(Path(__file__)) == protocol['source_sha256']
    assert digest(OUT/'records.jsonl') == protocol['producer_records_sha256']
    assert digest(OUT/'protocol.json') == protocol['producer_protocol_sha256']
    assert digest(MANIFEST) == protocol['manifest_sha256']
    records = [json.loads(s) for s in (OUT/'records.jsonl').read_text().splitlines()]
    original = {(r['series'], r['model']): r for r in records}
    assert len(original) == 96
    count = 0
    target = OUT/'integer-replay-witnesses.jsonl'
    with target.open('x') as stream:
        for row in read(MANIFEST)['series']:
            if row['series'] not in protocol['series']: continue
            npz = ROOT/row['npz_path']
            assert digest(npz) == row['npz_sha256']
            with np.load(npz, allow_pickle=False) as arrays:
                y = arrays['labels']
                p0 = int(sum(int(v) for v in y))
                runs = interval_runs(y)
                shapes = [geometry(y, w, runs) for w in range(31)]
                for model in protocol['models']:
                    scores = arrays[model]
                    values, ascending_group = np.unique(scores, return_inverse=True)
                    groups = len(values)-1-ascending_group
                    G = len(values)
                    counts = np.cumsum(np.bincount(groups, minlength=G))
                    original_counts = np.cumsum(np.bincount(groups[y.astype(bool)], minlength=G))
                    for w, (buffer, components) in enumerate(shapes):
                        low, high, hit = [0]*G, [0]*G, [0]*G
                        for position, (a, b) in buffer.items():
                            g = int(groups[position]); low[g] += a; high[g] += b
                        for a, b in components:
                            hit[int(np.min(groups[a:b+1]))] += 1
                        for i in range(1, G):
                            low[i] += low[i-1]; high[i] += high[i-1]; hit[i] += hit[i-1]
                        recorded = original[row['series'], model]['per_width'][w]
                        stop_count = recorded['saturation_global_count']
                        indices = np.flatnonzero(counts == stop_count)
                        assert len(indices) == 1
                        j = int(indices[0])
                        current = witness(counts[j], int(original_counts[j]), low[j], high[j], hit[j], len(components), p0)
                        before = (witness(counts[j-1], int(original_counts[j-1]), low[j-1], high[j-1], hit[j-1], len(components), p0)
                                  if j else witness(0, 0, 0, 0, 0, len(components), p0))
                        assert Fraction(*(int(v) for v in current['recall_lower_fraction'])) == 1
                        assert Fraction(*(int(v) for v in before['recall_upper_fraction'])) < 1
                        receipt = {'series': row['series'], 'model': model, 'width': w,
                            'npz_sha256': row['npz_sha256'], 'global_distinct_ordinal': j,
                            'total_original_positives': p0, 'current': current, 'previous': before,
                            'first_saturation_proved': True}
                        stream.write(json.dumps(receipt, allow_nan=False)+'\n')
                        count += 1
            print(row['series'], flush=True)
    assert count == 96*31
    assert digest(Path(__file__)) == protocol['source_sha256']
    write_new(OUT/'integer-replay-receipt.json', {'status': 'PASS',
        'protocol_sha256': digest(OUT/'integer-replay-protocol.json'),
        'source_sha256': digest(Path(__file__)), 'witnesses_sha256': digest(target),
        'model_records': 96, 'width_records': count, 'first_saturation_proofs': count,
        'method': 'Independent direct temporal ramps, global score classes, component coverage, Python integer roots and exact Fraction comparisons; no production metric imports'})
    print(json.dumps(read(OUT/'integer-replay-receipt.json'), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['freeze', 'run'])
    parser.add_argument('--timing-cpu-released', action='store_true')
    args = parser.parse_args()
    if args.command == 'freeze': freeze()
    else:
        if not args.timing_cpu_released: parser.error('--timing-cpu-released required')
        run()
