"""Download authorized YouTube audio and pass it to the Emilia pipeline."""

import argparse
import subprocess
import sys
from pathlib import Path

import yt_dlp


def read_urls(urls_file):
    """Read non-empty, non-comment URLs from a text file."""
    return [
        line.strip()
        for line in Path(urls_file).read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def download_audio(urls, output_dir, cookies_from_browser=None):
    """Download each URL as a 24 kHz mono WAV file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    options = {
        "format": "bestaudio/best",
        "noplaylist": True,
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
    args = parser.parse_args()

    urls = list(args.url or [])
    if args.urls_file:
        urls.extend(read_urls(args.urls_file))
    if not urls:
        parser.error("provide --url or --urls_file")

    download_audio(urls, args.output_dir, args.cookies_from_browser)

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