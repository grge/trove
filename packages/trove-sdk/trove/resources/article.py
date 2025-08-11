"""Article resource implementations for newspaper and gazette articles."""

from typing import Dict, Any, List, Union, Optional

from .base import BaseResource


class ArticleResource(BaseResource):
    """Base resource for accessing newspaper and gazette articles."""
    
    def __init__(self, transport, article_type: str = 'newspaper'):
        """Initialize article resource.
        
        Args:
            transport: Transport layer
            article_type: 'newspaper' or 'gazette'
        """
        super().__init__(transport)
        self.article_type = article_type
        
    @property
    def endpoint_path(self) -> str:
        """API endpoint path for article resources."""
        return f"/{self.article_type}"
        
    @property
    def valid_include_options(self) -> List[str]:
        """Valid include options for article resources."""
        return ['all', 'articletext', 'comments', 'lists', 'tags']
        
    def _post_process_response(self, response: Dict[str, Any], article_id: Union[str, int]) -> Dict[str, Any]:
        """Post-process article response.
        
        Args:
            response: Raw API response
            article_id: The article ID that was requested
            
        Returns:
            Processed article data
        """
        # Article responses are wrapped in 'article' container
        if 'article' in response:
            article_data = response['article']
            if isinstance(article_data, dict) and 'id' not in article_data:
                article_data['id'] = str(article_id)
            return article_data
        return response
        
    def get_full_text(self, article_id: Union[str, int]) -> Optional[str]:
        """Get full text of an article.
        
        Args:
            article_id: Article identifier
            
        Returns:
            Full text content or None if not available
        """
        article = self.get(article_id, include=['articletext'])
        return article.get('articleText')
        
    async def aget_full_text(self, article_id: Union[str, int]) -> Optional[str]:
        """Async version of get_full_text.
        
        Args:
            article_id: Article identifier
            
        Returns:
            Full text content or None if not available
        """
        article = await self.aget(article_id, include=['articletext'])
        return article.get('articleText')
        
    def get_pdf_urls(self, article_id: Union[str, int]) -> List[str]:
        """Get PDF URLs for article pages.
        
        Args:
            article_id: Article identifier
            
        Returns:
            List of PDF URLs
        """
        article = self.get(article_id)
        
        pdf_urls = []
        if 'pdf' in article:
            pdf_data = article['pdf']
            if isinstance(pdf_data, str):
                pdf_urls = [pdf_data]
            elif isinstance(pdf_data, list):
                pdf_urls = pdf_data
                
        return pdf_urls
        
    async def aget_pdf_urls(self, article_id: Union[str, int]) -> List[str]:
        """Async version of get_pdf_urls.
        
        Args:
            article_id: Article identifier
            
        Returns:
            List of PDF URLs
        """
        article = await self.aget(article_id)
        
        pdf_urls = []
        if 'pdf' in article:
            pdf_data = article['pdf']
            if isinstance(pdf_data, str):
                pdf_urls = [pdf_data]
            elif isinstance(pdf_data, list):
                pdf_urls = pdf_data
                
        return pdf_urls
        
    def is_coming_soon(self, article_id: Union[str, int]) -> bool:
        """Check if article has 'coming soon' status.
        
        Args:
            article_id: Article identifier
            
        Returns:
            True if article is coming soon
        """
        article = self.get(article_id)
        return article.get('status') == 'coming soon'
        
    async def ais_coming_soon(self, article_id: Union[str, int]) -> bool:
        """Async version of is_coming_soon.
        
        Args:
            article_id: Article identifier
            
        Returns:
            True if article is coming soon
        """
        article = await self.aget(article_id)
        return article.get('status') == 'coming soon'
        
    def is_withdrawn(self, article_id: Union[str, int]) -> bool:
        """Check if article has 'withdrawn' status.
        
        Args:
            article_id: Article identifier
            
        Returns:
            True if article is withdrawn
        """
        article = self.get(article_id)
        return article.get('status') == 'withdrawn'
        
    async def ais_withdrawn(self, article_id: Union[str, int]) -> bool:
        """Async version of is_withdrawn.
        
        Args:
            article_id: Article identifier
            
        Returns:
            True if article is withdrawn
        """
        article = await self.aget(article_id)
        return article.get('status') == 'withdrawn'
        
    def get_tags(self, article_id: Union[str, int]) -> List[Dict[str, Any]]:
        """Get public tags for an article.
        
        Args:
            article_id: Article identifier
            
        Returns:
            List of tag dictionaries
        """
        article = self.get(article_id, include=['tags'])
        
        tags = []
        if 'tag' in article:
            tag_data = article['tag']
            if isinstance(tag_data, dict):
                tags = [tag_data]
            elif isinstance(tag_data, list):
                tags = tag_data
                
        return tags
        
    async def aget_tags(self, article_id: Union[str, int]) -> List[Dict[str, Any]]:
        """Async version of get_tags.
        
        Args:
            article_id: Article identifier
            
        Returns:
            List of tag dictionaries
        """
        article = await self.aget(article_id, include=['tags'])
        
        tags = []
        if 'tag' in article:
            tag_data = article['tag']
            if isinstance(tag_data, dict):
                tags = [tag_data]
            elif isinstance(tag_data, list):
                tags = tag_data
                
        return tags
        
    def get_comments(self, article_id: Union[str, int]) -> List[Dict[str, Any]]:
        """Get public comments for an article.
        
        Args:
            article_id: Article identifier
            
        Returns:
            List of comment dictionaries
        """
        article = self.get(article_id, include=['comments'])
        
        comments = []
        if 'comment' in article:
            comment_data = article['comment']
            if isinstance(comment_data, dict):
                comments = [comment_data]
            elif isinstance(comment_data, list):
                comments = comment_data
                
        return comments
        
    async def aget_comments(self, article_id: Union[str, int]) -> List[Dict[str, Any]]:
        """Async version of get_comments.
        
        Args:
            article_id: Article identifier
            
        Returns:
            List of comment dictionaries
        """
        article = await self.aget(article_id, include=['comments'])
        
        comments = []
        if 'comment' in article:
            comment_data = article['comment']
            if isinstance(comment_data, dict):
                comments = [comment_data]
            elif isinstance(comment_data, list):
                comments = comment_data
                
        return comments


class NewspaperResource(ArticleResource):
    """Specialized resource for newspaper articles."""
    
    def __init__(self, transport):
        """Initialize newspaper resource."""
        super().__init__(transport, 'newspaper')


class GazetteResource(ArticleResource):
    """Specialized resource for gazette articles."""
    
    def __init__(self, transport):
        """Initialize gazette resource."""
        super().__init__(transport, 'gazette')