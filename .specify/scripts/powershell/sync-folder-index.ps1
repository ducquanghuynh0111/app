param(
    [string[]]$MarkRead = @()
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$memoryDir = Join-Path $projectRoot '.specify/memory'
$jsonPath = Join-Path $memoryDir 'folder-index.json'
$mdPath = Join-Path $memoryDir 'folder-index.md'

function RelativePath([string]$absolutePath) {
    $prefix = $projectRoot.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
    if (-not $absolutePath.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'Folder is outside the Spec Kit workspace.'
    }
    return $absolutePath.Substring($prefix.Length).Replace('\', '/')
}

$roots = @(
    (Join-Path $projectRoot '.specify'),
    (Join-Path $projectRoot 'specs')
)
$skillRoot = Join-Path $projectRoot '.agents/skills'
if (Test-Path -LiteralPath $skillRoot -PathType Container) {
    $roots += @(Get-ChildItem -LiteralPath $skillRoot -Directory -Filter 'speckit-*' | ForEach-Object FullName)
}

$folders = @()
foreach ($root in $roots) {
    if (Test-Path -LiteralPath $root -PathType Container) {
        $folders += RelativePath ((Resolve-Path -LiteralPath $root).Path)
        $folders += @(Get-ChildItem -LiteralPath $root -Directory -Recurse -Force | ForEach-Object { RelativePath $_.FullName })
    }
}
$folders = @($folders | Sort-Object -Unique)

$previous = @{}
if (Test-Path -LiteralPath $jsonPath -PathType Leaf) {
    $saved = Get-Content -LiteralPath $jsonPath -Raw | ConvertFrom-Json
    foreach ($entry in $saved.folders) { $previous[[string]$entry.path] = [string]$entry.readAt }
}

$markSet = @{}
foreach ($path in $MarkRead) {
    $normalized = $path.Trim().TrimEnd('/','\').Replace('\', '/')
    if ($normalized.StartsWith('./')) { $normalized = $normalized.Substring(2) }
    if ($normalized -notin $folders) { throw "Folder is not in the Spec Kit inventory: $normalized" }
    $markSet[$normalized] = $true
}

$now = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')
$entries = @($folders | ForEach-Object {
    $readAt = if ($markSet.ContainsKey($_)) { $now } elseif ($previous.ContainsKey($_)) { $previous[$_] } else { $null }
    [pscustomobject]@{ path = $_; readAt = $readAt }
})
$payload = [pscustomobject]@{ updatedAt = $now; folders = $entries }
$payload | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $jsonPath -Encoding utf8

$lines = @('# Spec Kit folder index', '', "Updated (UTC): $now", '', 'A `readAt` value records when an agent explicitly marked a folder after inspecting its contents. A blank value means only the folder was discovered.', '', '| Folder | Last marked read (UTC) |', '| --- | --- |')
foreach ($entry in $entries) {
    $value = if ($entry.readAt) { $entry.readAt } else { '' }
    $lines += "| ``$($entry.path)`` | $value |"
}
$lines | Set-Content -LiteralPath $mdPath -Encoding utf8
$readCount = @($entries | Where-Object { $_.readAt }).Count
Write-Output "Spec Kit folder index updated: $($entries.Count) folders discovered; $readCount marked read."
