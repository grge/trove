#!/usr/bin/env python3
"""
Fact Extractor - Analyzes Trove articles and extracts structured facts
Compatible with George's research methodology
"""
import json
import sys
import re
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "packages" / "trove-sdk"))

try:
    from trove import TroveClient
except ImportError:
    print("Error: Could not import Trove SDK", file=sys.stderr)
    sys.exit(1)

class FactExtractor:
    """Extract structured biographical facts from newspaper articles"""
    
    def __init__(self):
        self.client = TroveClient.from_env()
    
    def clean_text(self, text):
        """Clean OCR text"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[|]{2,}', ' ', text)
        text = text.replace(' , ', ', ').replace(' . ', '. ')
        return text.strip()
    
    def extract_biographical_facts(self, text, context):
        """Extract structured facts from article text"""
        facts = []
        text_clean = self.clean_text(text)
        
        # Birth information
        birth_patterns = [
            (r'born\s+(?:on\s+)?(\d{1,2}(?:st|nd|rd|th)?\s+\w+\s+\d{4})', 'birth_date'),
            (r'born\s+(?:in\s+)?(\d{4})', 'birth_year'),
            (r'born\s+(?:at|in)\s+([A-Z][a-zA-Z\s]+(?:,\s*[A-Z][a-zA-Z\s]+)?)', 'birthplace'),
        ]
        
        # Death information
        death_patterns = [
            (r'died?\s+(?:on\s+)?(\d{1,2}(?:st|nd|rd|th)?\s+\w+\s+\d{4})', 'death_date'),
            (r'died?\s+(?:on\s+)?(yesterday|last\s+\w+)', 'death_recent'),
            (r'aged?\s+(\d+)\s+years?', 'age_at_death'),
            (r'died?\s+(?:at|in)\s+([A-Z][a-zA-Z\s]+)', 'place_of_death'),
        ]
        
        # Marriage information
        marriage_patterns = [
            (r'married?\s+(?:to\s+)?([A-Z][a-z]+\s+[A-Z][a-z]+)', 'spouse_name'),
            (r'married?\s+(?:on\s+)?(\d{1,2}(?:st|nd|rd|th)?\s+\w+\s+\d{4})', 'marriage_date'),
            (r'wife\s+of\s+([A-Z][a-zA-Z\s]+)', 'husband_name'),
            (r'husband\s+of\s+([A-Z][a-zA-Z\s]+)', 'wife_name'),
            (r'widow\s+of\s+(?:the\s+late\s+)?([A-Z][a-zA-Z\s]+)', 'deceased_spouse'),
        ]
        
        # Family information
        family_patterns = [
            (r'son\s+of\s+([A-Z][a-zA-Z\s]+(?:and\s+[A-Z][a-zA-Z\s]+)?)', 'parents'),
            (r'daughter\s+of\s+([A-Z][a-zA-Z\s]+(?:and\s+[A-Z][a-zA-Z\s]+)?)', 'parents'),
            (r'(\d+)\s+sons?\s+and\s+(\d+)\s+daughters?', 'children_count'),
            (r'(\d+)\s+grandchildren', 'grandchildren_count'),
            (r'eldest\s+son\s+([A-Z][a-zA-Z\s]+)', 'eldest_son'),
        ]
        
        # Occupation and residence
        occupation_patterns = [
            (r'(?:was|is)\s+a\s+([a-z]+(?:\s+[a-z]+){0,2})\s+(?:by|of|at)', 'occupation'),
            (r'(?:bootmaker|shoemaker|blacksmith|farmer|publican|merchant)', 'occupation_direct'),
            (r'resided?\s+(?:at|in)\s+([A-Z][a-zA-Z\s]+)', 'residence'),
            (r'of\s+([A-Z][a-zA-Z]+(?:\s+Street|\s+Road|\s+Place))', 'address'),
        ]
        
        # Immigration information
        immigration_patterns = [
            (r'arrived?\s+(?:in|on)\s+(?:the\s+)?([A-Z][a-zA-Z\s]+)\s+(?:in\s+)?(\d{4})', 'arrival_ship_year'),
            (r'arrived?\s+(?:on|in)\s+(?:the\s+)?(\d{1,2}\s+\w+\s+\d{4})', 'arrival_date'),
            (r'immigrant\s+(?:on|via)\s+([A-Z][a-zA-Z\s]+)', 'immigration_ship'),
        ]
        
        all_patterns = (
            birth_patterns + death_patterns + marriage_patterns + 
            family_patterns + occupation_patterns + immigration_patterns
        )
        
        for pattern, fact_type in all_patterns:
            matches = re.finditer(pattern, text_clean, re.IGNORECASE)
            for match in matches:
                fact = {
                    'type': fact_type,
                    'value': match.group(1) if match.groups() else match.group(0),
                    'context': text_clean[max(0, match.start()-100):min(len(text_clean), match.end()+100)],
                    'confidence': self.assess_confidence(match, text_clean),
                    'source_context': context
                }
                facts.append(fact)
        
        return facts
    
    def assess_confidence(self, match, full_text):
        """Assess confidence level of extracted fact"""
        context = full_text[max(0, match.start()-50):min(len(full_text), match.end()+50)]
        
        # High confidence indicators
        if any(indicator in context.lower() for indicator in ['death notice', 'obituary', 'family notices']):
            return 'high'
        
        # Medium confidence indicators
        if any(indicator in context.lower() for indicator in ['mr.', 'mrs.', 'aged', 'late']):
            return 'medium'
        
        return 'low'
    
    def deduplicate_facts(self, facts):
        """Remove duplicate facts"""
        seen = set()
        unique = []
        
        for fact in facts:
            key = (fact['type'], fact['value'].lower().strip())
            if key not in seen:
                seen.add(key)
                unique.append(fact)
        
        return unique
    
    def format_fact_for_yaml(self, fact, article_id, article_date, source_id):
        """Format fact in George's YAML research format"""
        return {
            'claim': self.generate_claim_text(fact),
            'source_ids': [source_id],
            'timebound': article_date,
            'confidence': fact['confidence'],
            'tags': self.generate_tags(fact),
            'extracted': datetime.now().isoformat(),
            'extraction_context': fact['context'][:200]
        }
    
    def generate_claim_text(self, fact):
        """Generate human-readable claim text"""
        fact_type = fact['type']
        value = fact['value']
        
        claim_templates = {
            'birth_date': f"Born on {value}",
            'birth_year': f"Born in {value}",
            'birthplace': f"Born in {value}",
            'death_date': f"Died on {value}",
            'age_at_death': f"Aged {value} years at death",
            'place_of_death': f"Died at {value}",
            'spouse_name': f"Married to {value}",
            'marriage_date': f"Married on {value}",
            'parents': f"Child of {value}",
            'children_count': f"Had {value} children",
            'grandchildren_count': f"Had {value} grandchildren",
            'occupation': f"Worked as {value}",
            'occupation_direct': f"Worked as {value}",
            'residence': f"Resided at {value}",
            'address': f"Lived at {value}",
            'arrival_ship_year': f"Arrived on {value}",
        }
        
        return claim_templates.get(fact_type, f"Related to {fact_type}: {value}")
    
    def generate_tags(self, fact):
        """Generate tags for fact"""
        tags = [fact['type']]
        
        # Add contextual tags
        context_lower = fact['context'].lower()
        if 'death' in context_lower or 'died' in context_lower:
            tags.append('death')
        if 'family' in context_lower:
            tags.append('family')
        if 'business' in context_lower or 'occupation' in context_lower:
            tags.append('business')
        
        return tags
    
    def analyze_article(self, article_id, context=""):
        """Analyze a single article and extract all facts"""
        try:
            with self.client:
                newspaper_resource = self.client.resources.get_newspaper_resource()
                
                # Get article metadata
                article = newspaper_resource.get(article_id)
                full_text = newspaper_resource.get_full_text(article_id)
                
                if not full_text:
                    return {'error': 'No full text available', 'article_id': article_id}
                
                # Extract facts
                facts = self.extract_biographical_facts(full_text, context)
                facts = self.deduplicate_facts(facts)
                
                return {
                    'article_id': article_id,
                    'date': article.get('date', 'unknown'),
                    'title': article.get('heading', 'Unknown'),
                    'newspaper': self.extract_newspaper_name(article),
                    'facts_found': len(facts),
                    'facts': facts,
                    'text_length': len(full_text),
                    'url': f"https://trove.nla.gov.au/newspaper/article/{article_id}"
                }
                
        except Exception as e:
            return {'error': str(e), 'article_id': article_id}
    
    def extract_newspaper_name(self, article):
        """Extract newspaper name from article"""
        if 'title' in article:
            if isinstance(article['title'], dict):
                return article['title'].get('value', 'Unknown')
            return str(article['title'])
        return 'Unknown'

def main():
    """Analyze article and extract facts"""
    if len(sys.argv) < 2:
        print("Usage: python fact_extractor.py <article_id> [context]")
        sys.exit(1)
    
    article_id = sys.argv[1]
    context = sys.argv[2] if len(sys.argv) > 2 else ""
    
    extractor = FactExtractor()
    result = extractor.analyze_article(article_id, context)
    
    if 'error' in result:
        print(json.dumps({'error': result['error']}))
        sys.exit(1)
    
    # Format output
    output = {
        'article': {
            'id': result['article_id'],
            'date': result['date'],
            'title': result['title'],
            'newspaper': result['newspaper'],
            'url': result['url'],
            'text_length': result['text_length']
        },
        'analysis': {
            'facts_found': result['facts_found'],
            'facts': result['facts']
        }
    }
    
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
