"""Auditable four-contract case study from official NSE 2025-12-31 bhavcopy.

Run after data/prices.csv exists. No network access is used during analysis.
The market quote is the observed closing premium, never a model-generated quote.
"""
from pathlib import Path
from math import exp, log, sqrt, erf, pi
import hashlib
import json
import zipfile
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATE = '2025-12-31'
EXPIRY = '2026-01-27'
RF_EFFECTIVE = .06
R = log(1 + RF_EFFECTIVE)
Q = 0.
SOURCE = 'https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_20251231_F_0000.csv.zip'
ARCHIVE = ROOT / 'data/options_raw/fo_20251231_0.zip'
ARTIFACTS = ROOT / 'artifacts'
CHARTS = ROOT / 'charts'
ARTIFACTS.mkdir(exist_ok=True)
CHARTS.mkdir(exist_ok=True)

def norm_cdf(x):
    return .5 * (1 + erf(x / sqrt(2)))

def norm_pdf(x):
    return exp(-.5*x*x)/sqrt(2*pi)

def black_scholes(s, k, t, r, q, sigma, option_type):
    """Per-share INR prices; vega is INR per 1 percentage point annual volatility."""
    if min(s, k, t, sigma) <= 0 or option_type not in ('CE','PE'):
        raise ValueError('Positive inputs and CE/PE required')
    d1 = (log(s/k) + (r-q+.5*sigma*sigma)*t)/(sigma*sqrt(t))
    d2 = d1 - sigma*sqrt(t)
    ds, dk = exp(-q*t), exp(-r*t)
    if option_type == 'CE':
        price = s*ds*norm_cdf(d1) - k*dk*norm_cdf(d2)
        delta = ds*norm_cdf(d1)
    else:
        price = k*dk*norm_cdf(-d2) - s*ds*norm_cdf(-d1)
        delta = ds*(norm_cdf(d1)-1)
    gamma = ds*norm_pdf(d1)/(s*sigma*sqrt(t))
    vega = s*ds*norm_pdf(d1)*sqrt(t)/100
    return dict(price=price, delta=delta, gamma=gamma, vega_per_1pp=vega, d1=d1, d2=d2)

def implied_volatility(market, s, k, t, r, q, option_type):
    lower = max(0., s*exp(-q*t)-k*exp(-r*t)) if option_type == 'CE' else max(0., k*exp(-r*t)-s*exp(-q*t))
    upper = s*exp(-q*t) if option_type == 'CE' else k*exp(-r*t)
    if not lower < market < upper:
        raise ValueError(f'Observed price {market} outside model bounds ({lower}, {upper})')
    lo, hi = .00001, 5.
    if black_scholes(s,k,t,r,q,hi,option_type)['price'] < market:
        raise ValueError('IV above search interval')
    for _ in range(120):
        mid = (lo+hi)/2
        if black_scholes(s,k,t,r,q,mid,option_type)['price'] < market:
            lo = mid
        else:
            hi = mid
    return (lo+hi)/2

def history_vol(symbol):
    # Raw Yahoo adjusted-close JSON preserved by acquire_prices.py, allowing the
    # options module to reproduce its own trailing window without schema coupling.
    path=ROOT / f'data/raw/{symbol}.NS.json'
    result=json.loads(path.read_text(encoding='utf-8'))['chart']['result'][0]
    dates=pd.to_datetime(result['timestamp'],unit='s',utc=True).tz_convert('Asia/Kolkata').date
    closes=pd.Series(result['indicators']['adjclose'][0]['adjclose'],index=pd.to_datetime(dates),dtype=float).sort_index()
    closes=closes[closes.index <= pd.Timestamp(DATE)]
    returns=closes.pct_change(fill_method=None).dropna().tail(252)
    assert len(returns)==252 and str(returns.index[-1].date())==DATE
    log_returns=np.log(closes/closes.shift(1)).dropna().tail(252)
    return dict(sigma_historical=float(returns.std(ddof=1)*sqrt(252)),sigma_log_sensitivity=float(log_returns.std(ddof=1)*sqrt(252)),
                vol_window_first_return=str(returns.index[0].date()),vol_window_last_return=str(returns.index[-1].date()),vol_observations=len(returns),
                vol_source=f'data/raw/{symbol}.NS.json',vol_source_sha256=hashlib.sha256(path.read_bytes()).hexdigest())

def verify_math():
    tests=[]
    # Independent published textbook parameter benchmark, r=5%, no dividends.
    for typ, expected in [('CE',10.450583572185565),('PE',5.573526022256971)]:
        actual=black_scholes(100,100,1,.05,0,.2,typ)['price']
        assert abs(actual-expected)<1e-10
        tests.append(dict(check='standard_BS_benchmark_'+typ,expected=expected,actual=actual,status='PASS'))
    errors={'put_call_parity':0., 'iv_recovery':0., 'delta_finite_difference':0., 'gamma_finite_difference':0., 'vega_finite_difference':0.}
    for s,k,t,r,q,sigma in [(100,100,1,.05,0,.2),(986.8,990,27/365,R,0,.3),(991.2,990,27/365,R,.02,.15)]:
        call=black_scholes(s,k,t,r,q,sigma,'CE'); put=black_scholes(s,k,t,r,q,sigma,'PE')
        errors['put_call_parity']=max(errors['put_call_parity'],abs(call['price']-put['price']-(s*exp(-q*t)-k*exp(-r*t))))
        for typ in ['CE','PE']:
            v=black_scholes(s,k,t,r,q,sigma,typ)
            errors['iv_recovery']=max(errors['iv_recovery'],abs(implied_volatility(v['price'],s,k,t,r,q,typ)-sigma))
            h=.01; up=black_scholes(s+h,k,t,r,q,sigma,typ)['price']; down=black_scholes(s-h,k,t,r,q,sigma,typ)['price']
            errors['delta_finite_difference']=max(errors['delta_finite_difference'],abs((up-down)/(2*h)-v['delta']))
            errors['gamma_finite_difference']=max(errors['gamma_finite_difference'],abs((up+down-2*v['price'])/(h*h)-v['gamma']))
            hv=1e-5; vu=black_scholes(s,k,t,r,q,sigma+hv,typ)['price']; vd=black_scholes(s,k,t,r,q,sigma-hv,typ)['price']
            errors['vega_finite_difference']=max(errors['vega_finite_difference'],abs((vu-vd)/(2*hv)/100-v['vega_per_1pp']))
    tolerances=dict(put_call_parity=1e-10,iv_recovery=1e-10,delta_finite_difference=1e-7,gamma_finite_difference=1e-7,vega_finite_difference=1e-7)
    for name,error in errors.items():
        assert error<tolerances[name],(name,error)
        tests.append(dict(check=name,max_abs_error=error,tolerance=tolerances[name],status='PASS'))
    return tests

def main():
    with zipfile.ZipFile(ARCHIVE) as archive:
        table=pd.read_csv(archive.open(archive.namelist()[0]))
    symbols=['HDFCBANK','ICICIBANK','SBIN','BAJFINANCE','SHRIRAMFIN','MUTHOOTFIN']
    spots=table[table.TckrSymb.isin(symbols)].groupby('TckrSymb').UndrlygPric.agg(['first','nunique']).reset_index()
    assert spots['nunique'].eq(1).all()
    spots['date']=DATE; spots['source_url']=SOURCE
    spots.rename(columns={'TckrSymb':'symbol','first':'nse_underlying_price'}).to_csv(ROOT/'data/options_underlying_crosscheck.csv',index=False)
    candidates=table[(table.FinInstrmTp=='STO') & (table.TckrSymb.isin(['HDFCBANK','BAJFINANCE'])) & (table.XpryDt==EXPIRY)].copy()
    candidates.to_csv(ROOT/'data/options_candidate_contracts.csv',index=False)
    rows=[]; raw_selected=[]
    for symbol in ['HDFCBANK','BAJFINANCE']:
        t=candidates[candidates.TckrSymb==symbol]
        spot=float(t.UndrlygPric.iloc[0])
        # Deterministic rule: closest strike with traded, positive-OI call and put.
        eligible=t[(t.TtlTradgVol>0)&(t.OpnIntrst>0)&(t.ClsPric>0)].groupby('StrkPric').OptnTp.nunique()
        strikes=eligible[eligible==2].index.tolist()
        strike=min(strikes,key=lambda k:(abs(k-spot),k))
        selected=t[t.StrkPric==strike].sort_values('OptnTp')
        assert len(selected)==2
        hist=history_vol(symbol)
        for raw in selected.to_dict('records'):
            raw_selected.append(raw)
            days=(pd.Timestamp(raw['FininstrmActlXpryDt'])-pd.Timestamp(raw['TradDt'])).days
            tau=days/365
            model=black_scholes(spot,strike,tau,R,Q,hist['sigma_historical'],raw['OptnTp'])
            iv=implied_volatility(raw['ClsPric'],spot,strike,tau,R,Q,raw['OptnTp'])
            iv_pricing_error=black_scholes(spot,strike,tau,R,Q,iv,raw['OptnTp'])['price']-raw['ClsPric']
            # NSE notional turnover reconciles volume in contracts and lot size:
            # turnover/(volume*lot) - strike yields a within-day premium VWAP.
            implied_premium_vwap=raw['TtlTrfVal']/(raw['TtlTradgVol']*raw['NewBrdLotQty'])-strike
            assert raw['LwPric']-.01 <= implied_premium_vwap <= raw['HghPric']+.01
            assert raw['OpnIntrst'] % raw['NewBrdLotQty']==0
            row=dict(symbol=symbol,group='Bank' if symbol=='HDFCBANK' else 'NBFC',date=DATE,expiry=raw['FininstrmActlXpryDt'],
                     contract=raw['FinInstrmNm'],instrument_id=int(raw['FinInstrmId']),option_type=raw['OptnTp'],spot=spot,strike=strike,
                     market_price=float(raw['ClsPric']),settlement_price=float(raw['SttlmPric']),option_open=float(raw['OpnPric']),
                     option_high=float(raw['HghPric']),option_low=float(raw['LwPric']),days_to_expiry=days,time_years=tau,
                     volume_contracts=int(raw['TtlTradgVol']),open_interest_units=int(raw['OpnIntrst']),lot_size=int(raw['NewBrdLotQty']),
                     open_interest_contracts=int(raw['OpnIntrst']/raw['NewBrdLotQty']),number_trades=int(raw['TtlNbOfTxsExctd']),
                     risk_free_effective_annual=RF_EFFECTIVE,risk_free_continuous=R,dividend_yield_continuous=Q,
                     **hist,bs_price=model.pop('price'),**model,derived_iv=iv,derived_iv_reprice_error=iv_pricing_error,
                     market_minus_model=float(raw['ClsPric']-black_scholes(spot,strike,tau,R,Q,hist['sigma_historical'],raw['OptnTp'])['price']),
                     implied_premium_vwap=implied_premium_vwap,source_url=SOURCE)
            row['model_minus_market_pct']=row['bs_price']/row['market_price']-1
            row['price_q_2pct']=black_scholes(spot,strike,tau,R,.02,hist['sigma_historical'],raw['OptnTp'])['price']
            row['price_sigma_minus_5pp']=black_scholes(spot,strike,tau,R,Q,max(.001,hist['sigma_historical']-.05),raw['OptnTp'])['price']
            row['price_sigma_plus_5pp']=black_scholes(spot,strike,tau,R,Q,hist['sigma_historical']+.05,raw['OptnTp'])['price']
            row['price_log_vol']=black_scholes(spot,strike,tau,R,Q,hist['sigma_log_sensitivity'],raw['OptnTp'])['price']
            rows.append(row)
    df=pd.DataFrame(rows)
    df.to_csv(ROOT/'data/options_observations.csv',index=False,float_format='%.12g')
    pd.DataFrame(raw_selected).to_csv(ROOT/'data/options_selected_raw.csv',index=False)
    parity=[]
    for symbol,case in df.groupby('symbol',sort=False):
        ce=case[case.option_type=='CE'].iloc[0]; pe=case[case.option_type=='PE'].iloc[0]
        rhs=ce.spot*exp(-Q*ce.time_years)-ce.strike*exp(-R*ce.time_years)
        parity.append(dict(symbol=symbol,observed_call_minus_put=ce.market_price-pe.market_price,model_parity_rhs=rhs,
                           observed_parity_residual=ce.market_price-pe.market_price-rhs,model_parity_residual=ce.bs_price-pe.bs_price-rhs))
    checks=verify_math()
    assert np.abs(df.derived_iv_reprice_error).max()<1e-8
    checks += [dict(check='market_IV_repricing',max_abs_error=float(np.abs(df.derived_iv_reprice_error).max()),status='PASS'),
               dict(check='all_selected_contracts_traded_positive_OI',count=4,status='PASS'),
               dict(check='volume_units_reconcile_notional_turnover_and_lot',count=4,status='PASS'),
               dict(check='no_lookahead_252_return_volatility',last_return=DATE,count_each=252,status='PASS')]
    results=dict(valuation_date=DATE,expiry=EXPIRY,source_url=SOURCE,archive_sha256=hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(),
                 selection_rule='HDFCBANK (bank) and BAJFINANCE (NBFC), nearest unexpired monthly maturity, closest-to-spot strike with positive-volume positive-OI call and put; one paired strike per company.',
                 price_units='INR per share; premiums and Greeks are not multiplied by lot size.',
                 risk_free_convention='6% effective annual assumption converted to continuously compounded r=ln(1.06).',
                 volatility_convention='252 most recent daily simple returns from split/dividend-adjusted close; sample standard deviation (ddof=1) times sqrt(252), ending valuation date.',
                 greeks_convention='Baseline historical-volatility Greeks. Delta: INR option change per INR spot move; gamma: delta change per INR spot move; vega: INR per 1 percentage point annual volatility.',
                 observations=rows,parity_diagnostics=parity,validation=checks,
                 limitations=[
                     'This is an end-of-day, four-contract case study from one date, not evidence about all bank versus NBFC option markets.',
                     'NSE stock options are European style and physically settled; model outputs exclude delivery funding, taxes, margins and transaction costs.',
                     'Market price is reported ClsPric, not a simultaneous executable bid/ask midpoint. Underlying and options closing conventions can differ.',
                     'The baseline assumes q=0 and a constant 6% effective annual risk-free rate. Neither is a calibrated market forward curve. q=2% is illustrative sensitivity, not an observed yield.',
                     'Historical volatility is backward-looking; model-versus-price gaps may reflect expected volatility, carry, dividends, skew, bid/ask spreads or timing. They are not demonstrated mispricing or arbitrage.',
                     'Implied volatility is numerically inferred from closing premiums with the stated model. It is not supplied in the bhavcopy.',
                     'Reported volume is contracts; raw OpnIntrst is underlying units. Open-interest contracts divide those units by NewBrdLotQty.',
                     'The January 2026 expiry lies beyond the 2021-2025 equity sample, while the valuation inputs are observed only through 31 December 2025.'
                 ])
    (ARTIFACTS/'options_results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    pd.DataFrame(parity).to_csv(ARTIFACTS/'options_parity_diagnostics.csv',index=False)
    (ARTIFACTS/'options_validation.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    draw_charts(df)
    print(df[['symbol','option_type','spot','strike','market_price','sigma_historical','bs_price','derived_iv','delta','gamma','vega_per_1pp']].to_string(index=False))
    print('Wrote observations, results, validation and two charts.')

def draw_charts(df):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    labels=[f'{r.symbol}\n{"Call" if r.option_type=="CE" else "Put"}' for r in df.itertuples()]
    x=np.arange(len(df)); width=.35
    fig,ax=plt.subplots(figsize=(10,5.4),layout='constrained')
    bars1=ax.bar(x-width/2,df.market_price,width,label='Observed NSE closing premium',color='#167D9A')
    bars2=ax.bar(x+width/2,df.bs_price,width,label='Black-Scholes, historical volatility',color='#DE9C37')
    ax.bar_label(bars1,fmt='%.2f',padding=3,fontsize=9);ax.bar_label(bars2,fmt='%.2f',padding=3,fontsize=9)
    ax.set_xticks(x,labels);ax.set_ylabel('Option premium (INR per share)');ax.set_ylim(0,max(df.bs_price.max(),df.market_price.max())*1.3)
    ax.set_title('Observed premiums and historical-volatility model values',loc='left',weight='bold',pad=40)
    ax.text(0,1.03,'31 Dec 2025  |  Strike INR 990  |  Expiry 27 Jan 2026  |  r = ln(1.06), q = 0',transform=ax.transAxes,fontsize=9,color='#555555')
    ax.legend(loc='upper right',frameon=False,fontsize=9);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
    fig.savefig(CHARTS/'options_price_comparison.png',dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,5.4),layout='constrained')
    h=ax.bar(x-width/2,df.sigma_historical*100,width,label='Trailing 252-return historical volatility',color='#167D9A')
    v=ax.bar(x+width/2,df.derived_iv*100,width,label='Derived IV from closing premium',color='#DE9C37')
    ax.bar_label(h,fmt='%.1f%%',padding=3,fontsize=9);ax.bar_label(v,fmt='%.1f%%',padding=3,fontsize=9)
    ax.set_xticks(x,labels);ax.set_ylabel('Annualized volatility (%)');ax.set_ylim(0,max(df.sigma_historical.max(),df.derived_iv.max())*130)
    ax.set_title('Historical and market-implied volatility can differ',loc='left',weight='bold',pad=40)
    ax.text(0,1.03,'Implied volatility is inferred using Black-Scholes; it is not a field reported in the source archive.',transform=ax.transAxes,fontsize=9,color='#555555')
    ax.legend(loc='upper right',frameon=False,fontsize=9);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
    fig.savefig(CHARTS/'options_volatility_comparison.png',dpi=180);plt.close(fig)

if __name__=='__main__':
    main()
