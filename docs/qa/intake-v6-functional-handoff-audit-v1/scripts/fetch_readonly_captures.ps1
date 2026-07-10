# Read-only GET captures for Intake V6 functional handoff audit.
# Usage: .\fetch_readonly_captures.ps1
$ErrorActionPreference = "Stop"
$ws = "22ef834d-f2d0-453b-a7a7-118928c98a39"
$base = "http://127.0.0.1:8000/api/v1"
$dir = Join-Path $PSScriptRoot "..\captures"
New-Item -ItemType Directory -Force -Path $dir | Out-Null

function Save-Json($name, $url) {
  $resp = Invoke-RestMethod -Uri $url -Method GET -TimeoutSec 60
  ($resp | ConvertTo-Json -Depth 30) | Out-File -Encoding utf8 (Join-Path $dir "$name.json")
  Write-Host "saved $name"
}

Save-Json "workspace" "$base/intake-v6/workspaces/$ws"
$tpl = (Get-Content (Join-Path $dir "workspace.json") -Raw | ConvertFrom-Json).template_code
Save-Json "template_form_contract" "$base/intake-v6/workspaces/$ws/template-form-contract"
Save-Json "runtime_capture" "$base/intake-v6/workspaces/$ws/runtime-capture-read-model"
Save-Json "quote_handoff" "$base/intake-v6/workspaces/$ws/quote-handoff-preview"
Save-Json "pricing_input" "$base/intake-v6/workspaces/$ws/pricing-input-preview"
Save-Json "product_binding" "$base/intake-v6/workspaces/$ws/product-system-binding"
Save-Json "linked_segments" "$base/intake-v6/workspaces/$ws/linked-template-segments"
Save-Json "form_contract" "$base/intake-v6/form-contract/$tpl"
Save-Json "product_definition" "$base/product-system/product-definition/${tpl}?workspace_id=$ws"
Save-Json "product_aggregate" "$base/product-system/aggregate/$tpl"
Save-Json "material_breakdown" "$base/intake-v6/workspaces/$ws/material-breakdown"
Write-Host "template=$tpl captures=11"
