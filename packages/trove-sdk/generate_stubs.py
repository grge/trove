#!/usr/bin/env python3
"""Generate type stub files for better IDE support."""

def generate_model_stub(model_name: str, fields: list) -> str:
    """Generate a type stub for a Pydantic model."""
    stub = f'''"""Type stub for {model_name} model."""

from typing import List, Optional, Dict, Any
from .base import TroveBaseModel

class {model_name}(TroveBaseModel):
    """Type-safe {model_name.lower()} model."""
    
    # Core fields
    id: str
'''
    
    for field in fields:
        if field['optional']:
            stub += f"    {field['name']}: Optional[{field['type']}] = None\n"
        else:
            stub += f"    {field['name']}: {field['type']}\n"
    
    stub += '''
    # Properties
    @property
    def raw(self) -> Dict[str, Any]: ...
    
    def __getitem__(self, key: str) -> Any: ...
    
    def __contains__(self, key: str) -> bool: ...
    
    def get(self, key: str, default: Any = None) -> Any: ...
'''
    
    return stub

# Define model fields
work_fields = [
    {'name': 'title', 'type': 'str', 'optional': True},
    {'name': 'contributor', 'type': 'List[str]', 'optional': False},
    {'name': 'issued', 'type': 'str', 'optional': True},
    {'name': 'publication_year', 'type': 'int', 'optional': True},
]

article_fields = [
    {'name': 'heading', 'type': 'str', 'optional': True},
    {'name': 'date', 'type': 'str', 'optional': True},
    {'name': 'article_text', 'type': 'str', 'optional': True},
    {'name': 'word_count', 'type': 'int', 'optional': True},
]

# Generate stub files
stubs = {
    'work.pyi': generate_model_stub('Work', work_fields),
    'article.pyi': generate_model_stub('Article', article_fields),
}

for filename, content in stubs.items():
    with open(f'trove/models/{filename}', 'w') as f:
        f.write(content)
    print(f"Generated {filename}")

print("Type stub generation completed!")