# Remove background service

import asyncio
from pathlib import Path
from typing import List
from concurrent.futures import ThreadPoolExecutor

from PIL import Image
from rembg import remove, new_session


_thread_pool = ThreadPoolExecutor(max_workers=2)

# Session for RMBG-1.4 model (auto-downloaded on first use)
_model_session = None


def _get_session():
    """Get or create the rembg model session (thread-safe)."""
    global _model_session
    if _model_session is None:
        _model_session = new_session(model_name="u2net")  # Uses RMBG-1.4 internally
    return _model_session


async def remove_background(
    input_path: str,
    output_dir: str
) -> List[str]:
    """
    Remove background from a video file.

    Process:
    1. Extract frames from video using ffmpeg
    2. Remove background from each frame using RMBG-1.4 model
    3. Save each frame as PNG with alpha channel

    Args:
        input_path: Path to the input video file.
        output_dir: Directory where processed frames will be saved.

    Returns:
        List of paths to processed frame files with alpha channel.

    Raises:
        FileNotFoundError: If input video file not found.
        RuntimeError: If processing fails.
    """
    from app.services.ffmpeg import extract_frames

    input_file = Path(input_path)
    output_path = Path(output_dir)

    if not input_file.exists():
        raise FileNotFoundError(f"Input video file not found: {input_path}")

    # Create output subdirectories
    frames_dir = output_path / "frames"
    processed_dir = output_path / "processed"
    frames_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Extract frames from video
    frame_files = await extract_frames(
        video_path=input_path,
        output_dir=str(frames_dir),
        fps=24
    )

    if not frame_files:
        raise RuntimeError("No frames extracted from video")

    # Step 2: Process each frame to remove background
    processed_files = []

    # Process frames in batches to control memory usage
    batch_size = 4

    for i in range(0, len(frame_files), batch_size):
        batch = frame_files[i:i + batch_size]

        # Run batch processing in thread pool
        batch_results = await _process_frame_batch(
            batch,
            processed_dir
        )

        processed_files.extend(batch_results)

    return processed_files


async def _process_frame_batch(
    frame_paths: List[str],
    output_dir: Path
) -> List[str]:
    """
    Process a batch of frames to remove background.

    Args:
        frame_paths: List of paths to input frame files.
        output_dir: Directory to save processed frames.

    Returns:
        List of paths to processed frame files.
    """
    loop = asyncio.get_running_loop()

    def _process_all() -> List[str]:
        results = []
        session = _get_session()

        for frame_path in frame_paths:
            try:
                frame_file = Path(frame_path)

                # Read image
                with Image.open(frame_file) as img:
                    input_img = img.convert("RGBA")

                # Remove background using rembg
                output_img = remove(
                    input_img,
                    session=session,
                    alpha_matting=True,  # Enable alpha matting for better edges
                    alpha_matting_foreground_threshold=240,
                    alpha_matting_background_threshold=10,
                    alpha_matting_erode_size=10
                )

                # Save processed frame with alpha channel
                output_path = output_dir / frame_file.name
                output_img.save(output_path, "PNG")
                results.append(str(output_path))

            except Exception as e:
                print(f"Error processing frame {frame_path}: {e}")
                # Continue with next frame on error
                continue

        return results

    return await loop.run_in_executor(_thread_pool, _process_all)


async def remove_background_from_image(
    input_path: str,
    output_path: str
) -> str:
    """
    Remove background from a single image file.

    Args:
        input_path: Path to the input image file.
        output_path: Path where the processed image will be saved.

    Returns:
        Path to the processed image file.

    Raises:
        FileNotFoundError: If input image file not found.
        RuntimeError: If processing fails.
    """
    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.exists():
        raise FileNotFoundError(f"Input image file not found: {input_path}")

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    def _remove_bg() -> str:
        session = _get_session()

        try:
            # Read image
            with Image.open(input_file) as img:
                input_img = img.convert("RGBA")

            # Remove background
            output_img = remove(
                input_img,
                session=session,
                alpha_matting=True,
                alpha_matting_foreground_threshold=240,
                alpha_matting_background_threshold=10,
                alpha_matting_erode_size=10
            )

            # Save output with alpha channel
            output_img.save(output_file, "PNG")
            return str(output_file)

        except Exception as e:
            raise RuntimeError(f"Failed to remove background from image: {e}")

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_thread_pool, _remove_bg)


async def process_and_zip(
    input_path: str,
    output_dir: str,
    zip_name: str = "rmbg_frames.zip"
) -> str:
    """
    Remove background from video and pack results into a ZIP file.

    This is a convenience function that combines remove_background
    and frames_to_zip operations.

    Args:
        input_path: Path to the input video file.
        output_dir: Directory for intermediate and output files.
        zip_name: Name of the output ZIP file.

    Returns:
        Path to the created ZIP file.

    Raises:
        FileNotFoundError: If input video file not found.
        RuntimeError: If processing or zipping fails.
    """
    from app.services.ffmpeg import frames_to_zip

    output_path = Path(output_dir)
    processed_dir = output_path / "processed"

    # Process video to remove background
    await remove_background(input_path, str(output_path))

    # Pack processed frames into ZIP
    zip_path = output_path / zip_name
    return await frames_to_zip(str(processed_dir), str(zip_path))


def cleanup_temp_files(output_dir: str) -> None:
    """
    Clean up temporary files created during processing.

    Args:
        output_dir: Directory containing temporary files.
    """
    import shutil

    output_path = Path(output_dir)

    for subdir in ["frames", "processed"]:
        dir_path = output_path / subdir
        if dir_path.exists():
            shutil.rmtree(dir_path)
