"""People resource implementation for accessing people and organization records."""

from typing import Dict, Any, List, Union, Optional

from .base import BaseResource


class PeopleResource(BaseResource):
    """Resource for accessing people and organization records."""
    
    @property
    def endpoint_path(self) -> str:
        """API endpoint path for people resources."""
        return "/people"
        
    @property
    def valid_include_options(self) -> List[str]:
        """Valid include options for people resources."""
        return ['all', 'comments', 'lists', 'raweaccpf', 'tags']
        
    def _post_process_response(self, response: Dict[str, Any], person_id: Union[str, int]) -> Dict[str, Any]:
        """Post-process people response.
        
        Args:
            response: Raw API response
            person_id: The person ID that was requested
            
        Returns:
            Processed people data
        """
        if 'people' in response:
            people_data = response['people']
            if isinstance(people_data, dict) and 'id' not in people_data:
                people_data['id'] = str(person_id)
            return people_data
        return response
        
    def get_biographies(self, person_id: Union[str, int]) -> List[Dict[str, Any]]:
        """Get biographical information for a person/organization.
        
        Args:
            person_id: Person/organization identifier
            
        Returns:
            List of biography dictionaries
        """
        person = self.get(person_id, reclevel='full')
        
        biographies = []
        if 'biography' in person:
            bio_data = person['biography']
            if isinstance(bio_data, dict):
                biographies = [bio_data]
            elif isinstance(bio_data, list):
                biographies = bio_data
                
        return biographies
        
    async def aget_biographies(self, person_id: Union[str, int]) -> List[Dict[str, Any]]:
        """Async version of get_biographies.
        
        Args:
            person_id: Person/organization identifier
            
        Returns:
            List of biography dictionaries
        """
        person = await self.aget(person_id, reclevel='full')
        
        biographies = []
        if 'biography' in person:
            bio_data = person['biography']
            if isinstance(bio_data, dict):
                biographies = [bio_data]
            elif isinstance(bio_data, list):
                biographies = bio_data
                
        return biographies
        
    def get_raw_eac_cpf(self, person_id: Union[str, int]) -> Optional[str]:
        """Get raw EAC-CPF XML record.
        
        Args:
            person_id: Person/organization identifier
            
        Returns:
            Raw EAC-CPF XML or None if not available
        """
        person = self.get(person_id, include=['raweaccpf'])
        return person.get('raweaccpf')
        
    async def aget_raw_eac_cpf(self, person_id: Union[str, int]) -> Optional[str]:
        """Async version of get_raw_eac_cpf.
        
        Args:
            person_id: Person/organization identifier
            
        Returns:
            Raw EAC-CPF XML or None if not available
        """
        person = await self.aget(person_id, include=['raweaccpf'])
        return person.get('raweaccpf')
        
    def is_person(self, person_id: Union[str, int]) -> bool:
        """Check if record is a person (vs organization).
        
        Args:
            person_id: Person/organization identifier
            
        Returns:
            True if record is a person
        """
        person = self.get(person_id)
        return person.get('type') == 'person'
        
    async def ais_person(self, person_id: Union[str, int]) -> bool:
        """Async version of is_person.
        
        Args:
            person_id: Person/organization identifier
            
        Returns:
            True if record is a person
        """
        person = await self.aget(person_id)
        return person.get('type') == 'person'
        
    def is_organization(self, person_id: Union[str, int]) -> bool:
        """Check if record is an organization.
        
        Args:
            person_id: Person/organization identifier
            
        Returns:
            True if record is an organization
        """
        person = self.get(person_id)
        return person.get('type') in ['corporatebody', 'family']
        
    async def ais_organization(self, person_id: Union[str, int]) -> bool:
        """Async version of is_organization.
        
        Args:
            person_id: Person/organization identifier
            
        Returns:
            True if record is an organization
        """
        person = await self.aget(person_id)
        return person.get('type') in ['corporatebody', 'family']
        
    def get_occupations(self, person_id: Union[str, int]) -> List[str]:
        """Get occupations for a person record.
        
        Args:
            person_id: Person identifier
            
        Returns:
            List of occupation strings
        """
        person = self.get(person_id)
        occupations = person.get('occupation', [])
        
        if isinstance(occupations, str):
            return [occupations]
        elif isinstance(occupations, list):
            return occupations
        return []
        
    async def aget_occupations(self, person_id: Union[str, int]) -> List[str]:
        """Async version of get_occupations.
        
        Args:
            person_id: Person identifier
            
        Returns:
            List of occupation strings
        """
        person = await self.aget(person_id)
        occupations = person.get('occupation', [])
        
        if isinstance(occupations, str):
            return [occupations]
        elif isinstance(occupations, list):
            return occupations
        return []
        
    def get_primary_name(self, person_id: Union[str, int]) -> Optional[str]:
        """Get the primary name for a person/organization.
        
        Args:
            person_id: Person/organization identifier
            
        Returns:
            Primary name or None if not available
        """
        person = self.get(person_id)
        return person.get('primaryName') or person.get('primaryDisplayName')
        
    async def aget_primary_name(self, person_id: Union[str, int]) -> Optional[str]:
        """Async version of get_primary_name.
        
        Args:
            person_id: Person/organization identifier
            
        Returns:
            Primary name or None if not available
        """
        person = await self.aget(person_id)
        return person.get('primaryName') or person.get('primaryDisplayName')
        
    def get_alternate_names(self, person_id: Union[str, int]) -> List[str]:
        """Get alternate names for a person/organization.
        
        Args:
            person_id: Person/organization identifier
            
        Returns:
            List of alternate names
        """
        person = self.get(person_id)
        
        alt_names = []
        # Check both alternate name fields
        for field in ['alternateName', 'alternateDisplayName']:
            names = person.get(field, [])
            if isinstance(names, str):
                alt_names.append(names)
            elif isinstance(names, list):
                alt_names.extend(names)
                
        return alt_names
        
    async def aget_alternate_names(self, person_id: Union[str, int]) -> List[str]:
        """Async version of get_alternate_names.
        
        Args:
            person_id: Person/organization identifier
            
        Returns:
            List of alternate names
        """
        person = await self.aget(person_id)
        
        alt_names = []
        # Check both alternate name fields
        for field in ['alternateName', 'alternateDisplayName']:
            names = person.get(field, [])
            if isinstance(names, str):
                alt_names.append(names)
            elif isinstance(names, list):
                alt_names.extend(names)
                
        return alt_names
        
    def get_tags(self, person_id: Union[str, int]) -> List[Dict[str, Any]]:
        """Get public tags for a person/organization.
        
        Args:
            person_id: Person/organization identifier
            
        Returns:
            List of tag dictionaries
        """
        person = self.get(person_id, include=['tags'])
        
        tags = []
        if 'tag' in person:
            tag_data = person['tag']
            if isinstance(tag_data, dict):
                tags = [tag_data]
            elif isinstance(tag_data, list):
                tags = tag_data
                
        return tags
        
    async def aget_tags(self, person_id: Union[str, int]) -> List[Dict[str, Any]]:
        """Async version of get_tags.
        
        Args:
            person_id: Person/organization identifier
            
        Returns:
            List of tag dictionaries
        """
        person = await self.aget(person_id, include=['tags'])
        
        tags = []
        if 'tag' in person:
            tag_data = person['tag']
            if isinstance(tag_data, dict):
                tags = [tag_data]
            elif isinstance(tag_data, list):
                tags = tag_data
                
        return tags
        
    def get_comments(self, person_id: Union[str, int]) -> List[Dict[str, Any]]:
        """Get public comments for a person/organization.
        
        Args:
            person_id: Person/organization identifier
            
        Returns:
            List of comment dictionaries
        """
        person = self.get(person_id, include=['comments'])
        
        comments = []
        if 'comment' in person:
            comment_data = person['comment']
            if isinstance(comment_data, dict):
                comments = [comment_data]
            elif isinstance(comment_data, list):
                comments = comment_data
                
        return comments
        
    async def aget_comments(self, person_id: Union[str, int]) -> List[Dict[str, Any]]:
        """Async version of get_comments.
        
        Args:
            person_id: Person/organization identifier
            
        Returns:
            List of comment dictionaries
        """
        person = await self.aget(person_id, include=['comments'])
        
        comments = []
        if 'comment' in person:
            comment_data = person['comment']
            if isinstance(comment_data, dict):
                comments = [comment_data]
            elif isinstance(comment_data, list):
                comments = comment_data
                
        return comments