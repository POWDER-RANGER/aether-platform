# Read-only workstation inventory

Run from the repository root on the MSI:

\`\`\`powershell
powershell -ExecutionPolicy Bypass -File scripts/workstation/Test-Workstation.ps1
\`\`\`

The extended report writes \`evidence/workstation/<timestamp>.json\` and records ViGEmBus/HidHide driver presence and file version, nvidia-smi/GPU driver/free VRAM, Ollama API reachability and installed model tags, Tesseract availability, DXcam import availability, and free space on the repository drive.

This script is read-only. It does not install, update, enable, disable, hide, remove, or reconfigure drivers or software. Missing optional tools are reported as NOT_FOUND/UNREACHABLE. Script execution and all hardware observations remain UNVERIFIED until the owner runs it on the target workstation.
