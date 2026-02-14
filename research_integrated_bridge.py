#!/usr/bin/env python3
"""
Research-Integrated Trove Bridge
Combines Trove searching with George's research methodology
"""
import json
import sys
import asyncio
import re
import yaml
from pathlib import Path
from datetime import datetime

# Add the trove-sdk to the path
sys.path.insert(0, str(Path(__file__).parent / "packages" / "trove-sdk"))

try:
    from trove import TroveClient
except ImportError:
    print("Error: Could not import Trove SDK", file=sys.stderr)
    sys.exit(1)

class ResearchAwareSearch:
    """Integrates Trove searches with systematic research methodology"""
    
    def __init__(self, research_file_path=None):
        self.research_file_path = research_file_path
        self.research_data = self.load_research_file() if research_file_path else None
        self.client = TroveClient.from_env()
    
    def load_research_file(self):
        """Load existing research YAML file"""
        try:
            if Path(self.research_file_path).exists():
                with open(self.research_file_path, 'r') as f:
                    return yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Could not load research file: {e}", file=sys.stderr)
        return None
    
    def get_next_source_id(self):
        """Generate next available S## ID"""
        if not self.research_data or 'sources' not in self.research_data:
            return "S100"  # Start from S100 for new articles
        
        existing_ids = []
        for source in self.research_data['sources']:
            if source.get('id', '').startswith('S'):
                try:
                    num = int(source['id'][1:])
                    existing_ids.append(num)
                except ValueError:
                    continue
        
        next_num = max(existing_ids) + 1 if existing_ids else 100
        return f"S{next_num}"
    
    def extract_biographical_signals(self, text, search_terms):
        """Extract potential biographical information from article text"""
        if not text:
            return []
        
        signals = []
        text_lower = text.lower()
        
        # Look for biographical indicators
        bio_patterns = [
            (r'born\s+(\d{4})', 'birth_year'),
            (r'died?\s+(\d{4})', 'death_year'),
            (r'aged?\s+(\d+)', 'age_mention'),
            (r'married?\s+(\w+\s+\w+)', 'marriage_mention'),
            (r'son\s+of\s+(\w+\s+\w+)', 'father_mention'),
            (r'daughter\s+of\s+(\w+\s+\w+)', 'father_mention'),
            (r'widow\s+of\s+(\w+\s+\w+)', 'deceased_husband'),
            (r'(\w+\s+street|\w+\s+road)', 'address_mention'),
        ]
        
        for pattern, signal_type in bio_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                signals.append({
                    'type': signal_type,
                    'value': match.group(1) if match.groups() else match.group(0),
                    'context': text[max(0, match.start()-50):match.end()+50]
                })
        
        return signals
    
    def assess_article_priority(self, article, search_query, snippet):
        """Assess priority of article based on content and research context"""
        title = article.get('heading', '').lower()
        date = article.get('date', '')
        snippet_lower = snippet.lower()
        
        # High priority indicators - expanded to include legal/business records
        high_priority_signals = [
            'death' in title, 'obituary' in title, 'family notices' in title,
            'marriage' in title, 'business' in title, 'directory' in title,
            'insolvency' in title, 'insolvent' in title, 'bankruptcy' in title,
            'court' in title, 'legal notices' in title, 'probate' in title,
            'estate' in title, 'will' in title, 'administration' in title
        ]
        
        # Medium priority for business/legal content in snippet
        medium_priority_content = [
            'insolvent' in snippet_lower, 'bankruptcy' in snippet_lower,
            'court' in snippet_lower, 'solicitor' in snippet_lower,
            'merchant' in snippet_lower, 'trader' in snippet_lower,
            'business' in snippet_lower, 'occupation' in snippet_lower
        ]
        
        # Extract biographical signals from snippet
        bio_signals = self.extract_biographical_signals(snippet, search_query)
        
        if any(high_priority_signals) or len(bio_signals) > 2:
            return 'high'
        elif len(bio_signals) > 0 or any(medium_priority_content) or any(term in title for term in search_query.lower().split()):
            return 'medium'
        else:
            return 'low'
    
    def create_article_entry(self, article, search_context, snippet, priority):
        """Create properly formatted article entry for backlog"""
        return {
            'article_id': article.get('id', 'unknown'),
            'source': f"{search_context}",
            'snippet': snippet[:200] + "..." if len(snippet) > 200 else snippet,
            'priority': priority,
            'reason': self.generate_reason(article, priority, snippet),
            'date': article.get('date', 'unknown'),
            'title': article.get('heading', 'Unknown Title')[:100],
            'newspaper': self.extract_newspaper_name(article),
            'trove_url': f"https://trove.nla.gov.au/newspaper/article/{article.get('id', '')}",
            'added_timestamp': datetime.now().isoformat(),
            'bio_signals': self.extract_biographical_signals(snippet, "")
        }
    
    def generate_reason(self, article, priority, snippet):
        """Generate intelligent reason for including article"""
        title = article.get('heading', 'Unknown')
        date = article.get('date', '1800')
        year = date[:4] if len(date) >= 4 else '1800'
        
        if 'death' in title.lower() or 'obituary' in title.lower():
            return f"Death notice/obituary from {year} - likely contains comprehensive biographical information"
        elif 'family notices' in title.lower():
            return f"Family notices from {year} - may contain births, deaths, marriages, and family announcements"
        elif 'directory' in title.lower() or 'business' in title.lower():
            return f"Business/directory listing from {year} - may contain occupation and address details"
        elif priority == 'high':
            return f"High biographical signal density from {year} - multiple potential family/personal references"
        elif priority == 'medium':
            return f"Medium relevance from {year} - contains some biographical indicators"
        else:
            return f"Low priority from {year} - minimal biographical signals but may contain relevant context"
    
    def extract_newspaper_name(self, article):
        """Extract newspaper name from article metadata"""
        if 'title' in article:
            if isinstance(article['title'], dict):
                return article['title'].get('value', 'Unknown Paper')
            elif isinstance(article['title'], str):
                return article['title']
        return 'Unknown Paper'
    
    async def intelligent_search(self, query, date_range=None, max_articles=10, search_context="", sort_by="dateasc"):
        """Perform intelligent search with built-in curation"""
        try:
            with self.client:
                # Build search
                search = self.client.search().text(query).in_("newspaper")
                if date_range:
                    # Add date range logic here if needed
                    pass
                # Add date sorting for chronological research
                if sort_by == "dateasc":
                    search = search.sort_by("date_asc")
                elif sort_by == "datedesc":
                    search = search.sort_by("date_desc")
                # else use default relevance
                
                search = search.page_size(min(max_articles, 20))
                results = search.first_page()
                
                curated_articles = []
                newspaper_resource = self.client.resources.get_newspaper_resource()
                
                for category in results.categories:
                    if 'records' in category and 'article' in category['records']:
                        articles = category['records']['article'][:max_articles]
                        
                        for article in articles:
                            article_id = article.get('id')
                            
                            # Get snippet for assessment (not full text for curation)
                            try:
                                # Get just a snippet, not full text for efficiency
                                full_text = newspaper_resource.get_full_text(article_id)
                                snippet = full_text[:500] if full_text else ""
                            except:
                                snippet = article.get('snippet', '')
                            
                            priority = self.assess_article_priority(article, query, snippet)
                            
                            # Include ALL articles with priority assessment - don't filter out "low" priority
                            article_entry = self.create_article_entry(
                                article, search_context, snippet, priority
                            )
                            curated_articles.append(article_entry)
                
                return {
                    'query': query,
                    'total_results': results.total_results,
                    'curated_articles': curated_articles,
                    'search_context': search_context
                }
                
        except Exception as e:
            return {'error': str(e), 'query': query}

async def main():
    """Main function with research-aware searching"""
    try:
        # Parse command line arguments
        if len(sys.argv) < 2:
            print("Usage: python research_integrated_bridge.py 'search query' [research_file.yaml]")
            sys.exit(1)
        
        query = sys.argv[1]
        research_file = sys.argv[2] if len(sys.argv) > 2 else None
        
        # Create research-aware searcher
        searcher = ResearchAwareSearch(research_file)
        
        # Perform intelligent search
        result = await searcher.intelligent_search(
            query, 
            max_articles=5,  # Limit for focused curation
            search_context=f"Enhanced research search: {query}"
        )
        
        if 'error' in result:
            response = f"❌ Research search error: {result['error']}"
        else:
            # Format response with curation results
            curated = result['curated_articles']
            response_parts = [
                f"🔍 **Research-Aware Search:** '{result['query']}'",
                f"📊 **Total Trove Results:** {result['total_results']:,}",
                f"🎯 **High-Value Articles Curated:** {len([a for a in curated if a['priority'] == 'high'])}",
                f"📋 **Medium-Value Articles Curated:** {len([a for a in curated if a['priority'] == 'medium'])}",
                ""
            ]
            
            if curated:
                response_parts.append("## 📰 **Curated Articles Ready for Analysis:**")
                response_parts.append("")
                
                for i, article in enumerate(curated[:5], 1):
                    priority_emoji = "🔥" if article['priority'] == 'high' else "📌"
                    response_parts.extend([
                        f"{priority_emoji} **Article {i}: {article['title']}**",
                        f"   📅 {article['date']} | 🏛️ {article['newspaper']}",
                        f"   🎯 **Priority:** {article['priority'].upper()}",
                        f"   💡 **Reason:** {article['reason']}",
                        f"   📜 **Snippet:** \"{article['snippet']}\"",
                        f"   🔗 {article['trove_url']}",
                        ""
                    ])
                    
                    # Show biographical signals if any
                    if article['bio_signals']:
                        signals_text = ", ".join([f"{s['type']}:{s['value']}" for s in article['bio_signals'][:3]])
                        response_parts.append(f"   🧬 **Bio Signals:** {signals_text}")
                        response_parts.append("")
            else:
                response_parts.append("📝 **No high-value articles found** - search may need refinement.")
            
            response = "\\n".join(response_parts)
        
        # Return in OpenClaw CLI backend JSON format
        result = {
            "text": response,
            "session_id": f"research-aware-{hash(query) % 10000}"
        }
        
        print(json.dumps(result))
        
    except Exception as e:
        error_result = {
            "text": f"❌ Research bridge error: {str(e)}",
            "session_id": "research-error"
        }
        print(json.dumps(error_result))
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())