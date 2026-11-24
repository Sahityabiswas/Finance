# Validation report

## Methods and numerical tolerances

The independent validator reads archived vendor prices and the official NSE contract CSV directly. It reconstructs daily returns, portfolios, cumulative wealth, drawdowns, annual compounding, correlation, beta, volatility, CAGR, Sharpe, VaR and CVaR. It uses NumPy calculations from the adjusted-price panel and a separate NormalDist implementation for Black–Scholes values and Greeks. It checks nearest-strike selection and reported premiums against archived contract IDs. Numeric comparisons use relative tolerance 2e-9 and absolute tolerance 2e-10, including workbook agreement. The original equity/option scripts retain their own model validation tolerances.

Four contracts use 27 calendar days divided by 365 and historical volatility from the trailing 252 returns through 31 December 2025. Spot and strikes agree with the preserved NSE records. Implied volatility reproduces each observed input price with a maximum absolute residual of approximately 9.24e-14 INR. The option script also tests model put–call parity, textbook reference prices and finite differences for Delta, Gamma and Vega. The observed parity residuals are in the standalone diagnostic CSV. Closing fields, timing and trading costs limit their interpretation.

The aligned data contain 1,237 prices and 1,236 returns. Independent raw-data reconstruction agrees across all daily rows. The ten original top-level CSVs also agree with the rebuilt intermediates at relative tolerance 2e-10 and absolute tolerance 1e-11. Dates, leading wealth and reported columns agree. Corporate actions use already adjusted prices.

## Source difference

Yahoo's raw Muthoot Finance close is 3811.699951171875 INR. Rounding it to two decimals gives 3811.70 INR. Archived NSE F&O underlying is 3811.75 INR. The five-paise published-precision difference is about 0.13 basis points of the NSE value. The official NSE capital-market UDiFF and full cash-market bhavcopies each give INR 3811.70 for the 31 December 2025 MUTHOOTFIN EQ close. The public cash-market sources and their SHA-256 values are recorded in logs/nse-cash-crosscheck.log. The records do not establish how the derivatives underlying mark was set. Other underlying prices passed the original INR 0.011 check. The scoped exception preserves both source values. Historical Muthoot returns come from the archived adjusted close and neither option underlying is Muthoot Finance.

## Workbook and report

Seven sheets and two embedded charts were retained. The workbook's formula outputs across daily returns, wealth, drawdowns, annual returns, correlations, summary metrics and option valuations agree with independent calculations. A Calc test changed the effective rate from 6% to 8%. Bank Sharpe recalculated from roughly 0.796472 to 0.698006 and the HDFC call model premium from INR 19.525828 to INR 20.275122. The distributed workbook uses 6%. Stored implied volatility is the baseline-date calibration.

The report tables and figures are generated from the same verified JSON outputs. The validator checks report totals and option prices in Word, twelve PNGs for dimensions and readability at the file level, and the PDF signature. Rendering review covers pagination, equations, tables and embedded figures. The full pipeline rebuilds all output formats offline.
