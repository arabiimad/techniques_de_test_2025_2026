# Plan de tests - Triangulator

## Idée

On doit faire un micro-service de triangulation (Delaunay) en Python/Flask.
Le sujet demande de bosser test-first, donc l'idée c'est d'écrire les tests
avant le code. Du coup ici je liste ce que je compte tester et comment.

Ce plan pourra (devra ?) bouger en cours de route quand je vais me rendre
compte que j'avais oublié des trucs.

## Découpage du code

Je vais découper en 4 modules dans `src/triangulator/` :

- `binary_codec.py` : encode/decode des formats binaires PointSet et Triangles
- `triangulation.py` : l'algo de Delaunay (Bowyer-Watson)
- `point_set_client.py` : client HTTP pour aller chercher les points sur le PointSetManager
- `app.py` : l'API Flask (endpoint `/triangulation/{id}`)
- `exceptions.py` : les exceptions custom (juste de la donnée)

Comme ça chaque module se teste à peu près en isolation.

## Ce que je veux tester

### Codec binaire

C'est le plus important parce que c'est l'interop avec le PointSetManager
et avec le client. Si on se trompe d'un octet, plus rien marche.

Cas à couvrir :
- encode/decode d'un PointSet vide (0 points), 1 point, plein de points
- encode/decode d'une triangulation simple
- decode de données corrompues / tronquées → doit lever DecodingError
- roundtrip (encode puis decode redonne la même chose, modulo précision float)
- valeurs limites (très grandes, très petites)

Endianness : le sujet précise pas. Je pars sur little-endian, faut le noter
quelque part (et le tester pour pas que ça change par accident).

### Triangulation

Le coeur du truc. Tests :
- 3 points → 1 triangle, pas de surprise
- 4 points en carré → 2 triangles
- 0, 1, 2 points → 0 triangle (pas planter)
- points colinéaires → cas chiant, à voir comment je gère (probablement 0 triangle ou un truc dégénéré)
- doublons → pas planter, dédoublonner
- gros ensemble (100 points pseudo-aléatoires + grille + cercle) → triangulation valide
- propriété de Delaunay : aucun point dans le cercle circonscrit d'un triangle
  → fonction de validation à part qui parcourt tout

Pour le cercle circonscrit lui-même je vais tester séparément les fonctions
auxiliaires (`_circumcircle`, `_point_in_circumcircle`).

### Client PointSetManager

Là on parle HTTP, donc tests avec mock obligatoirement (pas de vrai serveur).
Scénarios :
- réponse 200 + bytes valides → liste de Points
- 400 → InvalidUUIDError
- 404 → PointSetNotFoundError
- 503 → ServiceUnavailableError
- timeout / pas de réseau → ServiceUnavailableError
- 200 + bytes corrompus → DecodingError

Validation UUID séparée : `validate_uuid()` doit accepter les UUIDs avec ou
sans tirets, rejeter le reste (vide, None, format pourri).

### API Flask

Endpoint `GET /triangulation/{uuid}`. Tests via le test_client Flask + un
mock du PointSetClient (j'injecte le client à la création de l'app, comme ça
les tests utilisent un mock contrôlé).

À vérifier :
- 200 + Content-Type `application/octet-stream` quand tout va bien
- 400 si l'UUID est pourri
- 404 si le PointSet n'existe pas
- 503 si le PointSetManager est down
- format JSON pour les erreurs avec `code` et `message`
- endpoint `/health` → 200 + JSON `{status: healthy}`

### Perfs

À part dans `tests/performance/`, marqueur `@pytest.mark.performance` pour
pouvoir les exclure des runs normaux (sinon ça ralentit tout).

Idée :
- triangulation 10 / 100 / 1000 / 10000 points avec budget temps
- encode/decode 10000 points (doit être rapide, c'est juste du struct.pack)
- vérifier scalabilité (genre temps / n*log(n) à peu près constant)
- cas chiants : grille, cercle, clusters

Les seuils de temps sont indicatifs, à ajuster selon la machine.

## Organisation des tests

```
tests/
  conftest.py             -> fixtures partagées
  unit/
    test_binary_codec.py
    test_triangulation.py
    test_point_set_client.py
    test_api.py           (j'avais mis ça en integration au début mais
                           finalement avec le test_client Flask ça reste
                           unitaire, je laisse dans unit/)
  performance/
    test_performance.py
```

Fixtures principales que je prévois (dans `conftest.py`) :
- `empty_point_set`, `single_point`, `two_points`, `triangle_points`,
  `square_points`, `collinear_points`, `duplicate_points`, `large_point_set`
- `valid_binary_point_set` (déjà encodé), `corrupted_binary_data`, `truncated_binary_data`
- `valid_uuid`, `invalid_uuid`, `another_valid_uuid`
- `mock_client` (mon `MockPointSetClient` configurable)
- `test_app`, `test_client` (Flask en mode TESTING avec mock injecté)

Marqueurs pytest :
- `unit` : tests rapides
- `integration` : tests qui touchent à plus d'un module (l'API)
- `performance` : benchs (exclus par défaut)
- `slow` : tests qui durent plus d'1s

## Outillage

Make targets :
- `make test` : tout
- `make unit_test` : sans les perfs
- `make perf_test` : que les perfs
- `make coverage` : rapport couverture (objectif viser ~haute couverture,
  100% c'est idéaliste mais on essaie)
- `make lint` : ruff
- `make doc` : pdoc3

## À faire dans cet ordre

1. Setup pytest + conftest + fixtures vides (cette séance)
2. Écrire les tests codec binaire (le plus simple)
3. Écrire les tests triangulation (gros morceau)
4. Tests client HTTP + API
5. Tests perfs
6. Implémentation guidée par les tests qui sont rouges
7. Doc + lint en fin
