"""Input identity and CPU conditions must survive subprocess boundaries."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiments'))
from external_supplement import validate_worker_receipt


def receipt():
    return {'n': 100, 'label_sha256': 'labels', 'score_sha256': 'scores',
            'threads': 1, 'threadpool_info': [{'num_threads': 1}],
            'calls': [{'seconds': .01}]}


@pytest.mark.parametrize('field,bad', [('n', 99), ('label_sha256', 'other'),
    ('score_sha256', 'other'), ('threads', 2)])
def test_worker_identity_mismatch_is_rejected(field, bad):
    row = {'n': 100, 'label_member_sha256': 'labels'}
    value = receipt()
    validate_worker_receipt(value, row, 'scores')
    value[field] = bad
    with pytest.raises(ValueError, match='mismatch'):
        validate_worker_receipt(value, row, 'scores')


def test_multithreaded_worker_is_rejected():
    value = receipt()
    value['threadpool_info'][0]['num_threads'] = 2
    with pytest.raises(ValueError, match='single-threaded'):
        validate_worker_receipt(value, {'n': 100, 'label_member_sha256': 'labels'}, 'scores')
