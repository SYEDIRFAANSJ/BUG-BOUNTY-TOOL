import re

def detect_asset_type(raw_identifier: str) -> str:
    raw = raw_identifier.strip().lower()
    if raw.startswith('*.'):
        return 'wildcard_domain'
    
    if re.match(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$', raw):
        return 'ip'
        
    if re.match(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}/[0-9]{1,2}$', raw):
        return 'ip_range'
        
    if raw.endswith('.apk'):
        return 'android'
        
    if raw.endswith('.ipa'):
        return 'ios'
        
    if '/api' in raw:
        return 'api'
        
    if re.match(r'^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$', raw):
        return 'domain'
        
    return 'other'

def normalize_scope_item(raw_item: dict, platform_name: str) -> dict | None:
    platform = platform_name.lower()
    
    if platform == 'hackerone':
        attrs = raw_item.get('attributes', {}) if 'attributes' in raw_item else raw_item
        identifier = attrs.get('asset_identifier', '')
        if not identifier:
            return None
            
        return {
            'asset_identifier': identifier,
            'asset_type': detect_asset_type(identifier),
            'in_scope': attrs.get('eligible_for_submission', False) or raw_item.get('eligible_for_submission', False),
            'eligible_for_bounty': attrs.get('eligible_for_bounty', False) or raw_item.get('eligible_for_bounty', False)
        }
        
    elif platform == 'bugcrowd':
        attrs = raw_item.get('attributes', {}) if 'attributes' in raw_item else raw_item
        identifier = attrs.get('name', '') or raw_item.get('name', '')
        if not identifier:
            return None
            
        return {
            'asset_identifier': identifier,
            'asset_type': detect_asset_type(identifier),
            'in_scope': raw_item.get('in_scope', False),
            'eligible_for_bounty': attrs.get('rewardable', False) or raw_item.get('rewardable', False)
        }
        
    elif platform == 'intigriti':
        identifier = raw_item.get('endpoint', '') or raw_item.get('id', '')
        if not identifier:
            return None
            
        return {
            'asset_identifier': str(identifier),
            'asset_type': detect_asset_type(str(identifier)),
            'in_scope': raw_item.get('in_scope', False),
            'eligible_for_bounty': raw_item.get('bountyTier') is not None or raw_item.get('eligible_for_bounty', False)
        }
        
    return None
