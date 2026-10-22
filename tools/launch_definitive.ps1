# Launch openQ4 as the Quake 4 Definitive Edition.
# The first launch with a profile applies config/definitive.cfg; later launches keep
# whatever the player changed in the settings menu.
# -PerfTrace records a performance trace (com_perfTrace) and Windows' GPU counters
# into <profile>/baseoq4/perftrace; summarize them with tools/perf_report.py.
#
#   pwsh tools/launch_definitive.ps1 [-Reapply] [-PerfTrace] [-- extra +set/+map arguments]
param(
    [switch]$Reapply,
    [switch]$PerfTrace,
    [Parameter(ValueFromRemainingArguments = $true)][string[]]$Extra
)

$repo = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $repo "reference\openQ4\builddir\openQ4-client_x64.exe"
$save = Join-Path $repo "reference\openQ4\.home"
$gameDir = Join-Path $save "baseoq4"
$marker = Join-Path $gameDir "definitive_applied.txt"

if (Get-Process openQ4-client_x64 -ErrorAction SilentlyContinue) {
    Write-Host "openQ4 is already running; not starting a second copy."
    exit 1
}

New-Item -ItemType Directory -Force $gameDir | Out-Null
Copy-Item (Join-Path $repo "config\definitive.cfg") (Join-Path $gameDir "definitive.cfg") -Force

$launch = @('+set', 'fs_savepath', "`"$save`"", '+set', 'logFile', '2', '+set', 'logFileName', 'logs/play.log')
if ($Reapply -or -not (Test-Path $marker)) {
    $launch += @('+exec', 'definitive.cfg')
    Set-Content -Path $marker -Value "definitive.cfg applied $(Get-Date -Format s)"
}
if ($PerfTrace) { $launch += @('+set', 'com_perfTrace', '1') }
if ($Extra) { $launch += $Extra }

$game = Start-Process -FilePath $exe -WorkingDirectory (Split-Path $exe) -ArgumentList $launch -PassThru
if ($PerfTrace) {
    $out = Join-Path $gameDir ("perftrace\gpu_{0:yyyyMMdd_HHmmss}.csv" -f (Get-Date))
    $shell = (Get-Process -Id $PID).Path
    Start-Process -FilePath $shell -WindowStyle Hidden -ArgumentList @('-NoProfile', '-File', "`"$PSScriptRoot\perf_sampler.ps1`"", '-ProcessId', $game.Id, '-Out', "`"$out`"")
    Write-Host "Performance trace on: $(Join-Path $gameDir 'perftrace')"
}
