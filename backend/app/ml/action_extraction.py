import spacy
import re
from typing import List, Dict
import asyncio
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ActionItemExtractor:
    """Extract action items and tasks from meeting transcripts using spaCy"""
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        self.model_name = model_name
        self.nlp = None
        
        # Action keywords and patterns
        self.action_keywords = [
            "will", "need to", "should", "must", "have to", "going to",
            "action item", "todo", "task", "assignment", "follow up",
            "by", "before", "until", "deadline", "due"
        ]
        
        self.date_patterns = [
            r"\b(?:by|before|until|due)\s+(?:today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
            r"\b(?:by|before|until|due)\s+\d{1,2}[\/\-]\d{1,2}(?:[\/\-]\d{2,4})?\b",
            r"\b(?:by|before|until|due)\s+(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}\b",
            r"\b(?:next week|this week|end of week|eow)\b"
        ]
        
    async def load_model(self):
        """Load spaCy model asynchronously"""
        if self.nlp is None:
            logger.info(f"Loading spaCy model: {self.model_name}")
            
            loop = asyncio.get_event_loop()
            self.nlp = await loop.run_in_executor(
                None, spacy.load, self.model_name
            )
            
            logger.info("spaCy model loaded successfully")
    
    async def extract_action_items(self, transcript: str) -> List[Dict]:
        """
        Extract action items from meeting transcript
        
        Args:
            transcript: Meeting transcript text
            
        Returns:
            List[Dict]: List of extracted action items
        """
        try:
            if self.nlp is None:
                await self.load_model()
            
            logger.info("Starting action item extraction")
            
            # Process text with spaCy
            loop = asyncio.get_event_loop()
            doc = await loop.run_in_executor(
                None, self.nlp, transcript
            )
            
            action_items = []
            sentences = [sent.text.strip() for sent in doc.sents]
            
            for sentence in sentences:
                if self._contains_action_keywords(sentence):
                    action_item = await self._process_action_sentence(sentence)
                    if action_item:
                        action_items.append(action_item)
            
            # Remove duplicates and rank by confidence
            unique_actions = self._deduplicate_actions(action_items)
            ranked_actions = sorted(unique_actions, key=lambda x: x['confidence'], reverse=True)
            
            logger.info(f"Extracted {len(ranked_actions)} action items")
            return ranked_actions
            
        except Exception as e:
            logger.error(f"Action item extraction failed: {str(e)}")
            raise Exception(f"Action item extraction failed: {str(e)}")
    
    def _contains_action_keywords(self, sentence: str) -> bool:
        """Check if sentence contains action keywords"""
        sentence_lower = sentence.lower()
        return any(keyword in sentence_lower for keyword in self.action_keywords)
    
    async def _process_action_sentence(self, sentence: str) -> Dict:
        """Process individual action sentence"""
        loop = asyncio.get_event_loop()
        doc = await loop.run_in_executor(None, self.nlp, sentence)
        
        # Extract entities
        persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
        dates = [ent.text for ent in doc.ents if ent.label_ in ["DATE", "TIME"]]
        orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
        
        # Extract dates using patterns
        extracted_dates = self._extract_dates(sentence)
        dates.extend(extracted_dates)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(sentence, persons, dates)
        
        if confidence > 0.3:  # Threshold for valid action items
            return {
                "text": sentence.strip(),
                "assignees": persons,
                "due_date": dates[0] if dates else None,
                "organizations": orgs,
                "confidence": confidence,
                "extracted_at": datetime.utcnow().isoformat(),
                "status": "pending"
            }
        
        return None
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates using regex patterns"""
        dates = []
        for pattern in self.date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                dates.append(match.group())
        return dates
    
    def _calculate_confidence(self, sentence: str, persons: List[str], dates: List[str]) -> float:
        """Calculate confidence score for action item"""
        score = 0.0
        sentence_lower = sentence.lower()
        
        # Base score for containing action keywords
        action_keyword_count = sum(1 for keyword in self.action_keywords if keyword in sentence_lower)
        score += min(action_keyword_count * 0.2, 0.6)
        
        # Boost for having assignees
        if persons:
            score += 0.3
        
        # Boost for having dates
        if dates:
            score += 0.2
        
        # Boost for imperative verbs
        if any(word in sentence_lower for word in ["must", "will", "should", "need"]):
            score += 0.1
        
        # Penalty for questions
        if "?" in sentence:
            score -= 0.2
        
        return min(score, 1.0)
    
    def _deduplicate_actions(self, actions: List[Dict]) -> List[Dict]:
        """Remove duplicate action items"""
        unique_actions = []
        seen_texts = set()
        
        for action in actions:
            # Simple deduplication based on text similarity
            text_key = action["text"].lower().strip()
            if text_key not in seen_texts:
                seen_texts.add(text_key)
                unique_actions.append(action)
        
        return unique_actions

# Global action item extractor instance
action_extractor = ActionItemExtractor()