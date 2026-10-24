"""Contrôles de l'environnement local (lot L1) sans Docker : versions épinglées, ports locaux,
variables toutes déclarées dans .env.example, aucun secret écrit, marqueurs des realms fournis à Keycloak.
Usage : python3 tools/check_infra.py infra
Le CI lance en plus « docker compose config » et démarre la pile.
"""
import json
import re
import sys
from pathlib import Path

import yaml

infra = Path(sys.argv[1] if len(sys.argv) > 1 else 'infra')
problems: list[str] = []
VARIABLE = re.compile(r'\$\{([A-Z0-9_]+)(?::?[-?][^}]*)?\}')


def check(condition: bool, message: str) -> None:
    if not condition:
        problems.append(message)


compose_text = (infra / 'docker-compose.yml').read_text(encoding='utf-8')
compose = yaml.safe_load(compose_text)
services = compose.get('services', {})
check(set(services) == {'postgres', 'keycloak', 'mailpit'}, f'services attendus : postgres, keycloak, mailpit ({sorted(services)})')

expected_images = {'postgres': 'postgres:18.6', 'keycloak': 'quay.io/keycloak/keycloak:26.8.1', 'mailpit': 'axllent/mailpit:v1.32.0'}
for name, service in services.items():
    image = service.get('image', '')
    check(':' in image and not image.endswith(':latest'), f'{name} : image sans version épinglée ({image})')
    check(image == expected_images.get(name), f'{name} : image {image}, attendue {expected_images.get(name)} (docs/versions.md)')
    for port in service.get('ports', []):
        check(str(port).startswith('127.0.0.1:'), f'{name} : port {port} ouvert hors de la machine locale')
    environment = service.get('environment', {})
    for key, value in environment.items():
        if re.search(r'PASSWORD|SECRET', key):
            check(isinstance(value, str) and VARIABLE.fullmatch(value) is not None,
                  f'{name} : {key} doit venir de infra/.env (valeur écrite en clair)')
for name in ('postgres', 'keycloak'):
    check('healthcheck' in services.get(name, {}), f'{name} : sonde de santé absente')

# Variables : toutes déclarées dans .env.example, secrets jamais renseignés dans le modèle.
example = {}
for line in (infra / '.env.example').read_text(encoding='utf-8').splitlines():
    if line and not line.startswith('#') and '=' in line:
        key, value = line.split('=', 1)
        example[key] = value
used = set(VARIABLE.findall(compose_text))
for variable in sorted(used):
    check(variable in example, f'{variable} utilisée par docker-compose.yml mais absente de .env.example')
for key, value in example.items():
    if re.search(r'PASSWORD|SECRET', key):
        check(value == 'a-generer', f'.env.example : {key} doit valoir « a-generer », jamais un secret')

# Script d'initialisation de PostgreSQL : ses variables sont transmises au conteneur.
init = (infra / 'postgres' / 'initdb' / '01-bases-et-roles.sh').read_text(encoding='utf-8')
postgres_env = set(services['postgres'].get('environment', {}))
for variable in sorted(set(re.findall(r'\b(ACU_[A-Z0-9_]+)', init))):
    check(variable in postgres_env, f'postgres : {variable} lue par l’initialisation mais non transmise au conteneur')

# Realms : chaque marqueur ${...} sans valeur par défaut est fourni au conteneur Keycloak.
keycloak_env = set(services['keycloak'].get('environment', {}))
for realm_file in sorted((infra / 'keycloak' / 'realms').glob('*.json')):
    text = realm_file.read_text(encoding='utf-8')
    json.loads(text)
    for match in re.finditer(r'\$\{(ACU_[A-Z0-9_]+)(:[^}]*)?\}', text):
        if match.group(2) is None:
            check(match.group(1) in keycloak_env, f'{realm_file.name} : {match.group(1)} non fournie à Keycloak')

if problems:
    print(f'{len(problems)} écart(s) :')
    for p in problems:
        print(' -', p)
    sys.exit(1)
print(f'Environnement local : {len(services)} services épinglés, ports locaux, {len(used)} variables déclarées, aucun secret écrit.')
