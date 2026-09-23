$ErrorActionPreference = 'Stop'

$revision = 'f7cf7359b7ac615a0b294831c5ba2bc95ee4a000'
$upstream = Join-Path $PSScriptRoot 'upstream'
$gitDir = Join-Path $upstream '.git'

New-Item -ItemType Directory -Force -Path $upstream | Out-Null
if (-not (Test-Path -LiteralPath $gitDir)) {
    & git -C $upstream init --quiet
    if ($LASTEXITCODE -ne 0) { throw 'git init failed' }
    & git -C $upstream remote add origin 'https://github.com/ShishirPatil/gorilla.git'
    if ($LASTEXITCODE -ne 0) { throw 'git remote add failed' }
    & git -C $upstream config core.sparseCheckout true
    if ($LASTEXITCODE -ne 0) { throw 'git sparse-checkout configuration failed' }
    Set-Content -LiteralPath (Join-Path $gitDir 'info/sparse-checkout') -Value '/berkeley-function-call-leaderboard/' -Encoding ascii
}

& git -C $upstream fetch --filter=blob:none origin $revision
if ($LASTEXITCODE -ne 0) { throw 'Fetching pinned BFCL revision failed' }
& git -C $upstream checkout --quiet --detach $revision
if ($LASTEXITCODE -ne 0) { throw 'Checking out pinned BFCL revision failed' }

$actual = (& git -C $upstream rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $actual -ne $revision) {
    throw "BFCL revision mismatch. Expected $revision, got $actual"
}

$package = Join-Path $upstream 'berkeley-function-call-leaderboard'
if (-not (Test-Path -LiteralPath $package)) { throw 'Expected BFCL source tree is missing' }
[pscustomobject]@{ repository = 'ShishirPatil/gorilla'; revision = $actual; source = 'upstream/berkeley-function-call-leaderboard' } | ConvertTo-Json -Compress
