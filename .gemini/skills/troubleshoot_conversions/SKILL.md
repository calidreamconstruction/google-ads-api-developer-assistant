---
name: troubleshoot_conversions
description: Investigates conversion upload issues and generates a structured diagnostic report based on Google Ads API conversion summaries and alerts.
---

# Troubleshoot Conversions

This skill investigates conversion upload issues and generates a structured diagnostic report by executing the mandatory conversion troubleshooting workflow.

## 1. Execution Instructions [MANDATORY]

When invoked to troubleshoot conversions:
1. Locate the required `customer_id` (from context or `customer_id.txt`). If missing, prompt the user.
2. Execute the mandatory diagnostic collector script within the sequestered virtual environment. As it runs, it will output high-level client and action summaries to stdout to inform your analysis:
```bash
./.venv/bin/python3 .gemini/skills/troubleshoot_conversions/scripts/troubleshoot_conversions.py --customer_id <customer_id> --api_version <api_version>
```
3. Note the consolidated troubleshooting report path returned by the script (e.g., `saved/data/conversion_troubleshooting_report_<epoch>.txt`).

## 2. Diagnostic Queries & Calculations

When analyzing conversion data directly:
- **Diagnostic Summaries**: Query both `offline_conversion_upload_client_summary` and `offline_conversion_upload_conversion_action_summary`.
- **Attributes & Totals**: Use `successful_count` and `failed_count`. Calculate daily total as `successful_count + failed_count + pending_count` (top-level `total_event_count` is only available on parent resources).
- **Alert Inspection**: Access `alerts` (OfflineConversionAlert) at the top-level resource. Inspect `alert.error` oneof via `WhichOneof("error_code")` and report `error_percentage`. If summaries are empty, append exactly: `Reason: No standard offline imports detected in last 90 days`.

## 3. Structured Screen Output & Reporting

You MUST structure your final response and duplicate this exact structure inside the output report file along with the details of each conversion:

```text
1. Introductory Conversion Analysis
For Customer ID: 8466202666, the overall conversion upload health is generally strong for API and Web Client imports (EXCELLENT), but shows significant degradation for the Ads Data Connector (GOOD). Approximately 12.47% of events via the Ads Data Connector are failing, primarily due to expiration issues.

2. Primary Errors & Critical Issues
 * EXPIRED_EVENT (12.00% - 100.00%): This is the most critical blocker. Several actions, including "When Status becomes New" and "DM API TEST [Not used]Hybrid Test", are seeing 100% failure rates. This indicates that conversions are being uploaded outside the supported lookback window (typically 90 days for GCLID-based uploads).
 * UNKNOWN Alert (100.00%): Actions "32-bit Purchase EC Tag - DDA" and "64-bit Type Purchase" are reporting 100% unknown alerts despite having high success counts, suggesting a potential metadata or reporting discrepancy in the diagnostic summaries.
 * ADS_DATA_CONNECTOR Health: This client is consistently failing ~1,000 events daily, dragging down the overall integration health.

3. General Health & Technical Findings
 * GOOGLE_ADS_API: EXCELLENT status with 6,974/6,976 successful uploads (99.97%).
 * GOOGLE_ADS_WEB_CLIENT: EXCELLENT status with 10,981/11,006 successful uploads (99.77%).
 * ADS_DATA_CONNECTOR: GOOD status with 8,119/9,276 successful uploads (87.53%).
 * BulkSheet Actions: Most "Dyetest" BulkSheet actions show 100% success, but action #57 is failing 100% due to EXPIRED_EVENT.

4. Actionable Recommendations
 1. Resolve Expiration Blocker: Verify the conversion_time for failing actions. Ensure events are uploaded within the 90-day window relative to the click time.
 2. Verify Data Terms: Ensure "Customer Data Terms" have been accepted in the Google Ads UI, as this can sometimes lead to UNKNOWN or unconsented event failures.
 3. Audit Ads Data Connector: Investigate the source pipeline for the Ads Data Connector to identify why a fixed portion of daily events (~12%) are consistently arriving as "expired."
 4. Review Lookback Settings: For the actions with 100% failure, check if the conversion window settings in Google Ads match the actual business lag between click and conversion.
```

## 4. Consolidation Mandate

All findings—including terminal summaries, structured analysis, verbatim screen output, and complete query data—MUST be consolidated into the single self-contained output report file generated in `saved/data/`. This file MUST start with the exact header `Created by the Google Ads API Developer Assistant` and MUST be the sole artifact submitted to the user for support. Placeholders or external references are strictly prohibited.