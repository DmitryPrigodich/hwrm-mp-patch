param(
    [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Homeworld',
    [ValidateSet('Russian','English')][string]$Language='Russian',
    [switch]$PrintOnly
)
$ErrorActionPreference='Stop'
$exe=Join-Path $GameRoot 'HomeworldRM\Bin\Release\HomeworldRM.exe'
$archive=Join-Path $GameRoot 'HomeworldRM\DataWorkshopMODs\HWMPPatch24\HWMPPatch24.big'
if (-not (Test-Path -LiteralPath $exe)) { throw 'Homeworld Remastered was not found. Supply -GameRoot.' }
if (-not (Test-Path -LiteralPath $archive)) { throw 'HWMP Patch 2.4 is not installed in DataWorkshopMODs\HWMPPatch24.' }
$arguments=@('-workshopmod','"HWMPPatch24\HWMPPatch24.big"','-locale',$Language)
if ($PrintOnly) { Write-Output ($exe+' '+($arguments -join ' ')); return }
if (Get-Process -Name HomeworldRM -ErrorAction SilentlyContinue) { throw 'Homeworld Remastered is already running.' }
# Explicitly running this starter opens the normal, visible game menu.
Start-Process -FilePath $exe -ArgumentList $arguments -WorkingDirectory (Split-Path $exe)
