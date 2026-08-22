# Fascinator v0.6R cleanup helper
# Run from E:\Utopia if you want to remove obsolete module-style files.
# This script does NOT delete your knowledge graph, pending writes, runtime state, llm logs, or snapshots.

$files = @(
  "backend\data\companion_profile.json",
  "backend\data\self_state.json",
  "backend\data\self_graph_seed.json",
  "backend\data\interaction_history.json",
  "backend\data\feedback_log.json",
  "README_UPDATE_v06.md",
  "README_UPDATE_v061.md",
  "README_UPDATE_v062.md"
)

foreach ($f in $files) {
  if (Test-Path $f) {
    Remove-Item $f -Force
    Write-Host "Deleted $f"
  }
}

if (Test-Path "backend\__pycache__") {
  Remove-Item "backend\__pycache__" -Recurse -Force
  Write-Host "Deleted backend\__pycache__"
}

Write-Host "Cleanup complete. Preserved graph/runtime/pending/snapshots."
