# Roadmap : régler le piège du `remotes[].host: ''` vide

## Contexte

`config/suggest --apply` crée un squelette `remotes:` dans chaque `.wex/env/<env>/config.yml` avec `host: ''` (vide). Le squelette n'est jamais rempli automatiquement — du coup la config est syntaxiquement valide mais sémantiquement cassée, et `remote_resolve` lève seulement à l'usage (`No 'host' field`).

Constat terrain (TPA, mai 2026) : sur 6 apps prod, **5 avaient `host: ''`** depuis la migration wex 6 — donc `master::info/show --remotes prod` plantait silencieusement pour ces 5 apps. Aucune erreur loud, juste des colonnes vides dans le dashboard. Le user a vécu avec, sans s'en rendre compte.

## Fichiers concernés

- [`wex-addon-app/src/wexample_wex_addon_app/commands/config/suggest.py`](../../../src/wexample_wex_addon_app/commands/config/suggest.py) — produit le squelette `_REMOTES_SKELETON`
- [`wex-addon-app/src/wexample_wex_addon_app/helpers/remote.py`](../../../src/wexample_wex_addon_app/helpers/remote.py) — `remote_resolve()` qui exige `host:` non-vide

## Friction connexe — RÉSOLUE 2026-05-28

Les configs prod ont aussi `server: {ip: X.X.X.X}` séparément. Donc **deux champs pour la même info** :
- `server.ip`
- `remotes[0].host`

**Cause du bug** : `migration_6_0_90__1.py` était censé convertir `server:` → `remotes:`, mais bail si `remotes:` existe déjà. Or `config/suggest --apply` ajoute un skeleton `remotes:[{host: ''}]` qui empêche 6.0.90 de fire. Résultat : duplication permanente.

**Fix appliqué** : nouvelle migration [`migration_6_0_103__1.py`](../../../src/wexample_wex_addon_app/migrations/migration_6_0_103__1.py) qui gère le cas où `server:` et un `remotes:` vide coexistent → fill host depuis server.ip + drop server. Idempotent. Sera appliquée au prochain `wex app::migration/run` sur les apps stampées à 6.0.101.

## Pistes de solution

### Option A — Auto-fill `host` depuis `server.ip`

Dans `remote_resolve()`, si `selected.host` est vide, fallback sur `server.ip` du même config. Avantage : zéro changement de schéma, marche rétroactivement sur les configs existantes. Inconvénient : silence sur le fait que `host` est vide → reste un piège si quelqu'un cherche à override le host d'un remote particulier.

### Option B — Faire de `server.ip` la source de vérité, virer `host`

Plus radical : le concept "ip du serveur" et "host du remote" sont en pratique le même truc. Garder `server.ip`, supprimer `host` du schéma `remotes`. Reste utile si on a un jour plusieurs remotes pour un même env (mais à ce stade c'est de la spec future, on n'a pas le cas).

### Option C — Validation early au start

Si on garde le schéma actuel, au moins valider à `app::config/check` (ou à la fin de `config/suggest --apply`) que `host:` est rempli. Erreur explicite : "Remote 'main' (env prod) needs a host — edit .wex/env/prod/config.yml".

### Option D — Skeleton plus loud

Au lieu de `host: ''`, mettre `host: REQUIRED_FILL_ME_OR_WEX_WILL_FAIL` (ou commentaire en gras). Pression sociale + plante avec un message clair quand `remote_resolve` essaie de SSH dessus.

## Recommandation

**A + C** :
- (A) auto-fill silencieux `host ← server.ip` pour la rétro-compat — règle immédiatement les 5 configs TPA et toutes les autres apps avec la même histoire
- (C) check explicite à `config/suggest` et au start pour planter early si vraiment rien n'est dispo

Garde le schéma `remotes` pour le jour où on aura besoin de multi-remote (failover, region).

## Verification

Après fix :
1. Reset un `.wex/env/prod/config.yml` à `host: ''` sur une app de test
2. `wex master::info/show --remotes prod` doit montrer les bonnes données (via fallback `server.ip`)
3. Supprimer aussi `server.ip` → `wex app::config/check` doit retourner une erreur explicite
