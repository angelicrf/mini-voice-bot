# Mini Voice Bot

This project is a simple voice bot. The initial phase of this project focuses on audio preprocessing, specifically cleaning and normalizing audio files to prepare them for further processing like speech recognition.

## Current Features

- **Audio Normalization**: A script is provided to normalize the volume of a `.wav` file. This ensures that the audio is at a consistent and audible level, which is a crucial step before feeding it into a voice recognition model.

## Project Structure

```
mini-voice-bot/
├── audio/
│   ├── sample.wav      # Example input audio file
│   └── clean.wav       # Generated normalized audio file
├── preprocessing/
│   └── clean_audio.py  # Script for audio normalization
└── README.md
```

## Getting Started

### Prerequisites

Make sure you have Python 3 installed on your system. You will also need `ffmpeg` for `pydub` to work correctly.

You can install the required Python package using pip:

```bash
pip install pydub
```

### Usage

1.  Place your input audio file (e.g., `sample.wav`) in the `audio/` directory.
2.  Run the cleaning script from the `preprocessing/` directory:

    ```bash
    python preprocessing/clean_audio.py
    ```

3.  The normalized audio will be saved as `clean.wav` in the `audio/` directory.
