# Emilia Pipeline Run Guide

This project preprocesses raw speech/audio into cleaned, segmented, transcribed clips for speech dataset creation.

The main entry point is:

- `preprocessors/Emilia/main.py`
- helper script: `preprocessors/Emilia/download_youtube.py`
- runtime config: `preprocessors/Emilia/config.json`

## 1) Prerequisites

- Python 3.9 recommended
- `ffmpeg` installed
- Git and internet access
- Hugging Face token with access to `pyannote/speaker-diarization-3.1`

## 2) Create and activate environment

Option A: conda

```bash
conda create -y -n AudioPipeline python=3.9
conda activate AudioPipeline
bash preprocessors/Emilia/env.sh
```

Option B: existing venv

```bash
source .venv/bin/activate
```

If needed, install the requirements:

```bash
pip install -r preprocessors/Emilia/requirements.txt
```

## 3) Download required model checkpoints

The pipeline expects these model files to exist and be referenced in config:

- `UVR-MDX-NET-Inst_3.onnx`
- `sig_bak_ovr.onnx`

You can download them from the official model repos linked in the project README.

Place them somewhere stable, then update `preprocessors/Emilia/config.json` with their full paths.

## 4) Create your Hugging Face token

1. Go to: https://huggingface.co/settings/tokens
2. Create a new token
3. Make sure it starts with `hf_`
4. Grant access to the gated Pyannote models:
   - `pyannote/speaker-diarization-3.1`
   - `pyannote/segmentation-3.0`
   - `pyannote/speaker-diarization-community-1`

Then put the token in a local `.env` file that is not committed:

```dotenv
HUGGINGFACE_TOKEN=hf_xxxxxxxxxxxxxxxxx
```

## 5) Configure the project

Edit `preprocessors/Emilia/config.json` and set:

- `entrypoint.input_folder_path` to the folder containing your audio
- `separate.step1.model_path` to the source-separation ONNX file
- `mos_model.primary_model_path` to the DNSMOS ONNX file
- `HUGGINGFACE_TOKEN` in your environment

Example:

```json
{
  "entrypoint": {
    "input_folder_path": "youtube_audio",
    "SAMPLE_RATE": 24000
  },
  "separate": {
    "step1": {
      "model_path": "/path/to/UVR-MDX-NET-Inst_3.onnx"
    }
  },
  "mos_model": {
    "primary_model_path": "/path/to/sig_bak_ovr.onnx"
  },
  "huggingface_token": ""
}
```

## 6) Run the pipeline on a local folder

From the repo root:

```bash
python preprocessors/Emilia/main.py \
  --input_folder_path youtube_audio \
  --config_path preprocessors/Emilia/config.json
```

This processes all audio files inside the given folder.

## 7) Download YouTube audio and process it automatically

Create a file named `urls.txt` with one YouTube URL per line:

```text
https://www.youtube.com/watch?v=VIDEO_ID_1
https://www.youtube.com/watch?v=VIDEO_ID_2
```

Then run:

```bash
python preprocessors/Emilia/download_youtube.py \
  --urls_file urls.txt \
  --output_dir youtube_audio
```

Single URL:

```bash
python preprocessors/Emilia/download_youtube.py \
  --url "https://www.youtube.com/watch?v=VIDEO_ID" \
  --output_dir youtube_audio
```

If YouTube blocks the download with a browser verification error, use cookies from your browser:

```bash
python preprocessors/Emilia/download_youtube.py \
  --urls_file urls.txt \
  --output_dir youtube_audio \
  --cookies_from_browser chrome
```

## 8) Output structure

The pipeline saves results into a folder named like:

```text
youtube_audio_processed/<video_title>/
```

Inside that folder you will get:

- `*.mp3` segments (one per detected speaker segment)
- `<original_name>.json` metadata file with entries like:

```json
[
  {
    "text": "Hello, this is a segment",
    "start": 10.5,
    "end": 18.7,
    "speaker": "SPEAKER_01",
    "language": "en",
    "dnsmos": 3.12
  }
]
```

## 9) Important notes

- The project expects audio files in a folder; it does not process a single file by default.
- The pipeline may take time on CPU; GPU is preferred if available.
- If YouTube downloads fail with `HTTP 403`, upgrade `yt-dlp`:

```bash
python -m pip install --upgrade yt-dlp
```

- If Hugging Face token access fails, make sure the model license/grant is approved on Hugging Face.

## 10) Typical working example

This is the exact pattern that worked in this project:

```bash
python preprocessors/Emilia/main.py \
  --input_folder_path youtube_audio \
  --config_path preprocessors/Emilia/config.json
```

If you want, this project can also be run in a cleaner dedicated Conda environment to avoid dependency conflicts.
