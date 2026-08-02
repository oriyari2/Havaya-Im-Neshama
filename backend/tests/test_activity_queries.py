from unittest import TestCase
from unittest.mock import Mock

from backend.app.application.services.activity_service import _visible_is_active
from backend.app.infrastructure.repositories.activity_repository import list_activities


class ActivityQueryTests(TestCase):
    def test_duration_sort_is_whitelisted_and_applied_before_pagination(self):
        cur = Mock(); cur.fetchall.return_value = []
        list_activities(cur, None, None, None, None, None, 25, 0, order_by="duration_minutes")
        sql, params = cur.execute.call_args.args
        self.assertIn("ORDER BY COALESCE(duration_minutes, default_duration_minutes) ASC NULLS LAST", sql)
        self.assertEqual(params[-2:], [25, 0])
        with self.assertRaises(ValueError):
            list_activities(cur, None, None, None, None, None, 25, 0, order_by="unsafe")

    def test_manager_all_has_no_active_predicate(self):
        cur = Mock(); cur.fetchall.return_value = []
        list_activities(cur, None, None, None, None, None, 25, 0)
        sql, params = cur.execute.call_args.args
        self.assertNotIn("is_active = %s", sql)
        self.assertEqual(params, [25, 0])

    def test_role_visibility_forces_non_manager_active(self):
        self.assertIsNone(_visible_is_active({"role": "manager"}, None))
        self.assertIs(_visible_is_active({"role": "manager"}, False), False)
        self.assertIs(_visible_is_active({"role": "instructor"}, False), True)
        self.assertIs(_visible_is_active({"role": "customer"}, None), True)

    def test_text_filters_are_case_insensitive_substrings_and_parameterized(self):
        cur = Mock(); cur.fetchall.return_value = []
        list_activities(cur, " Light ", " Youth ", " Summer ", " team ", True, 10, 5)
        sql, params = cur.execute.call_args.args
        self.assertGreaterEqual(sql.count("ILIKE %s"), 12)
        self.assertIn("%Light%", params); self.assertIn("%Youth%", params); self.assertIn("%Summer%", params); self.assertIn("%team%", params)
        self.assertEqual(params[-2:], [10, 5])
