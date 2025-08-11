"""Work resource implementation for accessing work records."""

from typing import Dict, Any, List, Union, Optional

from .base import BaseResource


class WorkResource(BaseResource):
    """Resource for accessing work records (books, images, maps, music, etc.)."""
    
    @property
    def endpoint_path(self) -> str:
        """API endpoint path for work resources."""
        return "/work"
        
    @property
    def valid_include_options(self) -> List[str]:
        """Valid include options for work resources."""
        return [
            'all', 'comments', 'holdings', 'links', 'lists', 
            'subscribinglibs', 'tags', 'workversions'
        ]
        
    def _post_process_response(self, response: Dict[str, Any], work_id: Union[str, int]) -> Dict[str, Any]:
        """Post-process work response to extract work data.
        
        Args:
            response: Raw API response
            work_id: The work ID that was requested
            
        Returns:
            Processed work data
        """
        # Work responses are wrapped in a 'work' container
        if 'work' in response:
            work_data = response['work']
            # Ensure work ID is present (it's in XML attributes)
            if isinstance(work_data, dict) and 'id' not in work_data:
                work_data['id'] = str(work_id)
            return work_data
        return response
        
    def get_versions(self, work_id: Union[str, int]) -> List[Dict[str, Any]]:
        """Get all versions of a work.
        
        Args:
            work_id: Work identifier
            
        Returns:
            List of version dictionaries
        """
        work = self.get(work_id, include=['workversions'], reclevel='full')
        
        versions = []
        if 'version' in work:
            version_data = work['version']
            # Handle both single version and list of versions
            if isinstance(version_data, dict):
                versions = [version_data]
            elif isinstance(version_data, list):
                versions = version_data
                
        return versions
        
    async def aget_versions(self, work_id: Union[str, int]) -> List[Dict[str, Any]]:
        """Async version of get_versions.
        
        Args:
            work_id: Work identifier
            
        Returns:
            List of version dictionaries
        """
        work = await self.aget(work_id, include=['workversions'], reclevel='full')
        
        versions = []
        if 'version' in work:
            version_data = work['version']
            # Handle both single version and list of versions
            if isinstance(version_data, dict):
                versions = [version_data]
            elif isinstance(version_data, list):
                versions = version_data
                
        return versions
        
    def get_holdings(self, work_id: Union[str, int]) -> List[Dict[str, Any]]:
        """Get library holdings for a work.
        
        Args:
            work_id: Work identifier
            
        Returns:
            List of holding dictionaries
        """
        work = self.get(work_id, include=['holdings'], reclevel='full')
        
        holdings = []
        if 'holding' in work:
            holding_data = work['holding']
            if isinstance(holding_data, dict):
                holdings = [holding_data] 
            elif isinstance(holding_data, list):
                holdings = holding_data
                
        return holdings
        
    async def aget_holdings(self, work_id: Union[str, int]) -> List[Dict[str, Any]]:
        """Async version of get_holdings.
        
        Args:
            work_id: Work identifier
            
        Returns:
            List of holding dictionaries
        """
        work = await self.aget(work_id, include=['holdings'], reclevel='full')
        
        holdings = []
        if 'holding' in work:
            holding_data = work['holding']
            if isinstance(holding_data, dict):
                holdings = [holding_data] 
            elif isinstance(holding_data, list):
                holdings = holding_data
                
        return holdings
        
    def get_tags(self, work_id: Union[str, int]) -> List[Dict[str, Any]]:
        """Get public tags for a work.
        
        Args:
            work_id: Work identifier
            
        Returns:
            List of tag dictionaries
        """
        work = self.get(work_id, include=['tags'])
        
        tags = []
        if 'tag' in work:
            tag_data = work['tag']
            if isinstance(tag_data, dict):
                tags = [tag_data]
            elif isinstance(tag_data, list):
                tags = tag_data
                
        return tags
        
    async def aget_tags(self, work_id: Union[str, int]) -> List[Dict[str, Any]]:
        """Async version of get_tags.
        
        Args:
            work_id: Work identifier
            
        Returns:
            List of tag dictionaries
        """
        work = await self.aget(work_id, include=['tags'])
        
        tags = []
        if 'tag' in work:
            tag_data = work['tag']
            if isinstance(tag_data, dict):
                tags = [tag_data]
            elif isinstance(tag_data, list):
                tags = tag_data
                
        return tags
        
    def get_comments(self, work_id: Union[str, int]) -> List[Dict[str, Any]]:
        """Get public comments for a work.
        
        Args:
            work_id: Work identifier
            
        Returns:
            List of comment dictionaries
        """
        work = self.get(work_id, include=['comments'])
        
        comments = []
        if 'comment' in work:
            comment_data = work['comment']
            if isinstance(comment_data, dict):
                comments = [comment_data]
            elif isinstance(comment_data, list):
                comments = comment_data
                
        return comments
        
    async def aget_comments(self, work_id: Union[str, int]) -> List[Dict[str, Any]]:
        """Async version of get_comments.
        
        Args:
            work_id: Work identifier
            
        Returns:
            List of comment dictionaries
        """
        work = await self.aget(work_id, include=['comments'])
        
        comments = []
        if 'comment' in work:
            comment_data = work['comment']
            if isinstance(comment_data, dict):
                comments = [comment_data]
            elif isinstance(comment_data, list):
                comments = comment_data
                
        return comments