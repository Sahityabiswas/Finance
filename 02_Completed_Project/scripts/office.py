"""Headless LibreOffice conversion with an isolated profile."""
import os
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory


def executable():
    configured = os.environ.get('FINANCE_SOFFICE')
    if configured:
        return configured
    installed = shutil.which('soffice') or shutil.which('libreoffice')
    if installed:
        return installed
    for var in ('ProgramFiles', 'ProgramFiles(x86)'):
        if os.environ.get(var):
            candidate = Path(os.environ[var]) / 'LibreOffice/program/soffice.exe'
            if candidate.is_file():
                return str(candidate)
    raise FileNotFoundError('Install LibreOffice or set FINANCE_SOFFICE to the executable path.')


def convert(source, destination, target):
    source = Path(source).resolve()
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix='finance-office-') as work:
        command = [executable(), f'-env:UserInstallation={Path(work).as_uri()}',
                   '--headless', '--convert-to', target, '--outdir', str(destination), str(source)]
        subprocess.run(command, check=True, timeout=150)
    file = destination / f'{source.stem}.{target.split(":")[0]}'
    if not file.is_file() or not file.stat().st_size:
        raise RuntimeError(f'LibreOffice did not create {file}')
    return file
