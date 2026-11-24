# Research notes for the project

Verified on 13 October 2026. This document supplies conceptual context and methodological guidance, not empirical findings. Sources in `artifacts/references.json` are primary publications, official regulators/exchanges, or original papers hosted by universities. Search-index evidence is distinguished from successful full-page access.

## Literature review (report-ready, concise paraphrases)

Markowitz (1952) established portfolio selection as a joint problem involving expected returns and the covariance of asset returns. Its relevance here is that a mixed portfolio's volatility depends on co-movement, not simply the average of the constituent volatilities. An equal-weight comparison illustrates diversification but does not estimate an efficient frontier or prove optimality. [markowitz1952]

Sharpe (1964) related expected returns to risk that remains relevant in a diversified market portfolio. This motivates reporting beta beside total volatility. The project's sample beta is an historical regression/covariance statistic against the chosen index, not a complete measure of risk or a test proving CAPM. [sharpe1964]

Sharpe (1966) introduced a reward-to-variability performance measure. Sharpe (1994) explains its use with differential returns and warns that historic ratios need not be unbiased forecasts. This project therefore subtracts an explicit risk-free assumption and compares ex-post Sharpe ratios over identical dates. The square-root-of-time annualization is a convention whose accuracy depends on return dependence. [sharpe1966; sharpe1994]

Black and Scholes (1973) derived option valuation using a no-arbitrage argument involving an option and its underlying security. Merton (1973) developed rational option-pricing restrictions and extensions, including dividend effects. Their framework supports a controlled comparison of model values, observed premiums and local sensitivities, subject to volatility, rate, dividend and market-friction assumptions. [blackscholes1973; merton1973]

The RBI distinguishes NBFCs from banks despite overlapping credit activities: NBFCs cannot accept demand deposits, do not issue cheques drawn on themselves as part of the payment system, and NBFC deposits do not receive DICGC insurance. Some NBFCs can accept permitted term deposits, so it is inaccurate to say that all NBFCs cannot accept deposits. These institutional distinctions motivate an equity-market comparison but do not predict a deterministic return ranking. [rbi_nbfc_faq]

RBI's October 2021 scale-based framework classified NBFCs across four regulatory layers by size, activity and perceived risk, generally effective October 2022. Regulation therefore changed within the observation window. Treat differences in observed returns as descriptive associations, not causal effects of regulatory status. [rbi_sbr2021]

NSE identifies stock options as European-style and physically settled. This supports European-option valuation as an analytical starting point, while physical delivery, margins and liquidity still matter to executable trading. NSE Indices distinguishes price indices from total-return indices that include reinvested dividends. Benchmark treatment must match or transparently qualify the stock-return treatment. [nse_stock_options; nifty_tri]

## Exact suggested report sequence

1. Title and authors copied from proposal, submission date, descriptive period.
2. Abstract written after results: sample, dates, sources, principal calculated comparisons and important qualification.
3. Introduction and problem statement: equity-investor perspective; distinguish equity risk from deposit safety or credit risk.
4. Institutional background and short literature review above.
5. Objectives and research questions/hypotheses.
6. Data and research design: six purposively selected firms, symbols and predecessor treatment, dates, market benchmark, source/provider, field meanings, exclusions and actual observation count.
7. Methods: simple returns, geometric growth/CAGR, annualized arithmetic mean, sample volatility, Sharpe, beta, drawdown, correlation, portfolio weights/rebalancing, option inputs/formulas and Greeks units.
8. Data validation: duplicate/missing dates, positive prices, adjustment checks and large-return checks, corporate actions and merger caveats.
9. Equity findings: common-date individual metrics, annual returns, group descriptive comparisons and portfolio results; charts should use a common scale/date basis.
10. Options case study: exact observation timestamp/date, selected contracts, time to expiry, independently selected historical volatility versus market prices, implied volatility as an inversion diagnostic, Greeks and model limits.
11. Discussion: answer each research question; separate realized sample evidence from conjectured mechanisms.
12. Conclusions and limitations, references, and reproducibility appendices/data dictionary.

## Research questions and non-overstated hypotheses

- RQ1: Which selected group had the higher realized return, volatility, drawdown and Sharpe ratio during the common sample window?
- H1 (descriptive working hypothesis): the equal-weight NBFC portfolio has higher sample annualized return and volatility than the equal-weight bank portfolio. Report whether BOTH inequalities hold, not that the hypothesis is statistically accepted.
- RQ2: How much does a 50:50 mix reduce volatility relative to the weighted average stand-alone volatility? Does it also improve Sharpe or drawdown?
- H2 (descriptive working hypothesis): mixed-portfolio volatility is less than 0.5 times bank volatility plus 0.5 times NBFC volatility. This diversification comparison is different from being less risky than each portfolio separately. A positive reduction does not imply better returns or higher Sharpe.
- RQ3: How do independently parameterized Black-Scholes values differ from observed option premiums, and how sensitive are values to price and volatility?
- Do not announce formal hypothesis tests, p-values or population inference unless they are actually implemented with time-series dependence respected. Three selected firms per group do not represent independent random samples of their sectors. Daily observations from one common market are not independent sector replicates.

## Critical implementation and interpretation checks

- Use adjusted closing prices consistently. Stock splits and bonus issues are not economic crashes. Vendor-adjusted OHLC may already be split-adjusted; do not double-adjust. Dividend-adjusted prices provide a vendor approximation to reinvested total return, while raw closes do not.
- Confirm 2025 HDFC Bank 1:1 bonus (record date 27 August), Bajaj Finance split from face value 2 to 1 plus 4:1 bonus (record date 16 June; combined share factor 10), and Shriram Finance five-for-one split (10 January). Verified company/exchange evidence should accompany these checks. [hdfc_bonus2025; bajaj_action2025]
- Shriram Finance's earlier observations represent Shriram Transport Finance; the merger/name change took effect 30 November 2022. HDFC's 2023 merger and Shriram's 2022 merger change business composition. The historical listed-stock series is not a constant-business panel. [shriram_merger2023]
- Prefer NIFTY 50 total return against dividend-adjusted stocks. If only NIFTY 50 price data are available, label it a price-index benchmark, do not describe excess total returns as a like-for-like outperformance estimate, and flag beta's benchmark choice. [nifty_tri]
- Add the immediately preceding available close to compute the first 2021 return. Otherwise state the first return begins after the first retained close. Wealth and drawdown should include the initial base observation.
- Align trading dates and never forward-fill missing stock quotes to create zero returns without explicit justification.
- Constant equal-weight daily returns imply daily rebalancing. State that transaction costs, spreads, taxes, slippage and dividend tax are excluded. Buy-and-hold is a different calculation and should be labeled if shown.
- Distinguish annualized arithmetic mean (252 times daily average) from CAGR (compounded growth). Do not insert CAGR into a daily-mean Sharpe formula.
- A 6% annual risk-free assumption is not a measured 2021-25 risk-free yield. Convert consistently to daily return: (1.06)^(1/252)-1. For Black-Scholes, state whether the 6% input is continuously compounded; using 6% as a continuous rate is a separate convention from a 6% effective annual rate.
- Sharpe depends on the rate assumption and realized sample; a simple 4%, 6%, 8% sensitivity is useful. Beta uses aligned asset and benchmark returns with consistent covariance/variance conventions.
- Maximum drawdown should be labeled as a negative return (or positive loss magnitude consistently). Drawdown and volatility do not capture all credit, funding, valuation, liquidity or tail risks.
- For options, use raw contemporaneous spot in the same share units as the contract strike, never a historically dividend-adjusted spot. Use prior information for historical volatility; do not use data after the option valuation date. Specify days/365 and expiration convention.
- A Black-Scholes inversion of an option's own price produces an implied volatility that reprices that input by construction. Repricing the same premium is a numerical check, not empirical model validation. Historical-volatility model price differences are not executable arbitrage or proof of mispricing.
- Call/put premiums may have stale last trades and differ from bid-ask midpoints. Record premium type, trade activity/open interest, date/time alignment, dividend assumptions and contract metadata. A tiny option sample cannot establish broad sector-level derivatives differences.
- Label Vega per one percentage-point volatility change (raw vega divided by 100); Delta per one rupee spot move and Gamma per rupee squared. Do not compare rupee premiums across stocks without moneyness/maturity normalization.
- Findings apply to six surviving, deliberately chosen listed firms and the chosen five-year period. Selection, survivorship, merger, endpoint, market-regime and estimation effects remain. Avoid investment recommendations and causal attribution.
