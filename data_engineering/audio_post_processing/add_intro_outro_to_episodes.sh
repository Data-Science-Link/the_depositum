#!/bin/bash
#
# Batch Audio Post-Processing Script
#
# This script allows you to manually add commands for processing multiple podcast episodes.
# Simply add your commands below, one per line, and run this script.
#
# Usage:
#     cd data_engineering/audio_post_processing
#     ./run_episodes.sh
#
# Or from project root:
#     bash data_engineering/audio_post_processing/add_intro_outro_to_episodes.sh
#

# set -e  # Exit on error (commented out to continue processing after individual episode failures)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Standard intro and outro file paths (outro volume is normalized to match podcast)
INTRO_FILE='/Users/michaellink/Library/CloudStorage/GoogleDrive-linkmichaelj@gmail.com/My Drive/2. Professional Development/4. Projects/The Depositum/Assets/mastered_standard_intro.mp3'
OUTRO_FILE='/Users/michaellink/Library/CloudStorage/GoogleDrive-linkmichaelj@gmail.com/My Drive/2. Professional Development/4. Projects/The Depositum/Assets/mastered_standard_outro.mp3'

# Counters
TOTAL=0
SUCCESS=0
FAILED=0

# Function to run a command and track results
# Automatically extracts episode name from EPISODE_FILE (removes extension)
run_command() {
    # Construct episode directory and full path
    local episode_dir="$EPISODES_DIR/$EPISODE_NUM"
    local podcast_path="$episode_dir/$EPISODE_FILE"

    # Extract episode name from EPISODE_FILE (remove extension)
    local episode_name="${EPISODE_FILE%.*}"

    TOTAL=$((TOTAL + 1))

    echo ""
    echo "=========================================="
    echo "Processing: $episode_name"
    echo "Podcast path: $podcast_path"
    echo "=========================================="

    # Note: Python script will handle file finding (including apostrophe mismatches)
    # Build command with properly quoted paths (outro is appended at end; its volume is normalized)
    local cmd="uv run python data_engineering/audio_post_processing/process_podcast.py --intro \"$INTRO_FILE\" --outro \"$OUTRO_FILE\" --podcast \"$podcast_path\""

    if eval "$cmd"; then
        echo -e "${GREEN}✓ Success: $episode_name${NC}"
        SUCCESS=$((SUCCESS + 1))
    else
        echo -e "${RED}✗ Failed: $episode_name${NC}"
        FAILED=$((FAILED + 1))
        # Continue processing other episodes even if one fails
        # (unless set -e is active, then comment out set -e at top)
    fi
}

# ============================================================================
# ADD YOUR COMMANDS BELOW
# ============================================================================
# Format for each episode:
#   EPISODE_NUM="01"
#   EPISODE_FILE="filename.m4a"
#   run_command
# Note: Episode name is automatically extracted from EPISODE_FILE (filename without extension)
# Note: Output file will be automatically created with "Mastered " prefix in the same directory
# Note: Paths with special characters (apostrophes, spaces, etc.) are handled automatically
#
# You can comment out commands with # to skip them temporarily
# ============================================================================

# Path to episode folders
EPISODES_DIR='/Users/michaellink/Library/CloudStorage/GoogleDrive-linkmichaelj@gmail.com/My Drive/2. Professional Development/4. Projects/The Depositum/Episodes/Episode Content'

# # Episode 01
# EPISODE_NUM="01"
# EPISODE_FILE="Jesus is God- The Evidence in John 1.m4a"
# run_command

# # Episode 02
# EPISODE_NUM="02"
# EPISODE_FILE="The Warning You Missed in the Christmas Story.m4a"
# run_command

# # Episode 03
# EPISODE_NUM="03"
# EPISODE_FILE="Parenting Panic- Mary's Search for Jesus.m4a"
# run_command

# # Episode 04
# EPISODE_NUM="04"
# EPISODE_FILE="Baptism- The Fight Starts at the Water's Edge.m4a"
# run_command

# # Episode 05
# EPISODE_NUM="05"
# EPISODE_FILE="Why the Devil Quoted Scripture to Jesus.m4a"
# run_command

# # Episode 06
# EPISODE_NUM="06"
# EPISODE_FILE="3 Miracles That Prove Jesus is God.m4a"
# run_command

# # Episode 07
# EPISODE_NUM="07"
# EPISODE_FILE="The Beatitudes- Heaven's Non-Negotiable Profile.m4a"
# run_command

# # Episode 08
# EPISODE_NUM="08"
# EPISODE_FILE="Transfiguration Meaning- A Vaccine for Spiritual Darkness.m4a"
# run_command

# # Episode 09
# EPISODE_NUM="09"
# EPISODE_FILE="Why Jesus Didn't Unbind Lazarus.m4a"
# run_command

# # Episode 10
# EPISODE_NUM="10"
# EPISODE_FILE="Why Jesus Chose an Unbroken Colt.m4a"
# run_command

# # Episode 11
# EPISODE_NUM="11"
# EPISODE_FILE="Why_Jesus_Doubled_Down_on_Eating_Flesh_Edited.m4a"
# run_command

# # Episode 12
# EPISODE_NUM="12"
# EPISODE_FILE="Stop_Compromising_The_Tragedy_of_Pontius_Pilate.m4a"
# run_command

# # Episode 13
# EPISODE_NUM="13"
# EPISODE_FILE="Why_Jesus_Quoted_Psalm_22_2.m4a"
# run_command

# # Episode 14
# EPISODE_NUM="14"
# EPISODE_FILE="Physical_Evidence_for_the_Resurrection.m4a"
# run_command

# # Episode 15
# EPISODE_NUM="15"
# EPISODE_FILE="Why_Jesus_Left_to_Send_the_Spirit.m4a"
# run_command

# # Episode 16
# EPISODE_NUM="16"
# EPISODE_FILE="How_fire_turned_cowards_into_the_Church_Edited.m4a"
# run_command

# # Episode 17
# EPISODE_NUM="17"
# EPISODE_FILE="How_Martyrs_Conquered_the_Roman_Empire.m4a"
# run_command

# # Episode 18
# EPISODE_NUM="18"
# EPISODE_FILE="Why_Judas_and_Peter_Chose_Differently_Edited.m4a"
# run_command

# Episode 19
EPISODE_NUM="19"
EPISODE_FILE="Why_Jesus_Built_His_Church_on_Fishermen.m4a"
run_command

# # Episode 20
# EPISODE_NUM="20"
# EPISODE_FILE=".m4a"
# run_command

# # Episode 21
# EPISODE_NUM="21"
# EPISODE_FILE=".m4a"
# run_command

# # Episode 22
# EPISODE_NUM="22"
# EPISODE_FILE=".m4a"
# run_command

# # Episode 23
# EPISODE_NUM="23"
# EPISODE_FILE=".m4a"
# run_command

# # Episode 24
# EPISODE_NUM="24"
# EPISODE_FILE=".m4a"
# run_command

# # Episode 25
# EPISODE_NUM="25"
# EPISODE_FILE=".m4a"
# run_command

# ============================================================================
# ADD MORE EPISODES ABOVE THIS LINE
# ============================================================================

# Summary
echo ""
echo "=========================================="
echo "Processing Complete"
echo "=========================================="
echo "Total episodes: $TOTAL"
echo -e "${GREEN}Successful: $SUCCESS${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED${NC}"
fi
echo "=========================================="

# Exit with error code if any failed
if [ $FAILED -gt 0 ]; then
    exit 1
else
    exit 0
fi
