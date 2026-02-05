# Desktop Shortcut Creator
# Run this to create a desktop shortcut for one-click startup

$WScriptShell = New-Object -ComObject WScript.Shell
$Desktop = [System.Environment]::GetFolderPath('Desktop')
$ShortcutPath = Join-Path $Desktop "Car Lease AI Assistant.lnk"

$Shortcut = $WScriptShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = Join-Path $PSScriptRoot "golive.bat"
$Shortcut.WorkingDirectory = $PSScriptRoot
$Shortcut.Description = "Start Car Lease Review AI Assistant"
$Shortcut.IconLocation = "shell32.dll,13"  # Car icon
$Shortcut.Save()

Write-Host "✅ Desktop shortcut created successfully!" -ForegroundColor Green
Write-Host "📍 Location: $ShortcutPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "Double-click the shortcut on your desktop to start the application!" -ForegroundColor Yellow
