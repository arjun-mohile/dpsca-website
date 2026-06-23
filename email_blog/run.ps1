# Launcher for blogchecker.py.
#
# Pulls the encrypted-password key (BLOG_FERNET_KEY) from the persisted Windows
# User-scope environment into THIS session, then runs blogchecker.py. This makes
# manual runs work in any terminal — even one opened before the key was set —
# without retyping the key or signing out/in. The key still lives only in the
# registry; it is never written to disk here.
#
# Usage (any arguments are passed straight through to blogchecker.py):
#   .\run.ps1                 # default: send now, then every 7 days
#   .\run.ps1 --check-replies # read Arjun's replies and act on them, then exit
#   .\run.ps1 --once          # send a single email and exit
#   .\run.ps1 --encrypt       # (re)store the Gmail App Password encrypted

$ErrorActionPreference = "Stop"

# Always operate from this script's own folder, regardless of where it's run.
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Load the key from the persisted User-scope variable into this session only.
$key = [Environment]::GetEnvironmentVariable("BLOG_FERNET_KEY", "User")
if (-not $key) {
    Write-Error "BLOG_FERNET_KEY is not set at User scope. Run 'python blogchecker.py --encrypt' first."
    exit 1
}
$env:BLOG_FERNET_KEY = $key

python blogchecker.py @args
exit $LASTEXITCODE
