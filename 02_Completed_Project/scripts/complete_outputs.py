"""Prepare the original workbook inputs and supplementary results from analysis outputs."""
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

ROOT = Path(__file__).resolve().parents[1]


def main():
    artifacts = ROOT / 'artifacts'
    equity = json.loads((artifacts / 'results.json').read_text(encoding='utf-8'))
    options = json.loads((artifacts / 'options_results.json').read_text(encoding='utf-8'))
    with (ROOT / 'data/adjusted_prices.csv').open(newline='', encoding='utf-8') as file:
        prices = list(csv.DictReader(file))
    (artifacts / 'workbook_equity_inputs.json').write_text(
        json.dumps({'prices': prices, 'results': equity}, indent=2), encoding='utf-8')
    mixed = equity['portfolio_metrics'][2]['annual_volatility']
    weighted = equity['comparison']['weighted_sector_volatility']
    comparison = {**equity['comparison'], 'mixed_volatility': mixed,
                  'volatility_reduction': weighted - mixed,
                  'volatility_reduction_percentage_points': 100 * (weighted - mixed),
                  'volatility_reduction_relative': (weighted - mixed) / weighted}
    for name, rows in [('portfolio_metrics', equity['portfolio_metrics']),
                       ('portfolio_comparison', [comparison])]:
        with (ROOT / f'data/{name}.csv').open('w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    equities = equity['individual_metrics']
    colors = ['#245782'] * 3 + ['#008b84'] * 3
    for field, title, label in [
        ('annual_mean', 'Annualized arithmetic mean returns', 'Arithmetic mean × 252'),
        ('annual_volatility', 'Annualized daily-return volatility', 'Daily sample SD × √252'),
        ('sharpe', 'Realized Sharpe ratio', 'Annualized Sharpe ratio')
    ]:
        fig, ax = plt.subplots(figsize=(9.2, 4.5), layout='constrained')
        ax.barh([item['name'] for item in equities], [item[field] for item in equities], color=colors)
        ax.invert_yaxis()
        ax.set(title=f'{title} | 2021–2025', xlabel=label)
        if field != 'sharpe':
            ax.xaxis.set_major_formatter(PercentFormatter(1))
        fig.savefig(ROOT / f'charts/equity_{field}.png', dpi=220, bbox_inches='tight')
        plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(11, 4.0), layout='constrained')
    observations = options['observations']
    labels = [x['symbol'] + '\n' + x['option_type'] for x in observations]
    for ax, (field, title, unit) in zip(axes, [
        ('delta', 'Delta', 'INR premium per INR spot move'),
        ('gamma', 'Gamma', 'Delta per INR spot move'),
        ('vega_per_1pp', 'Vega', 'INR per 1 volatility point')
    ]):
        ax.bar(labels, [x[field] for x in observations], color=['#245782'] * 2 + ['#008b84'] * 2)
        ax.axhline(0, color='#596574', linewidth=.8)
        ax.set(title=title, ylabel=unit)
        ax.tick_params(axis='x', labelsize=8)
    fig.savefig(ROOT / 'charts/options_greeks.png', dpi=220, bbox_inches='tight')
    plt.close(fig)
    print('Generated workbook inputs, portfolio comparisons and four supplementary charts.')


if __name__ == '__main__':
    main()
