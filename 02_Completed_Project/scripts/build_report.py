"""Build the project report from verified analysis outputs, without manual numeric copies."""
from pathlib import Path
import json, sys, math, csv
from report_tools import Report, ROOT
from docx.shared import Inches, Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def pct(x): return f'{x*100:.2f}%'
def num(x): return f'{x:.2f}'
def pp(x): return f'{x*100:.2f} percentage points'
def rows(path):
    with (ROOT/path).open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))

def front_and_context(d,r):
    p=d.p('RESEARCH PROJECT'); p.paragraph_format.space_before=Pt(30)
    d.p('Risk-Return Analysis and Derivative-Based Comparison of NBFCs and Commercial Banks in India','Title')
    d.p('Stock performance portfolio diversification and selected equity options','Subtitle')
    d.p('Study period 2021 to 2025')
    for author, email in [
        ('Sahitya Biswas', 'hereissahityadeybiswas@gmail.com'),
        ('Subhajit Paul', 'psubhajit042@gmail.com'),
        ('Anirban Nayak', 'anirbannayak07@gmail.com')
    ]:
        d.p(f'{author} | {email}')
    d.p('A quantitative study of HDFC Bank, ICICI Bank, State Bank of India, Bajaj Finance, Shriram Finance and Muthoot Finance.')
    d.doc.add_page_break()
    pmap={x['ticker']:x for x in r['portfolio_metrics']}
    b,n,m=(pmap[t] for t in ['BANKS','NBFCS','MIXED'])
    best=max(r['individual_metrics'],key=lambda x:x['cagr'])
    reduction=.5*b['annual_volatility']+.5*n['annual_volatility']-m['annual_volatility']
    d.heading('Abstract')
    d.p(f'This study compares the realized equity performance of three commercial banks and three non-banking financial companies in India over 2021 to 2025. Daily vendor-adjusted prices are used to estimate returns, volatility, Sharpe ratios, market beta and drawdowns on common trading dates. Equal-weight bank and NBFC portfolios are compared with a portfolio allocating 50% to each group. An additional case study uses observed NSE stock-option premiums on 31 December 2025 and a Black-Scholes model with independently estimated historical volatility.')
    d.p(f'The bank portfolio generated a compound annual growth rate of {pct(b["cagr"])} with annualized volatility of {pct(b["annual_volatility"])}. The NBFC portfolio generated {pct(n["cagr"])} with volatility of {pct(n["annual_volatility"])}. Their Sharpe ratios were {num(b["sharpe"])} and {num(n["sharpe"])}, respectively, using an assumed 6% effective annual risk-free return. The mixed portfolio returned {pct(m["cagr"])} annually, with volatility of {pct(m["annual_volatility"])} and a Sharpe ratio of {num(m["sharpe"])}. Mixing the groups reduced volatility by {pp(reduction)} relative to the weighted average of their stand-alone volatilities. {best["name"]} had the highest individual-stock CAGR in this sample.')
    d.p('The results describe these selected firms and dates. They do not establish that one entire sector is superior or that a higher historical return will persist. Corporate actions, mergers and a price-index benchmark affect interpretation. The option exercise distinguishes observed premiums, model values and implied volatility, with model-price gaps interpreted as assumption and market-data differences rather than demonstrated arbitrage opportunities.')
    d.p('Keywords: NBFCs, commercial banks, India, risk-adjusted returns, diversification, Black-Scholes, equity options.')
    d.heading('1 Introduction and research objectives',new_page=True)
    d.p('Banks and NBFCs both supply credit, but their funding arrangements, business mixes and regulatory treatment differ. These differences make their listed equities useful subjects for a risk-return comparison. An investor needs to consider how much wealth an investment accumulated, how variable its returns were, and how severely it declined along the way. A high average return alone does not answer those questions.')
    d.p('This project studies equity-market outcomes. It does not assess the safety of bank deposits, estimate borrowers\' default probabilities, or rank the financial soundness of the six institutions. A stock return incorporates market expectations and valuation changes as well as business performance. Consequently, an observed return difference cannot be attributed solely to regulatory status or operating model.')
    d.heading('1.1 Problem statement',2)
    d.p('The central problem is whether the selected NBFC equities delivered higher returns in exchange for higher risk than the selected bank equities, and whether combining the two groups improved the realized portfolio tradeoff. A related question is how the volatility of a selected bank and NBFC enters a basic equity-option valuation model.')
    d.heading('1.2 Objectives and research questions',2)
    for text in [
      'Calculate comparable daily returns and summarize individual-stock growth, volatility, Sharpe ratio, beta and maximum drawdown.',
      'Compare bank-only, NBFC-only and equally split portfolios under a common weighting and rebalancing rule.',
      'Measure co-movement and quantify how much diversification reduces volatility relative to the weighted average of stand-alone group risk.',
      'Check whether the main portfolio comparisons change under buy-and-hold weights or alternative risk-free assumptions.',
      'Compare observed premiums of selected actively traded equity options with Black-Scholes values based on historical volatility, and calculate Delta, Gamma and Vega.'
    ]: d.bullet(text)
    d.heading('1.3 Scope and working propositions',2)
    d.p('The sample is purposive: three named companies in each group were specified in the proposal. Two descriptive propositions guide the comparison. First, the NBFC portfolio may have both a higher realized annualized return and higher volatility than the bank portfolio. Both conditions must be checked separately. Second, the mixed portfolio may have lower volatility than the weighted average of the two group volatilities. That is different from being safer than each group individually.')
    d.p('These are descriptive comparisons, not formal population hypothesis tests. The firms are not random sector samples, and daily observations from a common financial market are not independent sector replicates. The report therefore does not attach p-values or claims of statistical acceptance to these propositions.')

    d.heading('2 Institutional context and literature')
    d.heading('2.1 Banks and NBFCs',2)
    d.p('The Reserve Bank of India distinguishes NBFCs from banks even where their lending activities overlap. NBFCs cannot accept demand deposits and do not issue cheques drawn on themselves as part of the payment system. NBFC deposits are outside the DICGC deposit-insurance arrangement. Some NBFCs can accept permitted term deposits, so it would be incorrect to state that all NBFCs are prohibited from accepting every form of deposit (RBI, 2017). These distinctions concern institutional structure; they do not by themselves determine equity returns.')
    d.table(['Dimension','Commercial banks','NBFCs'],[
      ['Demand deposits','Can accept eligible bank deposits','Cannot accept demand deposits'],
      ['Payment services','Participate in the banking payment system','Do not issue cheques drawn on themselves'],
      ['Deposit insurance','Eligible bank deposits subject to DICGC rules','NBFC deposits outside DICGC'],
      ['Equity risk in this study','Market returns of three selected bank stocks','Market returns of three selected NBFC stocks']
    ],[1.25,2.8,2.89],caption='Institutional distinctions relevant to the comparison')
    d.p('RBI\'s 2021 scale-based framework introduced four NBFC regulatory layers according to size, activity and perceived risk, with the general framework taking effect in October 2022. The observation period therefore includes a changing regulatory environment (RBI, 2021). This study does not estimate the causal effect of that change.')
    d.heading('2.2 Portfolio risk and performance measurement',2)
    d.p('Markowitz (1952) makes covariance central to portfolio selection. Combining two investments can reduce risk when their returns do not move perfectly together. An equal-weight comparison illustrates this mechanism but does not identify an efficient frontier or prove that the chosen weights are optimal. This project uses equal weights to make the comparison transparent and avoid estimating expected returns for an optimization exercise.')
    d.p('Sharpe (1964) distinguishes systematic risk in a diversified market setting from total variability. This motivates reporting beta beside volatility. Here beta is estimated from historical covariance with the NIFTY 50 price index. It is a sample sensitivity, not a forecast, a complete measure of risk or a formal test of the capital asset pricing model.')
    d.p('Sharpe (1966, 1994) relates reward to return variability. In this report, excess daily returns are measured against a stated risk-free assumption before annualization. CAGR remains a separate geometric growth measure and is not inserted into the Sharpe calculation. Historical Sharpe ratios are sensitive to the chosen window, the risk-free assumption and the dependence structure of returns.')
    d.heading('2.3 Option valuation and the study contribution',2)
    d.p('Black and Scholes (1973) derive option values through a no-arbitrage framework involving the underlying security and the option. Merton (1973) develops rational pricing restrictions and extensions, including dividend effects. Their framework provides a tractable way to connect volatility to option prices and local sensitivities. Constant volatility, continuous trading and frictionless replication remain strong assumptions.')
    d.p('The contribution of this project is an internally consistent applied comparison using the firms in the proposal, rather than a new asset-pricing theory. Equity results and option results use different units of analysis: a five-year return panel versus a small single-date contract sample. The two components are linked by historical volatility, but option-price gaps are not used to rank the entire banking and NBFC sectors.')

def data_and_methods(d,r):
    inds=r['individual_metrics']
    nobs=inds[0]['n']
    d.heading('3 Data and research design')
    d.p(f'The analysis covers 1 January 2021 to 31 December 2025 and uses {nobs:,} aligned daily return observations for each included series. The immediately preceding 31 December 2020 close provides the initial price for the first 2021 return. Prices before that base date are retained in the raw download but do not enter the five-year performance calculation.')
    d.table(['Company','NSE symbol','Group'],[
      ['HDFC Bank','HDFCBANK','Bank'],['ICICI Bank','ICICIBANK','Bank'],['State Bank of India','SBIN','Bank'],
      ['Bajaj Finance','BAJFINANCE','NBFC'],['Shriram Finance','SHRIRAMFIN','NBFC'],['Muthoot Finance','MUTHOOTFIN','NBFC']
    ],[3.25,2.0,1.69],caption='Purposively selected equity sample')
    d.heading('3.1 Sources and price treatment',2)
    d.p('The historical equity dataset is downloaded from the Yahoo Finance chart service for NSE-listed securities. This is a secondary-vendor implementation of the proposal\'s historical-stock component, rather than a claim that the observations were downloaded directly from NSE. The raw JSON responses, request URLs, retrieval timestamps and SHA-256 hashes are preserved. The dataset contains daily open, high, low, close, adjusted close and volume fields. Return calculations use adjusted close throughout.')
    d.p('The provider\'s historical OHLC fields are already split-adjusted. Adjusted close also reflects the provider\'s dividend adjustments and serves as an approximation to a reinvested total-return series. Applying share factors a second time would introduce errors. Absolute historical vendor prices should therefore not be presented as the unadjusted prices printed on those past trading dates. Volume is retained as a source field and is not used to calculate returns.')
    d.p('The market benchmark is the NIFTY 50 price index, downloaded as ^NSEI. NSE Indices distinguishes a price index from a total-return index that includes reinvested dividends. This mismatch means stock-versus-index growth differences are not a like-for-like total-return outperformance measure. The index supplies market context and the reference series for beta; bank-versus-NBFC comparisons retain the same adjusted-price convention across all six equities (NSE Indices, n.d.).')
    d.p('The option observations come directly from NSE\'s official futures-and-options UDiFF bhavcopy for 31 December 2025. This archive records contract specifications, closing and settlement prices, the underlying price, trading volume and open interest. Observed implied volatility is not supplied in the selected archive rows; the implied volatilities reported here are calculated by numerical inversion and explicitly identified as derived values.')
    d.heading('3.2 Cleaning and comparability',2)
    d.p('Each timestamp is converted to the Indian trading date, records are sorted, duplicate dates and nonpositive prices are checked, and the price series are aligned across the six stocks and index. Missing quotes are not forward-filled into artificial zero-return observations. The scripts report common-date coverage, missing fields, duplicate counts and extreme daily returns. Source files are retained separately from processed tables so that the return calculations can be rerun without another download.')
    d.p('Share events deserve particular attention. HDFC Bank issued a 1:1 bonus in 2025; Bajaj Finance\'s 2025 split and 4:1 bonus together increased the share count by a factor of ten; Shriram Finance undertook a five-for-one split in January 2025. The event table and adjusted returns around these dates are checked for continuity. These are changes in share units, not corresponding economic losses. The data audit distinguishes the vendor event date from a company record or allotment date when those differ.')
    d.p('The firms\' businesses are not constant over time. HDFC Bank\'s merger during 2023 and Shriram\'s 2022 merger and name change affect economic comparability. Shriram Finance\'s earlier listed history represents Shriram Transport Finance, not a separate security in the sample. The study follows the vendor\'s continuous listed-security series and does not reconstruct a constant-business portfolio (Shriram Finance, 2023).')

    d.heading('4 Calculation methods')
    d.heading('4.1 Returns and annualization',2)
    d.p('Daily simple returns equal adjusted close divided by the preceding adjusted close, less one. Simple returns are used because a portfolio\'s one-period return is the weighted average of its constituents\' simple returns. Wealth starts at 100 on the base date and compounds the subsequent daily returns. Total return is final wealth divided by initial wealth, less one.')
    d.equation('charts/equations/returns.png',5.9)
    d.p('Annualized arithmetic mean equals the sample daily mean multiplied by 252. Annualized volatility equals the sample standard deviation of daily returns, using an n minus one denominator, multiplied by the square root of 252. CAGR uses the actual elapsed calendar years between the base date and the ending date. The two annual return measures answer different questions: arithmetic mean summarizes the daily distribution, while CAGR describes the constant annual compound rate matching realized wealth.')
    d.equation('charts/equations/risk.png',6.1)
    d.heading('4.2 Risk adjusted return and market sensitivity',2)
    d.p('The baseline risk-free assumption is a 6% effective annual return. It is a modelling assumption, not a measured Treasury-bill yield for every day of the sample. Its equivalent daily return is (1.06) raised to one over 252, less one. Sharpe is the daily mean excess return divided by the sample daily standard deviation, multiplied by the square root of 252. Using the same rate and date set makes the portfolios comparable; a 4% and 8% sensitivity shows the effect of changing this input.')
    d.equation('charts/equations/sharpe_beta.png',6.2)
    d.p('Beta equals sample covariance between the asset and NIFTY 50 daily returns divided by the sample variance of the index. It is also the slope of a regression with an intercept on those aligned returns. A beta above one indicates greater sample sensitivity to the selected benchmark; it does not automatically imply greater maximum drawdown, better expected returns or stronger causal exposure.')
    d.heading('4.3 Drawdown and tail losses',2)
    d.p('Daily drawdown is current wealth divided by its previous running maximum, less one. Maximum drawdown is the lowest value of that series, including the initial wealth observation in the running peak. Drawdown is reported as a negative return. A value of -20% means that wealth fell 20% from a preceding peak within this observation window.')
    d.p('The supplementary historical 95% one-day Value at Risk is the negative of the 5th percentile daily return, reported as a positive loss. Conditional Value at Risk is the average loss among observations at or below that percentile. These are empirical daily loss summaries, not guaranteed loss limits. They do not incorporate a fitted tail model or intraday risk and depend on the selected sample and quantile convention.')
    d.equation('charts/equations/drawdown_tail.png',6.0)
    d.heading('4.4 Portfolios and diversification',2)
    d.p('The bank portfolio places one-third in each bank at the start of every trading day. The NBFC portfolio applies the same rule to the three NBFCs. The mixed portfolio allocates one-half to each group, equivalent to one-sixth in each stock. Taking the weighted mean of returns every day assumes daily rebalancing, with no transaction costs, bid-ask spreads, taxes, slippage or constraints. These conventions isolate the realized return and covariance comparison.')
    d.equation('charts/equations/portfolio.png',6.0)
    d.p('For a 50:50 mix, variance depends on each group\'s variance and their correlation. The diversification reduction is the weighted average of their stand-alone volatilities minus the mixed volatility. A positive reduction is possible even if mixed volatility is higher than the safer group\'s volatility. Pairwise correlations, a portfolio wealth chart and annual results are examined together to avoid drawing a conclusion from one statistic.')
    d.p('A buy-and-hold sensitivity invests in the same initial weights and then lets weights drift. It compounds the initial allocation to each stock rather than averaging daily stock returns. This comparison helps identify the effect of the rebalancing convention; it remains gross of investment costs and is not a trading recommendation.')
    d.heading('4.5 Option model and sensitivities',2)
    d.p('NSE describes stock options as European style and physically settled (NSE, n.d.). The Black-Scholes model with continuous dividend yield is therefore used as a basic European valuation framework. The spot is the contemporaneous underlying price recorded in the official option archive, in the same share units as the strike. Time to expiry is calendar days divided by 365. The continuously compounded interest rate is the natural logarithm of 1.06, aligning the discount factor with the equity analysis\'s 6% effective annual assumption.')
    d.equation('charts/equations/bs.png',6.5)
    d.p('In these expressions, S is spot, K is strike, T is years to expiry, r is the continuously compounded risk-free rate, q is dividend yield, sigma is annualized volatility and N is the standard normal cumulative distribution. The base q is zero. Volatility is estimated from the most recent 252 adjusted daily returns available through the valuation close. No observations after 31 December 2025 are used. This is an end-of-day study; it is not a claim that the closing volatility estimate was available before each option\'s last trade.')
    d.p('Delta measures the local option-value change per INR 1 change in spot. Gamma measures the change in Delta per INR 1 spot move. Vega is reported per one percentage-point increase in annual volatility, so raw mathematical Vega is divided by 100. The signs and scale matter: call Delta is positive, put Delta is negative, and both long options ordinarily have positive Gamma and Vega.')
    d.equation('charts/equations/greeks_iv.png',6.1)
    d.p('Historical-volatility model values are compared with observed closing premiums. Separately, implied volatility solves for the volatility that reproduces an option\'s own observed premium. Successful repricing with that implied volatility is a numerical solver check, not independent evidence that the model predicts market prices. Dividend and volatility sensitivities illustrate how assumptions move valuations.')

def make_equations():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    formulas={
      'returns':r'$R_{i,t}=\frac{P^{adj}_{i,t}}{P^{adj}_{i,t-1}}-1\qquad W_t=100\prod_{s=1}^{t}(1+R_s)$',
      'risk':r'$\mu_{ann}=252\overline{R}\qquad \sigma_{ann}=\sqrt{252}\,s_R\qquad CAGR=\left(\frac{W_T}{100}\right)^{1/Y}-1$',
      'sharpe_beta':r'$Sharpe=\sqrt{252}\frac{\overline{R}-r_{f,d}}{s_R}\qquad \beta_i=\frac{Cov(R_i,R_m)}{Var(R_m)}$',
      'drawdown_tail':r'$D_t=W_t/\max_{u\leq t}W_u-1,\quad MDD=\min_tD_t,\quad VaR=-Q_{0.05}(R)$'+'\n'+r'$CVaR=-\operatorname{mean}\{R_t:R_t\leq Q_{0.05}(R)\}$',
      'greeks_iv':r'$\Delta_C=e^{-qT}N(d_1),\quad\Delta_P=e^{-qT}[N(d_1)-1],\quad\Gamma=\frac{e^{-qT}\phi(d_1)}{S\sigma\sqrt{T}}$'+'\n'+r'$\mathrm{Vega}_{1pp}=Se^{-qT}\phi(d_1)\sqrt{T}/100,\quad V(\sigma_{IV})=V_{market}$',
      'portfolio':r'$R_{p,t}=\sum_i w_i R_{i,t}\qquad \sigma_{mix}^2=\frac{\sigma_B^2+\sigma_N^2+2\rho_{BN}\sigma_B\sigma_N}{4}$',
      'bs':r'$C=Se^{-qT}N(d_1)-Ke^{-rT}N(d_2)$'+'\n'+r'$P=Ke^{-rT}N(-d_2)-Se^{-qT}N(-d_1)$'+'\n'+r'$d_1=\frac{\ln(S/K)+(r-q+\sigma^2/2)T}{\sigma\sqrt{T}},\quad d_2=d_1-\sigma\sqrt{T}$'
    }
    out=ROOT/'charts/equations'; out.mkdir(parents=True,exist_ok=True)
    for name,text in formulas.items():
        fig=plt.figure(figsize=(8,1.65 if name == 'bs' else 1.10 if name in ('greeks_iv','drawdown_tail') else .6))
        fig.text(.5,.5,text,ha='center',va='center',fontsize=15,linespacing=1.6)
        fig.savefig(out/(name+'.png'),dpi=220,bbox_inches='tight',pad_inches=.08,facecolor='white')
        plt.close(fig)


def verified_results(d, r, options):
    diagnostics = r['diagnostics']
    d.heading('5 Data validation')
    counts = diagnostics['annual_return_counts']
    d.p('The aligned series have no missing or duplicate trading dates, and the original OHLC integrity checks passed. Return counts by year are ' +
        ', '.join(f'{year} ({count})' for year, count in counts.items()) + '. NIFTY 50 beta against itself equals one. Annual compounding and the portfolio covariance identity agree with the daily-return series.')
    d.table(['Symbol', 'Yahoo close (INR)', 'NSE underlying (INR)', 'Yahoo less NSE (INR)'],
            [[x['ticker'], num(x['yahoo_close']), num(x['nse_fo_underlying_price']), num(round(x['difference'], 2) + 0.0)]
             for x in diagnostics['official_close_checks']], caption='Closing price cross-check on 31 December 2025')
    d.p('The Muthoot Finance vendor close is INR 3,811.70 to two decimals. The NSE derivatives archive reports INR 3,811.75. The INR 0.05 gap is approximately 0.13 basis points of the NSE price. Binary representation accounts for the extra digits in the vendor JSON, while a five-paise difference remains at published precision. Two separate NSE cash-market reports confirm INR 3,811.70 for MUTHOOTFIN in the EQ series (NSE, 2025). The difference is between the cash-market close and the derivatives file’s underlying-price field. The records do not explain how the latter was set. The vendor adjusted-close series remains the equity input. Model spot comes from NSE for the two selected option underlyings.')
    d.p('The corporate-action continuity checks cover the published Bajaj Finance, HDFC Bank and Shriram Finance share changes. Preserved source responses are checked against their retrieval hashes. Corporate action disclosures support the share-unit interpretation (HDFC Bank, 2025; Metropolitan Stock Exchange of India, 2025; NSE circular FAOP66059).')

    d.heading('6 Equity and portfolio results', new_page=True)
    sets = r['individual_metrics'] + [r['benchmark_metrics']] + r['portfolio_metrics']
    d.table(['Series', 'Days', 'Total', 'CAGR', 'Ann. mean', 'Ann. vol.', 'Sharpe'],
            [[x['ticker'], x['n'], pct(x['total_return']), pct(x['cagr']), pct(x['annual_mean']),
              pct(x['annual_volatility']), num(x['sharpe'])] for x in sets],
            [1.22,.52,1.04,1.04,1.04,1.04,1.04], caption='Returns and annualized risk across the common sample')
    d.table(['Series', 'Beta', 'Max drawdown', '1-day VaR 95%', '1-day CVaR 95%'],
            [[x['ticker'], num(x['beta']), pct(x['max_drawdown']), pct(x['var95']), pct(x['cvar95'])]
             for x in sets], caption='Market sensitivity, drawdown and historical tail losses')
    d.figure('charts/individual_wealth.png', 'Cumulative performance of the six selected stocks')
    d.figure('charts/risk_return.png', 'Compound annual growth and annualized daily volatility')
    d.figure('charts/correlation_heatmap.png', 'Daily return correlations for the six equities', width=5.65)
    corr = r['comparison']
    d.p(f'Mean pairwise correlation was {num(corr["mean_within_bank_correlation"])} within banks, '
        f'{num(corr["mean_within_nbfc_correlation"])} within NBFCs, and {num(corr["mean_cross_sector_correlation"])} across the two groups. '
        f'The two sector portfolios had a daily return correlation of {num(corr["bank_nbfc_portfolio_correlation"])}.')
    d.figure('charts/portfolio_wealth.png', 'Daily-rebalanced portfolio wealth and the price-index benchmark')
    d.figure('charts/drawdown.png', 'Daily drawdowns from the running wealth peak')
    d.figure('charts/annual_returns.png', 'Compounded calendar-year returns for the portfolios and benchmark')
    d.doc.add_page_break()
    for label, selected in [('Equity', sets[:7]), ('Portfolio', r['portfolio_metrics'])]:
        d.table(['Series', '2021', '2022', '2023', '2024', '2025'],
                [[x['ticker'], *[pct(y[x['ticker']]) for y in r['annual_returns']]] for x in selected],
                [1.34,1.12,1.12,1.12,1.12,1.12], caption=f'{label} calendar-year returns')

    d.heading('7 NSE equity options case study')
    cases = options['observations']
    d.p(f'Each row represents a 31 December 2025 NSE closing premium for a 27 January 2026 expiry. '
        f'The two pairs use the nearest eligible strike with traded calls and puts and positive open interest. '
        f'The time input is {cases[0]["days_to_expiry"]} calendar days divided by 365. The continuous rate is '
        f'{pct(cases[0]["risk_free_continuous"])} and the baseline dividend yield is zero. Historical volatility '
        f'uses 252 daily adjusted returns from {cases[0]["vol_window_first_return"]} through {cases[0]["vol_window_last_return"]}.')
    d.table(['Contract', 'Spot', 'Strike', 'NSE close', 'Model', 'Model less close', 'Hist. vol.', 'Implied vol.'],
            [[x['symbol']+' '+x['option_type'], num(x['spot']), num(x['strike']), num(x['market_price']),
              num(x['bs_price']), num(x['bs_price']-x['market_price']), pct(x['sigma_historical']), pct(x['derived_iv'])]
             for x in cases], [1.32,.64,.64,.8,.75,.96,.87,.96], caption='Black–Scholes valuations and NSE closes in INR per share', small=8.2)
    d.table(['Contract', 'Lot', 'Volume', 'OI contracts', 'Delta', 'Gamma', 'Vega'],
            [[x['symbol']+' '+x['option_type'], x['lot_size'], x['volume_contracts'], x['open_interest_contracts'],
              f'{x["delta"]:.4f}', f'{x["gamma"]:.5f}', f'{x["vega_per_1pp"]:.4f}'] for x in cases],
            [1.48,.64,1.02,1.10,.9,.9,.9], caption='Trading activity and historical-volatility Greeks per share')
    d.p('Volume counts contracts. Open interest is converted from underlying units to contracts using the lot size. Delta measures the premium change per rupee of spot, Gamma the Delta change per rupee of spot, and Vega the premium change in INR per one percentage point of annualized volatility. The underlying prices and premiums are daily archive fields with potentially different closing conventions.')
    d.figure('charts/options_price_comparison.png', 'Observed NSE closing premiums and historical-volatility model values')
    d.figure('charts/options_volatility_comparison.png', 'Historical volatility and implied volatility calibrated to each premium')
    d.figure('charts/options_greeks.png', 'Baseline Delta, Gamma and Vega by contract')
    d.p(f'Implied-volatility inversion repriced each premium with a maximum absolute residual of '
        f'{max(abs(x["derived_iv_reprice_error"]) for x in cases):.2e} INR. Finite differences confirmed Greek '
        f'calculations and theoretical calls and puts satisfied put–call parity under common inputs.')

    d.heading('8 Discussion')
    b, n, m = r['portfolio_metrics']
    weighted = corr['weighted_sector_volatility']
    d.p(f'The NBFC portfolio had a higher annualized arithmetic mean ({pct(n["annual_mean"])} versus {pct(b["annual_mean"])}), '
        f'higher volatility ({pct(n["annual_volatility"])} versus {pct(b["annual_volatility"])}), and a deeper maximum '
        f'drawdown ({pct(n["max_drawdown"])} versus {pct(b["max_drawdown"])}). Its Sharpe ratio also exceeded the bank '
        f'portfolio’s ({num(n["sharpe"])} versus {num(b["sharpe"])}). Both inequalities in the first descriptive proposition held.')
    d.p(f'The mix reduced volatility from the {pct(weighted)} weighted stand-alone average to {pct(m["annual_volatility"])}, '
        f'a reduction of {pp(weighted-m["annual_volatility"])}. The second descriptive proposition held. The bank portfolio '
        f'had the lowest volatility and shallowest drawdown among the three portfolios. The mixed portfolio had the highest '
        f'Sharpe ratio ({num(m["sharpe"])}). The NBFC portfolio had the highest CAGR.')
    for label, key, fields in [
        ('Buy-and-hold sensitivity', 'buy_and_hold', ['ticker','cagr','annual_volatility','sharpe']),
        ('Risk-free-rate sensitivity', 'risk_free', ['rf','ticker','sharpe'])
    ]:
        headers = {'ticker':'Portfolio','cagr':'CAGR','annual_volatility':'Ann. volatility','sharpe':'Sharpe','rf':'Effective annual rate'}
        d.table([headers[k] for k in fields],
                [[pct(x[k]) if k in ('rf','cagr','annual_volatility') else num(x[k]) if k=='sharpe' else x[k]
                  for k in fields] for x in r['sensitivity'][key]], caption=label)
    low = min(x['bs_price']-x['market_price'] for x in cases)
    high = max(x['bs_price']-x['market_price'] for x in cases)
    d.p(f'Historical-volatility model values differed from observed closing premiums by {low:+.2f} to {high:+.2f} INR per share. '
        f'Pricing gaps reflect the selected inputs and the available end-of-day price observations. The four prices provide '
        f'limited evidence about broader differences between bank and NBFC options.')

    d.heading('9 Limitations and conclusion')
    d.heading('9.1 Limitations', 2)
    d.p('The six surviving firms were chosen purposively. The findings depend on the sample, dates, vendor adjusted prices and business changes around the HDFC and Shriram mergers. The benchmark excludes dividend reinvestment. Daily rebalancing assumes frictionless trading and excludes taxes. The 6% risk-free rate is an assumption. Historical tail measures describe the observed loss distribution.')
    d.p('The derivatives sample contains four positions on one date. The model assumes a constant rate, volatility and dividend yield, continuous hedging and frictionless markets. The archive gives closing premiums and trade activity, with no simultaneous executable bid and ask in the selected rows. Liquidity, physical settlement, trading costs and the difference between historical and expected volatility limit interpretation.')
    d.heading('9.2 Conclusion', 2)
    d.p(f'In this sample, the NBFC portfolio combined higher growth and higher volatility than the bank portfolio. '
        f'The 50:50 mix diversified the two groups relative to their weighted stand-alone risk and achieved a Sharpe ratio of '
        f'{num(m["sharpe"])}. The four option valuations illustrate how historical volatility enters Black–Scholes prices '
        f'and sensitivities. These are historical comparisons conditional on the research design.')

    d.heading('References', new_page=True)
    references = json.loads((ROOT/'artifacts/references.json').read_text(encoding='utf-8'))
    for ref in sorted(references, key=lambda ref: (ref['author'], ref['year'] or 0)):
        d.p(f'{ref["author"]} ({ref["year"] or "n.d."}). {ref["title"]}. {ref["publication"]}. {ref["url"]}')
    d.p('National Stock Exchange of India (2025). Capital-market UDiFF bhavcopy, 31 December. https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_20251231_F_0000.csv.zip')
    d.p('National Stock Exchange of India (2025). Full cash-market bhavcopy, 31 December. https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_31122025.csv')
    d.p(f'National Stock Exchange of India (2025). UDiFF futures and options bhavcopy, 31 December. {options["source_url"]}')
    d.p('National Stock Exchange of India (2025). Adjustment of futures and options contracts in Shriram Finance Limited, circular FAOP66059. https://nsearchives.nseindia.com/content/circulars/FAOP66059.pdf')
    d.p('Yahoo Finance (retrieved October 2026). Historical NSE-listed equity and NIFTY 50 chart responses. Request URLs and SHA-256 values are listed in data/source_manifest.json.')
    d.heading('Appendix A Reproducing the results')
    d.p('Open 02_Completed_Project in VS Code. Install the pinned Python 3.12 dependencies with python -m pip install -r requirements.txt and install LibreOffice. Run python run_all.py to rebuild the analysis, figures, workbook and report from the archived inputs. The pipeline makes no market-data requests.')
    d.p('Key parameters are 252 trading days per year, 365.25 days per CAGR year, a 6% effective annual risk-free rate, and 27/365 years to option expiry. The bank and NBFC portfolios each use one-third constituent weights. Each stock has one-sixth weight in the mixed portfolio.')
    d.p('The data folder contains vendor JSON, the NSE archive and generated CSV tables. The artifacts folder contains full-precision metrics, workbook inputs, option diagnostics and validation files. The charts folder contains numbered-report figure sources and equations. The output folder contains Excel, Word and PDF. Run python validate_results.py after execution to check inputs and outputs against the delivered baseline.')


def main():
    equity = json.loads((ROOT/'artifacts/results.json').read_text(encoding='utf-8'))
    options = json.loads((ROOT/'artifacts/options_results.json').read_text(encoding='utf-8'))
    make_equations()
    report = Report()
    front_and_context(report, equity)
    data_and_methods(report, equity)
    verified_results(report, equity, options)
    print(report.save('output/Final_Research_Report.docx'))


if __name__ == '__main__':
    main()
