param(
    [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Homeworld',
    [ValidateSet('Russian','English')][string]$Language='Russian',
    [switch]$PrintOnly
)
$ErrorActionPreference='Stop'
$exe=Join-Path $GameRoot 'HomeworldRM\Bin\Release\HomeworldRM.exe'
$archive=Join-Path $GameRoot 'HomeworldRM\DataWorkshopMODs\HWMPTestGrounds\HWMPTestGrounds.big'
$arguments=@('-workshopmod','"HWMPTestGrounds\HWMPTestGrounds.big"','-locale',$Language,'-luatrace')
if ($PrintOnly) { Write-Output ($exe+' '+($arguments -join ' ')); return }
if (-not (Test-Path -LiteralPath $exe)) { throw 'Homeworld Remastered was not found. Supply -GameRoot.' }
if (-not (Test-Path -LiteralPath $archive)) { throw 'HWMP Test Grounds must be installed separately before launch.' }
if (Get-Process -Name HomeworldRM -ErrorAction SilentlyContinue) { throw 'Homeworld Remastered is already running.' }
# Explicit invocation opens the interactive game. Package preparation never calls this.
Start-Process -FilePath $exe -ArgumentList $arguments -WorkingDirectory (Split-Path $exe)
