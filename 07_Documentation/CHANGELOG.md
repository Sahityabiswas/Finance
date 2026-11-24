# Changelog

All corrections apply to 02_Completed_Project. The supplied archive's extracted files are covered by the original SHA-256 manifest.

| File | Change and reason |
| --- | --- |
| scripts/analyze.py | Kept INR 0.011 tolerance for the five agreeing closes and added one precise documented exception for MUTHOOTFIN's vendor close rounding to 3811.70 versus the 3811.75 archived NSE underlying. The official cash-market close also equals 3811.70. Recorded check status. Inputs and formulas are unchanged. A new discrepancy still stops execution. |
| scripts/options_analyze.py | Replaced two attribute accesses with dictionary indexing for the existing actual-expiry date and trade date fields. Their difference yields the original intended ACT/365 maturity. |
| scripts/build_workbook.mjs | Mapped open interest in contracts to open_interest_contracts and implied volatility to derived_iv. Clarified the OI heading. Added generated workbook input JSON through separate output preparation. |
| scripts/build_report.py and report_tools.py | Retained formatting and narrative infrastructure. Restored the proposal title hyphenation, replaced the incomplete empty TOC field, added report sections from outputs, extra equations and a real document entry point. Removed the working copy's unused dependency-bundle path. |
| scripts/complete_outputs.py | Generates workbook input JSON, two portfolio CSVs and four supplementary charts from calculations. |
| scripts/build_workbook_portable.py, scripts/office.py, templates/ | Populates the original workbook layout with current analysis data and recalculates formulas. Uses isolated LibreOffice profiles and staging for XLSX and PDF. |
| run_all.py, requirements.txt | Adds a single offline run and a tested Python 3.12 dependency lock. |
| validate_results.py, validation/reference_results.json | Checks raw inputs, recalculates independent estimates, verifies workbook caches and report presence, and compares to the delivered run. |
| 03–07 deliverable folders | Copies verified numerical results and publication files, preserves debugging evidence and documents the workflow. |

The fresh source-download scripts were exercised in an isolated directory. The archived inputs were used for published results. The historical analysis code retains the original acquisition and financial design. 
