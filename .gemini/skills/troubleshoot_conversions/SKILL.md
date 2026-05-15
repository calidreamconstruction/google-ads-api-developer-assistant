---
name: troubleshoot_conversions
description: Investigates conversion upload issues and generates a structured diagnostic report based on Google Ads API conversion summaries and alerts.
---

# Troubleshoot Conversions

This skill investigates conversion upload issues and generates a structured diagnostic report by executing the mandatory conversion troubleshooting workflow.

## 1. Execution Instructions [MANDATORY]

When invoked to troubleshoot conversions:
1. Locate the required `customer_id` (from context or `customer_id.txt`). If missing, prompt the user.
2. Execute the mandatory diagnostic collector script within the sequestered virtual environment:
```bash
./.venv/bin/python3 api_examples/collect_conversions_troubleshooting_data.py --customer_id <customer_id> --api_version v23
```
3. Note the consolidated troubleshooting report path returned by the script (e.g., `saved/data/conversion_troubleshooting_report_<epoch>.txt`).

## 2. Diagnostic Queries & Calculations

When analyzing conversion data directly:
- **Diagnostic Summaries**: Query both `offline_conversion_upload_client_summary` and `offline_conversion_upload_conversion_action_summary`.
- **Attributes & Totals**: Use `successful_count` and `failed_count`. Calculate daily total as `successful_count + failed_count + pending_count` (top-level `total_event_count` is only available on parent resources).
- **Alert Inspection**: Access `alerts` (OfflineConversionAlert) at the top-level resource. Inspect `alert.error` oneof via `WhichOneof("error_code")` and report `error_percentage`. If summaries are empty, append exactly: `Reason: No standard offline imports detected in last 90 days`.

## 3. Structured Screen Output & Reporting

You MUST structure your final response and report to the user exactly as follows:
1. **Introductory Analysis**: State the Customer ID and provide a high-level summary overview of the problems identified (max 3 sentences, categorized with percentages).
2. **Primary Errors & Critical Issues**: Detailed breakdown of specific action failures, root causes, and fixes.
3. **General Health & Technical Findings**: Bulleted specific observations highlighting success rates and error occurrences.
4. **Actionable Recommendations**: Clear, prioritized next steps for the user.

## 4. Consolidation Mandate

All findings—including terminal summaries, structured analysis, verbatim screen output, and complete query data—MUST be consolidated into the single self-contained output report file generated in `saved/data/`. This file MUST start with the exact header `Created by the Google Ads API Developer Assistant` and MUST be the sole artifact submitted to the user for support. Placeholders or external references are strictly prohibited.