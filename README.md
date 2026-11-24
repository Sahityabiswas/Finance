# Risk-Return Analysis and Derivative-Based Comparison of NBFCs and Commercial Banks in India

This project compares three bank and three NBFC equities over 2021–2025, three daily-rebalanced portfolios, and four NSE options observed on 31 December 2025. NIFTY 50 price returns supply the benchmark. The common panel contains 1,237 closes including 31 December 2020 and 1,236 daily returns per series.

## Open and run in VS Code

1. Extract the ZIP with an extractor that supports long paths. On Windows, extract near the drive root if your extractor reports long-path errors for the original bundled dependencies.
2. Open **02_Completed_Project** as the folder in VS Code. Install Python 3.12 and the VS Code Python extension.
3. Install LibreOffice for the Excel recalculation and PDF export. On Windows the default installer location is detected. On Debian or Ubuntu, install `libreoffice-calc` and `libreoffice-writer`. If using a custom location, set `FINANCE_SOFFICE` to the full path to `soffice` or `soffice.exe`. Path values can include spaces.
4. Open **Terminal → New Terminal** and run the appropriate commands.

Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run_all.py
.\.venv\Scripts\python.exe validate_results.py
```

Linux Bash

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run_all.py
.venv/bin/python validate_results.py
```

In VS Code, use **Python: Select Interpreter** to select the .venv interpreter. In an activated virtual environment, the run command is `python run_all.py`. If PowerShell activation is restricted, use the direct interpreter commands above. Initial installation may require internet access. The analysis pipeline runs offline after setup.

## Run steps independently

Run from **02_Completed_Project** in the environment above. These are the underlying steps.

```bash
python scripts/analyze.py
python scripts/options_analyze.py
python scripts/complete_outputs.py
python scripts/build_workbook_portable.py
python scripts/build_report.py
python validate_results.py
```

The unified entry point also calls LibreOffice Writer to create the PDF, which the validator expects. To export only the PDF, open the DOCX in Writer and select **File → Export As → Export as PDF**, saving to `output/Final_Research_Report.pdf`. Use `python run_all.py --analysis-only` for CSV, JSON and charts without LibreOffice. If a stage fails, the runner prints its exit status. Close any open workbook or report before rebuilding if Windows locks the output path. If a validation check flags raw hashes, restore the supplied archived source files from the original copy.

### Original workbook and Windows export paths

The preserved JavaScript builder can also recreate the workbook layout if you have access to Node and `@oai/artifact-tool` 2.8.169. Tested with Node v24.22.3. Install the matching approved local tarball or private-registry package in **02_Completed_Project** with `npm install --no-save /path/to/approved-artifact-tool.tgz`, then run `node scripts/build_workbook.mjs` after the first three steps. A public npm registry lookup returned HTTP 404. The offline default uses the workbook layout exported by the original builder, refreshes its input cells from the verified JSONs, and recalculates the original formulas in LibreOffice. That route needs no Node installation.

On Windows with desktop Microsoft Word, the original `scripts/export_word_pdf.ps1` is also included for an optional COM-based export. Run it with `-InputDocx output/Final_Research_Report.docx -OutputPdf output/Final_Research_Report.pdf`. The delivered PDF was generated in LibreOffice.

### Optional data acquisition

The default rebuild uses the seven preserved Yahoo JSON responses and the primary NSE UDiFF archive. For source exploration, copy both acquisition scripts into the `scripts/` subdirectory of a separate empty project and run `python scripts/acquire_prices.py` and `python scripts/options_download.py` there. They write relative to their own project directory and may overwrite previously acquired files at those paths. Vendor corrections and adjustment updates can change a fresh download. The final results and reference validation are tied to the archived input hashes.

## Contents

| Folder | Contents |
| --- | --- |
| 01_Original_Project | Full extracted upload, including its bundled dependencies and workspace files |
| 02_Completed_Project | Runnable copy with frozen sources, original and extended scripts, workbook layout, validation baseline, generated data and outputs |
| 03_Final_Results | Summary and annual returns, correlations, portfolio comparisons, options inputs, results and diagnostics |
| 04_Visualizations | Twelve publication figures in PNG |
| 05_Excel_Workbook | Editable formula-based Finance_Analysis.xlsx |
| 06_Final_Report | Final_Research_Report.pdf and editable DOCX |
| 07_Documentation | Audit, original file hashes, changelog, validation, logs, checklist and limitations |

Regenerated outputs go into the working copy's `data/`, `artifacts/`, `charts/` and `output/` directories. Numbered deliverable directories are snapshots of the verified run. `data/raw/`, `data/options_raw/` and the source manifest hold the preserved research inputs. `validation/reference_results.json` pins the verified run's numeric values. The original project's files can be checked from the ZIP root using the cross-platform command below.

```bash
python 07_Documentation/verify_originals.py
```

See the documentation folder for the scope of validation and historical interpretation limits.
