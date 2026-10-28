from __future__ import annotations

import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw


def redact_run(run_dir, output_dir, boxes):
    source, output = Path(run_dir).resolve(), Path(output_dir).resolve()
    if not source.is_dir() or source == output or source in output.parents:
        raise ValueError("output must be outside source run")
    for box in boxes:
        if len(box) != 4 or not (0 <= box[0] < box[2] <= 1 and 0 <= box[1] < box[3] <= 1):
            raise ValueError(f"invalid normalized ROI: {box}")
    if output.exists():
        raise FileExistsError(output)
    shutil.copytree(source, output)
    frame_dir = output / "frames"
    if frame_dir.is_dir():
        for path in frame_dir.iterdir():
            if path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
                continue
            with Image.open(path) as image:
                image = image.convert("RGB")
                draw = ImageDraw.Draw(image)
                for x0, y0, x1, y1 in boxes:
                    draw.rectangle((round(x0 * image.width), round(y0 * image.height),
                                    round(x1 * image.width), round(y1 * image.height)), fill=(0, 0, 0))
                image.save(path, quality=95)
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    manifest["redaction"] = {
        "redacted": True,
        "frame_pixels_blacked": True,
        "source_run_id": manifest.get("identity", {}).get("run_id", source.name),
        "boxes_normalized": [list(box) for box in boxes],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return output


def assert_shareable(run_dir, for_sharing=False):
    if not for_sharing:
        return
    try:
        manifest = json.loads((Path(run_dir) / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("cannot share without a valid manifest") from exc
    redaction = manifest.get("redaction", {})
    if not redaction.get("redacted") or not redaction.get("frame_pixels_blacked"):
        raise ValueError("sharing refused: run contains unredacted frames")
