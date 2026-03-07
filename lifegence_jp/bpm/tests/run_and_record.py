#!/usr/bin/env python3
"""Parse unittest output from bench run-tests and update the markdown test procedure.

Usage:
    bench run-tests --app lifegence_bpm \
      --module lifegence_bpm.tests.test_workflow_transitions 2>&1 | \
      python apps/lifegence_bpm/lifegence_bpm/tests/run_and_record.py

The script:
  1. Reads unittest output from stdin
  2. Extracts pass/fail/error status for each test case
  3. Updates docs/manual_workflow_test_procedure.md with results
  4. Prints a summary to stdout
"""

import os
import re
import sys
from datetime import date

# ─── Configuration ──────────────────────────────────────────────────────────
DOCS_PATH = os.path.join(
	os.path.dirname(__file__), os.pardir, os.pardir, "docs", "manual_workflow_test_procedure.md"
)

# Map test method names to test case IDs
TEST_METHOD_TO_TC = {
	"test_tc_l01_lead_normal_flow": "TC-L01",
	"test_tc_l02_lead_disqualify_resubmit": "TC-L02",
	"test_tc_l03_lead_request_changes": "TC-L03",
	"test_tc_l04_lead_self_approval_prevention": "TC-L04",
	"test_tc_o01_opportunity_normal_approval": "TC-O01",
	"test_tc_o02_opportunity_reject_resubmit": "TC-O02",
	"test_tc_o03_opportunity_request_changes": "TC-O03",
	"test_tc_o04_opportunity_convert": "TC-O04",
	"test_tc_o05_opportunity_mark_as_lost": "TC-O05",
	"test_tc_q01_quotation_under_5m": "TC-Q01",
	"test_tc_q02_quotation_5m_to_20m": "TC-Q02",
	"test_tc_q03_quotation_over_20m": "TC-Q03",
	"test_tc_q04_quotation_confirm_submit": "TC-Q04",
	"test_tc_q05_quotation_reject_resubmit": "TC-Q05",
	"test_tc_s01_sales_order_under_20m": "TC-S01",
	"test_tc_s02_sales_order_20m_to_100m": "TC-S02",
	"test_tc_s03_sales_order_over_100m": "TC-S03",
	"test_tc_s04_sales_order_confirm": "TC-S04",
	"test_tc_s05_sales_order_reject_resubmit": "TC-S05",
	"test_tc_p01_purchase_order_under_10m": "TC-P01",
	"test_tc_p02_purchase_order_10m_to_50m": "TC-P02",
	"test_tc_p03_purchase_order_over_50m": "TC-P03",
	"test_tc_p04_purchase_order_budget_reject": "TC-P04",
	"test_tc_p05_purchase_order_confirm": "TC-P05",
	"test_tc_p06_purchase_order_reject_resubmit": "TC-P06",
}


def parse_test_output(text):
	"""Parse unittest output and return dict of {test_method: 'OK'|'FAIL'|'ERROR'}.

	Supports both verbose output (method ... ok/FAIL/ERROR) and non-verbose
	output (dots + error/failure blocks).
	"""
	results = {}

	# ── Try verbose format first ──────────────────────────────────────────
	# Pattern: "test_method (module.Class) ... ok" or "... FAIL" or "... ERROR"
	line_pattern = re.compile(
		r"(test_tc_\w+)\s+\(.*?\)\s+\.\.\.\s+(ok|FAIL|ERROR)", re.IGNORECASE
	)

	for line in text.splitlines():
		m = line_pattern.search(line)
		if m:
			method = m.group(1)
			status = m.group(2).upper()
			results[method] = status

	if results:
		return results

	# ── Try non-verbose format (bench run-tests default) ──────────────────
	# Non-verbose output:
	#   .........................     (dots for pass, F for fail, E for error)
	#   Ran 25 tests in 8.414s
	#   OK
	# Or with failures:
	#   ..................E......
	#   ERROR: test_tc_q04... (module.Class)
	#   FAIL: test_tc_l01... (module.Class)
	#   Ran 25 tests in 8.414s
	#   FAILED (errors=1)

	# Extract FAIL/ERROR block headers
	fail_error_pattern = re.compile(
		r"^(?:ERROR|FAIL):\s+(test_tc_\w+)\s+\(", re.MULTILINE
	)
	failed_methods = {}
	for m in fail_error_pattern.finditer(text):
		method = m.group(1)
		# Determine if ERROR or FAIL from the prefix
		prefix_line = text[m.start():m.start() + 10]
		if prefix_line.startswith("ERROR"):
			failed_methods[method] = "ERROR"
		else:
			failed_methods[method] = "FAIL"

	# Check overall test result
	ran_pattern = re.compile(r"Ran\s+(\d+)\s+tests?\s+in")
	ran_match = ran_pattern.search(text)

	# Detect "OK" on its own line (after "Ran N tests in X.Xs")
	all_ok = False
	lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
	for i, line in enumerate(lines):
		if ran_pattern.search(line):
			# Check subsequent lines for "OK"
			for j in range(i + 1, min(i + 3, len(lines))):
				if lines[j] == "OK":
					all_ok = True
					break
			break
	# Also check if the last non-empty line is "OK"
	if not all_ok and lines and lines[-1] == "OK":
		all_ok = True

	if ran_match or failed_methods:
		# Mark failed/errored tests
		for method, status in failed_methods.items():
			if method in TEST_METHOD_TO_TC:
				results[method] = status

		# Mark remaining known tests as OK if overall result is OK
		# or if we have explicit fail/error info for some tests
		if all_ok:
			# All tests passed
			for method in TEST_METHOD_TO_TC:
				results[method] = "OK"
		elif failed_methods:
			# Some failed — mark the rest as OK
			for method in TEST_METHOD_TO_TC:
				if method not in results:
					results[method] = "OK"

	return results


def update_markdown(results):
	"""Update the test result table in the markdown file."""
	md_path = os.path.normpath(DOCS_PATH)
	if not os.path.exists(md_path):
		print(f"WARNING: Markdown file not found: {md_path}")
		return False

	with open(md_path, "r", encoding="utf-8") as f:
		content = f.read()

	today_str = date.today().isoformat()

	# Build TC-ID → result mapping
	tc_results = {}
	for method, status in results.items():
		tc_id = TEST_METHOD_TO_TC.get(method)
		if tc_id:
			tc_results[tc_id] = status

	# Update each table row matching "| TC-XXX |"
	# Pattern: | TC-L01      | テスト名 | 日付 | 実施者 | 結果 | 備考 |
	def replace_row(match):
		full_line = match.group(0)
		tc_id = match.group(1).strip()
		if tc_id not in tc_results:
			return full_line

		status = tc_results[tc_id]
		result_mark = "PASS" if status == "OK" else status

		# Split the row into cells
		cells = full_line.split("|")
		if len(cells) >= 7:
			# cells[0] = "", cells[1]=TC-ID, cells[2]=name, cells[3]=date, cells[4]=executor, cells[5]=result, cells[6]=notes
			cells[3] = f" {today_str} "
			cells[4] = " auto "
			cells[5] = f" {result_mark} "
			if status != "OK" and cells[6].strip() == "":
				cells[6] = f" {status} "
			return "|".join(cells)

		return full_line

	row_pattern = re.compile(r"^\|[^|]*?(TC-[LOQSP]\d{2})\s*\|.*$", re.MULTILINE)
	updated = row_pattern.sub(replace_row, content)

	with open(md_path, "w", encoding="utf-8") as f:
		f.write(updated)

	return True


def print_summary(results):
	"""Print a formatted summary of test results."""
	print("\n" + "=" * 60)
	print("  Lifegence BPM Workflow Test Results")
	print("=" * 60)

	ok_count = sum(1 for v in results.values() if v == "OK")
	fail_count = sum(1 for v in results.values() if v == "FAIL")
	error_count = sum(1 for v in results.values() if v == "ERROR")
	total = len(results)

	# Group by workflow
	groups = {
		"Lead": [m for m in results if "_l0" in m],
		"Opportunity": [m for m in results if "_o0" in m],
		"Quotation": [m for m in results if "_q0" in m],
		"Sales Order": [m for m in results if "_s0" in m],
		"Purchase Order": [m for m in results if "_p0" in m],
	}

	for group_name, methods in groups.items():
		if not methods:
			continue
		print(f"\n  {group_name}:")
		for method in sorted(methods):
			tc_id = TEST_METHOD_TO_TC.get(method, method)
			status = results[method]
			mark = "PASS" if status == "OK" else status
			symbol = "[OK]" if status == "OK" else "[!!]"
			print(f"    {symbol} {tc_id}: {mark}")

	print(f"\n  Summary: {ok_count} passed, {fail_count} failed, {error_count} errors / {total} total")

	if total == 0:
		print("\n  WARNING: No test results parsed. Check that tests ran correctly.")

	print("=" * 60 + "\n")


def main():
	text = sys.stdin.read()
	results = parse_test_output(text)
	print_summary(results)

	if update_markdown(results):
		md_path = os.path.normpath(DOCS_PATH)
		print(f"Updated: {md_path}")
	else:
		print("Markdown file not updated (file not found).")

	# Exit with non-zero if any failures
	if any(v != "OK" for v in results.values()):
		sys.exit(1)
	if not results:
		sys.exit(2)


if __name__ == "__main__":
	main()
