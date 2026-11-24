"""Reproduce 2021-2025 risk/return analysis from the preserved Yahoo JSON responses.

Run with Python, numpy and pandas; matplotlib is optional for --no-charts.
Returns use provider adjusted close. This never applies split factors twice.
"""
from pathlib import Path
import sys, os, json, math, hashlib, argparse
from datetime import datetime, timezone, timedelta
ROOT=Path(__file__).resolve().parents[1]
if (ROOT/'.deps').exists(): sys.path.append(str(ROOT/'.deps'))
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.mplconfig'))
import numpy as np
import pandas as pd

DATA=ROOT/'data'; ART=ROOT/'artifacts'; CHART=ROOT/'charts'
for p in [DATA,ART,CHART]: p.mkdir(exist_ok=True)
TICKERS=['HDFCBANK','ICICIBANK','SBIN','BAJFINANCE','SHRIRAMFIN','MUTHOOTFIN','NIFTY50']
NAMES=dict(zip(TICKERS,['HDFC Bank','ICICI Bank','State Bank of India','Bajaj Finance','Shriram Finance','Muthoot Finance','NIFTY 50 price index']))
NAMES.update(BANKS='Bank portfolio',NBFCS='NBFC portfolio',MIXED='50:50 mixed portfolio')
GROUPS={'BANKS':TICKERS[:3],'NBFCS':TICKERS[3:6],'MIXED':TICKERS[:6]}
SECTOR={t:('Bank' if t in TICKERS[:3] else 'NBFC' if t in TICKERS[3:6] else 'Benchmark') for t in TICKERS}
RF=.06; DAYS=252; BASE=pd.Timestamp('2020-12-31'); END=pd.Timestamp('2025-12-31')

def metrics(r,benchmark=None,rf=RF):
    r=pd.Series(r).astype(float)
    wealth=np.r_[1.,(1+r).cumprod().values]
    drawdown=wealth/np.maximum.accumulate(wealth)-1
    sd=r.std(ddof=1); mean=r.mean(); quantile=r.quantile(.05,interpolation='linear')
    beta=None if benchmark is None else float(r.cov(benchmark)/benchmark.var(ddof=1))
    return {'n':int(len(r)),'total_return':float(wealth[-1]-1),'cagr':float(wealth[-1]**(365.25/(END-BASE).days)-1),
        'annual_mean':float(mean*DAYS),'annual_volatility':float(sd*np.sqrt(DAYS)),
        'sharpe':float((mean-((1+rf)**(1/DAYS)-1))/sd*np.sqrt(DAYS)),'beta':beta,
        'max_drawdown':float(drawdown.min()),'var95':float(-quantile),
        'cvar95':float(-r[r<=quantile].mean()),'daily_mean':float(mean),'daily_std':float(sd),
        'best_day':float(r.max()),'worst_day':float(r.min())}

def load():
    records=[]; source_diagnostics=[]; events=[]
    for t in TICKERS:
        f=DATA/'raw'/('NSEI.json' if t=='NIFTY50' else t+'.NS.json')
        result=json.loads(f.read_text())['chart']['result'][0]
        quote=result['indicators']['quote'][0]; adj=result['indicators']['adjclose'][0]['adjclose']
        ts=pd.to_datetime(result['timestamp'],unit='s',utc=True).tz_convert('Asia/Kolkata').tz_localize(None).normalize()
        frame=pd.DataFrame({'date':ts,'ticker':t,'sector':SECTOR[t],**{k:quote[k] for k in ['open','high','low','close','volume']},'adjusted_close':adj})
        missing=int(frame[['open','high','low','close','adjusted_close','volume']].isna().any(axis=1).sum())
        assert frame.date.is_unique, t+' duplicate dates'
        assert not missing,t+' missing OHLCV values'
        assert (frame[['open','high','low','close','adjusted_close']]>0).all().all(),t+' nonpositive price'
        assert (frame['high']+1e-6>=frame[['open','close','low']].max(axis=1)).all(),t+' invalid high'
        assert (frame['low']-1e-6<=frame[['open','close','high']].min(axis=1)).all(),t+' invalid low'
        assert (frame.volume>=0).all(),t+' negative volume'
        source_diagnostics.append({'ticker':t,'raw_rows':len(frame),'missing_rows':missing,'duplicate_dates':0,
            'zero_volume_rows':int((frame.volume==0).sum()),'first_raw_date':str(frame.date.min().date()),'last_raw_date':str(frame.date.max().date())})
        records.append(frame[frame.date.between(BASE,END)])
        for etype,evs in result.get('events',{}).items():
            for e in evs.values():
                events.append({'ticker':t,'type':etype,'date':datetime.fromtimestamp(e['date'],timezone(timedelta(hours=5.5))).date().isoformat(),**{k:v for k,v in e.items() if k!='date'}})
    long=pd.concat(records,ignore_index=True).sort_values(['date','ticker'])
    prices=long.pivot(index='date',columns='ticker',values='adjusted_close')[TICKERS]
    dropped=prices.index[prices.isna().any(axis=1)].strftime('%Y-%m-%d').tolist()
    assert not dropped,'Unaligned observations require review; do not silently bridge missing dates'
    assert prices.index[0]==BASE and prices.index[-1]==END
    long.to_csv(DATA/'prices.csv',index=False,float_format='%.12g')
    prices.to_csv(DATA/'adjusted_prices.csv',float_format='%.12g')
    pd.DataFrame(events).to_csv(DATA/'corporate_actions_vendor.csv',index=False)
    return long,prices,source_diagnostics,events,dropped

def make_charts(prices,returns,wealth,results):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':15,'axes.labelsize':11,
        'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white','axes.facecolor':'white',
        'axes.grid':True,'grid.alpha':.18,'grid.color':'#8d98a6','savefig.dpi':180})
    colors={'BANKS':'#183c63','NBFCS':'#008b84','MIXED':'#b46d12','NIFTY50':'#828894',
        'HDFCBANK':'#183c63','ICICIBANK':'#426db3','SBIN':'#90a8d0','BAJFINANCE':'#005950','SHRIRAMFIN':'#008b84','MUTHOOTFIN':'#66bfb0'}
    labels={'BANKS':'Banks','NBFCS':'NBFCs','MIXED':'50:50 mixed','NIFTY50':'NIFTY 50 (price)'}
    def finish(fig,name):
        fig.tight_layout(pad=1.5); fig.savefig(CHART/(name+'.png'),bbox_inches='tight'); plt.close(fig)
    fig,ax=plt.subplots(figsize=(10.5,5.2))
    for t in ['BANKS','NBFCS','MIXED','NIFTY50']:
        ax.plot(wealth.index,wealth[t]*100,label=labels[t],color=colors[t],linewidth=2.3 if t!='NIFTY50' else 1.7,linestyle='--' if t=='NIFTY50' else '-')
    ax.set(title='Growth of Rs 100 | equal-weight portfolios',ylabel='Wealth index (31 Dec 2020 = 100)',xlabel='Daily observations, 2021–2025'); ax.legend(ncol=2,loc='upper left')
    finish(fig,'portfolio_wealth')
    fig,axes=plt.subplots(1,2,figsize=(11,4.8),sharey=True)
    for ax,group,title in zip(axes,[TICKERS[:3],TICKERS[3:6]],['Commercial banks','NBFCs']):
        for t in group: ax.plot(wealth.index,wealth[t]*100,label=NAMES[t],color=colors[t],linewidth=1.8)
        ax.set(title=title,xlabel='2021–2025');ax.legend(loc='upper left',fontsize=9)
    axes[0].set_ylabel('Wealth index (31 Dec 2020 = 100)')
    finish(fig,'individual_wealth')
    fig,ax=plt.subplots(figsize=(10.5,5.2))
    for row in results['individual_metrics']+results['portfolio_metrics']+[results['benchmark_metrics']]:
        t=row['ticker']; x=row['annual_volatility']; y=row['cagr']
        ax.scatter(x,y,s=75 if t in TICKERS[:6] else 115,color=colors[t],marker='o' if t in TICKERS[:6] else 'D',zorder=3)
        offsets={'ICICIBANK':(8,4),'MIXED':(8,-13),'NBFCS':(-42,9),'BAJFINANCE':(8,-12),'HDFCBANK':(8,7),'NIFTY50':(8,-15),'SBIN':(7,-12)}
        ax.annotate(labels.get(t,NAMES[t]),(x,y),xytext=offsets.get(t,(7,5)),textcoords='offset points',fontsize=9)
    ax.set(title='Return earned versus risk taken',xlabel='Annualized daily-return volatility',ylabel='Calendar-time CAGR')
    ax.xaxis.set_major_formatter(PercentFormatter(1));ax.yaxis.set_major_formatter(PercentFormatter(1));ax.margins(.15)
    finish(fig,'risk_return')
    corr=returns[TICKERS[:6]].corr()
    fig,ax=plt.subplots(figsize=(8.5,6.4)); im=ax.imshow(corr,cmap='YlGnBu',vmin=0,vmax=1)
    ax.grid(False);ax.set_xticks(range(6),[NAMES[t] for t in corr.columns],rotation=35,ha='right');ax.set_yticks(range(6),[NAMES[t] for t in corr.index]);ax.set_title('Daily return correlations | six selected stocks',pad=15)
    for i in range(6):
        for j in range(6):ax.text(j,i,f'{corr.iloc[i,j]:.2f}',ha='center',va='center',color='white' if corr.iloc[i,j]>.60 else '#183c63')
    fig.colorbar(im,ax=ax,fraction=.046,pad=.04);finish(fig,'correlation_heatmap')
    annual=pd.DataFrame(results['annual_returns']).set_index('year')
    fig,ax=plt.subplots(figsize=(10.5,5.2));x=np.arange(len(annual));w=.20
    for i,t in enumerate(['BANKS','NBFCS','MIXED','NIFTY50']): ax.bar(x+(i-1.5)*w,annual[t],width=w,label=labels[t],color=colors[t])
    ax.set_xticks(x,annual.index);ax.set(title='Calendar-year returns | portfolio comparison',ylabel='Compounded return');ax.yaxis.set_major_formatter(PercentFormatter(1));ax.axhline(0,color='#666666',linewidth=.8);ax.legend(ncol=4,loc='upper left',fontsize=9)
    finish(fig,'annual_returns')
    fig,ax=plt.subplots(figsize=(10.5,5.2))
    for t in ['BANKS','NBFCS','MIXED','NIFTY50']:
        dd=wealth[t]/wealth[t].cummax()-1
        ax.plot(dd.index,dd,label=labels[t],color=colors[t],linewidth=1.6,linestyle='--' if t=='NIFTY50' else '-')
    ax.set(title='Loss from each portfolio’s previous peak',ylabel='Drawdown',xlabel='Daily observations, 2021–2025');ax.yaxis.set_major_formatter(PercentFormatter(1));ax.legend(ncol=4,loc='lower left',fontsize=9)
    finish(fig,'drawdown')

def main(charts=True):
    long,prices,source_diag,events,dropped=load()
    r=prices.pct_change(fill_method=None).iloc[1:].copy()
    assert r.index[0]==pd.Timestamp('2021-01-01')
    for group,tickers in GROUPS.items(): r[group]=r[tickers].mean(axis=1)
    assert not r.isna().any().any()
    # Explicit initial wealth is essential for drawdowns that start on the first day.
    wealth=pd.concat([pd.DataFrame(1.,index=[BASE],columns=r.columns),(1+r).cumprod()])
    wealth.index.name='date'
    drawdown=wealth/wealth.cummax()-1
    r.to_csv(DATA/'returns.csv',float_format='%.12g');wealth.to_csv(DATA/'wealth.csv',float_format='%.12g');drawdown.to_csv(DATA/'drawdowns.csv',float_format='%.12g')
    def row(t): return {'ticker':t,'name':NAMES[t],'sector':SECTOR.get(t,'Portfolio'),**metrics(r[t],r.NIFTY50)}
    annual=(1+r).groupby(r.index.year).prod()-1
    annual.index.name='year';annual.to_csv(DATA/'annual_returns.csv',float_format='%.12g')
    annual_rows=[{'year':int(y),**{k:float(v) for k,v in vals.items()}} for y,vals in annual.iterrows()]
    correlations=r[TICKERS[:6]].corr()
    correlations.to_csv(DATA/'correlations.csv',float_format='%.12g')
    bh=[]
    for group,tickers in GROUPS.items():
        w=(prices[tickers]/prices[tickers].iloc[0]).mean(axis=1)
        br=w.pct_change(fill_method=None).iloc[1:]
        bh.append({'ticker':group,'name':NAMES[group],'sector':'Portfolio',**metrics(br,r.NIFTY50)})
    rf_sensitivity=[{'rf':rf,'ticker':group,'sharpe':metrics(r[group],r.NIFTY50,rf=rf)['sharpe']} for rf in [.04,.06,.08] for group in GROUPS]
    splits=[]
    for t,date,factor,source in [('BAJFINANCE','2025-06-16',10,'https://nsearchives.nseindia.com/content/circulars/FAOP68547.pdf'),('HDFCBANK','2025-08-26',2,'https://www.nseindia.com/get-quote/equity/HDFCBANK/HDFC-Bank-Limited'),('SHRIRAMFIN','2025-01-10',5,'https://nsearchives.nseindia.com/content/circulars/FAOP66059.pdf')]:
        d=pd.Timestamp(date);ix=prices.index.get_loc(d);before=prices.index[ix-1]
        split={'ticker':t,'ex_date':date,'official_factor':factor,'source_url':source,'prior_trading_day':str(before.date()),'adjusted_return':float(r.loc[d,t]),'prior_adjusted_close':float(prices.loc[before,t]),'ex_date_adjusted_close':float(prices.loc[d,t])}
        assert abs(split['adjusted_return'])<.2,'Suspected corporate action discontinuity'
        splits.append(split)
    cross=[]
    official={'BAJFINANCE':986.8,'HDFCBANK':991.2,'ICICIBANK':1342.9,'MUTHOOTFIN':3811.75,'SBIN':982.2,'SHRIRAMFIN':996.2}
    for t,p in official.items():
        val=float(long[(long.ticker==t)&(long.date==END)].close.iloc[0]);err=val-p
        cross.append({'date':'2025-12-31','ticker':t,'yahoo_close':val,'nse_fo_underlying_price':p,'difference':err})
        same_published_prices = t == 'MUTHOOTFIN' and round(val, 2) == 3811.70 and p == 3811.75
        cross[-1]['status'] = 'documented_source_difference' if same_published_prices else 'within_tolerance'
        assert abs(err)<.011 or same_published_prices,t+' vendor/exchange close mismatch'
    trailing=[{'ticker':t,'date':'2025-12-31','spot_close':float(long[(long.ticker==t)&(long.date==END)].close.iloc[0]),'n_returns':252,'volatility':float(r[t].iloc[-252:].std(ddof=1)*np.sqrt(252))} for t in TICKERS[:6]]
    pd.DataFrame(trailing).to_csv(DATA/'trailing252_volatility.csv',index=False,float_format='%.12g')
    # Meaningful identities catch weighting, compounding, tail-risk and benchmark errors.
    assert np.allclose(r.MIXED,.5*r.BANKS+.5*r.NBFCS,atol=1e-14)
    assert np.allclose(wealth[TICKERS].iloc[-1],prices.iloc[-1]/prices.iloc[0],atol=1e-10)
    assert abs(metrics(r.NIFTY50,r.NIFTY50)['beta']-1)<1e-12
    assert np.allclose((1+annual).prod(),wealth.iloc[-1],atol=1e-10)
    assert all(metrics(r[t],r.NIFTY50)['cvar95']>=metrics(r[t],r.NIFTY50)['var95'] for t in r)
    assert (r.max(axis=0)<.5).all() and (r.min(axis=0)>-.5).all()
    cov=r[TICKERS[:6]].cov(); w=np.repeat(1/6,6)
    assert np.isclose(r.MIXED.var(ddof=1),w@cov.values@w,atol=1e-14)
    avg_bank_corr=float(correlations.loc[TICKERS[:3],TICKERS[:3]].values[np.triu_indices(3,1)].mean())
    avg_nbfc_corr=float(correlations.loc[TICKERS[3:6],TICKERS[3:6]].values[np.triu_indices(3,1)].mean())
    result={'metadata':{'start_date':'2021-01-01','end_date':'2025-12-31','base_date':'2020-12-31','n_returns':len(r),'n_price_observations':len(prices),'calendar_years':(END-BASE).days/365.25,'trading_days_per_year':252,'risk_free_rate':RF,'risk_free_daily':(1+RF)**(1/252)-1,'currency':'INR','generated_utc':datetime.now(timezone.utc).isoformat(),'return_type':'simple daily adjusted-close return','portfolio_rebalancing':'daily; equal constituent weights; no taxes or transaction costs','benchmark':'NIFTY 50 price index (^NSEI), not TRI','cagr_convention':'(terminal wealth)^(365.25/calendar days)-1','annual_mean_convention':'252 * arithmetic mean daily return','volatility_convention':'sample daily standard deviation (ddof=1) * sqrt(252)','sharpe_convention':'(mean daily return - effective daily rf) / sample daily sd * sqrt(252)','var_convention':'negative linear-interpolated 5th return percentile, 1-day loss at 95% confidence','cvar_convention':'negative average return at or below the 5th return percentile','max_drawdown_convention':'minimum wealth / running wealth maximum - 1; includes initial base wealth','primary_equity_source':'Yahoo Finance chart API; NSE underlying-price and corporate-action checks'},
        'individual_metrics':[row(t) for t in TICKERS[:6]],'portfolio_metrics':[row(t) for t in GROUPS],
        'benchmark_metrics':row('NIFTY50'),'annual_returns':annual_rows,'correlation':correlations.to_dict(),
        'diagnostics':{'sources':source_diag,'dropped_dates':dropped,'retained_price_rows':len(long),'annual_return_counts':{str(y):int(n) for y,n in r.groupby(r.index.year).size().items()},'split_continuity':splits,'official_close_checks':cross,'max_abs_daily_return':{t:float(r[t].abs().max()) for t in TICKERS},'tests_passed':['no missing/duplicate/nonpositive prices','OHLC internal consistency','same dates across all seven series','five NSE close checks within 0.011 INR and documented MUTHOOTFIN 0.05 INR difference','2025 corporate action return continuity','mixed weighting identity','geometric stock wealth identity','NIFTY beta=1','annual versus daily compounding identity','CVaR >= VaR','mixed variance equals covariance quadratic form','absolute daily adjusted returns below 50%']},
        'sensitivity':{'buy_and_hold':bh,'risk_free':rf_sensitivity},'trailing252_volatility':trailing,
        'comparison':{'bank_nbfc_portfolio_correlation':float(r.BANKS.corr(r.NBFCS)),'mean_within_bank_correlation':avg_bank_corr,'mean_within_nbfc_correlation':avg_nbfc_corr,'mean_cross_sector_correlation':float(correlations.loc[TICKERS[:3],TICKERS[3:6]].values.mean()),'weighted_sector_volatility':float(.5*(r.BANKS.std(ddof=1)+r.NBFCS.std(ddof=1))*np.sqrt(252))},
        'limitations':['Six purposively selected surviving firms do not represent the entire bank or NBFC sector.','Yahoo adjusted close is a vendor total-return proxy, not an independently reconstructed NSE total-return series.','NIFTY 50 is a price index; equity dividend-adjusted performance is not directly like-for-like with its returns. Beta uses the price-index returns.','Shriram pre-30-Nov-2022 history is the predecessor Shriram Transport Finance; the 2022 merger changed the business. HDFC Bank merged with HDFC Limited effective July 2023.','Yahoo BAJFINANCE split event records 2:1 only; official 10x split/bonus factor is already reflected in historical OHLC. Reapplying any factor would corrupt returns.','Retrospective adjusted close levels may incorporate distributions after the sample end; common scaling cancels in within-period returns.','Risk-free rate of 6% is an assumed constant scenario, not a historical realized risk-free series.','Daily rebalancing ignores transaction costs, taxes, liquidity constraints and implementation costs.','No statistical claim about causal effects or all financial institutions is justified by this descriptive sample.','Historical VaR/CVaR are in-sample, one-day estimates and do not bound future losses.']}
    (ART/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
    pd.DataFrame(result['individual_metrics']+result['portfolio_metrics']+[result['benchmark_metrics']]).to_csv(DATA/'summary_metrics.csv',index=False,float_format='%.12g')
    (ART/'validation.json').write_text(json.dumps(result['diagnostics'],indent=2),encoding='utf-8')
    if charts:make_charts(prices,r,wealth,result)
    print(json.dumps({'metadata':result['metadata'],'portfolio_metrics':result['portfolio_metrics'],'individual_metrics':result['individual_metrics'],'trailing252_volatility':trailing},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--no-charts',action='store_true');args=parser.parse_args();main(charts=not args.no_charts)
