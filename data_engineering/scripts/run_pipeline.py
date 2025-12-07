#!/usr/bin/env python3
"""
Main Pipeline Runner

Orchestrates the complete data extraction pipeline for all three sources:
1. Douay-Rheims Bible
2. Haydock Commentary
3. Roman Catechism

Usage:
    python data_engineering/scripts/run_pipeline.py [--source SOURCE] [--test] [--validate]
"""

import sys
import argparse
import logging
from pathlib import Path
import yaml
import shutil

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from data_engineering.data_sources.douay_rheims.extract_bible import main as extract_bible
from data_engineering.data_sources.haydock.extract_commentary import main as extract_commentary
from data_engineering.data_sources.catechism.extract_catechism import main as extract_catechism

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config():
    """Load pipeline configuration."""
    config_path = Path(__file__).parent.parent / "config" / "pipeline_config.yaml"
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return None


def copy_to_final_output(source_dir: Path, dest_dir: Path, description: str):
    """Copy processed files to final output directory.

    Args:
        source_dir: Source directory with processed files
        dest_dir: Destination directory for final output
        description: Description for logging
    """
    if not source_dir.exists():
        logger.warning(f"{description} output directory does not exist: {source_dir}")
        return

    dest_dir.mkdir(parents=True, exist_ok=True)

    # Copy all files
    files_copied = 0
    for file_path in source_dir.glob("*"):
        if file_path.is_file() and file_path.suffix == '.md':
            dest_file = dest_dir / file_path.name
            shutil.copy2(file_path, dest_file)
            files_copied += 1

    logger.info(f"Copied {files_copied} {description} files to final output")


def run_bible_extraction():
    """Run Douay-Rheims Bible extraction."""
    logger.info("=" * 60)
    logger.info("Extracting Douay-Rheims Bible...")
    logger.info("=" * 60)
    try:
        extract_bible()
        return True
    except Exception as e:
        logger.error(f"Bible extraction failed: {e}")
        return False


def run_commentary_extraction():
    """Run Haydock Commentary extraction."""
    logger.info("=" * 60)
    logger.info("Extracting Haydock Commentary...")
    logger.info("=" * 60)
    try:
        extract_commentary()
        return True
    except Exception as e:
        logger.error(f"Commentary extraction failed: {e}")
        return False


def run_catechism_extraction():
    """Run Catechism extraction."""
    logger.info("=" * 60)
    logger.info("Extracting Roman Catechism...")
    logger.info("=" * 60)
    try:
        extract_catechism()
        return True
    except Exception as e:
        logger.error(f"Catechism extraction failed: {e}")
        return False


def validate_outputs(config):
    """Validate that all expected outputs exist.

    Args:
        config: Pipeline configuration dictionary

    Returns:
        True if all validations pass, False otherwise
    """
    logger.info("=" * 60)
    logger.info("Validating outputs...")
    logger.info("=" * 60)

    all_valid = True

    # Validate Bible
    bible_dir = Path(config['paths']['processed_data']['douay_rheims'])
    expected_books = config['validation']['douay_rheims']['expected_books']
    bible_files = list(bible_dir.glob("*.md")) if bible_dir.exists() else []

    if len(bible_files) < expected_books:
        logger.warning(f"Bible: Expected {expected_books} books, found {len(bible_files)}")
        all_valid = False
    else:
        logger.info(f"✅ Bible: Found {len(bible_files)} books")

    # Validate Commentary
    commentary_dir = Path(config['paths']['processed_data']['haydock'])
    min_files = config['validation']['haydock']['min_files']
    commentary_files = list(commentary_dir.glob("*.md")) if commentary_dir.exists() else []

    if len(commentary_files) < min_files:
        logger.warning(f"Commentary: Expected at least {min_files} files, found {len(commentary_files)}")
        all_valid = False
    else:
        logger.info(f"✅ Commentary: Found {len(commentary_files)} files")

    # Validate Catechism
    catechism_dir = Path(config['paths']['processed_data']['catechism'])
    min_size_kb = config['validation']['catechism']['min_size_kb']
    catechism_file = list(catechism_dir.glob("*.md"))[0] if catechism_dir.exists() else None

    if not catechism_file:
        logger.warning("Catechism: No output file found")
        all_valid = False
    else:
        size_kb = catechism_file.stat().st_size / 1024
        if size_kb < min_size_kb:
            logger.warning(f"Catechism: File size {size_kb:.2f} KB is below minimum {min_size_kb} KB")
            all_valid = False
        else:
            logger.info(f"✅ Catechism: File size {size_kb:.2f} KB")

    return all_valid


def main():
    """Main pipeline function."""
    parser = argparse.ArgumentParser(description='Run The Depositum data extraction pipeline')
    parser.add_argument('--source', choices=['bible', 'commentary', 'catechism', 'all'],
                       default='all', help='Which source to extract')
    parser.add_argument('--test', action='store_true', help='Run in test mode')
    parser.add_argument('--validate', action='store_true', help='Only validate outputs')
    parser.add_argument('--copy-output', action='store_true',
                       help='Copy processed files to final output directory')

    args = parser.parse_args()

    # Load configuration
    config = load_config()
    if not config:
        logger.error("Failed to load configuration")
        return 1

    # Validation only mode
    if args.validate:
        success = validate_outputs(config)
        return 0 if success else 1

    # Run extractions
    results = {}

    if args.source in ['bible', 'all']:
        results['bible'] = run_bible_extraction()

    if args.source in ['commentary', 'all']:
        results['commentary'] = run_commentary_extraction()

    if args.source in ['catechism', 'all']:
        results['catechism'] = run_catechism_extraction()

    # Validate outputs
    if not args.test:
        validate_outputs(config)

    # Copy to final output if requested
    if args.copy_output:
        logger.info("=" * 60)
        logger.info("Copying files to final output directory...")
        logger.info("=" * 60)

        config = load_config()
        copy_to_final_output(
            Path(config['paths']['processed_data']['douay_rheims']),
            Path(config['paths']['final_output']['douay_rheims']),
            "Bible"
        )
        copy_to_final_output(
            Path(config['paths']['processed_data']['haydock']),
            Path(config['paths']['final_output']['haydock']),
            "Commentary"
        )
        copy_to_final_output(
            Path(config['paths']['processed_data']['catechism']),
            Path(config['paths']['final_output']['catechism']),
            "Catechism"
        )

    # Summary
    logger.info("=" * 60)
    logger.info("Pipeline Summary")
    logger.info("=" * 60)
    for source, success in results.items():
        status = "✅ Success" if success else "❌ Failed"
        logger.info(f"{source.capitalize()}: {status}")

    all_success = all(results.values())
    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())

