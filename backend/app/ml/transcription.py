import whisper
import torch
import asyncio
import logging
from typing import Optional
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class WhisperTranscriber:
    """OpenAI Whisper speech-to-text transcriber"""
    
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.model = None
        
    async def load_model(self):
        """Load Whisper model asynchronously"""
        if self.model is None:
            logger.info(f"Loading Whisper {self.model_size} model...")
            # Run model loading in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None, whisper.load_model, self.model_size
            )
            logger.info("Whisper model loaded successfully")
    
    async def transcribe_audio(self, audio_path: str) -> dict:
        """
        Transcribe audio file to text
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            dict: Transcription result with text and segments
        """
        try:
            if self.model is None:
                await self.load_model()
            
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            logger.info(f"Starting transcription for: {audio_path}")
            
            # Run transcription in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._transcribe_sync, audio_path
            )
            
            logger.info("Transcription completed successfully")
            return {
                "text": result["text"],
                "segments": [
                    {
                        "start": segment["start"],
                        "end": segment["end"],
                        "text": segment["text"]
                    }
                    for segment in result["segments"]
                ],
                "language": result["language"]
            }
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise Exception(f"Transcription failed: {str(e)}")
    
    def _transcribe_sync(self, audio_path: str):
        """Synchronous transcription method"""
        return self.model.transcribe(audio_path, verbose=True)

# Global transcriber instance
transcriber = WhisperTranscriber()