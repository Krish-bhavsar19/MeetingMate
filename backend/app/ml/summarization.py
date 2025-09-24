from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import asyncio
import logging
from typing import List, Dict
import torch

logger = logging.getLogger(__name__)

class MeetingSummarizer:
    """Meeting summarization using Hugging Face Transformers (BART/T5)"""
    
    def __init__(self, model_name: str = "facebook/bart-large-cnn"):
        self.model_name = model_name
        self.summarizer = None
        self.tokenizer = None
        self.model = None
        
    async def load_model(self):
        """Load summarization model asynchronously"""
        if self.summarizer is None:
            logger.info(f"Loading summarization model: {self.model_name}")
            
            loop = asyncio.get_event_loop()
            
            # Load model and tokenizer in thread pool
            self.tokenizer, self.model = await loop.run_in_executor(
                None, self._load_model_sync
            )
            
            # Create pipeline
            self.summarizer = pipeline(
                "summarization",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1
            )
            
            logger.info("Summarization model loaded successfully")
    
    def _load_model_sync(self):
        """Synchronously load model and tokenizer"""
        tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
        return tokenizer, model
    
    async def summarize_transcript(self, transcript: str, max_length: int = 150, min_length: int = 50) -> Dict:
        """
        Summarize meeting transcript
        
        Args:
            transcript: Meeting transcript text
            max_length: Maximum summary length
            min_length: Minimum summary length
            
        Returns:
            dict: Summary information
        """
        try:
            if self.summarizer is None:
                await self.load_model()
            
            logger.info("Starting transcript summarization")
            
            # Split long transcripts into chunks if needed
            chunks = self._split_text(transcript, max_chunk_length=1024)
            
            summaries = []
            for chunk in chunks:
                # Run summarization in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, 
                    lambda: self.summarizer(
                        chunk,
                        max_length=max_length,
                        min_length=min_length,
                        do_sample=False
                    )
                )
                summaries.append(result[0]['summary_text'])
            
            # If multiple chunks, summarize the summaries
            final_summary = summaries[0] if len(summaries) == 1 else await self._combine_summaries(summaries)
            
            logger.info("Summarization completed successfully")
            
            return {
                "summary": final_summary,
                "original_length": len(transcript.split()),
                "summary_length": len(final_summary.split()),
                "compression_ratio": len(transcript.split()) / len(final_summary.split())
            }
            
        except Exception as e:
            logger.error(f"Summarization failed: {str(e)}")
            raise Exception(f"Summarization failed: {str(e)}")
    
    def _split_text(self, text: str, max_chunk_length: int = 1024) -> List[str]:
        """Split text into chunks for processing"""
        words = text.split()
        chunks = []
        current_chunk = []
        
        for word in words:
            current_chunk.append(word)
            if len(' '.join(current_chunk)) > max_chunk_length:
                chunks.append(' '.join(current_chunk[:-1]))
                current_chunk = [word]
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    async def _combine_summaries(self, summaries: List[str]) -> str:
        """Combine multiple summaries into one final summary"""
        combined = ' '.join(summaries)
        
        # Summarize the combined summaries
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.summarizer(
                combined,
                max_length=200,
                min_length=100,
                do_sample=False
            )
        )
        
        return result[0]['summary_text']

# Global summarizer instance
summarizer = MeetingSummarizer()