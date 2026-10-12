$ErrorActionPreference = 'Stop'
$repairFile = Join-Path ([IO.Path]::GetTempPath()) (([guid]::NewGuid().ToString()) + '-WebView2Setup.exe')
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Write-Host 'Tai WebView2 Runtime tu Microsoft...'
    Invoke-WebRequest -UseBasicParsing -Uri 'https://go.microsoft.com/fwlink/p/?LinkId=2124703' -OutFile $repairFile
    $signature = Get-AuthenticodeSignature -FilePath $repairFile
    if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.GetNameInfo([Security.Cryptography.X509Certificates.X509NameType]::SimpleName, $false) -ne 'Microsoft Corporation') {
        throw 'Khong xac minh duoc chu ky Microsoft. Khong chay tep da tai.'
    }
    $repairProcess = Start-Process -FilePath $repairFile -ArgumentList '/silent','/install' -Wait -PassThru
    if ($repairProcess.ExitCode -ne 0) { throw ('WebView2 bao ma loi: ' + $repairProcess.ExitCode) }
    Write-Host 'Da cai WebView2. Mo lai Freelance Desk.'
} catch {
    Write-Host 'Chua cai duoc WebView2. Co the cai thu cong tu trang Microsoft:'
    Write-Host 'https://developer.microsoft.com/microsoft-edge/webview2/'
    Write-Host $_.Exception.Message
    exit 1
} finally {
    if (Test-Path -LiteralPath $repairFile) { Remove-Item -LiteralPath $repairFile -Force }
}
