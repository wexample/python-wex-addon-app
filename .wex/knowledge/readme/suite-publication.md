# Suite Publication

## Commande

```bash
wex package::suite/publish --yes
```

Depuis la racine de la suite (ex. `PACKAGES/PYTHON/`).

---

## Ce que fait `suite/publish`

**1. Affiche le statut**
Chaque package indique sa version, le type de bump prévu (`patch` / `minor` / `major`) et s'il est `to publish` ou `up to date`.

**2. Valide les dépendances internes**
Vérifie que les imports correspondent aux déclarations dans les `pyproject.toml`.
Auto-corrige aussi les pins `==` sur des packages internes → convertis en `>=` (les packages modifiés sont alors inclus automatiquement dans la publication).

**3. Synchronise les bibliothèques externes** (`libraries/sync`)
Si un package est configuré avec des `libraries` externes (suites tierces), leurs versions sont mises à jour.

**4. Publie dans l'ordre topologique** (feuilles → tronc)
Pour chaque package avec des changements :
- **Bump** : incrémente la version selon le type de changement détecté
- **Rectify** : applique le file state (README, structure, etc.)
- **Commit & push** : commit les changements sur une branche `version-x.y.z`
- **Propagate** : met à jour les dépendants dans la suite avec `>=nouvelle_version` (uniquement pour les bumps intermediate/major)
- **Publish** : upload sur PyPI

---

## Types de bump

| Type | Chiffre modifié | Propagation aux dépendants |
|---|---|---|
| `minor` (patch) | 3ème (`x.y.Z`) | Non — `>=` déjà satisfait |
| `intermediate` (minor) | 2ème (`x.Y.z`) | Oui |
| `major` | 1er (`X.y.z`) | Oui |

La détection est automatique : changements dans `src/` → intermediate ou major, reste → minor.

---

## Règles sur les contraintes

Les dépendances **internes** (packages de la suite) doivent toujours utiliser `>=`, jamais `==`.
Un pin `==` survivra aux bumps mineurs sans se mettre à jour, causant des échecs de résolution (`pip`/`uv` backtracking silencieux).

La validation au début de `suite/publish` auto-corrige les violations.

---

## Après la publication

Mettre à jour `requirements.txt` dans les projets consommateurs :

```bash
uv pip compile requirements.in --upgrade --output-file requirements.txt
```

> `pip-compile` peut échouer avec `ResolutionTooDeepError` sur des suites profondes — utiliser `uv` à la place.
