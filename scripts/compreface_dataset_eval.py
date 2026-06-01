"""
Enroll and evaluate a folder-based face dataset with CompreFace.

Default mode is a dry run. Pass --apply to create subjects and upload images.
The script supports both:
  1. Flat cropped folder: "Name_0.jpg", "Name_1.jpg"
  2. Directory per subject: "Name/img1.jpg"
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

from compreface_smoke_test import (
    DEFAULT_API_KEY,
    DEFAULT_BASE_URL,
    CompreFaceSmokeError,
    configure_console_encoding,
    create_subject,
    list_subjects,
    recognize_image,
    request_json,
    upload_image,
)


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def subject_slug(name: str, prefix: str) -> str:
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", normalized).strip("_").lower()
    return f"{prefix}{normalized}"


def name_from_flat_file(path: Path) -> str:
    return re.sub(r"_\d+$", "", path.stem).strip()


def discover_flat_dataset(root: Path) -> dict[str, list[Path]]:
    groups: dict[str, list[Path]] = defaultdict(list)
    for image in sorted(root.iterdir()):
        if image.is_file() and image.suffix.lower() in IMAGE_EXTENSIONS:
            groups[name_from_flat_file(image)].append(image)
    return dict(groups)


def discover_directory_dataset(root: Path) -> dict[str, list[Path]]:
    groups: dict[str, list[Path]] = {}
    for subject_dir in sorted(child for child in root.iterdir() if child.is_dir()):
        images = sorted(
            child
            for child in subject_dir.iterdir()
            if child.is_file() and child.suffix.lower() in IMAGE_EXTENSIONS
        )
        if images:
            groups[subject_dir.name] = images
    return groups


def discover_dataset(root: Path) -> dict[str, list[Path]]:
    if not root.exists():
        raise CompreFaceSmokeError(f"Dataset path does not exist: {root}")

    if root.is_file():
        raise CompreFaceSmokeError(f"Dataset path must be a folder: {root}")

    flat = discover_flat_dataset(root)
    if flat:
        return flat

    by_dir = discover_directory_dataset(root)
    if by_dir:
        return by_dir

    raise CompreFaceSmokeError(f"No supported images found in: {root}")


def recognize_for_result(base_url: str, api_key: str, image_path: Path, threshold: float) -> tuple[str | None, float, str]:
    url = f"{base_url.rstrip('/')}/api/v1/recognition/recognize?prediction_count=1"
    mime_type = "image/jpeg"
    with image_path.open("rb") as image_file:
        _, body = request_json(
            "POST",
            url,
            api_key,
            files={"file": (image_path.name, image_file, mime_type)},
        )

    results = body.get("result", []) if isinstance(body, dict) else []
    if not results:
        return None, 0.0, "NO_FACE"

    subjects = results[0].get("subjects", [])
    if not subjects:
        return None, 0.0, "UNKNOWN"

    best = subjects[0]
    subject = best.get("subject")
    similarity = float(best.get("similarity", 0.0))
    result_type = "MATCH" if similarity >= threshold else "LOW_CONFIDENCE"
    return subject, similarity, result_type


def print_plan(groups: dict[str, list[Path]], args: argparse.Namespace) -> list[tuple[str, str, list[Path], list[Path]]]:
    selected = sorted(groups.items(), key=lambda item: (-len(item[1]), item[0]))[: args.max_subjects]
    plan = []

    print(f"[INFO] Dataset subjects found: {len(groups)}")
    print(f"[INFO] Planning first {len(selected)} subject(s)")

    for name, images in selected:
        subject = subject_slug(name, args.subject_prefix)
        enroll_images = images[: args.enroll_per_subject]
        test_images = images[args.enroll_per_subject : args.enroll_per_subject + args.test_per_subject]
        plan.append((name, subject, enroll_images, test_images))
        print(
            f"  - {name} -> {subject}: "
            f"total={len(images)} enroll={len(enroll_images)} test={len(test_images)}"
        )

    return plan


def apply_plan(plan: list[tuple[str, str, list[Path], list[Path]]], args: argparse.Namespace) -> None:
    list_subjects(args.base_url, args.api_key)

    total_tests = 0
    correct = 0

    for name, subject, enroll_images, test_images in plan:
        print(f"\n[SUBJECT] {name} -> {subject}")
        if args.evaluate_only:
            print("[INFO] Evaluate-only mode: skipping subject creation and image upload")
        else:
            create_subject(args.base_url, args.api_key, subject)

            uploaded = 0
            for image in enroll_images:
                try:
                    upload_image(args.base_url, args.api_key, subject, image, args.det_prob_threshold)
                    uploaded += 1
                except CompreFaceSmokeError as exc:
                    print(f"[WARN] Upload skipped for {image}: {exc}")

            print(f"[INFO] Uploaded {uploaded}/{len(enroll_images)} enroll image(s)")

        for image in test_images:
            total_tests += 1
            try:
                predicted_subject, similarity, result_type = recognize_for_result(
                    args.base_url,
                    args.api_key,
                    image,
                    args.threshold,
                )
            except CompreFaceSmokeError as exc:
                print(f"[WARN] Recognition failed for {image}: {exc}")
                continue

            is_correct = predicted_subject == subject and result_type == "MATCH"
            correct += 1 if is_correct else 0
            verdict = "PASS" if is_correct else "FAIL"
            print(
                f"[TEST] {verdict} expected={subject} predicted={predicted_subject} "
                f"similarity={similarity:.4f} type={result_type} image={image.name}"
            )

    if total_tests:
        print(f"\n[SUMMARY] Correct {correct}/{total_tests} ({correct / total_tests:.1%})")
    else:
        print("\n[SUMMARY] No test images selected.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch-enroll a sample of a face dataset into CompreFace.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("archive") / "Faces" / "Faces",
        help="Dataset image folder. Default: archive/Faces/Faces",
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--api-key", default=DEFAULT_API_KEY)
    parser.add_argument("--subject-prefix", default="kaggle_")
    parser.add_argument("--max-subjects", type=int, default=3)
    parser.add_argument("--enroll-per-subject", type=int, default=5)
    parser.add_argument("--test-per-subject", type=int, default=2)
    parser.add_argument("--threshold", type=float, default=0.97)
    parser.add_argument("--det-prob-threshold", type=float)
    parser.add_argument("--apply", action="store_true", help="Actually create subjects, upload, and evaluate.")
    parser.add_argument(
        "--evaluate-only",
        action="store_true",
        help="With --apply, skip creation/upload and only recognize selected test images.",
    )
    return parser.parse_args()


def main() -> int:
    configure_console_encoding()
    args = parse_args()

    try:
        groups = discover_dataset(args.dataset)
        plan = print_plan(groups, args)

        if not args.apply:
            print("\n[DRY-RUN] Add --apply to create subjects, upload images, and run recognition tests.")
            return 0

        apply_plan(plan, args)
    except CompreFaceSmokeError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
