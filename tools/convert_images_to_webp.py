#!/usr/bin/env python3
"""Batch convert images to WebP and normalize filenames.

Examples:
  python tools/convert_images_to_webp.py "D:\\images"
  python tools/convert_images_to_webp.py "D:\\images" --output-dir "D:\\out" --name-style kebab
  python tools/convert_images_to_webp.py "D:\\images" --name-style pascal --lossless
  python tools/convert_images_to_webp.py "D:\\images" --dry-run
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path


SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert images to WebP and normalize file names.",
    )
    parser.add_argument("input_dir", help="Directory containing source images.")
    parser.add_argument(
        "--output-dir",
        help="Directory for converted files. Defaults to the input directory.",
    )
    parser.add_argument(
        "--name-style",
        choices=("kebab", "snake", "pascal", "keep"),
        default="kebab",
        help="Filename normalization style for the output files.",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=88,
        help="WebP quality for lossy conversion. Range: 0-100. Default: 88.",
    )
    parser.add_argument(
        "--lossless",
        action="store_true",
        help="Use lossless WebP encoding.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        default=True,
        help="Recursively scan subdirectories. Enabled by default.",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_false",
        dest="recursive",
        help="Only scan the top-level input directory.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files if present.",
    )
    parser.add_argument(
        "--ascii-only",
        action="store_true",
        help="Strip non-ASCII characters from normalized file names.",
    )
    parser.add_argument(
        "--preserve-structure",
        action="store_true",
        help="Keep relative subdirectory structure under the output directory.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned operations without converting files.",
    )
    return parser


def normalize_name(stem: str, style: str, ascii_only: bool) -> str:
    value = unicodedata.normalize("NFKD", stem).strip()
    if ascii_only:
        value = value.encode("ascii", "ignore").decode("ascii")

    value = re.sub(r"[^\w\s-]", " ", value, flags=re.UNICODE)
    value = re.sub(r"[_\s-]+", " ", value, flags=re.UNICODE).strip()

    if not value:
        return "image"

    parts = [part for part in value.split(" ") if part]
    if not parts:
        return "image"

    if style == "keep":
        return stem.strip() or "image"
    if style == "snake":
        return "_".join(part.lower() for part in parts)
    if style == "pascal":
        return "".join(part[:1].upper() + part[1:] for part in parts)
    return "-".join(part.lower() for part in parts)


def iter_source_files(input_dir: Path, recursive: bool) -> list[Path]:
    pattern = "**/*" if recursive else "*"
    return sorted(
        path
        for path in input_dir.glob(pattern)
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def unique_target_path(target_path: Path, overwrite: bool) -> Path:
    if overwrite or not target_path.exists():
        return target_path

    counter = 2
    while True:
        candidate = target_path.with_name(f"{target_path.stem}-{counter}{target_path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def build_target_path(
    source_path: Path,
    input_dir: Path,
    output_dir: Path,
    style: str,
    ascii_only: bool,
    preserve_structure: bool,
    overwrite: bool,
) -> Path:
    normalized_name = normalize_name(source_path.stem, style, ascii_only)

    if preserve_structure:
        relative_parent = source_path.relative_to(input_dir).parent
        target_dir = output_dir / relative_parent
    else:
        target_dir = output_dir

    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{normalized_name}.webp"
    return unique_target_path(target_path, overwrite)


def convert_to_webp(
    source_path: Path,
    target_path: Path,
    quality: int,
    lossless: bool,
) -> None:
    command = [
        shutil.which("ffmpeg") or "ffmpeg",
        "-y",
        "-i",
        str(source_path),
        "-vframes",
        "1",
    ]

    if lossless:
        command += ["-c:v", "libwebp", "-lossless", "1"]
    else:
        command += ["-c:v", "libwebp", "-quality", str(quality)]

    command += [str(target_path)]

    completed = subprocess.run(
        command,
        capture_output=True,
        check=False,
    )

    if completed.returncode != 0:
        stderr_output = decode_process_output(completed.stderr)
        raise RuntimeError(
            f"ffmpeg failed for {source_path} -> {target_path}\n{stderr_output.strip()}",
        )


def decode_process_output(output: bytes | None) -> str:
    if not output:
        return ""

    for encoding in ("utf-8", "gb18030", sys.getdefaultencoding()):
        try:
            return output.decode(encoding)
        except UnicodeDecodeError:
            continue

    return output.decode("utf-8", errors="replace")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        print("ffmpeg was not found in PATH.", file=sys.stderr)
        return 1

    if args.quality < 0 or args.quality > 100:
        print("--quality must be between 0 and 100.", file=sys.stderr)
        return 1

    input_dir = Path(args.input_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else input_dir

    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Input directory does not exist: {input_dir}", file=sys.stderr)
        return 1

    source_files = iter_source_files(input_dir, args.recursive)
    if not source_files:
        print(f"No supported images found in {input_dir}")
        return 0

    failures = 0
    print(f"Using ffmpeg: {ffmpeg_path}")
    print(f"Found {len(source_files)} source image(s).")

    for source_path in source_files:
        target_path = build_target_path(
            source_path=source_path,
            input_dir=input_dir,
            output_dir=output_dir,
            style=args.name_style,
            ascii_only=args.ascii_only,
            preserve_structure=args.preserve_structure,
            overwrite=args.overwrite,
        )
        relative_source = source_path.relative_to(input_dir)
        relative_target = target_path.relative_to(output_dir)
        print(f"{relative_source} -> {relative_target}")

        if args.dry_run:
            continue

        try:
            convert_to_webp(
                source_path=source_path,
                target_path=target_path,
                quality=args.quality,
                lossless=args.lossless,
            )
        except RuntimeError as error:
            failures += 1
            print(str(error), file=sys.stderr)

    if args.dry_run:
        print("Dry run completed.")
        return 0

    if failures:
        print(f"Completed with {failures} failure(s).", file=sys.stderr)
        return 2

    print("Conversion completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
