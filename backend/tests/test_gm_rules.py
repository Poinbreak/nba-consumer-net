"""CBA-rule and minutes-allocation tests (no database needed).   Run:  cd backend && python -m unittest discover tests"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nba_net.settings')
os.environ.setdefault('SUPABASE_URL', 'http://x')
os.environ.setdefault('SUPABASE_KEY', 'x')
import django  # noqa: E402

django.setup()
from api import gm  # noqa: E402
from ml import roster_model as rm  # noqa: E402

M = 1_000_000
CAP = gm.CAP


def player(name, salary, locked=False):
    return {'name': name, 'salary': salary, 'locked': locked}


class TradeRules(unittest.TestCase):
    def test_under_the_cap_after_trade_is_always_ok(self):
        ok, problems, _, post = gm.check_side('Team', CAP['cap'] - 30 * M, 15, [player('a', 5 * M)], [player('b', 30 * M)])
        self.assertTrue(ok, problems)
        self.assertEqual(post, CAP['cap'] - 30 * M - 5 * M + 30 * M)

    def test_over_cap_salary_matching_200_percent_plus_250k(self):
        payroll = CAP['cap'] + 10 * M
        ok, *_ = gm.check_side('Team', payroll, 15, [player('a', 10 * M)], [player('b', 20 * M)])      # 20.0 <= 2*10 + 0.25
        self.assertTrue(ok)
        ok, problems, *_ = gm.check_side('Team', payroll, 15, [player('a', 10 * M)], [player('b', 21 * M)])
        self.assertFalse(ok)
        self.assertIn('200%', problems[0])

    def test_above_first_apron_limited_to_110_percent(self):
        payroll = CAP['apron1'] + 5 * M
        ok, *_ = gm.check_side('Team', payroll, 15, [player('a', 20 * M)], [player('b', 22 * M)])       # 22.0 <= 1.1*20 + 0.1
        self.assertTrue(ok)
        ok, problems, *_ = gm.check_side('Team', payroll, 15, [player('a', 20 * M)], [player('b', 23 * M)])
        self.assertFalse(ok)
        self.assertIn('110%', problems[0])

    def test_above_second_apron_cannot_take_back_more_or_combine(self):
        payroll = CAP['apron2'] + 5 * M
        ok, problems, *_ = gm.check_side('Team', payroll, 15, [player('a', 20 * M)], [player('b', 21 * M)])
        self.assertFalse(ok)
        payroll = CAP['apron2'] + 20 * M      # still above the line after sending 20M and taking 15M
        ok, problems, *_ = gm.check_side('Team', payroll, 15, [player('a', 10 * M), player('c', 10 * M)], [player('b', 15 * M)])
        self.assertFalse(ok)
        self.assertTrue(any('combined' in p for p in problems))

    def test_recently_signed_players_cannot_be_traded(self):
        ok, problems, *_ = gm.check_side('Team', CAP['cap'] - 50 * M, 15, [player('Locked', 5 * M, locked=True)], [])
        self.assertFalse(ok)
        self.assertIn('recently signed', problems[0])

    def test_roster_ceiling(self):
        ok, problems, *_ = gm.check_side('Team', CAP['cap'] - 50 * M, gm.ROSTER_MAX, [], [player('b', 1 * M)])
        self.assertFalse(ok)
        self.assertIn('maximum', problems[0])


class Minutes(unittest.TestCase):
    def test_total_is_240_and_cap_respected(self):
        for mpg in ([30, 28, 25, 20, 12, 10, 8, 5], [38] * 10, [5] * 14, [34, 33, 32, 31, 30, 29, 25, 20, 15, 10, 8, 6]):
            m = rm.allocate_minutes(mpg, list(range(len(mpg), 0, -1)))
            self.assertAlmostEqual(m.sum(), 240.0, places=6)
            self.assertLessEqual(m.max(), 38.0 + 1e-9)

    def test_shortfall_goes_to_best_players(self):
        m = rm.allocate_minutes([20, 20, 20, 20], [1, 4, 3, 2])        # only 80 mpg: best players fill up first
        self.assertEqual(m[1], 38.0)
        self.assertGreaterEqual(m[2], m[3])


if __name__ == '__main__':
    unittest.main()
