$ErrorActionPreference = "Stop"

python -m pip install -r requirements-dev.txt
python -m black .

$node = Get-Command node -ErrorAction SilentlyContinue
if ($null -eq $node) {
    Write-Host "Node.js not found; skipping JS/Java formatting."
    exit 0
}

npx -y prettier@3.2.5 --write . --ignore-unknown

$javaFiles = Get-ChildItem -Path . -Recurse -Filter *.java -File -ErrorAction SilentlyContinue
if ($null -eq $javaFiles -or $javaFiles.Count -eq 0) {
    Write-Host "No .java files found; skipping Java formatting."
    exit 0
}

$javaScript = @'
const { spawnSync } = require('child_process');

const pluginPath = require.resolve('prettier-plugin-java');
const prettierCli = require.resolve('prettier/bin/prettier.cjs');
const args = [prettierCli, '--plugin', pluginPath, '--write', '**/*.java'];
const result = spawnSync(process.execPath, args, { stdio: 'inherit' });

process.exit(result.status === null ? 1 : result.status);
'@

npx -y -p prettier@3.2.5 -p prettier-plugin-java@2.6.5 node -e $javaScript
