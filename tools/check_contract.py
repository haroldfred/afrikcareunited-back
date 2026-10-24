"""Project-specific checks on the M0 OpenAPI contract, beyond Redocly and openapi-spec-validator.
Usage: python3 tools/check_contract.py contracts/afrikcareunited-m0-openapi.yaml
Exit code 1 if any check fails.
"""
import sys

import yaml

METHODS = ('get', 'post', 'put', 'patch', 'delete')
UNSAFE = ('post', 'put', 'patch', 'delete')
ORG_PREFIXES = ('/home', '/users', '/roles', '/permissions', '/audit-events', '/organization')

spec = yaml.safe_load(open(sys.argv[1], encoding='utf-8'))
comp = spec['components']
problems = []


def walk(node, refs):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == '$ref' and isinstance(v, str):
                refs.add(v)
            else:
                walk(v, refs)
    elif isinstance(node, list):
        for v in node:
            walk(v, refs)


refs = set()
walk(spec, refs)
for r in sorted(refs):
    parts = r.lstrip('#/').split('/')
    node = spec
    for part in parts:
        node = node.get(part) if isinstance(node, dict) else None
        if node is None:
            problems.append(f'unresolved $ref {r}')
            break
used = {r.split('/')[-1] for r in refs}
for kind in ('schemas', 'parameters', 'responses', 'headers'):
    for name in comp.get(kind, {}):
        if name not in used:
            problems.append(f'unused component {kind}/{name}')

permissions = set(comp['schemas']['PermissionCode']['enum']) | {'platform.operator'}
actions = set(comp['schemas']['AuditAction']['enum'])
op_ids = {}
n_ops = 0
for path, item in spec['paths'].items():
    for method in METHODS:
        op = item.get(method)
        if not op:
            continue
        n_ops += 1
        where = f'{method.upper()} {path}'
        oid = op.get('operationId')
        if oid in op_ids:
            problems.append(f'duplicate operationId {oid}: {where} and {op_ids[oid]}')
        op_ids[oid] = where
        if not op.get('x-user-stories') and path != '/config':
            problems.append(f'{where}: no x-user-stories')
        for p in op.get('x-permissions', []):
            if p not in permissions:
                problems.append(f'{where}: unknown permission {p}')
        a = op.get('x-audit-action')
        for one in (a if isinstance(a, list) else [a] if a else []):
            if one not in actions:
                problems.append(f'{where}: unknown audit action {one}')
        if path.startswith('/users/{userId}') and method in UNSAFE and not path.endswith('/phone/reveal'):
            if op.get('x-target-scope') is not True:
                problems.append(f'{where}: write on a person without x-target-scope')
        if op.get('x-target-scope') and '403' not in {str(c) for c in op['responses']}:
            problems.append(f'{where}: x-target-scope without 403')
        security = op.get('security', spec.get('security', []))
        if method in UNSAFE and path != '/auth/logout' or path == '/auth/logout':
            authed = [s for s in security if s]
            if method in UNSAFE and any('sessionCookie' in s and 'csrfToken' not in s for s in authed):
                problems.append(f'{where}: session without CSRF on an unsafe method')
            if method in UNSAFE and path.startswith(('/invitations',)) is False and not authed:
                problems.append(f'{where}: unsafe method without authentication')
        prm = [x.get('$ref', '').split('/')[-1] for x in op.get('parameters', [])]
        codes = {str(c) for c in op['responses']}
        if 'IdempotencyKey' in prm and '400' not in codes:
            problems.append(f'{where}: Idempotency-Key without 400')
        if path.startswith(ORG_PREFIXES):
            if 'ExpectedContext' not in prm:
                problems.append(f'{where}: no ACU-Context parameter')
            if '409' not in codes:
                problems.append(f'{where}: no 409 for context-mismatch')
            if '400' not in codes:
                problems.append(f'{where}: no 400 for context-required')
        if not path.startswith('/auth') and path != '/config' and 'UserActivity' not in prm:
            problems.append(f'{where}: no ACU-Activity parameter')
        if method in ('patch',) or (method == 'delete' and '{' in path.split('/')[-1]):
            if 'IfMatch' not in prm and not path.startswith('/session'):  # sessions are not versioned
                problems.append(f'{where}: no If-Match')
        body = op.get('requestBody', {}).get('content', {}).get('application/json', {}).get('schema', {})
        name = body.get('$ref', '').split('/')[-1]
        if method == 'post' and name.endswith('Create') or name == 'AssignmentInput':
            idp = comp['schemas'][name]['properties'].get('id', {})
            if idp.get('$ref', '').split('/')[-1] != 'Uuid7':
                problems.append(f'{where}: client id of {name} is not Uuid7')

print(f"{len(spec['paths'])} paths, {n_ops} operations, {len(comp['schemas'])} schemas, "
      f"{len(comp['schemas']['PermissionCode']['enum'])} permissions, {len(actions)} audit actions, "
      f"{len(comp['schemas']['ProblemCode']['enum'])} problem codes")
if problems:
    print(f'{len(problems)} problem(s):')
    for p in problems:
        print(' -', p)
    sys.exit(1)
print('all project checks passed')
