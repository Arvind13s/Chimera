"""Chimera CLI — Generate videos from the command line."""

import argparse
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


def main():
    parser = argparse.ArgumentParser(
        description="Chimera — Autonomous AI Video Generator (CLI)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py
  python cli.py --niche "A terrifying Space Anomaly"
  python cli.py --topic "The mystery of the Bermuda Triangle"
  python cli.py --voice "Jenny (Female, US)"
        """,
    )
    parser.add_argument("--niche", type=str, default=None, help="Niche topic category")
    parser.add_argument("--topic", type=str, default=None, help="Custom topic (overrides niche)")
    parser.add_argument("--voice", type=str, default="Christopher (Male, US)", help="TTS voice name")

    args = parser.parse_args()

    from backend.core.pipeline import generate_video_stream

    print("\n🦁 Chimera v3.0 — Autonomous AI Video Generator\n")
    print("=" * 55)

    final_path = None
    for message, video_path, metadata in generate_video_stream(
        niche=args.niche,
        custom_topic=args.topic,
        voice=args.voice,
    ):
        print(message)
        if video_path:
            final_path = video_path

    print("=" * 55)
    if final_path:
        print(f"\n🎉 Video saved: {final_path}\n")
    else:
        print("\n❌ Video generation failed.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
