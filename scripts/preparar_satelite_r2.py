import json
import os
import shutil
import urllib.request
from pathlib import Path
from copy import deepcopy

PRODUCT_ID = "TOP_C13_ARG_ALTA"
INPUT_MANIFEST = Path("docs/manifiesto.json")
OUTPUT_DIR = Path(".r2/satellite") / PRODUCT_ID
OUTPUT_MANIFEST = Path(".r2/satellite-manifiesto.json")

MEDIA_BASE_URL = os.environ.get(
    "SATELLITE_MEDIA_BASE_URL",
    f"https://media.weathervar.com/satellite/{PRODUCT_ID}"
).rstrip("/")


def download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "WeatherVar/1.0"
        },
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        with destination.open("wb") as output:
            shutil.copyfileobj(response, output)


def main() -> None:
    if not INPUT_MANIFEST.exists():
        raise FileNotFoundError(f"No existe {INPUT_MANIFEST}")

    manifest = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))

    source_frames = manifest.get("animation_frames") or manifest.get("frames") or []
    selected_frames = source_frames[-12:]

    if not selected_frames:
        raise RuntimeError("El manifiesto no contiene imágenes satelitales.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rewritten_frames = []

    for frame in selected_frames:
        original_url = frame.get("url")
        filename = frame.get("filename")

        if not original_url or not filename:
            raise RuntimeError(f"Frame incompleto: {frame}")

        local_file = OUTPUT_DIR / filename
        print(f"Descargando {original_url}")
        download_file(original_url, local_file)

        new_frame = deepcopy(frame)
        new_frame["url"] = f"{MEDIA_BASE_URL}/{filename}"
        rewritten_frames.append(new_frame)

    output_manifest = deepcopy(manifest)

    output_manifest["storage"] = {
        "mode": "cloudflare_r2_media",
        "stored_image_count": len(rewritten_frames),
        "media_base_url": MEDIA_BASE_URL,
        "bucket_hint": "weathervar-media"
    }

    output_manifest["counts"] = output_manifest.get("counts", {})
    output_manifest["counts"]["frames"] = len(rewritten_frames)
    output_manifest["counts"]["animation_frames"] = len(rewritten_frames)

    output_manifest["frames"] = rewritten_frames
    output_manifest["animation_frames"] = rewritten_frames
    output_manifest["latest"] = rewritten_frames[-1]

    OUTPUT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MANIFEST.write_text(
        json.dumps(output_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"Manifiesto R2 generado en {OUTPUT_MANIFEST}")
    print(f"Imágenes preparadas en {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
