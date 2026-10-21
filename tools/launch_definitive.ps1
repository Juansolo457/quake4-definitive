# Launch openQ4 as the Quake 4 Definitive Edition.
# The first launch with a profile applies config/definitive.cfg; later launches keep
# whatever the player changed in the settings menu.
#
#   pwsh tools/launch_definitive.ps1 [-Reapply] [-- extra +set/+map arguments]
param(
    [switch]$Reapply,
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
if ($Extra) { $launch += $Extra }

Start-Process -FilePath $exe -WorkingDirectory (Split-Path $exe) -ArgumentList $launch
