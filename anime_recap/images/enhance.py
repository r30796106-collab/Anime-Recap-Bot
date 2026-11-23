"""Optional anime image upscaling through Real-ESRGAN NCNN CLI."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def enhance_image(image: str | Path, output: str | Path, *, executable: str = "realesrgan-ncnn-vulkan", model: str = "realesr-animevideov3", scale: int = 2, timeout: int = 300) -> Path:
    """Upscale one image using an installed Real-ESRGAN NCNN/Vulkan executable."""
    source = Path(image)
    target = Path(output)
    if not source.is_file() or source.stat().st_size == 0:
        raise ValueError(f"Input image is missing or empty: {source}")
    if scale not in (2, 3, 4):
        raise ValueError("Scale must be 2, 3 or 4")
    binary = shutil.which(executable)
    if not binary:
        raise FileNotFoundError(f"Upscaler executable not found: {executable}")
    target.parent.mkdir(parents=True, exist_ok=True)
    command = [binary, "-i", str(source), "-o", str(target), "-n", model, "-s", str(scale)]
    subprocess.run(command, check=True, timeout=timeout, capture_output=True, text=True)
    if not target.is_file() or target.stat().st_size == 0:
        raise RuntimeError("Upscaler completed without a valid output file")
    return target


def enhance_images(image_paths: list[str | Path], output_dir: str | Path, *, executable: str = "realesrgan-ncnn-vulkan", model: str = "realesr-animevideov3", scale: int = 2) -> list[Path]:
    """Batch enhance images, preserving filenames."""
    if not image_paths:
        return []
    destination = Path(output_dir)
    outputs = []
    for source in image_paths:
        source = Path(source)
        outputs.append(enhance_image(source, destination / source.name, executable=executable, model=model, scale=scale))
    return outputs
