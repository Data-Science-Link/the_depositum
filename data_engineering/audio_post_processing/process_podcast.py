#!/usr/bin/env python3
"""
Podcast Audio Post-Processing Script

Appends a standardized intro to podcast audio and optionally an outro at the end.
Intro and outro are used as-is for format; podcast and outro loudness are normalized to -16 LUFS.
Intro is assumed already mastered; outro volume is adjusted to match target LUFS.

Usage:
    uv run python data_engineering/audio_post_processing/process_podcast.py \\
        --intro /path/to/intro.mp3 \\
        --podcast /path/to/podcast.m4a \\
        --output /path/to/output.m4a

    With outro:
    uv run python data_engineering/audio_post_processing/process_podcast.py \\
        --intro /path/to/intro.mp3 \\
        --outro /path/to/outro.mp3 \\
        --podcast /path/to/podcast.m4a \\
        --output /path/to/output.m4a

Requirements:
    - ffmpeg must be installed on the system (for m4a support)
    - Intro file should be .mp3 or .wav, mastered to -16 LUFS
    - Outro file (optional) is normalized to target LUFS before appending
    - Podcast file should be a .m4a file
"""

import os
import sys
import argparse
import logging
import subprocess
import shutil
import tempfile
from pathlib import Path
from typing import Optional

try:
    from pydub import AudioSegment
    import pyloudnorm as pyln
    import numpy as np
except ImportError as e:
    print(f"Error importing required audio libraries: {e}")
    print("Please install dependencies with: uv sync")
    sys.exit(1)

# Set up logging to both console and file
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "podcast_processing.log"

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.handlers.clear()  # Prevent duplicate handlers if script is imported

# Create formatter (shared between handlers)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# File handler
file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Target loudness in LUFS
TARGET_LUFS = -16.0

# Default export quality settings (high quality to preserve audio)
# For MP3: 256kbps VBR (Variable Bitrate) - better quality than CBR
# For M4A: 256kbps AAC - high quality standard
DEFAULT_MP3_BITRATE = '256k'
DEFAULT_M4A_BITRATE = '256k'

# Pad end of audio before export to avoid last 0.5-1s truncation when encoding
# MP3/AAC (ffmpeg encodes in frames; incomplete final frame can be dropped)
EXPORT_END_PADDING_MS = 500


def check_ffmpeg_available() -> bool:
    """Check if ffmpeg is installed and available in the system PATH.

    pydub uses ffmpeg via subprocess calls to handle m4a and other formats.
    This function verifies ffmpeg is accessible before attempting to use it.

    Returns:
        True if ffmpeg is available, False otherwise
    """
    # First check if ffmpeg command exists in PATH
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path is None:
        return False

    # Try to run ffmpeg to verify it works
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            timeout=5,
            check=False
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def find_matching_file(file_path: Path, file_type: str) -> Optional[Path]:
    """Try to find a matching file if exact path doesn't exist.

    Handles cases where apostrophe characters might differ (straight vs curly).

    Args:
        file_path: Path to the file to find
        file_type: Description of the file type for error messages

    Returns:
        Path to matching file if found, None otherwise
    """
    if file_path.exists():
        return file_path

    # If file doesn't exist, try to find a similar file in the same directory
    parent_dir = file_path.parent
    expected_stem = file_path.stem
    expected_ext = file_path.suffix

    if not parent_dir.exists():
        logger.warning(f"Parent directory does not exist: {parent_dir}")
        return None

    # Normalize apostrophes for comparison (treat all apostrophe variants as equivalent)
    def normalize_apostrophes(text: str) -> str:
        """Normalize all apostrophe variants to a standard character for comparison."""
        # Replace all common apostrophe variants (U+0027, U+2019, U+2018, U+02BC) with a standard character
        # Using straight apostrophe as the standard
        normalized = text
        # Replace curly apostrophe (U+2019) with straight
        normalized = normalized.replace('\u2019', "'")
        # Replace left single quotation mark (U+2018) with straight
        normalized = normalized.replace('\u2018', "'")
        # Replace modifier letter apostrophe (U+02BC) with straight
        normalized = normalized.replace('\u02BC', "'")
        return normalized

    normalized_expected = normalize_apostrophes(expected_stem)
    logger.info(f"File not found, searching for matching {file_type} file. Expected stem (normalized): '{normalized_expected}'")

    # List all files with the same extension in the directory
    try:
        candidates_found = []  # Only collect if no match found (for error reporting)
        for candidate in parent_dir.iterdir():
            if not candidate.is_file():
                continue
            if candidate.suffix.lower() != expected_ext.lower():
                continue

            candidate_stem = candidate.stem
            normalized_candidate = normalize_apostrophes(candidate_stem)

            if normalized_expected == normalized_candidate:
                logger.info(f"Found matching {file_type} file with different apostrophe: {candidate.name}")
                return candidate

            # Only collect candidates if we haven't found a match yet (for error reporting)
            candidates_found.append((candidate.name, normalized_candidate))

        # Log available files only if no match was found (for debugging)
        if candidates_found:
            logger.debug(f"Available {file_type} files in directory (normalized stems):")
            for name, norm_stem in candidates_found:
                logger.debug(f"  - '{name}' -> normalized: '{norm_stem}'")
    except (PermissionError, OSError) as e:
        logger.debug(f"Error searching for matching file: {e}")
        return None

    return None


def validate_file_path(file_path: Path, file_type: str) -> Path:
    """Validate that a file path exists and is readable.

    If the exact file doesn't exist, tries to find a matching file (handles apostrophe differences).

    Args:
        file_path: Path to the file to validate
        file_type: Description of the file type for error messages

    Returns:
        Path to the validated file (may differ from input if a match was found)

    Raises:
        FileNotFoundError: If the file does not exist and no match can be found
        PermissionError: If the file cannot be read
    """
    # Try to find the file (handles apostrophe mismatches)
    actual_path = find_matching_file(file_path, file_type)
    if actual_path is None:
        raise FileNotFoundError(f"{file_type} file not found: {file_path}")

    if not actual_path.is_file():
        raise ValueError(f"{file_type} path is not a file: {actual_path}")

    # Check if file is readable
    try:
        with open(actual_path, 'rb') as f:
            f.read(1)
    except PermissionError:
        raise PermissionError(f"Cannot read {file_type} file: {actual_path}")

    return actual_path


def get_audio_bitrate(file_path: Path) -> Optional[float]:
    """Get audio file bitrate in kbps if available (for informational logging).

    Uses ffprobe to detect the original bitrate. Returns None if unavailable.
    This is optional and won't fail if ffprobe is missing.

    Args:
        file_path: Path to the audio file

    Returns:
        Bitrate in kbps, or None if unavailable
    """
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'stream=bit_rate',
             '-of', 'default=noprint_wrappers=1:nokey=1', str(file_path)],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            bitrate_bps = int(result.stdout.strip())
            return bitrate_bps / 1000  # Convert to kbps
    except (subprocess.TimeoutExpired, ValueError, FileNotFoundError):
        pass
    return None


def get_audio_duration_seconds(file_path: Path) -> Optional[float]:
    """Get audio file duration in seconds from container metadata (ffprobe).

    Used to verify decoded length when loading m4a via temp WAV to avoid truncation.

    Args:
        file_path: Path to the audio file

    Returns:
        Duration in seconds, or None if unavailable
    """
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', str(file_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except (subprocess.TimeoutExpired, ValueError, FileNotFoundError):
        pass
    return None


def _load_m4a_via_temp_wav(file_path: Path) -> AudioSegment:
    """Load m4a by decoding to a temp WAV file, then loading the WAV.

    Uses ffmpeg file-to-file decode (no pipe). If container duration is known,
    we use apad=whole_dur so the output is at least that long—AAC decode can
    truncate the last ~0.5–1s; padding ensures we keep the same total length
    (trailing silence if the decoder dropped samples).

    Args:
        file_path: Path to the .m4a file

    Returns:
        AudioSegment with full decoded audio (possibly padded at end)

    Raises:
        Exception: If ffmpeg decode or WAV load fails
    """
    fd, wav_path_str = tempfile.mkstemp(suffix='.wav')
    wav_path = Path(wav_path_str)
    try:
        os.close(fd)
        source_dur_sec = get_audio_duration_seconds(file_path)
        # Base decode; -fflags +genpts and -ignore_editlist 1 can help preserve full duration
        base_args = [
            'ffmpeg', '-y', '-fflags', '+genpts', '-i', str(file_path),
            '-vn', '-acodec', 'pcm_s16le',
        ]
        if source_dur_sec is not None and source_dur_sec > 0:
            # Ensure output is at least container duration (AAC decode can truncate last ~0.5-1s)
            apad_filter = f"apad=whole_dur={source_dur_sec}"
            cmd = base_args + ['-af', apad_filter, str(wav_path)]
            logger.debug(f"Decoding m4a with apad=whole_dur={source_dur_sec}")
        else:
            cmd = base_args + [str(wav_path)]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode != 0:
            stderr = result.stderr or ''
            raise RuntimeError(f"ffmpeg decode failed: {stderr[-1000:]}")
        audio = AudioSegment.from_wav(str(wav_path))
        return audio
    finally:
        try:
            wav_path.unlink(missing_ok=True)
        except OSError:
            pass


def load_audio_file(file_path: Path, file_type: str) -> AudioSegment:
    """Load an audio file using pydub.

    Note: pydub uses ffmpeg (via subprocess) to handle m4a and other non-WAV formats.
    For .wav files, pydub uses the built-in wave module. For .m4a and other formats,
    pydub calls ffmpeg in the background to decode the audio.

    When loading compressed formats, the audio is decoded to uncompressed PCM.
    Re-encoding will cause some quality loss, so we use high bitrates to minimize this.

    Args:
        file_path: Path to the audio file
        file_type: Description of the file type for logging

    Returns:
        AudioSegment object containing the loaded audio

    Raises:
        Exception: If the file cannot be loaded (may indicate ffmpeg is missing)
    """
    logger.info(f"Loading {file_type}: {file_path}")

    try:
        # Log original bitrate if available (optional, won't fail if unavailable)
        bitrate = get_audio_bitrate(file_path)
        if bitrate:
            logger.info(f"Original {file_type} bitrate: {bitrate:.0f} kbps")

        # Determine format from extension
        file_ext = file_path.suffix.lower()
        if file_ext == '.wav':
            # WAV files use Python's built-in wave module (no ffmpeg needed)
            audio = AudioSegment.from_wav(str(file_path))
        elif file_ext == '.mp3':
            # MP3 files require ffmpeg (pydub calls it via subprocess)
            audio = AudioSegment.from_mp3(str(file_path))
        elif file_ext == '.m4a':
            # Decode via temp WAV to avoid pipe truncation (last ~0.5-1s can be lost
            # when pydub uses from_file() which pipes through ffmpeg)
            audio = _load_m4a_via_temp_wav(file_path)
        else:
            # Try auto-detection
            audio = AudioSegment.from_file(str(file_path))

        loaded_ms = len(audio)
        logger.info(f"Loaded {file_type}: {loaded_ms}ms duration, {audio.frame_rate}Hz, {audio.channels} channels")

        # Sanity check: if source has duration metadata, warn if we got less (e.g. truncation)
        if file_ext == '.m4a':
            source_duration_sec = get_audio_duration_seconds(file_path)
            if source_duration_sec is not None:
                source_ms = source_duration_sec * 1000
                if loaded_ms < source_ms - 500:  # more than 0.5s short
                    logger.warning(
                        f"Loaded m4a duration ({loaded_ms}ms) is >0.5s shorter than "
                        f"source duration ({source_ms:.0f}ms) - possible truncation"
                    )

        return audio

    except Exception as e:
        logger.error(f"Failed to load {file_type} file {file_path}: {e}")
        raise


def measure_loudness(audio: AudioSegment) -> float:
    """Measure the loudness of an audio segment in LUFS.

    Args:
        audio: AudioSegment to measure

    Returns:
        Loudness value in LUFS

    Raises:
        Exception: If loudness measurement fails
    """
    try:
        # Convert AudioSegment to numpy array for pyloudnorm
        # pyloudnorm expects float32 array with values between -1.0 and 1.0
        samples = np.array(audio.get_array_of_samples(), dtype=np.float32)

        # Normalize to -1.0 to 1.0 range
        if audio.sample_width == 1:
            samples = samples / 128.0 - 1.0
        elif audio.sample_width == 2:
            samples = samples / 32768.0
        elif audio.sample_width == 4:
            samples = samples / 2147483648.0
        else:
            samples = samples / (2 ** (audio.sample_width * 8 - 1))

        # Reshape for multi-channel audio
        if audio.channels > 1:
            samples = samples.reshape((-1, audio.channels))
        else:
            samples = samples.reshape((-1, 1))

        # Create meter and measure loudness
        meter = pyln.Meter(audio.frame_rate)
        loudness = meter.integrated_loudness(samples)

        logger.info(f"Measured loudness: {loudness:.2f} LUFS")
        return loudness

    except Exception as e:
        logger.error(f"Failed to measure loudness: {e}")
        raise


def normalize_loudness(audio: AudioSegment, target_lufs: float) -> AudioSegment:
    """Normalize audio to a target LUFS level.

    Args:
        audio: AudioSegment to normalize
        target_lufs: Target loudness in LUFS

    Returns:
        Normalized AudioSegment

    Raises:
        Exception: If normalization fails
    """
    try:
        # Measure current loudness
        current_lufs = measure_loudness(audio)

        # Calculate gain adjustment needed
        gain_db = target_lufs - current_lufs
        logger.info(f"Adjusting gain by {gain_db:.2f} dB to reach {target_lufs} LUFS")

        # Apply gain adjustment
        normalized = audio.apply_gain(gain_db)

        # Verify the result (only log if significantly off target)
        verified_lufs = measure_loudness(normalized)
        if abs(verified_lufs - target_lufs) > 0.1:
            logger.warning(f"Normalized loudness: {verified_lufs:.2f} LUFS (target: {target_lufs} LUFS) - slight deviation")
        else:
            logger.info(f"Normalized loudness: {verified_lufs:.2f} LUFS (target: {target_lufs} LUFS)")

        return normalized

    except Exception as e:
        logger.error(f"Failed to normalize loudness: {e}")
        raise


def _match_and_append(anchor: AudioSegment, segment: AudioSegment, segment_name: str) -> AudioSegment:
    """Match segment to anchor's frame rate and channels, then return anchor + segment."""
    if anchor.frame_rate != segment.frame_rate:
        logger.info(f"Resampling {segment_name} from {segment.frame_rate}Hz to {anchor.frame_rate}Hz")
        segment = segment.set_frame_rate(anchor.frame_rate)
    if anchor.channels != segment.channels:
        logger.info(f"Converting {segment_name} from {segment.channels} to {anchor.channels} channels")
        if anchor.channels == 1:
            segment = segment.set_channels(1)
        elif anchor.channels == 2:
            segment = segment.set_channels(2)
    return anchor + segment


def concatenate_audio(
    intro: AudioSegment,
    podcast: AudioSegment,
    outro: Optional[AudioSegment] = None,
) -> AudioSegment:
    """Concatenate intro, podcast, and optionally outro audio segments.

    Args:
        intro: Intro audio segment
        podcast: Podcast audio segment (already normalized)
        outro: Optional outro audio segment (caller should normalize before passing)

    Returns:
        Concatenated AudioSegment: intro + podcast [+ outro if provided]
    """
    logger.info("Concatenating intro and podcast audio...")
    combined = _match_and_append(intro, podcast, "podcast")

    if outro is not None:
        logger.info("Appending outro...")
        combined = _match_and_append(combined, outro, "outro")

    total_duration = len(combined) / 1000.0  # Convert to seconds
    logger.info(f"Combined audio duration: {total_duration:.1f} seconds")
    return combined


def _export_via_temp_wav(
    audio: AudioSegment,
    output_path: Path,
    *,
    add_end_padding: bool = True,
) -> None:
    """Export audio to MP3 or M4A by writing a temp WAV, then encoding with ffmpeg.

    Avoids pydub's pipe-based export which can truncate the end of the stream.
    File-to-file encoding preserves full duration.

    Args:
        audio: AudioSegment to export
        output_path: Final output path (.mp3 or .m4a)
        add_end_padding: If True, append EXPORT_END_PADDING_MS silence before encoding

    Raises:
        RuntimeError: If ffmpeg encode fails
    """
    if add_end_padding:
        audio = audio + AudioSegment.silent(
            duration=EXPORT_END_PADDING_MS, frame_rate=audio.frame_rate
        )
    fd, wav_path_str = tempfile.mkstemp(suffix='.wav')
    wav_path = Path(wav_path_str)
    try:
        os.close(fd)
        # pydub WAV export uses built-in wave module (no pipe)
        expected_wav_sec = len(audio) / 1000.0
        audio.export(str(wav_path), format='wav')
        wav_dur_sec = get_audio_duration_seconds(wav_path)
        if wav_dur_sec is not None and wav_dur_sec < expected_wav_sec - 0.1:
            logger.warning(
                f"Temp WAV duration {wav_dur_sec:.2f}s is shorter than segment {expected_wav_sec:.2f}s "
                f"(pydub WAV export may have truncated)"
            )
        file_ext = output_path.suffix.lower()
        if file_ext == '.mp3':
            logger.info(f"Encoding WAV -> MP3 (VBR q=2, ~{DEFAULT_MP3_BITRATE})")
            result = subprocess.run(
                ['ffmpeg', '-y', '-i', str(wav_path), '-q:a', '2', str(output_path)],
                capture_output=True,
                text=True,
                timeout=600,
            )
        elif file_ext == '.m4a':
            logger.info(f"Encoding WAV -> M4A (AAC {DEFAULT_M4A_BITRATE})")
            result = subprocess.run(
                [
                    'ffmpeg', '-y', '-i', str(wav_path),
                    '-c:a', 'aac', '-b:a', DEFAULT_M4A_BITRATE,
                    str(output_path),
                ],
                capture_output=True,
                text=True,
                timeout=600,
            )
        else:
            raise ValueError(f"Unsupported extension for WAV export: {file_ext}")
        if result.returncode != 0:
            stderr = result.stderr or ''
            raise RuntimeError(f"ffmpeg encode failed: {stderr[-1000:]}")
    finally:
        try:
            wav_path.unlink(missing_ok=True)
        except OSError:
            pass


def export_audio(audio: AudioSegment, output_path: Path) -> Path:
    """Export audio segment to a file.

    For WAV we use pydub's built-in export. For MP3/M4A we export via a temp WAV
    then encode with ffmpeg (file-to-file) to avoid pipe truncation at the end.

    Args:
        audio: AudioSegment to export
        output_path: Path where the file should be saved

    Returns:
        Path to the exported file (may differ if extension was changed)

    Raises:
        Exception: If export fails (may indicate ffmpeg is missing)
    """
    logger.info(f"Exporting audio to: {output_path}")

    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine format from extension and adjust if needed
    file_ext = output_path.suffix.lower()
    actual_output_path = output_path

    try:
        if file_ext == '.wav':
            # WAV files use Python's built-in wave module (no ffmpeg needed)
            audio.export(str(output_path), format='wav')
        elif file_ext == '.mp3':
            _export_via_temp_wav(audio, output_path, add_end_padding=True)
        elif file_ext == '.m4a':
            _export_via_temp_wav(audio, output_path, add_end_padding=True)
        else:
            # Default to MP3 (most compatible for podcasting)
            logger.warning(f"Unknown extension {file_ext}, defaulting to MP3 format")
            actual_output_path = output_path.with_suffix('.mp3')
            _export_via_temp_wav(audio, actual_output_path, add_end_padding=True)

        # Verify file was created
        if not actual_output_path.exists():
            raise FileNotFoundError(f"Output file was not created: {actual_output_path}")

        file_size_mb = actual_output_path.stat().st_size / (1024 * 1024)
        logger.info(f"Successfully exported audio: {file_size_mb:.2f} MB")

        return actual_output_path

    except Exception as e:
        logger.error(f"Failed to export audio to {output_path}: {e}")
        raise


def process_podcast(
    intro_path: Path,
    podcast_path: Path,
    output_path: Path,
    target_lufs: float = TARGET_LUFS,
    outro_path: Optional[Path] = None,
) -> int:
    """Main processing function: append intro (and optionally outro), normalize loudness.

    Args:
        intro_path: Path to the intro file (.mp3 or .wav)
        podcast_path: Path to the podcast .m4a file
        output_path: Path where the processed file should be saved
        target_lufs: Target loudness in LUFS (default: -16.0)
        outro_path: Optional path to the outro file (.mp3 or .wav); volume is normalized to target_lufs

    Returns:
        0 on success, 1 on failure
    """
    try:
        # Validate input files (may return different paths if matches found)
        logger.info("Validating input files...")
        intro_path = validate_file_path(intro_path, "Intro")
        podcast_path = validate_file_path(podcast_path, "Podcast")
        if outro_path is not None:
            outro_path = validate_file_path(outro_path, "Outro")

        # Load audio files
        intro_audio = load_audio_file(intro_path, "intro")
        podcast_audio = load_audio_file(podcast_path, "podcast")

        # Duration diagnostics (to track truncation)
        podcast_ms = len(podcast_audio)
        source_dur_sec = get_audio_duration_seconds(podcast_path)
        logger.info(
            f"Duration check: podcast loaded {podcast_ms}ms"
            + (f" (source metadata: {source_dur_sec:.2f}s)" if source_dur_sec is not None else "")
        )

        # Intro is used as-is (already mastered); normalize podcast loudness
        logger.info("Normalizing podcast loudness...")
        normalized_podcast = normalize_loudness(podcast_audio, target_lufs)

        # Optional: load and normalize outro
        outro_audio: Optional[AudioSegment] = None
        if outro_path is not None:
            outro_audio = load_audio_file(outro_path, "outro")
            logger.info("Normalizing outro loudness...")
            outro_audio = normalize_loudness(outro_audio, target_lufs)

        # Concatenate intro + podcast [+ outro]
        combined_audio = concatenate_audio(intro_audio, normalized_podcast, outro_audio)
        combined_ms = len(combined_audio)
        logger.info(f"Duration check: combined segment {combined_ms}ms ({combined_ms/1000:.2f}s)")

        # Export the final file
        final_output_path = export_audio(combined_audio, output_path)

        out_dur_sec = get_audio_duration_seconds(final_output_path)
        if out_dur_sec is not None:
            expected_sec = (combined_ms + EXPORT_END_PADDING_MS) / 1000.0
            diff_sec = out_dur_sec - expected_sec
            logger.info(f"Duration check: output file {out_dur_sec:.2f}s (expected ~{expected_sec:.2f}s, diff {diff_sec:+.2f}s)")

        logger.info("=" * 60)
        logger.info("Podcast processing completed successfully!")
        logger.info(f"Output file: {final_output_path}")
        logger.info("=" * 60)

        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except PermissionError as e:
        logger.error(f"Permission error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        return 1


def main() -> int:
    """Main entry point for the script.

    Returns:
        Exit code: 0 for success, non-zero for failure
    """
    parser = argparse.ArgumentParser(
        description="Process podcast audio: append intro (and optional outro), normalize loudness to -16 LUFS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    uv run python data_engineering/audio_post_processing/process_podcast.py \\
        --intro /Users/me/audio/intro.mp3 \\
        --podcast /Users/me/audio/episode_01.m4a \\
        --output /Users/me/audio/episode_01_processed.mp3

    # With outro (volume normalized and appended at end)
    uv run python data_engineering/audio_post_processing/process_podcast.py \\
        --intro /Users/me/audio/intro.mp3 \\
        --outro /Users/me/audio/outro.mp3 \\
        --podcast /Users/me/audio/episode_01.m4a

    # Without --output, defaults to "Mastered <podcast_name>.mp3" in same directory
    uv run python data_engineering/audio_post_processing/process_podcast.py \\
        --intro /Users/me/audio/intro.mp3 \\
        --podcast /Users/me/audio/episode_01.m4a

Note: ffmpeg must be installed on your system for MP3/m4a support.
        """
    )

    parser.add_argument(
        '--intro',
        type=str,
        required=True,
        help='Path to the intro file (.mp3 or .wav, mastered to -16 LUFS)'
    )

    parser.add_argument(
        '--outro',
        type=str,
        required=False,
        default=None,
        help='Path to the outro file (.mp3 or .wav); volume is normalized to target LUFS and appended at the end'
    )

    parser.add_argument(
        '--podcast',
        type=str,
        required=True,
        help='Path to the raw podcast .m4a file'
    )

    parser.add_argument(
        '--output',
        type=str,
        required=False,
        default=None,
        help='Path where the processed output file should be saved (default: "Mastered " prefix added to podcast filename)'
    )

    parser.add_argument(
        '--target-lufs',
        type=float,
        default=TARGET_LUFS,
        help=f'Target loudness in LUFS (default: {TARGET_LUFS})'
    )

    args = parser.parse_args()

    # Check for ffmpeg before processing (required for m4a support)
    logger.info("Checking for ffmpeg...")
    if not check_ffmpeg_available():
        logger.error("=" * 60)
        logger.error("ffmpeg is not installed or not available in PATH")
        logger.error("=" * 60)
        logger.error("ffmpeg is required for m4a file support.")
        logger.error("Installation instructions:")
        logger.error("  macOS:    brew install ffmpeg")
        logger.error("  Linux:    sudo apt-get install ffmpeg  (or sudo yum install ffmpeg)")
        logger.error("  Windows: Download from https://ffmpeg.org/download.html")
        logger.error("")
        logger.error("After installing, ensure ffmpeg is in your system PATH.")
        return 1

    logger.info("ffmpeg is available")

    # Convert string paths to Path objects
    intro_path = Path(args.intro).expanduser().resolve()
    podcast_path = Path(args.podcast).expanduser().resolve()
    outro_path: Optional[Path] = None
    if args.outro:
        outro_path = Path(args.outro).expanduser().resolve()

    # Generate default output path if not provided
    if args.output is None:
        # Add "Mastered " prefix to podcast filename, change extension to .mp3
        podcast_stem = podcast_path.stem
        output_path = podcast_path.parent / f"Mastered {podcast_stem}.mp3"
        logger.info(f"No output path provided, using default: {output_path}")
    else:
        output_path = Path(args.output).expanduser().resolve()
        # If no extension provided, default to .mp3
        if not output_path.suffix:
            output_path = output_path.with_suffix('.mp3')
            logger.info(f"No extension in output path, defaulting to MP3: {output_path}")

    # Process the podcast
    return process_podcast(
        intro_path=intro_path,
        podcast_path=podcast_path,
        output_path=output_path,
        target_lufs=args.target_lufs,
        outro_path=outro_path,
    )


if __name__ == '__main__':
    sys.exit(main())
