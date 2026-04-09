param(
    [string]$SolutionFile = ".\sr3.sln",
    [string]$ProjectFile = ".\sr3.vcxproj",
    [string]$RepoLibDir = ".\lib",
    [string[]]$SearchRoots = @("$env:USERPROFILE\Downloads", "$env:USERPROFILE\source", "C:\libs", "C:\SDL2", "C:\dev")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Find-X64Candidate {
    param(
        [Parameter(Mandatory = $true)] [string]$FileName,
        [Parameter(Mandatory = $true)] [string[]]$Roots
    )

    $all = New-Object System.Collections.Generic.List[object]
    foreach ($root in $Roots) {
        if (-not (Test-Path $root)) { continue }
        try {
            $hits = Get-ChildItem -Path $root -Recurse -File -Filter $FileName -ErrorAction SilentlyContinue
            foreach ($h in $hits) {
                $p = $h.FullName.ToLowerInvariant()
                $score = 0
                if ($p -match "x64|win64|64-bit|64bit") { $score += 10 }
                if ($p -match "\\lib\\x64|\\lib64|\\x86_64") { $score += 8 }
                if ($p -match "msvc|vc\\lib") { $score += 2 }
                if ($h.Length -gt 0) { $score += 1 }
                $all.Add([PSCustomObject]@{ File = $h; Score = $score })
            }
        } catch {
        }
    }

    if ($all.Count -eq 0) { return $null }
    return $all | Sort-Object Score, @{Expression={$_.File.LastWriteTimeUtc}} -Descending | Select-Object -First 1
}

function Update-ProjectX64LibDir {
    param([string]$Path)

    [xml]$xml = Get-Content -Path $Path
    $changed = $false

    $groups = $xml.Project.ItemDefinitionGroup
    foreach ($g in $groups) {
        if (-not $g.Condition) { continue }
        if ($g.Condition -notmatch "\|x64'") { continue }

        if (-not $g.Link) {
            $g.AppendChild($xml.CreateElement("Link", $xml.Project.NamespaceURI)) | Out-Null
        }

        if (-not $g.Link.AdditionalLibraryDirectories) {
            $g.Link.AppendChild($xml.CreateElement("AdditionalLibraryDirectories", $xml.Project.NamespaceURI)) | Out-Null
        }

        $desired = '$(SolutionDir)lib\x64;%(AdditionalLibraryDirectories)'
        if ($g.Link.AdditionalLibraryDirectories -ne $desired) {
            $g.Link.AdditionalLibraryDirectories = $desired
            $changed = $true
        }
    }

    if ($changed) {
        Copy-Item $Path "$Path.bak" -Force
        $xml.Save($Path)
        Write-Host "Actualizado $Path -> usa lib\\x64 en configuraciones x64"
    } else {
        Write-Host "$Path ya estaba configurado para usar lib\\x64 en x64"
    }
}

$requiredLibs = @("SDL2.lib", "SDL2main.lib", "SDL2_image.lib", "bass.lib", "coldet.lib")
$repoRoot = (Resolve-Path ".").Path
$solution = (Resolve-Path $SolutionFile).Path
$project = (Resolve-Path $ProjectFile).Path
$libDir = Join-Path (Resolve-Path $RepoLibDir).Path "x64"

New-Item -ItemType Directory -Force -Path $libDir | Out-Null

Write-Host "Buscando y copiando libs x64 a $libDir"
$missing = New-Object System.Collections.Generic.List[string]

foreach ($lib in $requiredLibs) {
    $candidate = Find-X64Candidate -FileName $lib -Roots $SearchRoots
    if ($null -eq $candidate) {
        Write-Warning "No encontrada: $lib"
        $missing.Add($lib)
        continue
    }

    $src = $candidate.File.FullName
    $dst = Join-Path $libDir $lib

    if ($src.StartsWith($repoRoot, [System.StringComparison]::OrdinalIgnoreCase) -and $src -notmatch "\\lib\\x64\\") {
        Write-Warning "Solo encontré $lib dentro del repo (probablemente x86): $src"
        $missing.Add($lib)
        continue
    }

    Copy-Item -Path $src -Destination $dst -Force
    Write-Host "OK $lib <= $src"
}

Update-ProjectX64LibDir -Path $project

if ($missing.Count -gt 0) {
    Write-Warning "Faltan librerías x64: $($missing -join ', ')"
    Write-Host "Colócalas manualmente en $libDir y vuelve a ejecutar el script."
    exit 2
}

Write-Host "Compilando Debug|x64"
& msbuild $solution /m /nologo /v:m /p:Configuration=Debug /p:Platform=x64
$debugExit = $LASTEXITCODE

Write-Host "Compilando Release|x64"
& msbuild $solution /m /nologo /v:m /p:Configuration=Release /p:Platform=x64
$releaseExit = $LASTEXITCODE

if ($debugExit -eq 0 -and $releaseExit -eq 0) {
    Write-Host "OK: Debug y Release x64 compilan."
    exit 0
}

Write-Warning "Compilación con errores. Debug=$debugExit Release=$releaseExit"
exit 1
