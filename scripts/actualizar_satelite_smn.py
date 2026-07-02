#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Publica un manifiesto de imágenes satelitales oficiales del SMN.

No descarga ni almacena imágenes en GitHub. Únicamente publica las URLs
oficiales de los cuadros más recientes.

Salida:
    docs/manifiesto.json
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import requests


PRODUCT_ID = "TOP_C13_ARG_ALTA"
PRODUCT_NAME = "Topes Nubosos"
REGION_NAME = "Argentina"

TOKEN_PAGES = (
    "https://ws2.smn.gob.ar/pronostico",
    "https://www.smn.gob.ar/satelite",
    "https://ws2.smn.gob.ar/satelite",
)

CATALOG_URL = (
    "https://ws1.smn.gob.ar/v1/images/satellite/"
    f"{PRODUCT_ID}"
)
STATIC_BASE_URL = "https://estaticos.smn.gob.ar/vmsr/satelite/"

OUTPUT_PATH = Path("docs/manifiesto.json")
MAX_FRAMES = 24
ANIMATION_FRAMES = 12
TIMEOUT_SECONDS = 35

ARGENTINA_TZ = ZoneInfo("America/Argentina/Buenos_Aires")

BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "es-AR,es;q=0.9",
}

FILENAME_RE = re.compile(
    rf"^{re.escape(PRODUCT_ID)}_(\d{{8}})_(\d{{6}})Z\."
    r"(?:jpg|jpeg|png|webp)$",
    re.IGNORECASE,
)


class TokenRejected(RuntimeError):
    """El endpoint rechazó el JWT temporal."""


def now_argentina() -> str:
    return datetime.now(ARGENTINA_TZ).isoformat(timespec="seconds")


def read_existing() -> dict[str, Any] | None:
    if not OUTPUT_PATH.exists():
        return None
    try:
        value = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def extract_token(html: str) -> str | None:
    patterns = (
        r"localStorage\.setItem\(\s*[\"']token[\"']\s*,\s*[\"']([^\"']+)[\"']\s*\)",
        r"localStorage\.setItem\(\s*`token`\s*,\s*`([^`]+)`\s*\)",
        r"[\"']token[\"']\s*:\s*[\"']([^\"']+)[\"']",
        r"[\"']jwt[\"']\s*:\s*[\"']([^\"']+)[\"']",
        r"(eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)",
    )
    for pattern in patterns:
        match = re.search(pattern, html)
        if not match:
            continue
        token = match.group(1).strip()
        if token.count(".") == 2 and len(token) > 40:
            return token
    return None


def obtain_token(session: requests.Session) -> str:
    errors: list[str] = []

    for page_url in TOKEN_PAGES:
        try:
            response = session.get(
                page_url,
                headers={
                    **BASE_HEADERS,
                    "Accept": "text/html,application/xhtml+xml",
                },
                timeout=TIMEOUT_SECONDS,
            )
            response.raise_for_status()

            token = extract_token(response.text)
            if token:
                print(f"Token temporal obtenido desde {page_url}")
                return token

            errors.append(f"{page_url}: no se encontró token")
        except requests.RequestException as exc:
            errors.append(f"{page_url}: {exc}")

    raise RuntimeError(
        "No se pudo obtener el token temporal del SMN. "
        + " | ".join(errors)
    )


def api_headers(token: str) -> dict[str, str]:
    return {
        **BASE_HEADERS,
        "Accept": "application/json",
        "Authorization": f"JWT {token}",
        "Origin": "https://www.smn.gob.ar",
        "Referer": "https://www.smn.gob.ar/satelite",
    }


def request_catalog(
    session: requests.Session,
    token: str,
) -> Any:
    response = session.get(
        CATALOG_URL,
        headers=api_headers(token),
        timeout=TIMEOUT_SECONDS,
    )

    if response.status_code in (401, 403):
        raise TokenRejected(
            "El endpoint de imágenes satelitales rechazó el token."
        )

    response.raise_for_status()

    try:
        return response.json()
    except ValueError as exc:
        raise RuntimeError(
            "El catálogo satelital no devolvió JSON válido."
        ) from exc


def find_catalog_object(data: Any) -> dict[str, Any]:
    if isinstance(data, dict):
        if isinstance(data.get("list"), list):
            return data

        for key in ("data", "result", "results", "items"):
            child = data.get(key)

            if isinstance(child, dict) and isinstance(
                child.get("list"),
                list,
            ):
                return child

            if isinstance(child, list):
                for item in child:
                    if (
                        isinstance(item, dict)
                        and isinstance(item.get("list"), list)
                    ):
                        return item

    if isinstance(data, list):
        for item in data:
            if (
                isinstance(item, dict)
                and isinstance(item.get("list"), list)
            ):
                return item

    raise RuntimeError(
        "La respuesta satelital tiene una estructura desconocida."
    )


def parse_frame(filename: str) -> dict[str, Any] | None:
    filename = filename.strip()
    match = FILENAME_RE.match(filename)
    if not match:
        return None

    date_part, time_part = match.groups()

    try:
        utc_dt = datetime.strptime(
            date_part + time_part,
            "%Y%m%d%H%M%S",
        ).replace(tzinfo=timezone.utc)
    except ValueError:
        return None

    local_dt = utc_dt.astimezone(ARGENTINA_TZ)

    return {
        "filename": filename,
        "url": STATIC_BASE_URL + filename,
        "timestamp_utc": (
            utc_dt.isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        ),
        "timestamp_argentina": local_dt.isoformat(
            timespec="seconds"
        ),
        "date_argentina": local_dt.strftime("%Y-%m-%d"),
        "time_argentina": local_dt.strftime("%H:%M:%S"),
    }


def build_manifest(data: Any) -> dict[str, Any]:
    catalog = find_catalog_object(data)
    raw_list = catalog.get("list")

    if not isinstance(raw_list, list):
        raise RuntimeError(
            "El catálogo no contiene una lista válida de imágenes."
        )

    frames_by_name: dict[str, dict[str, Any]] = {}

    for raw_item in raw_list:
        if not isinstance(raw_item, str):
            continue

        frame = parse_frame(raw_item)
        if frame is not None:
            frames_by_name[frame["filename"]] = frame

    frames = sorted(
        frames_by_name.values(),
        key=lambda item: item["timestamp_utc"],
    )[-MAX_FRAMES:]

    if not frames:
        raise RuntimeError(
            "El catálogo no contiene imágenes reconocibles "
            f"para {PRODUCT_ID}."
        )

    animation_frames = frames[-ANIMATION_FRAMES:]
    generated_at = now_argentina()

    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "last_success_at": generated_at,
        "enabled": True,
        "status": "ok",
        "source": {
            "name": "Servicio Meteorológico Nacional",
            "product_id": str(catalog.get("id") or PRODUCT_ID),
            "product": str(catalog.get("product") or PRODUCT_NAME),
            "region": str(catalog.get("region") or REGION_NAME),
            "catalog_endpoint": CATALOG_URL,
            "static_base_url": STATIC_BASE_URL,
        },
        "storage": {
            "mode": "remote_urls_only",
            "stored_image_count": 0,
        },
        "counts": {
            "frames": len(frames),
            "animation_frames": len(animation_frames),
        },
        "latest": frames[-1],
        "animation_frames": animation_frames,
        "frames": frames,
    }


def frame_names(value: dict[str, Any] | None) -> list[str]:
    if not value:
        return []

    frames = value.get("frames")
    if not isinstance(frames, list):
        return []

    return [
        str(frame.get("filename"))
        for frame in frames
        if isinstance(frame, dict) and frame.get("filename")
    ]


def preserve_previous_on_error(message: str) -> int:
    previous = read_existing()

    if previous and previous.get("frames"):
        stale = dict(previous)
        stale["generated_at"] = now_argentina()
        stale["status"] = "stale"
        stale["last_error"] = message
        write_json_atomic(OUTPUT_PATH, stale)

        print(
            "No se pudo renovar el catálogo. "
            "Se conserva el último manifiesto válido."
        )
        print(f"Motivo: {message}")
        return 1

    initial = {
        "schema_version": 1,
        "generated_at": now_argentina(),
        "last_success_at": None,
        "enabled": True,
        "status": "error",
        "source": {
            "name": "Servicio Meteorológico Nacional",
            "product_id": PRODUCT_ID,
            "product": PRODUCT_NAME,
            "region": REGION_NAME,
            "catalog_endpoint": CATALOG_URL,
            "static_base_url": STATIC_BASE_URL,
        },
        "storage": {
            "mode": "remote_urls_only",
            "stored_image_count": 0,
        },
        "counts": {
            "frames": 0,
            "animation_frames": 0,
        },
        "latest": None,
        "animation_frames": [],
        "frames": [],
        "last_error": message,
    }
    write_json_atomic(OUTPUT_PATH, initial)
    print(f"No se pudo crear el catálogo satelital: {message}")
    return 1


def main() -> int:
    session = requests.Session()

    try:
        token = obtain_token(session)

        try:
            response_data = request_catalog(session, token)
        except TokenRejected:
            print("El primer token fue rechazado. Se solicita otro.")
            token = obtain_token(session)
            response_data = request_catalog(session, token)

        manifest = build_manifest(response_data)
        previous = read_existing()

        if frame_names(previous) == frame_names(manifest):
            print(
                "El SMN todavía no publicó un cuadro nuevo. "
                "No se modifica el manifiesto."
            )
            return 0

        write_json_atomic(OUTPUT_PATH, manifest)

        latest = manifest["latest"]
        print(
            "Satélite actualizado correctamente: "
            f"{manifest['counts']['frames']} cuadros disponibles."
        )
        print(
            "Último cuadro: "
            f"{latest['filename']} "
            f"({latest['timestamp_argentina']})"
        )
        print(
            "No se almacenaron imágenes en GitHub; "
            "solo se publicaron URLs oficiales."
        )
        return 0

    except Exception as exc:
        return preserve_previous_on_error(str(exc))


if __name__ == "__main__":
    sys.exit(main())
