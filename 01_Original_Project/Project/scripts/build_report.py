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
    d.p('Risk Return Analysis and Derivative Based Comparison of NBFCs and Commercial Banks in India','Title')
    d.p('Stock performance portfolio diversification and selected equity options','Subtitle')
    d.p('Study period 2021 to 2025')
    d.p('Sahitya Biswas\nSubhajit Paul\nAnirban Nayak')
    d.p('14 October 2026')
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
    d.heading('Contents',level=2)
    p=d.p('')
    f=OxmlElement('w:fldSimple'); f.set(qn('w:instr'),'TOC \\o "1-1" \\h \\z \\u')
    p._p.append(f)

    d.heading('1 Introduction and research objectives',new_page=True)
    d.p('Banks and NBFCs both supply credit, but their funding arrangements, business mixes and regulatory treatment differ. These differences make their listed equities useful subjects for a risk-return comparison. An investor needs to consider how much wealth an investment accumulated, how variable its returns were, and how severely it declined along the way. A high average return alone does not answer those questions.')
    d.p('This project studies equity-market outcomes. It does not assess the safety of bank deposits, estimate borrowers\' default probabilities, or rank the financial soundness of the six institutions. A stock return incorporates market expectations and valuation changes as well as business performance. Consequently, an observed return difference cannot be attributed solely to regulatory status or operating model.')
    d.heading('1 1 Problem statement',2)
    d.p('The central problem is whether the selected NBFC equities delivered higher returns in exchange for higher risk than the selected bank equities, and whether combining the two groups improved the realized portfolio tradeoff. A related question is how the volatility of a selected bank and NBFC enters a basic equity-option valuation model.')
    d.heading('1 2 Objectives and research questions',2)
    for text in [
      'Calculate comparable daily returns and summarize individual-stock growth, volatility, Sharpe ratio, beta and maximum drawdown.',
      'Compare bank-only, NBFC-only and equally split portfolios under a common weighting and rebalancing rule.',
      'Measure co-movement and quantify how much diversification reduces volatility relative to the weighted average of stand-alone group risk.',
      'Check whether the main portfolio comparisons change under buy-and-hold weights or alternative risk-free assumptions.',
      'Compare observed premiums of selected actively traded equity options with Black-Scholes values based on historical volatility, and calculate Delta, Gamma and Vega.'
    ]: d.bullet(text)
    d.heading('1 3 Scope and working propositions',2)
    d.p('The sample is purposive: three named companies in each group were specified in the proposal. Two descriptive propositions guide the comparison. First, the NBFC portfolio may have both a higher realized annualized return and higher volatility than the bank portfolio. Both conditions must be checked separately. Second, the mixed portfolio may have lower volatility than the weighted average of the two group volatilities. That is different from being safer than each group individually.')
    d.p('These are descriptive comparisons, not formal population hypothesis tests. The firms are not random sector samples, and daily observations from a common financial market are not independent sector replicates. The report therefore does not attach p-values or claims of statistical acceptance to these propositions.')

    d.heading('2 Institutional context and literature',new_page=True)
    d.heading('2 1 Banks and NBFCs',2)
    d.p('The Reserve Bank of India distinguishes NBFCs from banks even where their lending activities overlap. NBFCs cannot accept demand deposits and do not issue cheques drawn on themselves as part of the payment system. NBFC deposits are outside the DICGC deposit-insurance arrangement. Some NBFCs can accept permitted term deposits, so it would be incorrect to state that all NBFCs are prohibited from accepting every form of deposit (RBI, 2017). These distinctions concern institutional structure; they do not by themselves determine equity returns.')
    d.table(['Dimension','Commercial banks','NBFCs'],[
      ['Demand deposits','Can accept eligible bank deposits','Cannot accept demand deposits'],
      ['Payment services','Participate in the banking payment system','Do not issue cheques drawn on themselves'],
      ['Deposit insurance','Eligible bank deposits subject to DICGC rules','NBFC deposits outside DICGC'],
      ['Equity risk in this study','Market returns of three selected bank stocks','Market returns of three selected NBFC stocks']
    ],[1.25,2.8,2.89],caption='Institutional distinctions relevant to the comparison')
    d.p('RBI\'s 2021 scale-based framework introduced four NBFC regulatory layers according to size, activity and perceived risk, with the general framework taking effect in October 2022. The observation period therefore includes a changing regulatory environment (RBI, 2021). This study does not estimate the causal effect of that change.')
    d.heading('2 2 Portfolio risk and performance measurement',2)
    d.p('Markowitz (1952) makes covariance central to portfolio selection. Combining two investments can reduce risk when their returns do not move perfectly together. An equal-weight comparison illustrates this mechanism but does not identify an efficient frontier or prove that the chosen weights are optimal. This project uses equal weights to make the comparison transparent and avoid estimating expected returns for an optimization exercise.')
    d.p('Sharpe (1964) distinguishes systematic risk in a diversified market setting from total variability. This motivates reporting beta beside volatility. Here beta is estimated from historical covariance with the NIFTY 50 price index. It is a sample sensitivity, not a forecast, a complete measure of risk or a formal test of the capital asset pricing model.')
    d.p('Sharpe (1966, 1994) relates reward to return variability. In this report, excess daily returns are measured against a stated risk-free assumption before annualization. CAGR remains a separate geometric growth measure and is not inserted into the Sharpe calculation. Historical Sharpe ratios are sensitive to the chosen window, the risk-free assumption and the dependence structure of returns.')
    d.heading('2 3 Option valuation and the study contribution',2)
    d.p('Black and Scholes (1973) derive option values through a no-arbitrage framework involving the underlying security and the option. Merton (1973) develops rational pricing restrictions and extensions, including dividend effects. Their framework provides a tractable way to connect volatility to option prices and local sensitivities. Constant volatility, continuous trading and frictionless replication remain strong assumptions.')
    d.p('The contribution of this project is an internally consistent applied comparison using the firms in the proposal, rather than a new asset-pricing theory. Equity results and option results use different units of analysis: a five-year return panel versus a small single-date contract sample. The two components are linked by historical volatility, but option-price gaps are not used to rank the entire banking and NBFC sectors.')

def data_and_methods(d,r):
    inds=r['individual_metrics']
    nobs=inds[0]['n']
    d.heading('3 Data and research design',new_page=True)
    d.p(f'The analysis covers 1 January 2021 to 31 December 2025 and uses {nobs:,} aligned daily return observations for each included series. The immediately preceding 31 December 2020 close provides the initial price for the first 2021 return. Prices before that base date are retained in the raw download but do not enter the five-year performance calculation.')
    d.table(['Company','NSE symbol','Group'],[
      ['HDFC Bank','HDFCBANK','Bank'],['ICICI Bank','ICICIBANK','Bank'],['State Bank of India','SBIN','Bank'],
      ['Bajaj Finance','BAJFINANCE','NBFC'],['Shriram Finance','SHRIRAMFIN','NBFC'],['Muthoot Finance','MUTHOOTFIN','NBFC']
    ],[3.25,2.0,1.69],caption='Purposively selected equity sample')
    d.heading('3 1 Sources and price treatment',2)
    d.p('The historical equity dataset is downloaded from the Yahoo Finance chart service for NSE-listed securities. This is a secondary-vendor implementation of the proposal\'s historical-stock component, rather than a claim that the observations were downloaded directly from NSE. The raw JSON responses, request URLs, retrieval timestamps and SHA-256 hashes are preserved. The dataset contains daily open, high, low, close, adjusted close and volume fields. Return calculations use adjusted close throughout.')
    d.p('The provider\'s historical OHLC fields are already split-adjusted. Adjusted close also reflects the provider\'s dividend adjustments and serves as an approximation to a reinvested total-return series. Applying share factors a second time would introduce errors. Absolute historical vendor prices should therefore not be presented as the unadjusted prices printed on those past trading dates. Volume is retained as a source field and is not used to calculate returns.')
    d.p('The market benchmark is the NIFTY 50 price index, downloaded as ^NSEI. NSE Indices distinguishes a price index from a total-return index that includes reinvested dividends. This mismatch means stock-versus-index growth differences are not a like-for-like total-return outperformance measure. The index supplies market context and the reference series for beta; bank-versus-NBFC comparisons retain the same adjusted-price convention across all six equities (NSE Indices, n.d.).')
    d.p('The option observations come directly from NSE\'s official futures-and-options UDiFF bhavcopy for 31 December 2025. This archive records contract specifications, closing and settlement prices, the underlying price, trading volume and open interest. Observed implied volatility is not supplied in the selected archive rows; the implied volatilities reported here are calculated by numerical inversion and explicitly identified as derived values.')
    d.heading('3 2 Cleaning and comparability',2)
    d.p('Each timestamp is converted to the Indian trading date, records are sorted, duplicate dates and nonpositive prices are checked, and the price series are aligned across the six stocks and index. Missing quotes are not forward-filled into artificial zero-return observations. The scripts report common-date coverage, missing fields, duplicate counts and extreme daily returns. Source files are retained separately from processed tables so that the return calculations can be rerun without another download.')
    d.p('Share events deserve particular attention. HDFC Bank issued a 1:1 bonus in 2025; Bajaj Finance\'s 2025 split and 4:1 bonus together increased the share count by a factor of ten; Shriram Finance undertook a five-for-one split in January 2025. The event table and adjusted returns around these dates are checked for continuity. These are changes in share units, not corresponding economic losses. The data audit distinguishes the vendor event date from a company record or allotment date when those differ.')
    d.p('The firms\' businesses are not constant over time. HDFC Bank\'s merger during 2023 and Shriram\'s 2022 merger and name change affect economic comparability. Shriram Finance\'s earlier listed history represents Shriram Transport Finance, not a separate sixth-year security. The study follows the vendor\'s continuous listed-security series and does not reconstruct a constant-business portfolio (Shriram Finance, 2023).')

    d.heading('4 Calculation methods',new_page=True)
    d.heading('4 1 Returns and annualization',2)
    d.p('Daily simple returns equal adjusted close divided by the preceding adjusted close, less one. Simple returns are used because a portfolio\'s one-period return is the weighted average of its constituents\' simple returns. Wealth starts at 100 on the base date and compounds the subsequent daily returns. Total return is final wealth divided by initial wealth, less one.')
    d.equation('charts/equations/returns.png',5.9)
    d.p('Annualized arithmetic mean equals the sample daily mean multiplied by 252. Annualized volatility equals the sample standard deviation of daily returns, using an n minus one denominator, multiplied by the square root of 252. CAGR uses the actual elapsed calendar years between the base date and the ending date. The two annual return measures answer different questions: arithmetic mean summarizes the daily distribution, while CAGR describes the constant annual compound rate matching realized wealth.')
    d.equation('charts/equations/risk.png',6.1)
    d.heading('4 2 Risk adjusted return and market sensitivity',2)
    d.p('The baseline risk-free assumption is a 6% effective annual return. It is a modelling assumption, not a measured Treasury-bill yield for every day of the sample. Its equivalent daily return is (1.06) raised to one over 252, less one. Sharpe is the daily mean excess return divided by the sample daily standard deviation, multiplied by the square root of 252. Using the same rate and date set makes the portfolios comparable; a 4% and 8% sensitivity shows the effect of changing this input.')
    d.equation('charts/equations/sharpe_beta.png',6.2)
    d.p('Beta equals sample covariance between the asset and NIFTY 50 daily returns divided by the sample variance of the index. It is also the slope of a regression with an intercept on those aligned returns. A beta above one indicates greater sample sensitivity to the selected benchmark; it does not automatically imply greater maximum drawdown, better expected returns or stronger causal exposure.')
    d.heading('4 3 Drawdown and tail losses',2)
    d.p('Daily drawdown is current wealth divided by its previous running maximum, less one. Maximum drawdown is the lowest value of that series, including the initial wealth observation in the running peak. Drawdown is reported as a negative return. A value of -20% means that wealth fell 20% from a preceding peak within this observation window.')
    d.p('The supplementary historical 95% one-day Value at Risk is the negative of the 5th percentile daily return, reported as a positive loss. Conditional Value at Risk is the average loss among observations at or below that percentile. These are empirical daily loss summaries, not guaranteed loss limits. They do not incorporate a fitted tail model or intraday risk and depend on the selected sample and quantile convention.')
    d.heading('4 4 Portfolios and diversification',2)
    d.p('The bank portfolio places one-third in each bank at the start of every trading day. The NBFC portfolio applies the same rule to the three NBFCs. The mixed portfolio allocates one-half to each group, equivalent to one-sixth in each stock. Taking the weighted mean of returns every day assumes daily rebalancing, with no transaction costs, bid-ask spreads, taxes, slippage or constraints. These conventions isolate the realized return and covariance comparison.')
    d.equation('charts/equations/portfolio.png',6.0)
    d.p('For a 50:50 mix, variance depends on each group\'s variance and their correlation. The diversification reduction is the weighted average of their stand-alone volatilities minus the mixed volatility. A positive reduction is possible even if mixed volatility is higher than the safer group\'s volatility. Pairwise correlations, a portfolio wealth chart and annual results are examined together to avoid drawing a conclusion from one statistic.')
    d.p('A buy-and-hold sensitivity invests in the same initial weights and then lets weights drift. It compounds the initial allocation to each stock rather than averaging daily stock returns. This comparison helps identify the effect of the rebalancing convention; it remains gross of investment costs and is not a trading recommendation.')
    d.heading('4 5 Option model and sensitivities',2)
    d.p('NSE describes stock options as European style and physically settled (NSE, n.d.). The Black-Scholes model with continuous dividend yield is therefore used as a basic European valuation framework. The spot is the contemporaneous underlying price recorded in the official option archive, in the same share units as the strike. Time to expiry is calendar days divided by 365. The continuously compounded interest rate is the natural logarithm of 1.06, aligning the discount factor with the equity analysis\'s 6% effective annual assumption.')
    d.equation('charts/equations/bs.png',6.5)
    d.p('In these expressions, S is spot, K is strike, T is years to expiry, r is the continuously compounded risk-free rate, q is dividend yield, sigma is annualized volatility and N is the standard normal cumulative distribution. The base q is zero. Volatility is estimated from the most recent 252 adjusted daily returns available through the valuation close. No observations after 31 December 2025 are used. This is an end-of-day study; it is not a claim that the closing volatility estimate was available before each option\'s last trade.')
    d.p('Delta measures the local option-value change per INR 1 change in spot. Gamma measures the change in Delta per INR 1 spot move. Vega is reported per one percentage-point increase in annual volatility, so raw mathematical Vega is divided by 100. The signs and scale matter: call Delta is positive, put Delta is negative, and both long options ordinarily have positive Gamma and Vega.')
    d.p('Historical-volatility model values are compared with observed closing premiums. Separately, implied volatility solves for the volatility that reproduces an option\'s own observed premium. Successful repricing with that implied volatility is a numerical solver check, not independent evidence that the model predicts market prices. Dividend and volatility sensitivities illustrate how assumptions move valuations.')

def make_equations():
    sys.path.insert(0,str(ROOT/'.deps'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    formulas={
      'returns':r'$R_{i,t}=\frac{P^{adj}_{i,t}}{P^{adj}_{i,t-1}}-1\qquad W_t=100\prod_{s=1}^{t}(1+R_s)$',
      'risk':r'$\mu_{ann}=252\overline{R}\qquad \sigma_{ann}=\sqrt{252}\,s_R\qquad CAGR=\left(\frac{W_T}{100}\right)^{1/Y}-1$',
      'sharpe_beta':r'$Sharpe=\sqrt{252}\frac{\overline{R}-r_{f,d}}{s_R}\qquad \beta_i=\frac{Cov(R_i,R_m)}{Var(R_m)}$',
      'portfolio':r'$R_{p,t}=\sum_i w_i R_{i,t}\qquad \sigma_{mix}^2=\frac{\sigma_B^2+\sigma_N^2+2\rho_{BN}\sigma_B\sigma_N}{4}$',
      'bs':r'$C=Se^{-qT}N(d_1)-Ke^{-rT}N(d_2)$'+'\n'+r'$P=Ke^{-rT}N(-d_2)-Se^{-qT}N(-d_1)$'+'\n'+r'$d_1=\frac{\ln(S/K)+(r-q+\sigma^2/2)T}{\sigma\sqrt{T}},\quad d_2=d_1-\sigma\sqrt{T}$'
    }
    out=ROOT/'charts/equations'; out.mkdir(parents=True,exist_ok=True)
    for name,text in formulas.items():
        fig=plt.figure(figsize=(8,1.65 if name=='bs' else .6))
        fig.text(.5,.5,text,ha='center',va='center',fontsize=15,linespacing=1.6)
        fig.savefig(out/(name+'.png'),dpi=220,bbox_inches='tight',pad_inches=.08,facecolor='white')
        plt.close(fig)

