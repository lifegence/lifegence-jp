# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

"""
Tests for bpm/automation/dispatcher.py — document update trigger dispatch.

Covers:
  1. on_document_update — no workflow_state attribute
  2. on_document_update — same state (no change)
  3. on_document_update — automation disabled in settings
  4. on_document_update — BPM Settings not found
  5. on_document_update — state change with matching BPM Actions
  6. on_document_update — previous_state filter
  7. on_document_update — condition evaluation
  8. on_document_update — background vs foreground execution
  9. on_document_update — condition evaluation failure
"""

import frappe
from frappe.tests.utils import FrappeTestCase
from unittest.mock import patch, MagicMock, call


class TestOnDocumentUpdate(FrappeTestCase):
    """Tests for on_document_update dispatcher."""

    def _make_doc(self, doctype="Sales Order", name="SO-001",
                  workflow_state="Approved", is_new=False):
        doc = MagicMock()
        doc.doctype = doctype
        doc.name = name
        doc.workflow_state = workflow_state
        doc.is_new.return_value = is_new
        return doc

    def test_no_workflow_state(self):
        """Documents without workflow_state should be silently skipped."""
        from lifegence_jp.bpm.automation.dispatcher import on_document_update
        doc = MagicMock(spec=[])  # No attributes
        # Should not raise
        on_document_update(doc, "on_update")

    def test_same_state_no_dispatch(self):
        """No dispatch when workflow_state hasn't changed."""
        from lifegence_jp.bpm.automation.dispatcher import on_document_update
        doc = self._make_doc(workflow_state="Draft")
        doc.get_db_value.return_value = "Draft"

        with patch("lifegence_jp.bpm.automation.dispatcher.frappe.get_cached_doc") as mock_settings:
            on_document_update(doc, "on_update")
            mock_settings.assert_not_called()

    def test_automation_disabled(self):
        """No dispatch when automation is disabled in settings."""
        from lifegence_jp.bpm.automation.dispatcher import on_document_update
        doc = self._make_doc(workflow_state="Approved")
        doc.get_db_value.return_value = "Draft"

        settings = MagicMock()
        settings.enable_automation = False

        with patch("lifegence_jp.bpm.automation.dispatcher.frappe.get_cached_doc", return_value=settings):
            with patch("lifegence_jp.bpm.automation.dispatcher.frappe.get_all") as mock_get_all:
                on_document_update(doc, "on_update")
                mock_get_all.assert_not_called()

    def test_settings_not_found(self):
        """Gracefully handles missing BPM Settings (first run)."""
        from lifegence_jp.bpm.automation.dispatcher import on_document_update
        doc = self._make_doc(workflow_state="Approved")
        doc.get_db_value.return_value = "Draft"

        with patch("lifegence_jp.bpm.automation.dispatcher.frappe.get_cached_doc",
                   side_effect=frappe.DoesNotExistError("BPM Settings")):
            # Should not raise
            on_document_update(doc, "on_update")

    def test_dispatches_matching_actions(self):
        """Matching BPM Actions should be dispatched."""
        from lifegence_jp.bpm.automation.dispatcher import on_document_update
        doc = self._make_doc(workflow_state="Approved")
        doc.get_db_value.return_value = "Draft"

        settings = MagicMock()
        settings.enable_automation = True

        actions = [
            {"name": "ACT-001", "previous_state": None, "condition": None, "run_in_background": False},
        ]

        with patch("lifegence_jp.bpm.automation.dispatcher.frappe.get_cached_doc", return_value=settings):
            with patch("lifegence_jp.bpm.automation.dispatcher.frappe.get_all", return_value=actions):
                with patch("lifegence_jp.bpm.automation.handlers.execute_action") as mock_exec:
                    on_document_update(doc, "on_update")
                    mock_exec.assert_called_once_with(
                        action_name="ACT-001",
                        reference_doctype="Sales Order",
                        reference_name="SO-001",
                        workflow_state="Approved",
                        previous_state="Draft",
                    )

    def test_previous_state_filter(self):
        """Actions with previous_state filter should only run when matching."""
        from lifegence_jp.bpm.automation.dispatcher import on_document_update
        doc = self._make_doc(workflow_state="Approved")
        doc.get_db_value.return_value = "Submitted"  # Was Submitted, not Draft

        settings = MagicMock()
        settings.enable_automation = True

        actions = [
            {"name": "ACT-001", "previous_state": "Draft", "condition": None, "run_in_background": False},
        ]

        with patch("lifegence_jp.bpm.automation.dispatcher.frappe.get_cached_doc", return_value=settings):
            with patch("lifegence_jp.bpm.automation.dispatcher.frappe.get_all", return_value=actions):
                with patch("lifegence_jp.bpm.automation.handlers.execute_action") as mock_exec:
                    on_document_update(doc, "on_update")
                    mock_exec.assert_not_called()

    def test_condition_evaluation(self):
        """Actions with conditions should evaluate them against the document."""
        from lifegence_jp.bpm.automation.dispatcher import on_document_update
        doc = self._make_doc(workflow_state="Approved")
        doc.get_db_value.return_value = "Draft"

        settings = MagicMock()
        settings.enable_automation = True

        actions = [
            {"name": "ACT-001", "previous_state": None, "condition": "doc.grand_total > 100000", "run_in_background": False},
        ]

        with patch("lifegence_jp.bpm.automation.dispatcher.frappe.get_cached_doc", return_value=settings):
            with patch("lifegence_jp.bpm.automation.dispatcher.frappe.get_all", return_value=actions):
                # Condition evaluates to False
                with patch("lifegence_jp.bpm.automation.dispatcher.frappe.safe_eval", return_value=False):
                    with patch("lifegence_jp.bpm.automation.handlers.execute_action") as mock_exec:
                        on_document_update(doc, "on_update")
                        mock_exec.assert_not_called()

    def test_condition_true_dispatches(self):
        """Actions with condition=True should be dispatched."""
        from lifegence_jp.bpm.automation.dispatcher import on_document_update
        doc = self._make_doc(workflow_state="Approved")
        doc.get_db_value.return_value = "Draft"

        settings = MagicMock()
        settings.enable_automation = True

        actions = [
            {"name": "ACT-001", "previous_state": None, "condition": "doc.grand_total > 100000", "run_in_background": False},
        ]

        with patch("lifegence_jp.bpm.automation.dispatcher.frappe.get_cached_doc", return_value=settings):
            with patch("lifegence_jp.bpm.automation.dispatcher.frappe.get_all", return_value=actions):
                with patch("lifegence_jp.bpm.automation.dispatcher.frappe.safe_eval", return_value=True):
                    with patch("lifegence_jp.bpm.automation.handlers.execute_action") as mock_exec:
                        on_document_update(doc, "on_update")
                        mock_exec.assert_called_once()

    def test_background_execution(self):
        """Actions with run_in_background should be enqueued."""
        from lifegence_jp.bpm.automation.dispatcher import on_document_update
        doc = self._make_doc(workflow_state="Approved")
        doc.get_db_value.return_value = "Draft"

        settings = MagicMock()
        settings.enable_automation = True

        actions = [
            {"name": "ACT-001", "previous_state": None, "condition": None, "run_in_background": True},
        ]

        with patch("lifegence_jp.bpm.automation.dispatcher.frappe.get_cached_doc", return_value=settings):
            with patch("lifegence_jp.bpm.automation.dispatcher.frappe.get_all", return_value=actions):
                with patch("lifegence_jp.bpm.automation.dispatcher.frappe.enqueue") as mock_enqueue:
                    on_document_update(doc, "on_update")
                    mock_enqueue.assert_called_once()
                    call_kwargs = mock_enqueue.call_args
                    self.assertEqual(call_kwargs.kwargs["action_name"], "ACT-001")

    def test_condition_error_skips_action(self):
        """Condition evaluation errors should skip the action, not crash."""
        from lifegence_jp.bpm.automation.dispatcher import on_document_update
        doc = self._make_doc(workflow_state="Approved")
        doc.get_db_value.return_value = "Draft"

        settings = MagicMock()
        settings.enable_automation = True

        actions = [
            {"name": "ACT-001", "previous_state": None, "condition": "bad_expression()", "run_in_background": False},
        ]

        with patch("lifegence_jp.bpm.automation.dispatcher.frappe.get_cached_doc", return_value=settings):
            with patch("lifegence_jp.bpm.automation.dispatcher.frappe.get_all", return_value=actions):
                with patch("lifegence_jp.bpm.automation.dispatcher.frappe.safe_eval",
                           side_effect=Exception("eval error")):
                    with patch("lifegence_jp.bpm.automation.dispatcher.frappe.log_error") as mock_log:
                        with patch("lifegence_jp.bpm.automation.handlers.execute_action") as mock_exec:
                            on_document_update(doc, "on_update")
                            mock_exec.assert_not_called()
                            mock_log.assert_called()

    def test_new_document_no_old_state(self):
        """New documents should have old_state=None."""
        from lifegence_jp.bpm.automation.dispatcher import on_document_update
        doc = self._make_doc(workflow_state="Draft", is_new=True)

        settings = MagicMock()
        settings.enable_automation = True

        actions = [
            {"name": "ACT-001", "previous_state": None, "condition": None, "run_in_background": False},
        ]

        with patch("lifegence_jp.bpm.automation.dispatcher.frappe.get_cached_doc", return_value=settings):
            with patch("lifegence_jp.bpm.automation.dispatcher.frappe.get_all", return_value=actions):
                with patch("lifegence_jp.bpm.automation.handlers.execute_action") as mock_exec:
                    on_document_update(doc, "on_update")
                    call_kwargs = mock_exec.call_args
                    self.assertIsNone(call_kwargs.kwargs["previous_state"])
