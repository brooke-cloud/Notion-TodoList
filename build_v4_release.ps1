$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

python -m PyInstaller --noconfirm --clean NotionTodoListV4.spec

$ReleaseDir = Join-Path $ProjectRoot "dist\Notion TodoList V4"
Copy-Item -LiteralPath (Join-Path $ProjectRoot "settings.json") -Destination $ReleaseDir -Force

$Forbidden = Get-ChildItem -LiteralPath $ReleaseDir -Recurse -Force -File | Where-Object {
    $_.Name -eq ".env" -or $_.Name -match "(?i)^(notion_token|api[_-]?key|secret)(\..+)?$"
}
if ($Forbidden) {
    throw "Sensitive-looking files found in V4 release directory."
}

Write-Host "V4 Release Candidate created at: $ReleaseDir"
