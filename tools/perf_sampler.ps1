# Sample Windows' GPU counters for one process once a second until it exits.
# These are the numbers Task Manager shows: the game's 3D engine utilization, the
# whole adapter's 3D utilization (every process), and the game's dedicated VRAM.
# launch_definitive.ps1 -PerfTrace starts this next to the game's own trace.
#
#   pwsh tools/perf_sampler.ps1 -ProcessId <pid> -Out <file.csv>
param(
    [Parameter(Mandatory = $true)][int]$ProcessId,
    [Parameter(Mandatory = $true)][string]$Out
)

$paths = @(
    "\GPU Engine(pid_$($ProcessId)_*engtype_3D)\Utilization Percentage",
    "\GPU Process Memory(pid_$($ProcessId)_*)\Dedicated Usage",
    "\GPU Engine(*engtype_3D)\Utilization Percentage"
)
$invariant = [Globalization.CultureInfo]::InvariantCulture

New-Item -ItemType Directory -Force (Split-Path $Out) | Out-Null
Set-Content -Path $Out -Value "unix_time,game_3d_pct,adapter_3d_pct,game_vram_mb" -Encoding ascii

while (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue) {
    # Takes about a second: utilization is a rate over the sample interval.
    $set = Get-Counter -Counter $paths -SampleInterval 1 -MaxSamples 1 -ErrorAction SilentlyContinue
    if (-not $set) { continue }
    $samples = $set.CounterSamples
    $mine = $samples | Where-Object { $_.Path -match "pid_$($ProcessId)_" }
    $memory = $mine | Where-Object { $_.Path -match 'dedicated usage$' }
    # The adapter the game renders on is the one holding its VRAM.
    $top = $memory | Sort-Object CookedValue -Descending | Select-Object -First 1
    $luid = if ($top -and $top.InstanceName -match '(luid_0x[0-9a-f]+_0x[0-9a-f]+)') { $Matches[1] } else { '' }
    $engines = $samples | Where-Object { $_.Path -match 'utilization percentage$' -and $_.InstanceName -match $luid }
    $game = ($engines | Where-Object { $_.Path -match "pid_$($ProcessId)_" } | Measure-Object CookedValue -Sum).Sum
    $all = ($engines | Measure-Object CookedValue -Sum).Sum
    $vram = ($memory | Measure-Object CookedValue -Sum).Sum / 1MB
    $time = [DateTimeOffset]::new($set.Timestamp).ToUnixTimeMilliseconds() / 1000.0
    $line = [string]::Format($invariant, "{0:F3},{1:F1},{2:F1},{3:F0}", $time, [Math]::Min(100, [double]$game), [Math]::Min(100, [double]$all), $vram)
    Add-Content -Path $Out -Value $line -Encoding ascii
}
