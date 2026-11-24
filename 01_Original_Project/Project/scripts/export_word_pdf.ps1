param([Parameter(Mandatory=$true)][string]$InputDocx,[Parameter(Mandatory=$true)][string]$OutputPdf)
$ErrorActionPreference = 'Stop'
$inputFull = (Resolve-Path -LiteralPath $InputDocx).Path
$outputFull = [IO.Path]::GetFullPath($OutputPdf)
$workspaceFull = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')) + [IO.Path]::DirectorySeparatorChar
if (-not $inputFull.StartsWith($workspaceFull,[StringComparison]::OrdinalIgnoreCase) -or -not $outputFull.StartsWith($workspaceFull,[StringComparison]::OrdinalIgnoreCase)) { throw 'Report paths must stay inside the project.' }
$word = $null
$document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open($inputFull,$false,$false,$false)
    $document.Fields.Update() | Out-Null
    foreach ($toc in $document.TablesOfContents) { $toc.Update() }
    $document.Save()
    $document.ExportAsFixedFormat($outputFull,17)
    Write-Output "Exported $outputFull"
}
finally {
    if ($null -ne $document) { $document.Close(0); [Runtime.InteropServices.Marshal]::FinalReleaseComObject($document) | Out-Null }
    if ($null -ne $word) { $word.Quit(); [Runtime.InteropServices.Marshal]::FinalReleaseComObject($word) | Out-Null }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
