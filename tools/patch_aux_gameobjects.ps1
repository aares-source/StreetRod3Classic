# patch_aux_gameobjects.ps1
# Adds required $-anchor game objects to a StreetRod3 .aux file.
# Usage: .\patch_aux_gameobjects.ps1 <path\to\car.aux>

param([Parameter(Mandatory)][string]$AuxPath)

$SIG = [byte[]](0x41,0x75,0x78,0x69,0x6C,0x69,0x61,0x72,0x79,0x20,0x33,0x44,0x1A,0x08,0x04)

function Read-UInt32 { param($data, $off)
    [BitConverter]::ToUInt32($data, $off)
}
function Read-Float { param($data, $off)
    [BitConverter]::ToSingle($data, $off)
}

# Write helpers using a shared MemoryStream passed by reference
function ms-WriteUInt32 { param($ms, [uint32]$v)
    $b = [BitConverter]::GetBytes($v); $ms.Write($b,0,4)
}
function ms-WriteFloat { param($ms, [float]$v)
    $b = [BitConverter]::GetBytes($v); $ms.Write($b,0,4)
}
function ms-WritePascalString { param($ms, [string]$s)
    $enc = [System.Text.Encoding]::ASCII.GetBytes($s)
    $len = [byte][Math]::Min($enc.Length, 255)
    $ms.WriteByte($len)
    $ms.Write($enc, 0, $len)
}
function ms-WriteGameObject { param($ms, [string]$name, [float]$x, [float]$y, [float]$z)
    ms-WritePascalString $ms $name
    ms-WriteFloat $ms $x; ms-WriteFloat $ms $y; ms-WriteFloat $ms $z
    # Identity matrix (9 floats row-major)
    foreach ($v in @(1,0,0, 0,1,0, 0,0,1)) { ms-WriteFloat $ms ([float]$v) }
}

# -- Read file --
$data = [System.IO.File]::ReadAllBytes($AuxPath)

# -- Verify signature --
for ($i=0; $i -lt 15; $i++) {
    if ($data[$i] -ne $SIG[$i]) { Write-Error "Bad signature"; exit 1 }
}

# -- Parse header --
$numVerts  = Read-UInt32 $data 35
$numUVs    = Read-UInt32 $data 39
$numNorms  = Read-UInt32 $data 43
Write-Host "Vertices=$numVerts  UVs=$numUVs  Normals=$numNorms"

# -- Bounding box from vertices --
$off = 47
$minX = [float]::MaxValue; $maxX = [float]::MinValue
$minY = [float]::MaxValue; $maxY = [float]::MinValue
$minZ = [float]::MaxValue; $maxZ = [float]::MinValue

for ($i=0; $i -lt $numVerts; $i++) {
    $vx = Read-Float $data $off; $off+=4
    $vy = Read-Float $data $off; $off+=4
    $vz = Read-Float $data $off; $off+=4
    if ($vx -lt $minX) { $minX=$vx }; if ($vx -gt $maxX) { $maxX=$vx }
    if ($vy -lt $minY) { $minY=$vy }; if ($vy -gt $maxY) { $maxY=$vy }
    if ($vz -lt $minZ) { $minZ=$vz }; if ($vz -gt $maxZ) { $maxZ=$vz }
}
Write-Host ("BBox X=[{0:F3},{1:F3}] Y=[{2:F3},{3:F3}] Z=[{4:F3},{5:F3}]" -f $minX,$maxX,$minY,$maxY,$minZ,$maxZ)

# -- Estimate anchor positions --
$cx     = [float](($minX+$maxX)/2)
$halfX  = [float](($maxX-$minX)*0.38)
$frontZ = [float]($maxZ*0.62)
$backZ  = [float]($minZ*0.62)
$wheelY = [float]($minY + ($maxY-$minY)*0.12)
$shockY = [float]($minY + ($maxY-$minY)*0.30)
$midY   = [float]($minY + ($maxY-$minY)*0.40)
$camY   = [float]($minY + ($maxY-$minY)*0.75)
$camZ   = [float](($minZ+$maxZ)/2 * 0.3)

# Each entry: [name, x, y, z]
$anchors = [ordered]@{
    '$flwheel'   = @($halfX,       $wheelY, $frontZ)
    '$frwheel'   = @(-$halfX,      $wheelY, $frontZ)
    '$brwheel'   = @(-$halfX,      $wheelY, $backZ)
    '$blwheel'   = @($halfX,       $wheelY, $backZ)
    '$flshock'   = @($halfX,       $shockY, $frontZ)
    '$frshock'   = @(-$halfX,      $shockY, $frontZ)
    '$brshock'   = @(-$halfX,      $shockY, $backZ)
    '$blshock'   = @($halfX,       $shockY, $backZ)
    '$lmuffler'  = @([float]($halfX*0.6),  $wheelY, [float]($backZ*0.7))
    '$rmuffler'  = @([float](-$halfX*0.6), $wheelY, [float]($backZ*0.7))
    '$block'     = @($cx,          $midY,   [float]($backZ*0.5))
    '$diff'      = @($cx,          $wheelY, [float]($backZ*0.8))
    '$trans'     = @($cx,          $midY,   [float]($backZ*0.6))
    '$incar_cam' = @($cx,          $camY,   $camZ)
}

Write-Host "`nAdding $($anchors.Count) game objects:"
foreach ($name in $anchors.Keys) {
    $pos = $anchors[$name]
    Write-Host ("  {0,-15}  ({1:F3}, {2:F3}, {3:F3})" -f $name,$pos[0],$pos[1],$pos[2])
}

# -- Build extra bytes with MemoryStream --
$ms = New-Object System.IO.MemoryStream
foreach ($name in $anchors.Keys) {
    $pos = $anchors[$name]
    ms-WriteGameObject $ms $name $pos[0] $pos[1] $pos[2]
}
$extra = $ms.ToArray()
$ms.Dispose()

# -- Update NumGameObjects in header (offset 31) --
$countBytes = [BitConverter]::GetBytes([uint32]$anchors.Count)
[System.Array]::Copy($countBytes, 0, $data, 31, 4)

# -- Append to file data --
$patched = New-Object byte[] ($data.Length + $extra.Length)
[System.Array]::Copy($data,  0, $patched, 0,            $data.Length)
[System.Array]::Copy($extra, 0, $patched, $data.Length, $extra.Length)

# -- Backup and write --
$backup = $AuxPath + ".bak"
Copy-Item $AuxPath $backup -Force
[System.IO.File]::WriteAllBytes($AuxPath, $patched)
Write-Host "`nDone. Backup at $backup"
