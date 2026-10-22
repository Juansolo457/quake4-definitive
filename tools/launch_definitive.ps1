# Launch openQ4 as the Quake 4 Definitive Edition.
# The first launch with a profile applies config/definitive.cfg and a graphics tier
# picked from the GPU's video memory; later launches keep whatever the player changed
# in the settings menu. -Reapply applies them again; -Tier forces a tier.
#   ultra   12 GB or more   definitive.cfg as is (4x MSAA + SMAA, 2048 shadow maps, 240 fps cap)
#   high    8 to 12 GB      + config/tier_high.cfg
#   medium  4 to 8 GB       + config/tier_medium.cfg (also when the memory can't be read)
#   low     under 4 GB      + config/tier_low.cfg
# -ShowTier prints the tier and exits. -PerfTrace records a performance trace
# (com_perfTrace) and Windows' GPU counters into <profile>/baseoq4/perftrace;
# summarize them with tools/perf_report.py.
#
#   pwsh tools/launch_definitive.ps1 [-Reapply] [-Tier auto|ultra|high|medium|low] [-ShowTier] [-PerfTrace] [-- extra +set/+map arguments]
param(
    [switch]$Reapply,
    [ValidateSet('auto', 'ultra', 'high', 'medium', 'low')][string]$Tier = 'auto',
    [switch]$ShowTier,
    [switch]$PerfTrace,
    [Parameter(ValueFromRemainingArguments = $true)][string[]]$Extra
)

$repo = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $repo "reference\openQ4\builddir\openQ4-client_x64.exe"
$save = Join-Path $repo "reference\openQ4\.home"
$gameDir = Join-Path $save "baseoq4"
$marker = Join-Path $gameDir "definitive_applied.txt"

# The largest dedicated video memory of any display adapter. The registry's 64-bit
# size is exact; Win32_VideoController.AdapterRAM is 32-bit and stops at 4 GB.
function Get-VideoMemory {
    $best = $null
    $class = 'HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}'
    foreach ($key in Get-ChildItem $class -ErrorAction SilentlyContinue | Where-Object { $_.PSChildName -match '^\d{4}$' }) {
        $p = Get-ItemProperty $key.PSPath -ErrorAction SilentlyContinue
        $bytes = $p.'HardwareInformation.qwMemorySize'
        if (-not $bytes) {
            $size = $p.'HardwareInformation.MemorySize'
            $bytes = if ($size -is [byte[]]) { [BitConverter]::ToUInt32($size, 0) } else { $size }
        }
        if ($bytes -and (-not $best -or [uint64]$bytes -gt $best.Bytes)) {
            $best = [pscustomobject]@{ Name = $p.DriverDesc; Bytes = [uint64]$bytes }
        }
    }
    if (-not $best) {
        $adapter = Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue |
            Where-Object { $_.AdapterRAM } | Sort-Object AdapterRAM -Descending | Select-Object -First 1
        if ($adapter) { $best = [pscustomobject]@{ Name = $adapter.Name; Bytes = [uint64]$adapter.AdapterRAM } }
    }
    return $best
}

$gpu = Get-VideoMemory
$why = 'forced with -Tier'
if ($Tier -eq 'auto') {
    if (-not $gpu) {
        $Tier = 'medium'; $why = 'video memory unknown'
    } else {
        $gb = $gpu.Bytes / 1GB
        $Tier = if ($gb -ge 11.5) { 'ultra' } elseif ($gb -ge 7.5) { 'high' } elseif ($gb -ge 3.5) { 'medium' } else { 'low' }
        $why = "{0}, {1:N0} GB" -f $gpu.Name, $gb
    }
}
$tierMessage = "Graphics tier: $Tier ($why)"
if ($ShowTier) {
    Write-Host $tierMessage
    exit 0
}

if (Get-Process openQ4-client_x64 -ErrorAction SilentlyContinue) {
    Write-Host "openQ4 is already running; not starting a second copy."
    exit 1
}

New-Item -ItemType Directory -Force $gameDir | Out-Null
Copy-Item (Join-Path $repo "config\definitive.cfg") (Join-Path $gameDir "definitive.cfg") -Force
foreach ($t in 'high', 'medium', 'low') {
    Copy-Item (Join-Path $repo "config\tier_$t.cfg") (Join-Path $gameDir "tier_$t.cfg") -Force
}

$launch = @('+set', 'fs_savepath', "`"$save`"", '+set', 'logFile', '2', '+set', 'logFileName', 'logs/play.log')
if ($Reapply -or -not (Test-Path $marker)) {
    $launch += @('+exec', 'definitive.cfg')
    if ($Tier -ne 'ultra') { $launch += @('+exec', "tier_$Tier.cfg") }
    Set-Content -Path $marker -Value "definitive.cfg applied $(Get-Date -Format s); $tierMessage"
    Write-Host "Applying the definitive defaults. $tierMessage"
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
