import subprocess
import uuid
from pathlib import Path


def combine_mp3_files_for_podcast(
    mp3_files: list[str], output_filename: str = "podcast.mp3", output_dir: str = "podcasts"
) -> str:
    """Combines a list of MP3 audio files into a single MP3 podcast file using ffmpeg.

    This function requires ffmpeg to be installed and accessible in the system's PATH.
    It creates a temporary file list for ffmpeg's concat demuxer.

    Args:
        mp3_files: A list of absolute or relative paths to the MP3 files to be combined.
                   The order in the list determines the order in the output file.
        output_filename: The name for the combined output MP3 file.
                         Defaults to "podcast.mp3".
        output_dir: The directory where the combined podcast file will be saved.
                    Defaults to "podcasts". Created if it doesn't exist.

    Returns:
        The absolute path to the combined podcast MP3 file if successful.
        Returns an error message string if ffmpeg fails or an error occurs.
    """
    if not mp3_files:
        return "Error: No MP3 files provided for combination."

    for f_path in mp3_files:
        if not Path(f_path).exists():
            return f"Error: Input file not found: {f_path}"

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_filepath = Path(output_dir) / output_filename

    # Create a temporary file list for ffmpeg
    list_filename = f"ffmpeg_list_{uuid.uuid4().hex}.txt"
    try:
        with Path(list_filename).open("w", encoding="utf-8") as f:
            for mp3_file in mp3_files:
                # ffmpeg's concat demuxer requires 'file' directive and paths to be escaped or simple.
                # Using absolute paths and -safe 0 is generally more robust.
                abs_mp3_file = Path(mp3_file).resolve()
                f.write(f"file '{abs_mp3_file}'\n")

        # Construct and run the ffmpeg command
        # -y: overwrite output without asking
        # -f concat: use the concat demuxer
        # -safe 0: allow unsafe file paths (needed for absolute paths in list file)
        # -c copy: copy audio stream without re-encoding (fast, preserves quality)
        command = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            list_filename,
            "-c",
            "copy",
            str(Path(output_filepath).resolve()),
        ]

        process = subprocess.run(command, capture_output=True, text=True, check=False)

        if process.returncode != 0:
            return f"Error combining MP3 files with ffmpeg: {process.stderr}"

        return str(Path(output_filepath).resolve())

    except FileNotFoundError:
        return "Error: ffmpeg command not found. Please ensure ffmpeg is installed and in your PATH."
    except Exception as e:
        return f"An unexpected error occurred during MP3 combination: {e}"
    finally:
        # Clean up the temporary list file
        if Path(list_filename).exists():
            Path(list_filename).unlink()
