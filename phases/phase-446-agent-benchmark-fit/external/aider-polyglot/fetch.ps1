$ErrorActionPreference = 'Stop'

$revision = '7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f'
$repositoryUrl = 'https://github.com/Aider-AI/polyglot-benchmark.git'
$upstream = Join-Path $PSScriptRoot 'upstream'

if (-not (Test-Path -LiteralPath (Join-Path $upstream '.git'))) {
    if (Test-Path -LiteralPath $upstream) {
        $existing = Get-ChildItem -LiteralPath $upstream -Force
        if ($existing.Count -gt 0) { throw "Refusing to initialize non-empty path: $upstream" }
    } else {
        New-Item -ItemType Directory -Path $upstream | Out-Null
    }
    & git -C $upstream init --quiet
    if ($LASTEXITCODE -ne 0) { throw 'git init failed' }
    & git -C $upstream remote add origin $repositoryUrl
    if ($LASTEXITCODE -ne 0) { throw 'git remote add failed' }
}

& git -C $upstream fetch --filter=blob:none origin $revision
if ($LASTEXITCODE -ne 0) { throw 'Fetching pinned Aider Polyglot revision failed' }
& git -C $upstream checkout --quiet --detach $revision
if ($LASTEXITCODE -ne 0) { throw 'Checking out pinned Aider Polyglot revision failed' }

$actual = (& git -C $upstream rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $actual -ne $revision) {
    throw "Aider Polyglot revision mismatch. Expected $revision, got $actual"
}

$count = 0
foreach ($language in @('cpp', 'go', 'java', 'javascript', 'python', 'rust')) {
    $practice = Join-Path $upstream "$language/exercises/practice"
    if (-not (Test-Path -LiteralPath $practice)) { throw "Missing benchmark language tree: $language" }
    $count += @(Get-ChildItem -LiteralPath $practice -Directory).Count
}
if ($count -ne 225) { throw "Expected 225 exercises, found $count" }
[pscustomobject]@{ repository = 'Aider-AI/polyglot-benchmark'; revision = $actual; exercises = $count; source = 'upstream/' } | ConvertTo-Json -Compress
