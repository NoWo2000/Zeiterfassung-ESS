$ErrorActionPreference = 'Stop'

# Resolve paths
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$targetPath = Join-Path $projectRoot 'main.pyw'

if (-not (Test-Path $targetPath)) {
    throw "main.pyw not found at: $targetPath"
}

$startupFolder = [Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startupFolder 'Zeiterfassung-ESS.lnk'

# Create shortcut
$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetPath
$shortcut.WorkingDirectory = $projectRoot
$shortcut.WindowStyle = 7
$shortcut.Save()

Write-Host "Shortcut created: $shortcutPath"