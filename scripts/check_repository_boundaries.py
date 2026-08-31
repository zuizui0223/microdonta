"""Fail when repository ownership or programme boundaries drift."""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY_PATH=ROOT/'repository_programs.json'
PYPROJECT_PATH=ROOT/'pyproject.toml'

def imported_modules(path:Path)->set[str]:
    tree=ast.parse(path.read_text(encoding='utf-8'),filename=str(path)); out=set()
    for node in ast.walk(tree):
        if isinstance(node,ast.Import): out.update(a.name for a in node.names)
        elif isinstance(node,ast.ImportFrom) and node.module: out.add(node.module)
    return out

def distribution_packages()->set[str]:
    text=PYPROJECT_PATH.read_text(encoding='utf-8')
    block=re.search(r'\[tool\.setuptools\](.*?)(?:\n\[|\Z)',text,flags=re.DOTALL)
    match=re.search(r'packages\s*=\s*\[(.*?)\]',block.group(1),flags=re.DOTALL) if block else None
    if not match: raise SystemExit('cannot parse tool.setuptools packages')
    return set(re.findall(r'["\']([^"\']+)["\']',match.group(1)))

def main():
    registry=json.loads(REGISTRY_PATH.read_text(encoding='utf-8')); errors=[]
    for name,program in registry['programs'].items():
        for rel in program['roots']:
            if not (ROOT/rel).exists(): errors.append(f'{name}: missing registered root {rel}')
    expected=set(registry['distribution_packages']); actual=distribution_packages()
    if actual!=expected: errors.append(f'distribution package boundary changed: expected {sorted(expected)}, got {sorted(actual)}')

    for name,external in registry['external_programs'].items():
        for rel in external['forbidden_roots']:
            if (ROOT/rel).exists(): errors.append(f'external programme copied locally ({name}): {rel}')
        for module in external.get('forbidden_module_names',[]):
            stale=ROOT/'causal_model'/f'{module}.py'
            if stale.exists(): errors.append(f'external module remains in causal_model ({name}): {stale.relative_to(ROOT)}')

    for rule in registry['forbidden_imports']:
        source=ROOT/rule['from_root']; target=rule['to_module']
        for path in source.rglob('*.py'):
            for module in imported_modules(path):
                if module==target or module.startswith(target+'.'):
                    errors.append(f'forbidden dependency {path.relative_to(ROOT)} -> {module}')

    if (ROOT/'streamlit_app.py').exists(): errors.append('interactive app returned to repository root')

    translation=json.loads((ROOT/'examples/island_pollination_translation/CURRENT_STATE.json').read_text(encoding='utf-8'))
    expected_tracks=registry['programs']['island_pollination_translation']['track_ids']
    actual_tracks=[row['track_id'] for row in translation['tracks']]
    if actual_tracks!=expected_tracks: errors.append(f'island translation tracks changed: expected {expected_tracks}, got {actual_tracks}')

    portfolio=json.loads((ROOT/registry['portfolio_registry']).read_text(encoding='utf-8'))
    expected_repositories={
        'hotarubukuro','azami','bita','island','microdonta','boundary','pollipi','insepi','acsp',
        'eco-genetic-criticality','ccoc','izu-core','eco-genetic-warning-extensions','mltr','ced','mrm',
        'shimahotarubukuro','fcp','eog','odsp','EAzami','chun','sdmr','crest'
    }
    listed=[e['name'] for e in portfolio['repositories']]
    if len(listed)!=len(set(listed)): errors.append('portfolio registry contains duplicate names')
    if set(listed)!=expected_repositories:
        errors.append(f'portfolio registry drift: missing={sorted(expected_repositories-set(listed))}, extra={sorted(set(listed)-expected_repositories)}')

    if errors: raise SystemExit('repository boundary check failed:\n- '+'\n- '.join(errors))
    print('repository program boundaries OK')
    print('distribution: '+', '.join(sorted(actual)))
    print('boundary paper owner: zuizui0223/boundary')
    print('portfolio repositories: 24')
    print('izu-core adapters: '+', '.join(actual_tracks))

if __name__=='__main__': main()
