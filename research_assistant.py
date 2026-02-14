#!/usr/bin/env python3
"""
Research Assistant - Complete workflow automation
Combines searching, curation, fact extraction, and YAML updates
"""
import json
import yaml
import subprocess
import sys
from pathlib import Path
from datetime import datetime

class ResearchAssistant:
    """Automates complete research workflow following George's methodology"""
    
    def __init__(self, research_file_path):
        self.research_file_path = Path(research_file_path)
        self.backlog_file = self.research_file_path.parent / f"{self.research_file_path.stem}_article_backlog.yaml"
        self.facts_file = self.research_file_path.parent / f"{self.research_file_path.stem}_proposed_facts.yaml"
        
        self.research = self.load_yaml(self.research_file_path)
        self.backlog = self.load_yaml(self.backlog_file) if self.backlog_file.exists() else {'pending_articles': []}
        
    def load_yaml(self, path):
        """Load YAML file with error tolerance"""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            print(f"⚠️  YAML parsing issue in {path.name}: {str(e)[:100]}", file=sys.stderr)
            print(f"   Attempting to work with backlog file instead...", file=sys.stderr)
            return {}
        except Exception as e:
            print(f"Error loading {path}: {e}", file=sys.stderr)
            return {}
    
    def save_yaml(self, data, path):
        """Save YAML file"""
        try:
            with open(path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            return True
        except Exception as e:
            print(f"Error saving {path}: {e}", file=sys.stderr)
            return False
    
    def process_pending_articles(self, max_articles=5):
        """Process pending articles from backlog and extract facts"""
        pending = self.backlog.get('pending_articles', [])
        high_priority = [a for a in pending if a.get('priority') == 'high'][:max_articles]
        
        if not high_priority:
            print("ℹ️  No high-priority articles in backlog")
            return
        
        print(f"📊 Processing {len(high_priority)} high-priority articles...")
        
        proposed_facts = []
        articles_processed = []
        
        for article in high_priority:
            article_id = article.get('article_id')
            if not article_id:
                continue
            
            print(f"\n🔍 Analyzing article {article_id}...")
            
            # Extract facts from article
            try:
                result = subprocess.run([
                    'python', str(Path(__file__).parent / 'fact_extractor.py'),
                    article_id,
                    article.get('source', 'research')
                ], capture_output=True, text=True, 
                env={'TROVE_API_KEY': 'zkx4Pf9cnEaOQ6MRW0P2MR7WAFV5iTeu',
                     'PYTHONPATH': str(Path(__file__).parent / 'packages' / 'trove-sdk')})
                
                if result.returncode == 0:
                    analysis = json.loads(result.stdout)
                    facts_found = analysis['analysis']['facts_found']
                    
                    if facts_found > 0:
                        print(f"   ✅ Found {facts_found} facts")
                        proposed_facts.extend(analysis['analysis']['facts'])
                        articles_processed.append({
                            'article_id': article_id,
                            'facts_extracted': facts_found,
                            'article_info': analysis['article']
                        })
                    else:
                        print(f"   ℹ️  No facts found")
                else:
                    print(f"   ❌ Error: {result.stderr}")
                    
            except Exception as e:
                print(f"   ❌ Exception: {e}")
        
        # Save proposed facts
        if proposed_facts:
            facts_output = {
                'generated': datetime.now().isoformat(),
                'research_file': str(self.research_file_path),
                'articles_analyzed': len(articles_processed),
                'total_facts': len(proposed_facts),
                'articles': articles_processed,
                'proposed_facts': proposed_facts
            }
            
            if self.save_yaml(facts_output, self.facts_file):
                print(f"\n✅ Saved {len(proposed_facts)} proposed facts to {self.facts_file.name}")
                return facts_output
        
        return None
    
    def search_and_queue(self, query, max_results=5):
        """Execute search and queue articles"""
        print(f"🔍 Searching Trove: '{query}'")
        
        try:
            result = subprocess.run([
                str(Path(__file__).parent / 'run_research_bridge.sh'),
                query
            ], capture_output=True, text=True,
            env={'TROVE_API_KEY': 'zkx4Pf9cnEaOQ6MRW0P2MR7WAFV5iTeu'})
            
            if result.returncode == 0:
                response = json.loads(result.stdout)
                print(f"   ✅ Search completed: {response.get('session_id', 'unknown')}")
                return response
            else:
                print(f"   ❌ Search failed: {result.stderr}")
                return None
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return None
    
    def generate_research_report(self):
        """Generate comprehensive research report"""
        pending_count = len(self.backlog.get('pending_articles', []))
        high_priority = len([a for a in self.backlog.get('pending_articles', []) if a.get('priority') == 'high'])
        
        plan_steps = self.research.get('plan', [])
        pending_steps = len([s for s in plan_steps if s.get('status') in ['pending', 'in_progress']])
        
        questions = self.research.get('questions', [])
        open_questions = len([q for q in questions if q.get('status') == 'open'])
        
        report = f"""
╔═══════════════════════════════════════════════════════════════╗
║           RESEARCH STATUS REPORT                              ║
╠═══════════════════════════════════════════════════════════════╣
║ Research File: {self.research_file_path.name:<44} ║
║ Topic: {self.research.get('topic', 'Unknown')[:50]:<53} ║
╠═══════════════════════════════════════════════════════════════╣
║ 📊 STATISTICS                                                 ║
║   Articles in backlog: {pending_count:<42} ║
║   High priority articles: {high_priority:<38} ║
║   Pending research steps: {pending_steps:<38} ║
║   Open research questions: {open_questions:<37} ║
╠═══════════════════════════════════════════════════════════════╣
║ 📋 NEXT ACTIONS                                               ║
║   1. Process {high_priority} high-priority articles                     ║
║   2. Execute {pending_steps} pending research steps                       ║
║   3. Address {open_questions} open research questions                      ║
╚═══════════════════════════════════════════════════════════════╝
"""
        return report

def main():
    """Main research assistant interface"""
    if len(sys.argv) < 3:
        print("Usage: python research_assistant.py <research.yaml> <command> [args]")
        print("\nCommands:")
        print("  status              - Show research status")
        print("  process [N]         - Process N high-priority articles (default: 5)")
        print("  search 'query'      - Execute search and queue articles")
        sys.exit(1)
    
    research_file = sys.argv[1]
    command = sys.argv[2]
    
    assistant = ResearchAssistant(research_file)
    
    if command == "status":
        print(assistant.generate_research_report())
    
    elif command == "process":
        max_articles = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        result = assistant.process_pending_articles(max_articles)
        if result:
            print(f"\n✅ Processing complete: {result['total_facts']} facts proposed")
    
    elif command == "search":
        if len(sys.argv) < 4:
            print("Error: search command requires a query")
            sys.exit(1)
        query = sys.argv[3]
        assistant.search_and_queue(query)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
