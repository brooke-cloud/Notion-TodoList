$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$DistRoot = Join-Path $ProjectRoot "dist"
$ReleaseDir = Join-Path $DistRoot "Notion TodoList V4"
$StagingRoot = Join-Path $ProjectRoot "build\release-staging"
$StagingDist = Join-Path $StagingRoot "dist"
$StagingWork = Join-Path $StagingRoot "work"
$BuiltDir = Join-Path $StagingDist "Notion TodoList V4"
$PrivateEnvBackup = Join-Path $StagingRoot "private.env"
$ExistingEnv = Join-Path $ReleaseDir ".env"

if (Test-Path -LiteralPath $StagingRoot) {
    Remove-Item -LiteralPath $StagingRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $StagingRoot -Force | Out-Null

# Preserve an existing local runtime configuration without feeding it to
# PyInstaller or including it in the staged release validation.
if (Test-Path -LiteralPath $ExistingEnv) {
    Copy-Item -LiteralPath $ExistingEnv -Destination $PrivateEnvBackup -Force
}

$PythonExe = (Get-Command python -ErrorAction Stop).Source
$PythonDir = Split-Path -Parent $PythonExe
$OriginalPath = $env:PATH
$env:PATH = @(
    $PythonDir,
    (Join-Path $PythonDir "Scripts"),
    (Join-Path $env:SystemRoot "System32"),
    $env:SystemRoot
) -join ";"
try {
    & $PythonExe -m PyInstaller --noconfirm --clean `
        --distpath $StagingDist `
        --workpath $StagingWork `
        NotionTodoListV4.spec
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE. Existing release was not replaced."
    }
}
finally {
    $env:PATH = $OriginalPath
}

if (-not (Test-Path -LiteralPath $BuiltDir)) {
    throw "PyInstaller did not create the expected onedir release: $BuiltDir"
}

$SettingsPath = Join-Path $ProjectRoot "settings.json"
if (Test-Path -LiteralPath $SettingsPath) {
    Copy-Item -LiteralPath $SettingsPath -Destination $BuiltDir -Force
}

$RequiredFiles = @(
    "Notion TodoList.exe",
    "_internal\python313.dll",
    "_internal\certifi\cacert.pem",
    "_internal\qml\Main.qml",
    "_internal\design\bg.jpg",
    "_internal\assets\ui\app.ico"
)
foreach ($RelativePath in $RequiredFiles) {
    $RequiredPath = Join-Path $BuiltDir $RelativePath
    if (-not (Test-Path -LiteralPath $RequiredPath -PathType Leaf)) {
        throw "Incomplete V4 release; required file is missing: $RelativePath"
    }
    if ((Get-Item -LiteralPath $RequiredPath).Length -le 0) {
        throw "Incomplete V4 release; required file is empty: $RelativePath"
    }
}

$UnexpectedFiles = @(
    "_internal\icuuc.dll",
    "_internal\icudt78.dll"
)
foreach ($RelativePath in $UnexpectedFiles) {
    if (Test-Path -LiteralPath (Join-Path $BuiltDir $RelativePath)) {
        throw "Contaminated V4 release; foreign build-environment file was collected: $RelativePath"
    }
}

$Forbidden = Get-ChildItem -LiteralPath $BuiltDir -Recurse -Force -File | Where-Object {
    $_.Name -eq ".env" -or $_.Name -match "(?i)^(notion_token|api[_-]?key|secret)(\..+)?$"
}
if ($Forbidden) {
    throw "Sensitive-looking files found in staged V4 release directory."
}

if (-not (Test-Path -LiteralPath $DistRoot)) {
    New-Item -ItemType Directory -Path $DistRoot -Force | Out-Null
}
if (Test-Path -LiteralPath $ReleaseDir) {
    Remove-Item -LiteralPath $ReleaseDir -Recurse -Force
}
Move-Item -LiteralPath $BuiltDir -Destination $ReleaseDir

if (Test-Path -LiteralPath $PrivateEnvBackup) {
    Copy-Item -LiteralPath $PrivateEnvBackup -Destination (Join-Path $ReleaseDir ".env") -Force
    Remove-Item -LiteralPath $PrivateEnvBackup -Force
    Write-Host "Preserved existing local .env next to the rebuilt EXE; it was not bundled by PyInstaller."
}

Write-Host "V4 Release Candidate created at: $ReleaseDir"
