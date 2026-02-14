#!/usr/bin/env python3
"""
Research Curator Agent
Automates the systematic research methodology George has developed
"""
import yaml
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

class ResearchCurator:
    """Automates systematic research following George's methodology"""
    
    def __init__(self, research_file_path):
        self.research_file_path = Path(research_file_path)
        self.backlog_file_path = self.research_file_path.parent / f"{self.research_file_path.stem}_article_backlog.yaml"
        
        self.research_data = self.load_yaml(self.research_file_path)
        self.backlog_data = self.load_yaml(self.backlog_file_path) if self.backlog_file_path.exists() else self.create_backlog_structure()
    
    def load_yaml(self, file_path):
        """Load YAML file safely"""
        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {e}", file=sys.stderr)
            return {}
    
    def save_yaml(self, data, file_path):
        """Save YAML file safely"""
        try:
            with open(file_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            return True
        except Exception as e:
            print(f"Error saving {file_path}: {e}", file=sys.stderr)
            return False
    
    def create_backlog_structure(self):
        """Create backlog file structure if it doesn't exist"""
        return {
            'topic': f"{self.research_data.get('topic', 'Unknown')} Article Backlog",
            'scope': "Articles from systematic research searches - to be processed when needed",
            'pending_articles': []
        }
    
    def get_pending_research_steps(self):
        """Extract pending research steps from plan"""
        plan = self.research_data.get('plan', [])
        return [step for step in plan if step.get('status') in ['pending', 'in_progress']]
    
    def get_next_source_id(self):
        """Generate next S## ID"""
        sources = self.research_data.get('sources', [])
        existing_nums = []
        
        for source in sources:
            source_id = source.get('id', '')
            if source_id.startswith('S'):
                try:
                    num = int(source_id[1:])
                    existing_nums.append(num)
                except ValueError:
                    continue
        
        next_num = max(existing_nums) + 1 if existing_nums else 100
        return f"S{next_num}"
    
    def execute_search_step(self, step):
        """Execute a research plan step using the enhanced bridge"""
        step_num = step.get('step', 'unknown')
        objective = step.get('objective', 'Unknown objective')
        queries = step.get('queries', [])
        
        print(f"🎯 Executing Step {step_num}: {objective}")
        
        articles_found = []
        for query in queries:
            print(f"   🔍 Searching: '{query}'")
            
            try:
                # Use the research-aware bridge
                result = subprocess.run([
                    'python', str(Path(__file__).parent / 'research_integrated_bridge.py'),
                    query, str(self.research_file_path)
                ], capture_output=True, text=True, env={'TROVE_API_KEY': 'zkx4Pf9cnEaOQ6MRW0P2MR7WAFV5iTeu'})
                
                if result.returncode == 0:
                    response_data = json.loads(result.stdout)
                    # Parse the curated articles from the response
                    # This would need to be enhanced based on the actual response format
                    print(f"   ✅ Search completed")
                else:
                    print(f"   ❌ Search failed: {result.stderr}")
                    
            except Exception as e:
                print(f"   ❌ Error executing search: {e}")
        
        return articles_found
    
    def add_articles_to_backlog(self, articles, step_context):
        """Add articles to backlog with proper formatting"""
        if not articles:
            return
        
        for article in articles:
            backlog_entry = {
                'article_id': article.get('article_id', 'unknown'),
                'source': f"Step {step_context.get('step', '?')}: {article.get('source', 'unknown')}",
                'snippet': article.get('snippet', ''),
                'priority': article.get('priority', 'medium'),
                'reason': article.get('reason', 'Research step execution'),
                'added_timestamp': datetime.now().isoformat(),
                'step_context': step_context.get('objective', '')
            }
            self.backlog_data['pending_articles'].append(backlog_entry)
    
    def update_step_status(self, step, status, notes=""):
        """Update research step status"""
        plan = self.research_data.get('plan', [])
        for plan_step in plan:
            if plan_step.get('step') == step.get('step'):
                plan_step['status'] = status
                if notes:
                    plan_step['notes'] = f"{datetime.now().strftime('%Y-%m-%d')}: {notes}"
                break
    
    def add_decision_log(self, action, why, summary, outcome):
        """Add decision to log following George's format"""
        decision = {
            't': datetime.now().isoformat(),
            'action': action,
            'why': why,
            'summary': summary,
            'outcome': outcome
        }
        
        if 'decisions' not in self.research_data:
            self.research_data['decisions'] = []
        
        self.research_data['decisions'].append(decision)
    
    def execute_research_plan(self):
        """Execute pending research plan steps systematically"""
        pending_steps = self.get_pending_research_steps()
        
        if not pending_steps:
            print("✅ No pending research steps found")
            return
        
        print(f"📋 Found {len(pending_steps)} pending research steps")
        
        total_articles = 0
        for step in pending_steps:
            articles = self.execute_search_step(step)
            
            if articles:
                self.add_articles_to_backlog(articles, step)
                self.update_step_status(step, 'completed', f"Found {len(articles)} articles")
                total_articles += len(articles)
            else:
                self.update_step_status(step, 'in_progress', "Searches executed, awaiting manual analysis")
        
        # Add decision log entry
        self.add_decision_log(
            action='automated_research',
            why='Execute pending research plan steps using systematic methodology',
            summary=f"Automated execution of {len(pending_steps)} research steps, found {total_articles} articles total",
            outcome='completed' if total_articles > 0 else 'partially_completed'
        )
        
        # Save files
        if self.save_yaml(self.research_data, self.research_file_path):
            print(f"✅ Updated research file: {self.research_file_path}")
        
        if self.save_yaml(self.backlog_data, self.backlog_file_path):
            print(f"✅ Updated backlog file: {self.backlog_file_path}")
        
        print(f"🎯 Research execution complete: {total_articles} articles queued for analysis")

def main():
    if len(sys.argv) != 2:
        print("Usage: python research_curator_agent.py research_file.yaml")
        sys.exit(1)
    
    research_file = sys.argv[1]
    curator = ResearchCurator(research_file)
    curator.execute_research_plan()

if __name__ == "__main__":
    main()