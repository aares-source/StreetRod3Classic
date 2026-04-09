param(
    [string]$Root = "."
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$rootPath = (Resolve-Path $Root).Path
$depsDir = Join-Path $rootPath "third_party"
$libX64 = Join-Path $rootPath "lib\x64"
New-Item -ItemType Directory -Force -Path $depsDir | Out-Null
New-Item -ItemType Directory -Force -Path $libX64 | Out-Null

function Download-FirstAvailable {
    param(
        [string[]]$Urls,
        [string]$OutFile
    )

    foreach ($u in $Urls) {
        try {
            Write-Host "Intentando: $u"
            Invoke-WebRequest -Uri $u -OutFile $OutFile -UseBasicParsing
            if ((Test-Path $OutFile) -and (Get-Item $OutFile).Length -gt 0) {
                Write-Host "Descargado: $OutFile"
                return $true
            }
        } catch {
            Write-Warning "Falló: $u"
        }
    }
    return $false
}

function Extract-Zip {
    param([string]$ZipPath, [string]$ExtractTo)
    if (Test-Path $ExtractTo) { Remove-Item -Recurse -Force $ExtractTo }
    New-Item -ItemType Directory -Force -Path $ExtractTo | Out-Null
    Expand-Archive -Path $ZipPath -DestinationPath $ExtractTo -Force
}

# SDL2
$sdlZip = Join-Path $depsDir "SDL2-devel-VC.zip"
$sdlOk = Download-FirstAvailable -OutFile $sdlZip -Urls @(
    "https://github.com/libsdl-org/SDL/releases/download/release-2.30.11/SDL2-devel-2.30.11-VC.zip",
    "https://github.com/libsdl-org/SDL/releases/download/release-2.30.10/SDL2-devel-2.30.10-VC.zip",
    "https://github.com/libsdl-org/SDL/releases/download/release-2.30.9/SDL2-devel-2.30.9-VC.zip",
    "https://github.com/libsdl-org/SDL/releases/download/release-2.30.2/SDL2-devel-2.30.2-VC.zip"
)
if (-not $sdlOk) { throw "No se pudo descargar SDL2 devel VC" }

$sdlExtract = Join-Path $depsDir "SDL2"
Extract-Zip -ZipPath $sdlZip -ExtractTo $sdlExtract
$sdlLib = Get-ChildItem -Path $sdlExtract -Recurse -File | Where-Object { $_.FullName -match "\\lib\\x64\\SDL2\.lib$" } | Select-Object -First 1
$sdlMainLib = Get-ChildItem -Path $sdlExtract -Recurse -File | Where-Object { $_.FullName -match "\\lib\\x64\\SDL2main\.lib$" } | Select-Object -First 1
$sdlDll = Get-ChildItem -Path $sdlExtract -Recurse -File | Where-Object { $_.FullName -match "\\lib\\x64\\SDL2\.dll$" } | Select-Object -First 1
if (-not $sdlLib -or -not $sdlMainLib) { throw "No encontré SDL2.lib/SDL2main.lib x64" }
Copy-Item $sdlLib.FullName (Join-Path $libX64 "SDL2.lib") -Force
Copy-Item $sdlMainLib.FullName (Join-Path $libX64 "SDL2main.lib") -Force
if ($sdlDll) { Copy-Item $sdlDll.FullName (Join-Path $libX64 "SDL2.dll") -Force }

# SDL2_image
$imgZip = Join-Path $depsDir "SDL2_image-devel-VC.zip"
$imgOk = Download-FirstAvailable -OutFile $imgZip -Urls @(
    "https://github.com/libsdl-org/SDL_image/releases/download/release-2.8.8/SDL2_image-devel-2.8.8-VC.zip",
    "https://github.com/libsdl-org/SDL_image/releases/download/release-2.8.2/SDL2_image-devel-2.8.2-VC.zip",
    "https://github.com/libsdl-org/SDL_image/releases/download/release-2.6.3/SDL2_image-devel-2.6.3-VC.zip"
)
if (-not $imgOk) { throw "No se pudo descargar SDL2_image devel VC" }

$imgExtract = Join-Path $depsDir "SDL2_image"
Extract-Zip -ZipPath $imgZip -ExtractTo $imgExtract
$imgLib = Get-ChildItem -Path $imgExtract -Recurse -File | Where-Object { $_.FullName -match "\\lib\\x64\\SDL2_image\.lib$" } | Select-Object -First 1
if (-not $imgLib) { throw "No encontré SDL2_image.lib x64" }
Copy-Item $imgLib.FullName (Join-Path $libX64 "SDL2_image.lib") -Force
Get-ChildItem -Path $imgExtract -Recurse -File | Where-Object { $_.DirectoryName -match "\\lib\\x64$" -and $_.Extension -eq ".dll" } | ForEach-Object {
    Copy-Item $_.FullName (Join-Path $libX64 $_.Name) -Force
}

# BASS
$bassZip = Join-Path $depsDir "bass24.zip"
$bassOk = Download-FirstAvailable -OutFile $bassZip -Urls @(
    "https://www.un4seen.com/files/bass24.zip"
)
if (-not $bassOk) { throw "No se pudo descargar BASS" }

$bassExtract = Join-Path $depsDir "bass"
Extract-Zip -ZipPath $bassZip -ExtractTo $bassExtract
$bassLib = Get-ChildItem -Path $bassExtract -Recurse -File | Where-Object { $_.FullName -match "\\c\\x64\\bass\.lib$" } | Select-Object -First 1
$bassDll = Get-ChildItem -Path $bassExtract -Recurse -File | Where-Object { $_.FullName -match "\\x64\\bass\.dll$" } | Select-Object -First 1
if (-not $bassLib) { throw "No encontré bass.lib x64" }
Copy-Item $bassLib.FullName (Join-Path $libX64 "bass.lib") -Force
if ($bassDll) { Copy-Item $bassDll.FullName (Join-Path $libX64 "bass.dll") -Force }

Write-Host "Descargas x64 completadas en $libX64"