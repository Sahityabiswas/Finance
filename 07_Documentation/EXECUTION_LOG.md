# Execution record

The files under logs/ are process output captured during the completion work on 18 November 2026. Terminal paths in these logs refer to the test environment.

| Log | Command and outcome |
| --- | --- |
| equity-original.log | Original logic with `python scripts/analyze.py --no-charts` stopped on the MUTHOOTFIN close check. |
| options-original.log | Original `python scripts/options_analyze.py` stopped on dictionary attribute access. |
| workbook-original.log | Original `node build_workbook.mjs` exited 1 because workbook_equity_inputs.json was absent. |
| equity-repaired.log, options-repaired.log | Successful runs of the minimally repaired analysis scripts, with their numeric output. |
| workbook-js.log | Original workbook architecture exercised under Node 24.22.3 with artifact-tool 2.8.169. Cached formula scan found zero matches. It includes the rate-change check and all summary/option values. |
| yahoo-acquisition.log, nse-acquisition.log | Optional source scripts exercised in an isolated project. Fresh Yahoo payload hashes differed from the frozen records. Two NSE URLs returned matching archives and two fallbacks returned 404. |
| nse-cash-crosscheck.log | Two supplementary official NSE cash-market files confirmed the MUTHOOTFIN close at 3811.70 INR. |
| clean-install.log, clean-pipeline.log | Dependency installation and full offline run in a fresh venv, with generated files absent before execution. |
| original-integrity.log | Original files compared to both the uploaded ZIP and the SHA-256 manifest. |
| archive-rebuild.log | Final package extraction, integrity check and offline rebuild. |
| final-report-validation.log | Rebuilt the report from the extracted project after adding the supplementary cash-market cross-check. Report and numerical checks passed. |

The public npm package lookup returned E404. The original Windows Word PowerShell exporter requires desktop Microsoft Word and COM. The Linux build used LibreOffice Writer. The portable XLSX was opened and recalculated in LibreOffice Calc, including a rate-edit test isolated from the published workbook.
