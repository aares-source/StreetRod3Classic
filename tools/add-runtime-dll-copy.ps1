param([string]$ProjectFile = '.\sr3.vcxproj')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$projectPath = (Resolve-Path $ProjectFile).Path
[xml]$xml = Get-Content -Path $projectPath
$ns = $xml.Project.NamespaceURI

function Ensure-ChildNode {
    param([xml]$Doc, [System.Xml.XmlNode]$Parent, [string]$Name, [string]$NamespaceUri)
    $node = $Parent.SelectSingleNode("*[local-name()='$Name']")
    if (-not $node) {
        $node = $Doc.CreateElement($Name, $NamespaceUri)
        [void]$Parent.AppendChild($node)
    }
    return $node
}

$copyLines = @(
    'copy /Y "$(SolutionDir)lib\x64\SDL2.dll" "$(OutDir)"',
    'copy /Y "$(SolutionDir)lib\x64\SDL2_image.dll" "$(OutDir)"',
    'copy /Y "$(SolutionDir)lib\x64\bass.dll" "$(OutDir)"'
)
$commandText = ($copyLines -join "`r`n")

$groups = $xml.Project.SelectNodes("*[local-name()='ItemDefinitionGroup']")
foreach ($group in $groups) {
    $condition = $group.Attributes['Condition']
    if (-not $condition) { continue }
    if ($condition.Value -notmatch "'\$\(Configuration\)\|\$\(Platform\)'=='(Debug|Release)\|x64'") { continue }

    $postBuild = Ensure-ChildNode -Doc $xml -Parent $group -Name 'PostBuildEvent' -NamespaceUri $ns
    $command = Ensure-ChildNode -Doc $xml -Parent $postBuild -Name 'Command' -NamespaceUri $ns
    $command.InnerText = $commandText
}

Copy-Item $projectPath "$projectPath.bak" -Force
$xml.Save($projectPath)
Write-Host 'Actualizado PostBuildEvent para copiar DLLs x64.'
