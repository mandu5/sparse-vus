"""Acquire a prospectively selected MSAD stored-score corpus; no metric evaluation."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import struct
import threading
import time
import urllib.request
import zipfile
import zlib

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = 'experiments/fetch_msad_score_corpus.py'
DESIGN = 'docs/msad_score_corpus_design_20261023.md'
OUT = ROOT / 'artifacts/msad-corpus-20261023'
CACHE = ROOT / '.cache/msad-corpus-20261023'
URL = 'https://drive.usercontent.google.com/download?id=1PQKwu5lZTnTmsmms1ipko9KF712Oc5DE&export=download&confirm=t'
ARCHIVE_BYTES = 841275484
MODELS = ('AE', 'CNN', 'HBOS', 'IFOREST', 'IFOREST1', 'LOF', 'LSTM', 'MP', 'NORMA', 'OCSVM', 'PCA', 'POLY')
SALT = 'msad-vus-20261023-v1\0'
MAX_RESPONSE_BYTES = 500000000
PRIOR = ('artifacts/selected_series.json', 'artifacts/saturation/external-inputs/manifest.json')


def require(value, message):
    if not value:
        raise ValueError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1 << 20):
            h.update(block)
    return h.hexdigest()


def write_new(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def array_sha(array):
    array = np.ascontiguousarray(array)
    header = json.dumps({'dtype': array.dtype.str, 'shape': list(array.shape)}, sort_keys=True).encode()
    return sha(header + b'\0' + array.tobytes())


def observation_hashes(values):
    values = np.asarray(values, dtype=np.float64)
    exact = array_sha(values)
    scale = float(np.std(values))
    normalized = (values - float(np.mean(values))) / scale if scale > 0 else np.zeros_like(values)
    normalized = np.round(normalized, 10)
    normalized[normalized == 0] = 0.0
    return exact, array_sha(normalized)


def read_directory(reader, total):
    tail = reader(max(0, total - 65536), total - 1)
    at = tail.rfind(b'PK\x05\x06')
    require(at >= 0 and len(tail) >= at + 22, 'ZIP end record missing')
    end = struct.unpack_from('<4s4H2LH', tail, at)
    require(end[1:3] == (0, 0) and end[3] == end[4] and end[4] < 65535,
            'Unsupported split/ZIP64 central directory')
    size, start = end[5:7]
    require(0 <= start < total and start + size + 22 + end[7] == total,
            'Central directory length mismatch')
    central = reader(start, total - 1)
    with zipfile.ZipFile(io.BytesIO(central)) as archive:
        infos = archive.infolist()
        require(len(infos) == end[4], 'ZIP member count mismatch')
        require(len({p.filename for p in infos}) == len(infos), 'Duplicate ZIP path')
        rows = [{'path': p.filename, 'bytes': p.file_size, 'compressed_bytes': p.compress_size,
                 'offset': p.header_offset + start, 'crc32': p.CRC,
                 'method': p.compress_type, 'flags': p.flag_bits} for p in infos]
    return rows, {'central_offset': start, 'central_bytes': len(central),
                  'central_sha256': sha(central), 'members': len(rows), 'archive_bytes': total}


def decode_member(raw, row):
    require(len(raw) >= 30, 'Truncated local header')
    h = struct.unpack_from('<4s5H3L2H', raw)
    require(h[0] == b'PK\x03\x04', 'Invalid ZIP local header')
    flags, method, name_length, extra_length = h[2], h[3], h[-2], h[-1]
    require(not flags & 1 and method in (0, 8) and method == row['method'], 'Unsupported member method')
    name = raw[30:30 + name_length].decode('utf-8' if flags & 2048 else 'cp437')
    require(name == row['path'], 'Local member name differs')
    start = 30 + name_length + extra_length
    payload = raw[start:start + row['compressed_bytes']]
    require(len(payload) == row['compressed_bytes'], 'Truncated member payload')
    require(row['bytes'] <= 40000000, 'Member uncompressed size exceeds bound')
    if method == 8:
        decoder = zlib.decompressobj(-15)
        content = decoder.decompress(payload, row['bytes'] + 1)
        require(decoder.eof and not decoder.unused_data and len(content) <= row['bytes'],
                'Invalid or oversized deflate payload')
    else:
        content = payload
    require(len(content) == row['bytes'], 'Uncompressed length mismatch')
    require(zlib.crc32(content) == row['crc32'], 'Member CRC mismatch')
    return content


def candidate_queue(rows):
    raw, scores = {}, defaultdict(dict)
    for row in rows:
        p = row['path'].split('/')
        if len(p) == 4 and p[:2] == ['TSB', 'data'] and p[3]:
            raw[(p[2], p[3])] = row
        if len(p) == 6 and p[:2] == ['TSB', 'scores'] and p[4] == 'score' and p[5]:
            scores[(p[2], p[5])][p[3]] = row
    by_family = defaultdict(list)
    for key in sorted(raw):
        family, name = key
        if set(scores[key]) == set(MODELS) and '.train.' not in name and raw[key]['bytes'] <= 12000000:
            by_family[family].append({'family': family, 'series': name,
                'raw': raw[key], 'scores': {m: scores[key][m] for m in MODELS}})
    for family in by_family:
        by_family[family].sort(key=lambda row: sha((SALT + family + '/' + row['series']).encode()))
    result = []
    for index in range(max(map(len, by_family.values()), default=0)):
        for family in sorted(by_family):
            if index < len(by_family[family]):
                result.append(by_family[family][index])
    return result


def parse_raw(raw):
    data = np.loadtxt(io.BytesIO(raw), delimiter=',', dtype=np.float64, ndmin=2)
    require(data.ndim == 2 and data.shape[1] == 2 and len(data) >= 2, 'Invalid raw two-column shape')
    require(np.isfinite(data).all(), 'Nonfinite raw data')
    y = data[:, 1]
    require(np.isin(y, [0, 1]).all() and 0 < y.sum() < len(y), 'Need both binary label classes')
    return {'observations': np.ascontiguousarray(data[:, 0]), 'labels': y.astype(np.int8)}


def parse_case(raw, scores):
    require(set(scores) == set(MODELS), 'Incomplete model set')
    arrays = parse_raw(raw)
    for model in MODELS:
        values = np.loadtxt(io.BytesIO(scores[model]), dtype=np.float64, ndmin=1)
        require(values.ndim == 1 and len(values) == len(arrays['labels']), 'Score length/shape mismatch')
        require(np.isfinite(values).all(), 'Nonfinite stored score')
        arrays[model] = values
    return arrays


class Ranges:
    def __init__(self, url=URL, total=ARCHIVE_BYTES):
        self.url, self.total, self.bytes = url, total, 0
        self.lock = threading.Lock()

    def __call__(self, start, stop):
        require(0 <= start <= stop < self.total, 'Range outside archive')
        expected = stop - start + 1
        with self.lock:
            require(self.bytes + expected <= MAX_RESPONSE_BYTES, 'Response budget exceeded')
            self.bytes += expected
        for attempt in range(4):
            try:
                request = urllib.request.Request(self.url, headers={'Range': f'bytes={start}-{stop}',
                    'User-Agent': 'sparse-vus-published-score-acquisition/1'})
                with urllib.request.urlopen(request, timeout=90) as response:
                    require(response.status == 206, 'Server did not honor Range')
                    require(response.headers.get('Content-Range') == f'bytes {start}-{stop}/{self.total}',
                            'Content-Range mismatch')
                    data = response.read(expected + 1)
                    require(len(data) == expected, 'Range response length mismatch')
                return data
            except Exception:
                if attempt == 3:
                    raise
                time.sleep(2 ** attempt)
        raise AssertionError('unreachable')


def get_member(reader, row):
    target = CACHE / 'members' / (sha(row['path'].encode()) + '.data')
    if target.exists():
        content = target.read_bytes()
        require(len(content) == row['bytes'] and zlib.crc32(content) == row['crc32'], 'Changed cached member')
    else:
        start = row['offset']
        stop = min(ARCHIVE_BYTES - 1, start + 30 + len(row['path'].encode()) + 4096 + row['compressed_bytes'] - 1)
        content = decode_member(reader(start, stop), row)
        with target.open('xb') as stream:
            stream.write(content)
    return content, {'path': row['path'], 'bytes': len(content), 'sha256': sha(content),
                     'crc32': row['crc32'], 'compressed_bytes': row['compressed_bytes'],
                     'archive_offset': row['offset']}


def external_raw_path(row):
    return ROOT / 'cache/saturation-external/raw' / row['family'] / (row['series'] + '.csv')


def prior_index():
    """Compare all previously measured observations/labels, never old scores/results."""
    import pandas as pd
    entries = []
    selected = json.loads((ROOT / PRIOR[0]).read_text())['ordered_series']
    with zipfile.ZipFile(ROOT / 'cache/TSB-AD-U.zip') as archive:
        names = {Path(n).stem: n for n in archive.namelist() if n.endswith('.csv')}
        for name in selected:
            raw = archive.read(names[name])
            frame = pd.read_csv(io.BytesIO(raw))
            y = frame['Label'].to_numpy(np.int8)
            values = frame.drop(columns=['Label']).to_numpy(np.float64)
            entries.append({'source': 'prior-tsb-ad', 'series': name, 'raw_sha256': sha(raw),
                'label_hash': array_sha(y), 'observation_hashes': [list(observation_hashes(values[:, i]))
                    for i in range(values.shape[1])]})
    prior = json.loads((ROOT / PRIOR[1]).read_text())
    for row in prior['series']:
        raw_path = external_raw_path(row)
        raw = raw_path.read_bytes()
        require(sha(raw) == row['raw_sha256'], 'Prior external source identity changed')
        frame = pd.read_csv(io.BytesIO(raw))
        with np.load(ROOT / row['npz_path'], allow_pickle=False) as arrays:
            y = arrays['labels'].astype(np.int8)
        feature_names = row['preprocessing']['feature_columns']
        entries.append({'source': 'prior-mtsbench', 'series': row['series'], 'raw_sha256': sha(raw),
            'label_hash': array_sha(y), 'observation_hashes': [list(observation_hashes(frame[c].to_numpy(np.float64)))
                for c in feature_names if np.isfinite(frame[c].to_numpy(np.float64)).all()]})
    return entries


def freeze():
    require(not OUT.exists() and not CACHE.exists(), 'Acquisition directories must be new')
    OUT.mkdir(parents=True)
    (CACHE / 'members').mkdir(parents=True)
    (CACHE / 'arrays').mkdir()
    reader = Ranges()
    rows, info = read_directory(reader, ARCHIVE_BYTES)
    queue = candidate_queue(rows)
    require(len(rows) == 26354 and len(queue) == 1863, 'Published source metadata changed')
    prior = prior_index()
    write_new(OUT / 'archive-directory.json', {'source_url': URL, **info, 'rows': rows})
    write_new(OUT / 'prior-identity-index.json', {'series_count': len(prior), 'entries': prior})
    write_new(OUT / 'candidate-queue.json', queue)
    protocol = {'created_utc': now(), 'stage': 'before candidate metric outcomes and bulk acquisition',
        'target_series': 128, 'models': list(MODELS), 'source_url': URL,
        'source_repository': 'https://github.com/boniolp/MSAD/tree/8141b94eb3d2b1811f81ffcf7bc8aa5dcbd6c204',
        'source_archive': info, 'eligible_series': len(queue), 'eligible_families': dict(Counter(r['family'] for r in queue)),
        'salt': SALT, 'order': 'sorted-family round-robin over per-family SHA256 order',
        'max_download_response_bytes': MAX_RESPONSE_BYTES, 'metric_outcomes_computed': False,
        'source_sha256': {p: file_sha(ROOT / p) for p in (SCRIPT, DESIGN, *PRIOR)},
        'metadata_sha256': {p: file_sha(OUT / p) for p in ('archive-directory.json', 'prior-identity-index.json', 'candidate-queue.json')},
        'identity_scope': 'Exact label and exact/rounded-standardized observation equality rejection; not proof against every cropped/transformed overlap.',
        'data_license': 'Individual original dataset licenses apply; raw data and scores not redistributed.'}
    write_new(OUT / 'protocol.json', protocol)
    print(json.dumps({'status': 'FROZEN', 'protocol_sha256': file_sha(OUT / 'protocol.json'),
                      'candidates': len(queue), 'prior_series': len(prior)}), flush=True)


def acquire():
    protocol = json.loads((OUT / 'protocol.json').read_text())
    for path, expected in protocol['source_sha256'].items():
        require(file_sha(ROOT / path) == expected, 'Frozen source changed: ' + path)
    for path, expected in protocol['metadata_sha256'].items():
        require(file_sha(OUT / path) == expected, 'Frozen metadata changed: ' + path)
    require(not (OUT / 'manifest.json').exists(), 'Corpus is already complete')
    queue = json.loads((OUT / 'candidate-queue.json').read_text())
    prior = json.loads((OUT / 'prior-identity-index.json').read_text())['entries']
    label_index = {row['label_hash']: 'prior:' + row['series'] for row in prior}
    obs_index = {h: 'prior:' + row['series'] for row in prior for pair in row['observation_hashes'] for h in pair}
    log = OUT / 'acquisition.jsonl'
    previous = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
    accepted = [row['input'] for row in previous if row['status'] == 'ACCEPTED']
    completed = {row['candidate_index'] for row in previous if row['status'] in ('ACCEPTED', 'EXCLUDED')}
    for row in accepted:
        require(file_sha(ROOT / row['npz_path']) == row['npz_sha256'], 'Previously accepted array changed')
        label_index[row['array_sha256']['labels']] = 'new:' + row['series']
        for h in row['observation_hashes']:
            obs_index[h] = 'new:' + row['series']
    reader = Ranges()
    start = now()
    with ThreadPoolExecutor(max_workers=12) as pool, log.open('a') as stream:
        for index, candidate in enumerate(queue):
            if len(accepted) >= protocol['target_series']:
                break
            if index in completed:
                continue
            row = {'candidate_index': index, 'family': candidate['family'], 'series': candidate['series'], 'time_utc': now()}
            try:
                raw, raw_receipt = get_member(reader, candidate['raw'])
                base = parse_raw(raw)
                label_hash = array_sha(base['labels'])
                observations = observation_hashes(base['observations'])
                duplicate = label_index.get(label_hash) or next((obs_index[h] for h in observations if h in obs_index), None)
                if duplicate:
                    row.update(status='EXCLUDED', reason='Prior/retained label or observation identity match', matched=duplicate, raw=raw_receipt)
                else:
                    fetched = list(pool.map(lambda m: get_member(reader, candidate['scores'][m]), MODELS))
                    arrays = parse_case(raw, {m: f[0] for m, f in zip(MODELS, fetched)})
                    path = CACHE / 'arrays' / f'{index:04d}.npz'
                    require(not path.exists(), 'Unrecorded existing array file')
                    with path.open('xb') as output:
                        np.savez_compressed(output, **arrays)
                    item = {'series': candidate['family'] + '/' + candidate['series'], 'family': candidate['family'],
                        'source_filename': candidate['series'], 'candidate_index': index,
                        'n': len(arrays['labels']), 'positive_points': int(arrays['labels'].sum()),
                        'npz_path': path.relative_to(ROOT).as_posix(), 'npz_sha256': file_sha(path), 'npz_bytes': path.stat().st_size,
                        'array_sha256': {name: array_sha(a) for name, a in arrays.items()},
                        'observation_hashes': list(observations), 'raw': raw_receipt,
                        'scores': {m: f[1] for m, f in zip(MODELS, fetched)}, 'metric_outcomes_computed': False}
                    accepted.append(item)
                    label_index[label_hash] = 'new:' + item['series']
                    for h in observations:
                        obs_index[h] = 'new:' + item['series']
                    row.update(status='ACCEPTED', input=item)
            except ValueError as error:
                # Numeric-invalid inputs are excluded by the prespecified rule.
                # Provenance/HTTP/CRC failures abort; they must never change selection.
                if str(error) in ('Invalid raw two-column shape', 'Nonfinite raw data', 'Need both binary label classes',
                                  'Score length/shape mismatch', 'Nonfinite stored score'):
                    row.update(status='EXCLUDED', reason=str(error))
                else:
                    row.update(status='FAILED', reason=repr(error))
                    stream.write(json.dumps(row, allow_nan=False) + '\n'); stream.flush()
                    raise
            except Exception as error:
                row.update(status='FAILED', reason=repr(error))
                stream.write(json.dumps(row, allow_nan=False) + '\n'); stream.flush()
                raise
            stream.write(json.dumps(row, allow_nan=False) + '\n'); stream.flush()
            print(json.dumps({'candidate': index, 'accepted': len(accepted), 'status': row['status'],
                              'downloaded_response_bytes': reader.bytes}), flush=True)
    require(len(accepted) == protocol['target_series'], 'Eligible corpus exhausted before target')
    manifest = {'status': 'INPUTS_VERIFIED_NO_METRIC_OUTCOMES', 'started_utc': start, 'completed_utc': now(),
        'protocol_sha256': file_sha(OUT / 'protocol.json'), 'models': list(MODELS), 'series_count': len(accepted),
        'score_vectors': len(accepted) * len(MODELS), 'family_count': len({r['family'] for r in accepted}),
        'families': dict(Counter(r['family'] for r in accepted)), 'total_rows': sum(r['n'] for r in accepted),
        'downloaded_response_bytes_this_invocation': reader.bytes, 'metric_outcomes_computed': False,
        'acquisition_log_sha256': file_sha(log), 'series': accepted}
    write_new(OUT / 'manifest.json', manifest)
    print(json.dumps({'status': manifest['status'], 'series': len(accepted), 'score_vectors': manifest['score_vectors'],
                      'manifest_sha256': file_sha(OUT / 'manifest.json')}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['freeze', 'acquire'])
    command = parser.parse_args().command
    freeze() if command == 'freeze' else acquire()
