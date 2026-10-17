"""Download authorized YouTube audio and pass it to the Emilia pipeline."""

import argparse
import subprocess
import sys
from pathlib import Path

import yt_dlp
from yt_dlp.utils import parse_duration


def read_urls(urls_file):
    """Read non-empty, non-comment URLs from a text file."""
    return [
        line.strip()
        for line in Path(urls_file).read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def download_audio(
    urls,
    output_dir,
    cookies_from_browser=None,
    cookies_file=None,
    start_time=None,
    end_time=None,
):
    """Download each URL as a 24 kHz mono WAV file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    options = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "source_address": "0.0.0.0",
        "js_runtimes": {"node": {}},
        "remote_components": ["ejs:github"],
        "outtmpl": str(output_dir / "%(title)s [%(id)s].%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "0",
            }
        ],
        "postprocessor_args": {"FFmpegExtractAudio": ["-ar", "24000", "-ac", "1"]},
    }
    if cookies_from_browser:
        options["cookiesfrombrowser"] = (cookies_from_browser,)
    if cookies_file:
        options["cookiefile"] = str(cookies_file)
    if start_time or end_time:
        options["download_ranges"] = yt_dlp.utils.download_range_func(
            None, [(start_time or 0, end_time or float("inf"))]
        )
        options["force_keyframes_at_cuts"] = True

    with yt_dlp.YoutubeDL(options) as downloader:
        downloader.download(urls)


def main():
    parser = argparse.ArgumentParser(
        description="Download YouTube audio, then process it with Emilia."
    )
    parser.add_argument("--url", action="append", help="YouTube URL; repeatable")
    parser.add_argument("--urls_file", type=Path, help="Text file containing one URL per line")
    parser.add_argument(
        "--output_dir",
        type=Path,
        default=Path("youtube_audio"),
        help="Directory for downloaded and processed audio",
    )
    parser.add_argument(
        "--skip_processing",
        action="store_true",
        help="Only download audio; do not start main.py",
    )
    parser.add_argument(
        "--cookies_from_browser",
        choices=("chrome", "edge", "firefox", "safari"),
        help="Use cookies from this browser when YouTube requires verification",
    )
    parser.add_argument(
        "--cookies_file",
        type=Path,
        help="Netscape-format cookies file exported from a browser",
    )
    parser.add_argument(
        "--start_time",
        help="Start time for a partial download, for example 00:10:00",
    )
    parser.add_argument(
        "--end_time",
        help="End time for a partial download, for example 00:20:00",
    )
    args = parser.parse_args()

    if args.end_time and not args.start_time:
        parser.error("--end_time requires --start_time")
    if args.cookies_from_browser and args.cookies_file:
        parser.error("use only one of --cookies_from_browser or --cookies_file")

    try:
        start_time = parse_duration(args.start_time) if args.start_time else None
        end_time = parse_duration(args.end_time) if args.end_time else None
    except (TypeError, ValueError):
        parser.error("timestamps must use seconds or HH:MM:SS format")
    if args.start_time and start_time is None:
        parser.error(f"invalid --start_time value: {args.start_time}")
    if args.end_time and end_time is None:
        parser.error(f"invalid --end_time value: {args.end_time}")
    if start_time is not None and end_time is not None and end_time <= start_time:
        parser.error("--end_time must be greater than --start_time")

    urls = list(args.url or [])
    if args.urls_file:
        urls.extend(read_urls(args.urls_file))
    if not urls:
        parser.error("provide --url or --urls_file")

    download_audio(
        urls,
        args.output_dir,
        args.cookies_from_browser,
        args.cookies_file,
        start_time,
        end_time,
    )

    if not args.skip_processing:
        repo_root = Path(__file__).resolve().parents[2]
        subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve().with_name("main.py")),
                "--input_folder_path",
                str(args.output_dir),
                "--config_path",
                str(Path(__file__).resolve().with_name("config.json")),
            ],
            cwd=repo_root,
            check=True,
        )


if __name__ == "__main__":
    main()
