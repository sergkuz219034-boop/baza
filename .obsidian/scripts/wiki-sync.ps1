[CmdletBinding()]
param(
    [switch]$AllowDirty,
    [switch]$Strict
)

$ErrorActionPreference = 'Stop'
$vault = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $vault

function Fail([string]$Message) {
    Write-Error "[wiki-sync] $Message"
    exit 1
}

git fetch origin --prune
if ($LASTEXITCODE -ne 0) { Fail 'git fetch failed' }

$status = @(git status --porcelain)
if ($status.Count -gt 0 -and -not $AllowDirty) {
    Fail "vault has $($status.Count) uncommitted changes; review before sync"
}

$counts = (git rev-list --left-right --count HEAD...origin/main).Trim().Split("`t")
$ahead = [int]$counts[0]
$behind = [int]$counts[1]
Write-Output "[wiki-sync] ahead=$ahead behind=$behind dirty=$($status.Count)"
if ($ahead -gt 0 -or $behind -gt 0) {
    Fail 'vault is not synchronized with origin/main'
}

$missing = New-Object System.Collections.Generic.List[string]
Get-ChildItem -Recurse -File -Filter '*.md' | ForEach-Object {
    $source = $_.FullName
    foreach ($match in [regex]::Matches((Get-Content -Raw -LiteralPath $source), '\[\[([^\]|#]+)')) {
        $target = $match.Groups[1].Value.Trim().Replace('/', [IO.Path]::DirectorySeparatorChar)
        $candidates = @(
            (Join-Path $vault $target),
            (Join-Path $vault "$target.md"),
            (Join-Path $vault "$target\README.md")
        )
        if (-not ($candidates | Where-Object { Test-Path -LiteralPath $_ })) {
            $missing.Add("$($_.FullName.Substring($vault.Length + 1)): $target")
        }
    }
}
if ($missing.Count -gt 0) {
    $missing | Select-Object -First 30 | ForEach-Object { Write-Warning "[wiki-sync] broken link: $_" }
    if ($Strict) { Fail "found $($missing.Count) broken wiki links" }
    Write-Warning "[wiki-sync] found $($missing.Count) broken wiki links; run with -Strict to fail"
}

$secretPattern = '(?im)^\s*(?:[A-Z][A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|API_KEY)|(?:token|secret|password|api[_-]?key))\s*[:=]\s*[^\s]{8,}'
$secretHits = @(Get-ChildItem -Recurse -File -Include '*.md','*.json','*.yml','*.yaml' |
    Select-String -Pattern $secretPattern)
if ($secretHits.Count -gt 0) {
    $secretHits | Select-Object -First 30 | ForEach-Object { Write-Error "[wiki-sync] possible secret: $($_.Path):$($_.LineNumber)" }
    Fail "found $($secretHits.Count) possible secrets"
}

if ($missing.Count -gt 0) {
    Write-Output '[wiki-sync] RESULT=warnings'
} else {
    Write-Output '[wiki-sync] RESULT=clean'
}
