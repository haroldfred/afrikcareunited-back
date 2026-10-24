#!/usr/bin/env bash
# Crée infra/.env à partir de .env.example : chaque valeur « a-generer » devient un secret aléatoire.
# Ne remplace jamais un .env existant. Le fichier créé n'est lisible que par son propriétaire.
set -euo pipefail
cd "$(dirname "$0")"

if [ -f .env ]; then
  echo "infra/.env existe déjà : rien n'est modifié."
  exit 0
fi

umask 077
while IFS= read -r line || [ -n "$line" ]; do
  if [[ "$line" == *=a-generer ]]; then
    # 32 caractères alphanumériques : sans caractère spécial, utilisables tels quels dans les URL et le shell.
    # pipefail est levé dans la sous-commande : « head » ferme le tube, « tr » reçoit SIGPIPE, c'est attendu.
    secret="$(set +o pipefail; LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 32)"
    printf '%s=%s\n' "${line%%=*}" "$secret"
  else
    printf '%s\n' "$line"
  fi
done < .env.example > .env

echo "infra/.env créé avec des secrets aléatoires (droits 600)."
