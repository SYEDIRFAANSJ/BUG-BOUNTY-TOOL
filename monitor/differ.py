import hashlib
import json
from dataclasses import dataclass
from db.models import Program

@dataclass
class DiffResult:
    type: str  # 'new' | 'scope_changed' | 'unchanged'
    added: list[str]
    removed: list[str]

def compute_scope_hash(scope_list: list[dict]) -> str:
    sorted_scope = sorted(scope_list, key=lambda x: x.get('asset_identifier', ''))
    hash_data = []
    for item in sorted_scope:
        hash_data.append({
            'asset_identifier': item.get('asset_identifier'),
            'asset_type': item.get('asset_type'),
            'in_scope': item.get('in_scope'),
            'eligible_for_bounty': item.get('eligible_for_bounty')
        })
    json_str = json.dumps(hash_data, sort_keys=True)
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()

def diff_program(existing_program: Program | None, new_scope_hash: str, new_scope_data: list[dict]) -> DiffResult:
    if existing_program is None:
        return DiffResult(type='new', added=[item['asset_identifier'] for item in new_scope_data], removed=[])
    
    if existing_program.scope_hash != new_scope_hash:
        existing_assets = {scope.asset_identifier for scope in existing_program.scopes} if hasattr(existing_program, 'scopes') else set()
        new_assets = {item['asset_identifier'] for item in new_scope_data}
        
        added = list(new_assets - existing_assets)
        removed = list(existing_assets - new_assets)
        
        return DiffResult(type='scope_changed', added=added, removed=removed)
        
    return DiffResult(type='unchanged', added=[], removed=[])
