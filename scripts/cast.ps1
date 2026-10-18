# Windows entry point: bootstraps a private Python without touching system PATH.
$ErrorActionPreference = 'Stop'
$pluginRoot = Split-Path -Parent $PSScriptRoot
$dataRoot = $env:CODOOP_CAST_HOME
for ($castArgIndex = 0; $castArgIndex -lt $args.Count; $castArgIndex++) {
    if ($args[$castArgIndex] -eq '--root') {
        if ($castArgIndex + 1 -ge $args.Count) { throw '--root requires a directory.' }
        $dataRoot = $args[$castArgIndex + 1]
        break
    }
    if ($args[$castArgIndex] -like '--root=*') {
        $dataRoot = $args[$castArgIndex].Substring(7)
        break
    }
    if (-not $args[$castArgIndex].StartsWith('-')) { break }
}
if (-not $dataRoot) { $dataRoot = Join-Path $env:LOCALAPPDATA 'codoop-cast' }
$dataRoot = [IO.Path]::GetFullPath($dataRoot)
$env:CODOOP_CAST_HOME = $dataRoot
$tools = Join-Path $dataRoot 'tools'
New-Item -ItemType Directory -Force -Path $tools | Out-Null
$uv = Join-Path $tools 'uv.exe'
if (-not (Test-Path -LiteralPath $uv)) {
    $manifest = Get-Content -LiteralPath (Join-Path $pluginRoot 'runtime/codoop-cast/resources-voice.json') -Raw | ConvertFrom-Json
    $archive = Join-Path $tools ('uv-' + [guid]::NewGuid().ToString('N') + '.zip')
    [Console]::Error.WriteLine('Preparing private codoop-cast launcher...')
    Invoke-WebRequest -Uri $manifest.uv.url -OutFile $archive -UseBasicParsing
    $hash = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($hash -ne $manifest.uv.sha256) { throw 'Launcher checksum mismatch.' }
    Expand-Archive -LiteralPath $archive -DestinationPath $tools -Force
    Remove-Item -LiteralPath $archive
}
$env:UV_PYTHON_INSTALL_DIR = Join-Path $dataRoot 'python'
$env:UV_CACHE_DIR = Join-Path $dataRoot 'cache/uv'
$env:PYTHONUTF8 = '1'
& $uv run --no-project --python 3.10 (Join-Path $pluginRoot 'runtime/codoop-cast/cast.py') @args
exit $LASTEXITCODE
