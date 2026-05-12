import sys
import types
import unittest
from unittest.mock import MagicMock, patch


def _make_frappe_mock():
    """Return a plain MagicMock wired up as the 'frappe' module."""
    mock_frappe = MagicMock()
    # Ensure the module exists in sys.modules so 'import frappe' in setup.py
    # resolves to our mock when the module is first imported.
    sys.modules["frappe"] = mock_frappe
    # Also expose sub-modules that Frappe typically provides.
    for sub in ("frappe.utils", "frappe.model", "frappe.model.document"):
        sys.modules.setdefault(sub, MagicMock())
    return mock_frappe


# Install the mock *before* trade_mvp.setup is imported for the first time.
_frappe_mock = _make_frappe_mock()


class TestCreditLimit(unittest.TestCase):

    def setUp(self):
        # Reset relevant mock attrs before each test so call counts stay clean.
        _frappe_mock.db.get_value.reset_mock()
        _frappe_mock.db.sql.reset_mock()
        _frappe_mock.throw.reset_mock()
        _frappe_mock.format_value.reset_mock()

    def _make_so(self, customer, grand_total):
        so = MagicMock()
        so.customer = customer
        so.grand_total = grand_total
        return so

    def test_unlimited_credit_passes(self):
        """credit_limit=0 means unlimited — must not raise"""
        _frappe_mock.db.get_value.return_value = 0
        from trade_mvp.setup import check_credit_limit
        check_credit_limit(self._make_so("CUST-001", 999_999))
        _frappe_mock.throw.assert_not_called()

    def test_within_limit_passes(self):
        """outstanding=0, SO=30k, limit=50k — must not raise"""
        _frappe_mock.db.get_value.return_value = 50_000
        _frappe_mock.db.sql.return_value = [[0]]
        from trade_mvp.setup import check_credit_limit
        check_credit_limit(self._make_so("CUST-001", 30_000))
        _frappe_mock.throw.assert_not_called()

    def test_over_limit_throws(self):
        """outstanding=40k, SO=20k, limit=50k — must call frappe.throw"""
        _frappe_mock.db.get_value.return_value = 50_000
        _frappe_mock.db.sql.return_value = [[40_000]]
        _frappe_mock.format_value.side_effect = lambda v, _: str(v)
        _frappe_mock.throw.side_effect = Exception("credit limit exceeded")
        from trade_mvp.setup import check_credit_limit
        with self.assertRaises(Exception):
            check_credit_limit(self._make_so("CUST-001", 20_000))
        _frappe_mock.throw.assert_called_once()

    def test_no_customer_skips(self):
        """doc with no customer — must not call db.get_value"""
        from trade_mvp.setup import check_credit_limit
        check_credit_limit(self._make_so(None, 10_000))
        _frappe_mock.db.get_value.assert_not_called()

    def test_exactly_at_limit_passes(self):
        """outstanding=50k, SO=0, limit=50k — equal to limit must pass"""
        _frappe_mock.db.get_value.return_value = 50_000
        _frappe_mock.db.sql.return_value = [[50_000]]
        from trade_mvp.setup import check_credit_limit
        check_credit_limit(self._make_so("CUST-001", 0))
        _frappe_mock.throw.assert_not_called()
