from faster_whisper import WhisperModel
import os
import time
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Data structure for a single transcript segment
# ---------------------------------------------------------------------------
@dataclass
class TranscriptSegment:
    start_time: float
    end_time: float
    text: str


# ---------------------------------------------------------------------------
# Data structure for the full transcription result
# ---------------------------------------------------------------------------
@dataclass
class TranscriptionResult:
    full_text: str
    segments: list[TranscriptSegment]
    language: str
    duration: float


# ---------------------------------------------------------------------------
# Main transcriber class
# ---------------------------------------------------------------------------
class MeetingTranscriber:
    """
    Wraps Faster-Whisper to transcribe audio files.
    """

    VALID_MODELS = ["tiny", "base", "small", "medium", "large-v2", "large-v3"]

    def __init__(self, model_size: str = "base"):
        if model_size not in self.VALID_MODELS:
            raise ValueError(f"model_size must be one of {self.VALID_MODELS}")

        print(f"Loading Faster-Whisper model: {model_size} ...")

        self.model = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8"
        )

        self.model_size = model_size

        print("Faster-Whisper model loaded.")

    def transcribe(self, audio_path: str) -> TranscriptionResult:
        """
        Transcribe an audio file.

        Args:
            audio_path: Path to audio file.

        Returns:
            TranscriptionResult
        """

        # ----------------------------------------------------
        # Validate file
        # ----------------------------------------------------
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        size_mb = os.path.getsize(audio_path) / (1024 * 1024)

        if size_mb > 500:
            raise ValueError(
                f"File too large: {size_mb:.1f} MB. Maximum is 500 MB."
            )

        valid_extensions = {
            ".mp3",
            ".wav",
            ".m4a",
            ".mp4",
            ".ogg",
            ".flac",
            ".webm",
        }

        ext = os.path.splitext(audio_path)[1].lower()

        if ext not in valid_extensions:
            raise ValueError(
                f"Unsupported file type '{ext}'. "
                f"Supported: {', '.join(valid_extensions)}"
            )

        print(f"Transcribing: {audio_path} ({size_mb:.1f} MB)")

        start = time.time()

        try:
            segments_generator, info = self.model.transcribe(
                audio_path,
                beam_size=5
            )

            segments_list = list(segments_generator)

        except Exception as e:
            raise RuntimeError(
                f"Whisper transcription failed: {e}"
            ) from e

        elapsed = round(time.time() - start, 1)

        print(f"Transcription complete in {elapsed}s")

        parsed_segments = [
            TranscriptSegment(
                start_time=round(seg.start, 2),
                end_time=round(seg.end, 2),
                text=seg.text.strip(),
            )
            for seg in segments_list
        ]

        duration = parsed_segments[-1].end_time if parsed_segments else 0.0

        full_text = " ".join(seg.text for seg in parsed_segments)

        return TranscriptionResult(
            full_text=full_text,
            segments=parsed_segments,
            language=info.language,
            duration=duration,
        )

    def format_timestamp(self, seconds: float) -> str:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    def get_readable_segments(
        self,
        result: TranscriptionResult,
    ) -> list[dict]:
        return [
            {
                "timestamp": self.format_timestamp(seg.start_time),
                "start_time": seg.start_time,
                "end_time": seg.end_time,
                "text": seg.text,
            }
            for seg in result.segments
        ]