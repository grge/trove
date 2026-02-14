#!/bin/bash
# Analyze a Trove article using the research synthesis subagent
#
# Usage: ./analyze_article.sh <article_id> <research_file.yaml>

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <article_id> <research_file.yaml>"
    exit 1
fi

ARTICLE_ID="$1"
RESEARCH_FILE="$2"

# Get article content
echo "📥 Fetching article ${ARTICLE_ID}..."
cd /home/grge/code/trove/packages/trove-sdk
ARTICLE_JSON=$(TROVE_API_KEY=zkx4Pf9cnEaOQ6MRW0P2MR7WAFV5iTeu uv run python ../../fact_extractor.py "$ARTICLE_ID" 2>/dev/null)

if [ $? -ne 0 ]; then
    echo "❌ Failed to fetch article"
    exit 1
fi

# Load research context
echo "📚 Loading research context from ${RESEARCH_FILE}..."
RESEARCH_CONTEXT=$(head -100 "$RESEARCH_FILE" 2>/dev/null | grep -E "^(topic:|scope:|questions:|sources:)" -A 5)

# Create analysis prompt
PROMPT="Analyze this Trove article using careful historical reasoning.

## RESEARCH CONTEXT
$(echo "$RESEARCH_CONTEXT")

## ARTICLE DATA
$(echo "$ARTICLE_JSON")

## YOUR TASK
1. Determine if this article is about the research subject or someone else
2. Extract relevant facts with appropriate skepticism about identity
3. Reason about temporal consistency and name disambiguation  
4. Propose fact updates with confidence levels
5. Note any hypothesis confirmations or contradictions

Remember: Be conservative about identity attribution. People share names!"

echo ""
echo "🔍 Analyzing article with research synthesis subagent..."
echo ""

# Call subagent (this would use OpenClaw's subagent system)
# For now, just output the prompt for manual testing
echo "=== ANALYSIS PROMPT ==="
echo "$PROMPT"
echo ""
echo "=== To run analysis, use: ==="
echo "openclaw subagent research-synthesis \"$PROMPT\""
