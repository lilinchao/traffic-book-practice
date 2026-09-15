"""Check real-case exports and small isolated algorithm invariants."""
import hashlib
import json
import unittest

import numpy as np

from case_algorithms import OUTPUT, ROOT, associate, count_events, metrics, state_forecasts


class AlgorithmsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = {c: json.loads((OUTPUT / f'ch{c}.json').read_text(encoding='utf-8')) for c in range(4, 9)}

    def test_sources_and_table_shapes(self):
        for chapter, result in self.data.items():
            self.assertEqual(result['chapter'], chapter)
            self.assertEqual(len(result['cases']), 2)
            for path, digest in result['inputs'].items():
                self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), digest)
            for case in result['cases'].values():
                for t in case['tables']:
                    self.assertTrue(t['rows'])
                    self.assertTrue(all(len(r) == len(t['columns']) for r in t['rows']))
                    self.assertTrue(all(np.isfinite(x) for r in t['rows'] for x in r if isinstance(x, (float, int))))

    def test_regression_predictions_match_tables(self):
        d = self.data[4]['details']
        rows = np.array([r[3:] for r in d['test_rows']])
        self.assertEqual(len(rows), 4376)
        self.assertEqual(len({r[0] for r in d['test_rows']}), 4376)
        self.assertFalse(any('casual' in n or 'registered' in n for n in d['feature_names']))
        for i, row in enumerate(self.data[4]['cases']['bike-leakage']['tables'][0]['rows']):
            np.testing.assert_allclose(row[1:], metrics(rows[:, 0], rows[:, i+1]))
        selection = self.data[4]['cases']['poisson-ridge']['tables'][0]['rows']
        self.assertEqual(d['selected_alpha'], min(selection, key=lambda r: (r[3], r[0]))[0])

    def test_spatial_masks_and_memberships(self):
        d = self.data[5]['details']
        self.assertEqual(len(d['xy_m']), 7068)
        self.assertEqual(len(d['cells']), 2069)
        for values in d['dbscan'].values():
            self.assertEqual(len(values), len(d['xy_m']))
            self.assertTrue(all(isinstance(v, int) and v >= -1 for v in values))
        t = self.data[5]['cases']['no-coordinates']['tables'][0]['rows']
        self.assertEqual(t[1][1], t[2][1])
        self.assertEqual(t[0][3], 20)
        for r in t:
            self.assertEqual(r[1]+r[2], 7068)

    def test_temporal_protocol_and_results(self):
        d = self.data[6]['details']
        self.assertEqual(len(d['targets']), 2169)
        self.assertTrue(all('2018-07' <= t < '2018-10' for t in d['targets']))
        for row in self.data[6]['cases']['forecast-origin']['tables'][0]['rows']:
            if row[0] in d['predictions']:
                np.testing.assert_allclose(row[2:], metrics(d['actual'], d['predictions'][row[0]][str(row[1])]))
        self.assertTrue(all(m['converged'] for m in d['fits'].values()))

    def test_filtered_state_future_invariance(self):
        from statsmodels.tsa.statespace.sarimax import SARIMAX
        # Synthetic unit test only; not used as a teaching observation or result.
        values = np.sin(np.arange(100)/4)+2
        model = SARIMAX(values[:60], order=(1, 0, 0), trend='c').fit(disp=False)
        original = SARIMAX(values, order=(1, 0, 0), trend='c').filter(model.params)
        changed = values.copy(); changed[71:] += 10000
        modified = SARIMAX(changed, order=(1, 0, 0), trend='c').filter(model.params)
        for h in [1, 3, 6]:
            a = state_forecasts(original, [70+h], [h])[h]
            b = state_forecasts(modified, [70+h], [h])[h]
            np.testing.assert_allclose(a, b)

    def test_var_common_targets_and_cluster_memberships(self):
        d = self.data[7]['details']
        self.assertEqual(d['test_hour_indices'], list(range(24*24, 31*24)))
        self.assertEqual(np.array(d['actual']).shape, (168, 4))
        for name, prediction in d['predictions'].items():
            self.assertEqual(np.array(prediction).shape, (168, 4))
            row = next(r for r in self.data[7]['cases']['weekday-denominator']['tables'][0]['rows'] if r[0] == name)
            np.testing.assert_allclose(row[1:], metrics(np.array(d['actual']).ravel(), np.array(prediction).ravel()))
        for key, members in d['memberships'].items():
            self.assertEqual(len(members), 31)
            self.assertEqual(len(set(members)), int(key.split('-')[0]))
        np.testing.assert_allclose(np.array(d['profile_shares']).sum(axis=1), np.ones(31))

    def test_assignment_is_not_row_order_and_no_future(self):
        a = [(0., np.array([[0., 0.], [10., 0.]])), (.1, np.array([[9.9, 0.], [.1, 0.]]))]
        for mode in ['position', 'kalman']:
            labels = associate(a, mode)
            self.assertEqual(labels, [[1, 2], [2, 1]])
            extended = associate(a+[(.2, np.array([[100., 100.]]))], mode)
            self.assertEqual(extended[:2], labels)

    def test_events_and_actual_reference_reassociation(self):
        for variant, d in self.data[8]['details'].items():
            self.assertEqual(len({(r[0], r[2]) for r in d['assignments']}), len(d['assignments']))
            predicted = [[r[1], r[2], r[3], r[4]] for r in d['assignments']]
            reference = [[r[0], r[2], r[3], r[4]] for r in d['assignments']]
            self.assertEqual(count_events(predicted), d['events'])
            # Source IDs are strings in the audit, so normalize reference IDs for comparison.
            self.assertEqual([(str(r[0]), *r[1:]) for r in count_events(reference)], [(str(r[0]), *r[1:]) for r in d['reference_events']])
        self.assertEqual(len(self.data[8]['details']['1-kalman']['reference_events']), 20)


if __name__ == '__main__':
    unittest.main(verbosity=2)
