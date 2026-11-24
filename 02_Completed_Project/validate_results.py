"""Validate offline results against independent calculations and original inputs."""
import hashlib
import json
from math import exp, log, sqrt
from pathlib import Path
from statistics import NormalDist
from zipfile import ZipFile

from docx import Document
import numpy as np
from openpyxl import load_workbook
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parent
ASSETS = ['HDFCBANK', 'ICICIBANK', 'SBIN', 'BAJFINANCE', 'SHRIRAMFIN', 'MUTHOOTFIN', 'NIFTY50']
SERIES = ASSETS + ['BANKS', 'NBFCS', 'MIXED']
RTOL = 2e-9
ATOL = 2e-10


def load(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def same(actual, expected):
    np.testing.assert_allclose(actual, expected, rtol=RTOL, atol=ATOL)


def compare_json(actual, expected, path=''):
    if isinstance(expected, dict):
        assert set(actual) == set(expected), path
        for key in expected:
            compare_json(actual[key], expected[key], f'{path}/{key}')
    elif isinstance(expected, list):
        assert len(actual) == len(expected), path
        for i, pair in enumerate(zip(actual, expected)):
            compare_json(*pair, f'{path}/{i}')
    elif isinstance(expected, float):
        assert np.isclose(actual, expected, rtol=RTOL, atol=ATOL), (path, actual, expected)
    else:
        assert actual == expected, (path, actual, expected)


def check_sources():
    manifest = load('data/source_manifest.json')
    prices = []
    for key, source in zip(ASSETS, manifest['sources'], strict=True):
        path = ROOT / source['raw_file']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == source['sha256'], path
        item = load(source['raw_file'])['chart']['result'][0]
        dt = pd.to_datetime(item['timestamp'], unit='s', utc=True).tz_convert('Asia/Kolkata').tz_localize(None).normalize()
        values = pd.Series(item['indicators']['adjclose'][0]['adjclose'], index=dt, name=key)
        assert len(values) == source['observations'] and values.index.is_unique
        prices.append(values.loc['2020-12-31':'2025-12-31'])
    prices = pd.concat(prices, axis=1).sort_index()
    assert len(prices) == 1237 and not prices.isna().any().any() and (prices > 0).all().all()
    assert prices.index[[0, 1, -1]].strftime('%Y-%m-%d').tolist() == ['2020-12-31', '2021-01-01', '2025-12-31']
    for i in range(4):
        name = f'data/options_raw/fo_20251231_{i}'
        provenance = load(name + '_provenance.json')
        if provenance['status'] == 200:
            assert hashlib.sha256((ROOT / (name + '.zip')).read_bytes()).hexdigest() == provenance['sha256']
    archive = ROOT / 'data/options_raw/fo_20251231_0.zip'
    with ZipFile(archive) as file:
        assert file.testzip() is None
        nse = pd.read_csv(file.open(file.namelist()[0]))
    print('PASS: raw source hashes, aligned dates and archived NSE data')
    return prices, nse


def check_equity(prices, equity, nse):
    x = prices.to_numpy()
    stock = x[1:] / x[:-1] - 1
    banks = stock[:, :3] @ np.full(3, 1/3)
    nbfcs = stock[:, 3:6] @ np.full(3, 1/3)
    returns = np.column_stack([stock, banks, nbfcs, .5 * (banks + nbfcs)])
    wealth = np.vstack([np.ones(10), np.cumprod(1 + returns, axis=0)])
    drawdown = wealth / np.maximum.accumulate(wealth, axis=0) - 1
    annual = np.array([np.prod(1 + returns[prices.index[1:].year == y], axis=0) - 1 for y in range(2021, 2026)])
    corr = np.corrcoef(returns[:, :6], rowvar=False)
    for name, values, columns, dates in [
        ('adjusted_prices', x, ASSETS, prices.index),
        ('returns', returns, SERIES, prices.index[1:]),
        ('wealth', wealth, SERIES, prices.index),
        ('drawdowns', drawdown, SERIES, prices.index),
    ]:
        csv = pd.read_csv(ROOT / f'data/{name}.csv', parse_dates=['date']).set_index('date')
        assert csv.columns.tolist() == columns and csv.index.equals(dates), name
        same(csv, values)
    same(pd.read_csv(ROOT / 'data/annual_returns.csv')[SERIES], annual)
    same(pd.read_csv(ROOT / 'data/correlations.csv', index_col=0).loc[ASSETS[:6], ASSETS[:6]], corr)
    actual_spots = nse[nse.TckrSymb.isin(ASSETS[:6])].groupby('TckrSymb').UndrlygPric
    assert actual_spots.nunique().eq(1).all()
    for row in equity['diagnostics']['official_close_checks']:
        same(row['nse_fo_underlying_price'], actual_spots.first()[row['ticker']])
    rows = equity['individual_metrics'] + [equity['benchmark_metrics']] + equity['portfolio_metrics']
    assert [row['ticker'] for row in rows] == SERIES
    metrics = ['n', 'total_return', 'cagr', 'annual_mean', 'annual_volatility', 'sharpe', 'beta',
               'max_drawdown', 'var95', 'cvar95']
    for j, row in enumerate(rows):
        r = returns[:, j]
        daily_vol = np.std(r, ddof=1)
        daily_mean = np.mean(r)
        q = np.quantile(r, .05)
        beta = np.cov(r, returns[:, 6], ddof=1)[0, 1] / np.var(returns[:, 6], ddof=1)
        checks = [len(r), wealth[-1, j]-1, wealth[-1, j]**(365.25/(prices.index[-1]-prices.index[0]).days)-1,
                  daily_mean*252, daily_vol*sqrt(252), (daily_mean-(1.06**(1/252)-1))*sqrt(252)/daily_vol,
                  beta, drawdown[:, j].min(), -q, -np.mean(r[r <= q])]
        same([row[k] for k in metrics], checks)
    sigma_b, sigma_n, sigma_m = np.std(returns[:, 7:], axis=0, ddof=1)*sqrt(252)
    rho = np.corrcoef(banks, nbfcs)[0, 1]
    same(sigma_m**2, .25*(sigma_b**2 + sigma_n**2 + 2*rho*sigma_b*sigma_n))
    reduction = .5*(sigma_b + sigma_n) - sigma_m
    same(pd.read_csv(ROOT / 'data/portfolio_comparison.csv')['volatility_reduction'], [reduction])
    print('PASS: raw adjusted-price returns, equity metrics, annual returns, drawdown and portfolio diversification')
    return rows, metrics, returns, wealth, drawdown, annual, corr, reduction


def check_options(prices, nse, result):
    normal = NormalDist()
    cases = result['observations']
    assert len(cases) == 4
    for case in cases:
        market = nse.loc[nse.FinInstrmId.eq(case['instrument_id'])]
        assert len(market) == 1
        market = market.iloc[0]
        symbol = case['symbol']
        typ = case['option_type']
        assert market.TckrSymb == symbol and market.OptnTp == typ
        assert market.TradDt == case['date'] == '2025-12-31'
        assert market.FininstrmActlXpryDt == case['expiry'] == '2026-01-27'
        same([case['spot'], case['strike'], case['market_price'], case['lot_size'], case['volume_contracts'],
              case['open_interest_units']], [market.UndrlygPric, market.StrkPric, market.ClsPric,
                                             market.NewBrdLotQty, market.TtlTradgVol, market.OpnIntrst])
        eligible = nse.loc[(nse.TckrSymb == symbol) & (nse.FinInstrmTp == 'STO') &
                           (nse.XpryDt == case['expiry']) & (nse.TtlTradgVol > 0) &
                           (nse.OpnIntrst > 0) & (nse.ClsPric > 0)].groupby('StrkPric').OptnTp.nunique()
        assert case['strike'] == min(eligible[eligible == 2].index, key=lambda k: (abs(k-case['spot']), k))
        s, k, t = case['spot'], case['strike'], case['time_years']
        history = prices.loc[:case['date'], symbol].iloc[-253:].to_numpy()
        sigma = np.std(history[1:]/history[:-1]-1, ddof=1)*sqrt(252)
        rate = log(1.06)
        assert case['dividend_yield_continuous'] == 0
        same([t, case['sigma_historical'], case['risk_free_continuous']], [27/365, sigma, rate])

        def price(vol):
            d1 = (log(s/k) + (rate + vol**2/2)*t)/(vol*sqrt(t))
            d2 = d1 - vol*sqrt(t)
            call = s*normal.cdf(d1) - k*exp(-rate*t)*normal.cdf(d2)
            return (call if typ == 'CE' else call - s + k*exp(-rate*t),
                    normal.cdf(d1) - (typ == 'PE'), normal.pdf(d1)/(s*vol*sqrt(t)),
                    s*normal.pdf(d1)*sqrt(t)/100)

        same([case['bs_price'], case['delta'], case['gamma'], case['vega_per_1pp']], price(sigma))
        same(case['market_price'], price(case['derived_iv'])[0])
        same(case['market_minus_model'], case['market_price']-case['bs_price'])
    print('PASS: NSE contract selection, spot and premiums, pre-expiry volatility, pricing, implied volatility and Greeks')


def check_workbook(equity, cases):
    rows, metrics, returns, wealth, drawdown, annual, correlation, reduction = equity
    path = ROOT / 'output/Finance_Analysis.xlsx'
    values = load_workbook(path, data_only=True)
    formulas = load_workbook(path)
    assert values.sheetnames == ['Summary', 'Assumptions', 'Daily returns', 'Wealth', 'Options', 'Prices', 'Option inputs']
    assert len(formulas['Summary']._charts) == 2
    assert not any(c.data_type == 'e' for sheet in values for row in sheet for c in row)
    summary = values['Summary']
    same([[c.value for c in row] for row in summary['D7:M16']], [[r[k] for k in metrics] for r in rows])
    same([[c.value for c in row] for row in summary['D22:M26']], annual)
    same([[c.value for c in row] for row in summary['D31:I36']], correlation)
    same(summary['K41'].value, reduction)
    same([[c.value for c in row] for row in values['Assumptions']['D19:I21']],
         [[1/3]*3+[0]*3, [0]*3+[1/3]*3, [1/6]*6])
    same([[c.value for c in row] for row in values['Daily returns']['B7:K1242']], returns)
    same([[c.value for c in row] for row in values['Wealth']['B6:K1242']], 100*wealth)
    same([[c.value for c in row] for row in values['Wealth']['M6:V1242']], drawdown)
    for i, case in enumerate(cases, start=4):
        op = values['Options']
        wanted = {6: case['spot'], 7: case['strike'], 8: case['time_years'], 9: case['sigma_historical'],
                  12: case['market_price'], 18: case['bs_price'], 19: -case['market_minus_model'],
                  21: case['delta'], 22: case['gamma'], 23: case['vega_per_1pp'],
                  24: case['derived_iv'], 25: case['market_price'], 26: 0}
        same([op.cell(r, i).value for r in wanted], list(wanted.values()))
        same(values['Option inputs'].cell(i+2, 9).value, case['open_interest_contracts'])
        assert formulas['Options'].cell(18, i).data_type == 'f'
    for sheet, cell in [('Summary', 'H14'), ('Daily returns', 'I7'), ('Wealth', 'B7')]:
        assert formulas[sheet][cell].data_type == 'f'
    print('PASS: 7 workbook sheets, 2 charts, no cached formula errors and full-series agreement with independent Python')


def check_deliverables(equity, options):
    charts = ('portfolio_wealth', 'individual_wealth', 'risk_return', 'correlation_heatmap', 'annual_returns',
              'drawdown', 'options_price_comparison', 'options_volatility_comparison', 'equity_annual_mean',
              'equity_annual_volatility', 'equity_sharpe', 'options_greeks')
    for name in charts:
        with Image.open(ROOT / f'charts/{name}.png') as image:
            assert image.width >= 1200 and image.height >= 650, name
            image.verify()
    doc = Document(ROOT / 'output/Final_Research_Report.docx')
    assert len(doc.tables) == 11 and len(doc.inline_shapes) >= 14
    text = ' '.join(p.text for table in doc.tables for row in table.rows for cell in row.cells for p in cell.paragraphs)
    for item in equity['individual_metrics'] + equity['portfolio_metrics']:
        assert f'{item["cagr"]:.2%}' in text
    for option in options['observations']:
        assert f'{option["bs_price"]:.2f}' in text
    with (ROOT / 'output/Final_Research_Report.pdf').open('rb') as file:
        assert file.read(5) == b'%PDF-'
    print('PASS: 12 final charts, verified report values and both report formats')


def main():
    prices, nse = check_sources()
    equity = load('artifacts/results.json')
    options = load('artifacts/options_results.json')
    baseline = load('validation/reference_results.json')
    equity['metadata'].pop('generated_utc')
    compare_json(equity, baseline['equity'])
    compare_json(options, baseline['options'])
    print('PASS: agreement with delivered numerical baseline')
    values = check_equity(prices, equity, nse)
    check_options(prices, nse, options)
    check_workbook(values, options['observations'])
    check_deliverables(equity, options)


if __name__ == '__main__':
    try:
        main()
    except (AssertionError, ValueError, OSError, KeyError) as error:
        print(f'FAIL: {type(error).__name__}: {error}', flush=True)
        raise
