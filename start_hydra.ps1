Set-Location 'C:\Users\gamer\Desktop\Hydra'

$backendPsi = New-Object System.Diagnostics.ProcessStartInfo
$backendPsi.FileName = 'cmd.exe'
$backendPsi.Arguments = '/c run_backend.cmd'
$backendPsi.WorkingDirectory = 'C:\Users\gamer\Desktop\Hydra'
$backendPsi.UseShellExecute = $true
[System.Diagnostics.Process]::Start($backendPsi)

Start-Sleep -Seconds 2

$frontendPsi = New-Object System.Diagnostics.ProcessStartInfo
$frontendPsi.FileName = 'cmd.exe'
$frontendPsi.Arguments = '/c run_frontend.cmd'
$frontendPsi.WorkingDirectory = 'C:\Users\gamer\Desktop\Hydra'
$frontendPsi.UseShellExecute = $true
[System.Diagnostics.Process]::Start($frontendPsi)

Start-Sleep -Seconds 3

Start-Process 'http://localhost:5173/'
Write-Host "Hydra services successfully launched in dedicated persistent Windows consoles."

