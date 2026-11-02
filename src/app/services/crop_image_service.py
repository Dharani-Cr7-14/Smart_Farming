import re
from pathlib import Path


DATASET_DIR = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "raw"
    / "PlantVillage-Dataset-master"
    / "raw"
    / "color"
)
STATIC_IMAGE_DIR = Path(__file__).resolve().parents[1] / "static" / "images"

# Curated real crop photos cover crops that are not included in PlantVillage.
CURATED_IMAGES = {
    "jute": STATIC_IMAGE_DIR / "jute.jpg",
}


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def find_crop_image(crop_name: str) -> Path | None:
    """Find a real crop photo from curated assets or the PlantVillage dataset."""
    if not crop_name:
        return None

    target = _normalize(crop_name)
    curated_image = CURATED_IMAGES.get(target)
    if curated_image and curated_image.is_file():
        return curated_image

    if not DATASET_DIR.is_dir():
        return None

    candidates = []
    for directory in DATASET_DIR.iterdir():
        if not directory.is_dir():
            continue
        dataset_crop = directory.name.split("___", 1)[0]
        if _normalize(dataset_crop) != target:
            continue
        candidates.append(directory)

    candidates.sort(key=lambda path: ("healthy" not in path.name.lower(), path.name))
    for directory in candidates:
        images = sorted(
            path for path in directory.iterdir()
            if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
        )
        if images:
            return images[0]
    return None
