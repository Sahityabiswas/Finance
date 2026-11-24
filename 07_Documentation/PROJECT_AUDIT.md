# Project audit

The input is an existing academic study proposed by Sahitya Biswas, Subhajit Paul and Anirban Nayak. The proposal PDF, extracted proposal, reference notes and citation manifest establish the research scope. The original code and its preserved historical data determine the implemented conventions. The original directory remains intact. The SHA-256 manifest lists every original file, including the bundled dependency tree. The inventory CSV also records directory entries.

## Initial state

| Component | Initial status | Evidence and required action |
| --- | --- | --- |
| Proposal and references | Completed | Proposal PDF and text, research notes and thirteen reference records. |
| Historical Yahoo data and provenance | Completed | Seven chart responses with 1,240 raw dates each, hash manifest and vendor actions. Data use 1,237 aligned prices including the 2020 base close. |
| NSE archive and provenance | Completed | Two identical successful source ZIPs and two unsuccessful fallback provenance records. |
| Equity CSV intermediates | Completed | Prices, returns, wealth, annual returns, correlations and drawdowns existed. Frozen-data rerun agrees with the original files. |
| Complete equity run | Failing | Muthoot Finance close difference stopped the script before summary JSON, metrics and charts. |
| Portfolio calculations | Partially Completed | Daily weighting and most intermediates existed. Summary metrics and the diversification comparison needed output and independent verification. |
| Option candidates and cross-check | Completed | 154 eligible-universe option rows before liquidity filtering and six underlying rows. Both CSVs reproduced. |
| Complete options run | Failing | Dictionary attribute lookup stopped selected-contract calculations before JSON, CSV results and figures. |
| Workbook JS | Failing | Missing input JSONs, incompatible option IV and open-interest fields, and package unavailable from public npm. |
| Report builder | Partially Completed | Styling, introduction, literature and methods existed. Original script exited without a report because it had no entry point or results sections. |
| Word PDF export | Partially Completed | Windows Word COM script existed. Linux lacks desktop Word and PowerShell here. |
| End-to-end runner and independent numerical validator | Not Implemented | Added both. |

## Original files and roles

| Path within original Project | Role |
| --- | --- |
| PROJECT PROPOSAL ... .pdf, proposal_extracted.txt | Original title, authors, scope and methodology |
| research_notes.md, artifacts/references.json | Methodological guidance and citations |
| scripts/acquire_prices.py | Optional Yahoo download and source manifest |
| scripts/analyze.py | Raw equity parsing, annualization, portfolio construction, diagnostics and six figures |
| scripts/options_download.py | Optional acquisition from four NSE URLs and provenance |
| scripts/options_analyze.py | NSE parsing, contract selection, Black–Scholes, calibration, sensitivity and two figures |
| scripts/build_workbook.mjs | Seven worksheet layout, formulas, formatting, charts and workbook diagnostics |
| scripts/build_report.py, scripts/report_tools.py | Report front matter, methods, equations and formatting |
| scripts/export_word_pdf.ps1 | Desktop Word COM conversion |
| data/raw/*.json, data/source_manifest.json | Historical primary vendor inputs and request provenance |
| data/options_raw/* | NSE archives and request provenance |
| data/adjusted_prices.csv, data/prices.csv, data/corporate_actions_vendor.csv | Vendor-adjusted panel, long OHLCV, event table |
| data/returns.csv, data/wealth.csv, data/drawdowns.csv | Daily equity and portfolio series |
| data/annual_returns.csv, data/correlations.csv | Compounded calendar returns and stock correlation matrix |
| data/options_candidate_contracts.csv, data/options_underlying_crosscheck.csv | Contract universe and underlying audit |
| charts/, output/ | Empty delivery directories on upload |
| tmp/proposal/page1.png | Original proposal preview |
| .deps/ | Original platform-specific bundled dependencies, preserved for integrity |

## Execution order

Historic input checks and equity analysis precede options and output preparation. Once supplemental output preparation generates the expected workbook input JSON, the workbook can use either the existing JS builder or its portable layout-based route. The extended report consumes result JSONs and plots. LibreOffice converts its DOCX to PDF. Finally the validator compares results to independent calculations and the frozen reference.

The 252-day annualization, 6% effective rate, adjusted-close returns, daily rebalancing, and base close were already implemented. The options comparison retains the fixed pair of symbols, 27 January 2026 expiry, official spot prices, q=0 assumption and 252-return historical volatility. The portable path refreshes data cells and evaluates the existing formulas without a private Node package. Remaining verification boundaries are recorded in KNOWN_LIMITATIONS.md.
