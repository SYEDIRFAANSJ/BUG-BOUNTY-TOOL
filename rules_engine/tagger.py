import yaml
import re
import os

RULES_PATH = os.path.join(os.path.dirname(__file__), 'rules.yaml')
with open(RULES_PATH, 'r') as f:
    RULES = yaml.safe_load(f).get('rules', [])

def match_params(rule, data):
    if 'match_params' not in rule: return False
    return any(p in rule['match_params'] for p in data.get('params', []))

def match_params_regex(rule, data):
    if 'match_params_regex' not in rule: return False
    pat = re.compile(rule['match_params_regex'])
    return any(pat.match(p) for p in data.get('params', []))

def match_path_contains(rule, data):
    if 'match_path_contains' not in rule: return False
    return any(s in data.get('url', '') for s in rule['match_path_contains'])

def match_path_exact(rule, data):
    if 'match_path_exact' not in rule: return False
    return any(data.get('url', '').endswith(s) for s in rule['match_path_exact'])

def match_content_type(rule, data):
    if 'match_content_type' not in rule: return False
    return data.get('content_type') in rule['match_content_type']

def match_tech(rule, data):
    if 'match_tech' not in rule: return False
    return any(t in rule['match_tech'] for t in data.get('tech_stack', []))

def match_content_contains_patterns(rule, data):
    if 'match_content_contains_patterns' not in rule: return False
    return False # Placeholder

def is_api_endpoint(rule, data):
    if 'is_api_endpoint' not in rule: return False
    return '/api/' in data.get('url', '')

def match_header_or_param(rule, data):
    if 'match_header_or_param' not in rule: return False
    return any(p in rule['match_header_or_param'] for p in data.get('params', []))

def tech_version_check(rule, data):
    return False

MATCHER_REGISTRY = [
    match_params, match_params_regex, match_path_contains, match_path_exact,
    match_content_type, match_tech, match_content_contains_patterns,
    is_api_endpoint, match_header_or_param, tech_version_check
]

PRIORITY_MAP = {'high': 3, 'medium': 2, 'low': 1}
REV_PRIORITY_MAP = {3: 'high', 2: 'medium', 1: 'low'}

def tag_endpoint(endpoint_data: dict) -> tuple[list[str], str]:
    tags = set()
    max_priority = 0
    
    for rule in RULES:
        for matcher in MATCHER_REGISTRY:
            if matcher(rule, endpoint_data):
                tags.add(rule['tag'])
                max_priority = max(max_priority, PRIORITY_MAP.get(rule.get('priority', 'low'), 1))
                break
                
    priority_str = REV_PRIORITY_MAP.get(max_priority, 'low') if tags else 'low'
    return list(tags), priority_str
