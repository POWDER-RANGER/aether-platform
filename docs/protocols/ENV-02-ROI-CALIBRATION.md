# ENV-02 ROI calibration

Open \`http://127.0.0.1:<configured-port>/calibrate\` while the read-only Command Center is running. Load a frame by run ID and JPEG filename or choose a local image. Drag a rectangle, name the ROI, and save it to the page's in-memory list. The page displays normalized coordinates and exports a YAML snippet under \`perception.rois\`.

The page does not write \`configuration/platform/ENV-02.yaml\`. Review the coordinates and paste the snippet manually. A calibration image is only an input to the offline reader probe; it is not automatically a live or ground-truth fact.

Offline probe:

\`\`\`powershell
python -m aether.cli_ext probe-reader <image-path> --roi 0.1,0.2,0.8,0.3 --reader bar --rgb 220,220,220
\`\`\`

Use an owner-controlled capture and preserve its provenance. The example coordinates and RGB values above are syntax examples only, not calibration values.
