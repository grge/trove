"""List resource implementation for accessing user-created lists."""

from typing import Dict, Any, List, Union, Optional

from .base import BaseResource


class ListResource(BaseResource):
    """Resource for accessing user-created lists."""
    
    @property
    def endpoint_path(self) -> str:
        """API endpoint path for list resources."""
        return "/list"
        
    @property
    def valid_include_options(self) -> List[str]:
        """Valid include options for list resources."""
        return ['all', 'comments', 'listitems', 'tags']
        
    def _post_process_response(self, response: Dict[str, Any], list_id: Union[str, int]) -> Dict[str, Any]:
        """Post-process list response.
        
        Args:
            response: Raw API response
            list_id: The list ID that was requested
            
        Returns:
            Processed list data
        """
        if 'list' in response:
            list_data = response['list']
            if isinstance(list_data, dict) and 'id' not in list_data:
                list_data['id'] = str(list_id)
            return list_data
        return response
        
    def get_items(self, list_id: Union[str, int]) -> List[Dict[str, Any]]:
        """Get all items in a list.
        
        Args:
            list_id: List identifier
            
        Returns:
            List of item dictionaries
        """
        list_data = self.get(list_id, include=['listitems'])
        
        items = []
        if 'listItem' in list_data:
            item_data = list_data['listItem'] 
            if isinstance(item_data, dict):
                items = [item_data]
            elif isinstance(item_data, list):
                items = item_data
                
        return items
        
    async def aget_items(self, list_id: Union[str, int]) -> List[Dict[str, Any]]:
        """Async version of get_items.
        
        Args:
            list_id: List identifier
            
        Returns:
            List of item dictionaries
        """
        list_data = await self.aget(list_id, include=['listitems'])
        
        items = []
        if 'listItem' in list_data:
            item_data = list_data['listItem'] 
            if isinstance(item_data, dict):
                items = [item_data]
            elif isinstance(item_data, list):
                items = item_data
                
        return items
        
    def get_creator(self, list_id: Union[str, int]) -> str:
        """Get the username of the list creator.
        
        Args:
            list_id: List identifier
            
        Returns:
            Creator username
        """
        list_data = self.get(list_id)
        return list_data.get('creator') or list_data.get('by', 'unknown')
        
    async def aget_creator(self, list_id: Union[str, int]) -> str:
        """Async version of get_creator.
        
        Args:
            list_id: List identifier
            
        Returns:
            Creator username
        """
        list_data = await self.aget(list_id)
        return list_data.get('creator') or list_data.get('by', 'unknown')
        
    def get_item_count(self, list_id: Union[str, int]) -> int:
        """Get the number of items in the list.
        
        Args:
            list_id: List identifier
            
        Returns:
            Number of items in the list
        """
        list_data = self.get(list_id)
        return int(list_data.get('listItemCount', 0))
        
    async def aget_item_count(self, list_id: Union[str, int]) -> int:
        """Async version of get_item_count.
        
        Args:
            list_id: List identifier
            
        Returns:
            Number of items in the list
        """
        list_data = await self.aget(list_id)
        return int(list_data.get('listItemCount', 0))
        
    def get_title(self, list_id: Union[str, int]) -> Optional[str]:
        """Get the title of the list.
        
        Args:
            list_id: List identifier
            
        Returns:
            List title or None if not available
        """
        list_data = self.get(list_id)
        return list_data.get('title')
        
    async def aget_title(self, list_id: Union[str, int]) -> Optional[str]:
        """Async version of get_title.
        
        Args:
            list_id: List identifier
            
        Returns:
            List title or None if not available
        """
        list_data = await self.aget(list_id)
        return list_data.get('title')
        
    def get_description(self, list_id: Union[str, int]) -> Optional[str]:
        """Get the description of the list.
        
        Args:
            list_id: List identifier
            
        Returns:
            List description or None if not available
        """
        list_data = self.get(list_id)
        return list_data.get('description')
        
    async def aget_description(self, list_id: Union[str, int]) -> Optional[str]:
        """Async version of get_description.
        
        Args:
            list_id: List identifier
            
        Returns:
            List description or None if not available
        """
        list_data = await self.aget(list_id)
        return list_data.get('description')
        
    def get_last_updated(self, list_id: Union[str, int]) -> Optional[str]:
        """Get when the list was last updated.
        
        Args:
            list_id: List identifier
            
        Returns:
            Last updated timestamp or None if not available
        """
        list_data = self.get(list_id)
        return list_data.get('lastupdated')
        
    async def aget_last_updated(self, list_id: Union[str, int]) -> Optional[str]:
        """Async version of get_last_updated.
        
        Args:
            list_id: List identifier
            
        Returns:
            Last updated timestamp or None if not available
        """
        list_data = await self.aget(list_id)
        return list_data.get('lastupdated')
        
    def get_tags(self, list_id: Union[str, int]) -> List[Dict[str, Any]]:
        """Get public tags for a list.
        
        Args:
            list_id: List identifier
            
        Returns:
            List of tag dictionaries
        """
        list_data = self.get(list_id, include=['tags'])
        
        tags = []
        if 'tag' in list_data:
            tag_data = list_data['tag']
            if isinstance(tag_data, dict):
                tags = [tag_data]
            elif isinstance(tag_data, list):
                tags = tag_data
                
        return tags
        
    async def aget_tags(self, list_id: Union[str, int]) -> List[Dict[str, Any]]:
        """Async version of get_tags.
        
        Args:
            list_id: List identifier
            
        Returns:
            List of tag dictionaries
        """
        list_data = await self.aget(list_id, include=['tags'])
        
        tags = []
        if 'tag' in list_data:
            tag_data = list_data['tag']
            if isinstance(tag_data, dict):
                tags = [tag_data]
            elif isinstance(tag_data, list):
                tags = tag_data
                
        return tags
        
    def get_comments(self, list_id: Union[str, int]) -> List[Dict[str, Any]]:
        """Get public comments for a list.
        
        Args:
            list_id: List identifier
            
        Returns:
            List of comment dictionaries
        """
        list_data = self.get(list_id, include=['comments'])
        
        comments = []
        if 'comment' in list_data:
            comment_data = list_data['comment']
            if isinstance(comment_data, dict):
                comments = [comment_data]
            elif isinstance(comment_data, list):
                comments = comment_data
                
        return comments
        
    async def aget_comments(self, list_id: Union[str, int]) -> List[Dict[str, Any]]:
        """Async version of get_comments.
        
        Args:
            list_id: List identifier
            
        Returns:
            List of comment dictionaries
        """
        list_data = await self.aget(list_id, include=['comments'])
        
        comments = []
        if 'comment' in list_data:
            comment_data = list_data['comment']
            if isinstance(comment_data, dict):
                comments = [comment_data]
            elif isinstance(comment_data, list):
                comments = comment_data
                
        return comments