"""Run the frozen historical study and build all publication outputs offline."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from scripts.office import convert, executable

ROOT = Path(__file__).resolve().parent


def run(script, env):
    command = [sys.executable, '-X', 'utf8', script]
    print(f'RUN: python -X utf8 {script}', flush=True)
    completed = subprocess.run(command, cwd=ROOT, env=env, check=False)
    print(f'EXIT {completed.returncode}: {script}', flush=True)
    completed.check_returncode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analysis-only', action='store_true', help='Generate CSVs, JSON and charts without LibreOffice.')
    args = parser.parse_args()
    print(f'Python {sys.version}', flush=True)
    with TemporaryDirectory(prefix='finance-plot-cache-') as cache:
        env = {**os.environ, 'MPLCONFIGDIR': cache, 'PYTHONDONTWRITEBYTECODE': '1'}
        for script in ('scripts/analyze.py', 'scripts/options_analyze.py', 'scripts/complete_outputs.py'):
            run(script, env)
        if args.analysis_only:
            print('Analysis and charts completed.')
            return
        subprocess.run([executable(), '--version'], check=True, timeout=30)
        run('scripts/build_workbook_portable.py', env)
        run('scripts/build_report.py', env)
        with TemporaryDirectory(prefix='finance-report-') as work:
            pdf = convert(ROOT / 'output/Final_Research_Report.docx', work, 'pdf:writer_pdf_Export')
            shutil.copyfile(pdf, ROOT / 'output' / pdf.name)
        run('validate_results.py', env)
    print(f'PASS: offline project rebuilt and validated in {ROOT / "output"}')


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        sys.exit(f'FAIL: {exc}')
