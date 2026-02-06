#!/usr/bin/env python3
"""
Podcast Episode Transcription Script

Transcribes .m4a audio files using OpenAI Whisper and outputs markdown-formatted transcripts
with word-level timestamps.

Usage:
    uv run python data_engineering/audio_post_processing/transcribe_episode.py \\
        --audio /path/to/episode.m4a

Requirements:
    - ffmpeg must be installed on the system (for m4a support)
    - openai-whisper package must be installed
    
Note: If you encounter dependency issues with uv (especially on macOS x86_64), try installing
openai-whisper directly with pip:
    pip install openai-whisper
This may have better pre-built wheel support for your platform.
"""

import sys
import argparse
import logging
import ssl
import os
from pathlib import Path
from datetime import datetime

# Set CMAKE_PREFIX_PATH for llvmlite if LLVM is installed via Homebrew
# This is needed because llvmlite needs to find LLVM to work properly
llvm_path = "/usr/local/opt/llvm@20"
if os.path.exists(llvm_path) and "CMAKE_PREFIX_PATH" not in os.environ:
    os.environ["CMAKE_PREFIX_PATH"] = llvm_path

try:
    import whisper
except ImportError as e:
    print(f"Error importing whisper: {e}")
    print("Please install with: uv pip install openai-whisper")
    sys.exit(1)

# Handle SSL certificate issues for model downloads
# This is often needed in corporate environments or with certain network setups
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

# Set up logging
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "transcription.log"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.handlers.clear()

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setFormatter(formatter)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def format_timestamp(seconds: float) -> str:
    """Format seconds as MM:SS timestamp."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def generate_markdown(audio_path: Path, result: dict, timestamp: datetime) -> str:
    """Generate markdown-formatted transcript."""
    lines = [
        "# Episode Transcript",
        "",
        f"**File:** `{audio_path.name}`",
        f"**Transcribed:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        "",
    ]

    full_text = result.get("text", "").strip()
    if full_text:
        lines.append("## Transcript")
        lines.append("")
        
        # Add simple timestamps at natural breaks (every ~10 seconds)
        segments = result.get("segments", [])
        if segments:
            current_text = []
            last_timestamp = 0

            for seg in segments:
                text = seg.get("text", "").strip()
                start_time = seg.get("start", 0)

                if text:
                    # Add timestamp every ~10 seconds
                    if start_time - last_timestamp >= 10:
                        if current_text:
                            lines.append(" ".join(current_text))
                            lines.append("")
                        lines.append(f"[{format_timestamp(start_time)}]")
                        lines.append("")
                        current_text = [text]
                        last_timestamp = start_time
                    else:
                        current_text.append(text)
            
            # Add remaining text
            if current_text:
                lines.append(" ".join(current_text))
        else:
            # Fallback to just full text if no segments
            lines.append(full_text)

    return "\n".join(lines)


def transcribe_episode(audio_path: Path, model_size: str = "base") -> int:
    """Main transcription function."""
    try:
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"Loading Whisper model: {model_size}")
        model = whisper.load_model(model_size)

        logger.info(f"Transcribing: {audio_path}")
        result = model.transcribe(str(audio_path), word_timestamps=True, verbose=False)

        output_path = audio_path.parent / f"Transcript {audio_path.stem}.md"
        markdown = generate_markdown(audio_path, result, datetime.now())

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)

        logger.info("=" * 60)
        logger.info("Transcription completed successfully!")
        logger.info(f"Output: {output_path}")
        logger.info("=" * 60)
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except PermissionError as e:
        logger.error(f"Permission error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Transcription failed: {e}", exc_info=True)
        return 1


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Transcribe .m4a audio files to markdown with timestamps",
        epilog="""
Examples:
    uv run python data_engineering/audio_post_processing/transcribe_episode.py \\
        --audio /Users/me/audio/episode_01.m4a

    uv run python data_engineering/audio_post_processing/transcribe_episode.py \\
        --audio /Users/me/audio/episode_01.m4a \\
        --model large

Note: Output defaults to "Transcript {filename}.md" in the same directory.
Whisper models: tiny (fastest), base (default), small, medium, large (most accurate)
        """
    )
    parser.add_argument('--audio', type=str, required=True, help='Path to .m4a audio file')
    parser.add_argument(
        '--model',
        type=str,
        default='base',
        choices=['tiny', 'base', 'small', 'medium', 'large'],
        help='Whisper model size (default: base)'
    )

    args = parser.parse_args()
    audio_path = Path(args.audio).expanduser().resolve()
    return transcribe_episode(audio_path, args.model)


if __name__ == '__main__':
    sys.exit(main())
