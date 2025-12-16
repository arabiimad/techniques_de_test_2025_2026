# RETEX - Triangulator

## En gros

Le TP m'a obligé à faire du test-first sur un vrai projet et franchement
ça change pas mal de ma manière habituelle de coder. Au début j'étais
sceptique mais à la fin je trouve que c'est plutôt mieux. Le projet en
lui-même (algo de triangulation + format binaire custom + micro-service)
c'était pas évident, surtout l'algo.

## Ce qui a marché

Écrire les tests avant le code, ça m'a forcé à réfléchir à ce que chaque
fonction devait faire avant de la pondre. Du coup j'ai pondu moins de
fonctions n'importe comment, et quand j'ai dû refactorer j'avais les
tests pour me protéger.

Le découpage en 4 modules (`binary_codec`, `triangulation`,
`point_set_client`, `app`) c'était une bonne idée : chaque module se
teste tout seul, et quand un test pète je sais où regarder. L'injection
du client dans `create_app(point_set_client=...)` m'a sauvé pour les
tests API parce que j'ai pu passer un mock au lieu de monter un vrai
serveur.

Les tests de perf séparés (`@pytest.mark.performance`) c'était cool
aussi parce que comme ça je lance pas les benchs à chaque modif.

## Ce qui a été chiant

L'algo de Bowyer-Watson. De loin le plus pénible.

- Les points colinéaires : ça fait diviser par zéro dans le calcul du
  cercle circonscrit. J'ai ajouté un epsilon `abs(d) < 1e-10` pour
  détecter, et dans ce cas je retourne `None` et le triangle est
  considéré non valide. Au début j'avais mis `1e-6` mais c'était trop
  strict, certains triangles légitimes passaient pour colinéaires.

- Super-triangle trop petit : mon premier essai prenait juste le
  bounding-box +1, certains points se retrouvaient en bordure et l'algo
  partait en cacahuète. J'ai fini par mettre `20 * delta_max` autour
  du centre. Pas joli mais ça marche.

- Bug du cercle circonscrit : j'ai passé genre 2h sur un truc où des
  triangles se chevauchaient. C'était parce que je comparais `dist² < r²`
  mais j'avais en fait `dist < r²` (j'avais oublié la racine carrée
  quelque part dans la comparaison). Hyper bête.

- Pas de visu : c'est dur de débugger une triangulation rien qu'avec
  des nombres. J'aurais dû faire un petit script qui sort un SVG ou
  matplotlib mais j'ai pas pris le temps, du coup j'ai galéré.

Pour le format binaire, le sujet est précis mais y'a quelques détails :

- Endianness pas spec : j'ai mis little-endian (`<` dans `struct.pack`)
  parce que c'est le plus courant. Si jamais le client est big-endian
  ça pétera, faudrait un test contractuel avec le client réel.
- Validation à chaque étape du décodage : sinon on tombe sur des
  erreurs `struct.error` cryptiques. J'ai mis des `DecodingError` avec
  des messages explicites.
- Calcul de la taille des buffers : j'ai fait 2-3 typos avant que ça
  tombe juste (oubli du champ count, etc.). Les tests "roundtrip" ont
  vite trouvé le souci.

Les mocks pour `PointSetClient` c'était la première fois que je faisais
ça vraiment proprement. Ma classe `MockPointSetClient` configurable avec
`set_points()` et `set_failure()` m'a pas mal aidé. Au début j'avais
juste fait `unittest.mock.MagicMock()` et c'était illisible, donc j'ai
fait une vraie classe.

## Ce que je referais autrement

Le plan de tests initial était trop tabulé / trop formel avec des IDs
genre `BC-01`. Sur papier ça fait pro mais en pratique j'ai jamais
relu ces IDs après. Je ferais un plan plus court, plus orienté "voilà
les cas que je veux couvrir et pourquoi" sans le côté checklist.

Pour l'algo, j'aurais dû commencer par une version naïve qui marche
(genre un brute force qui teste tous les triangles possibles avec 5
points) puis remplacer par Bowyer-Watson en gardant les tests.
J'ai voulu attaquer Bowyer-Watson direct, et comme j'avais pas d'algo
de référence pour comparer, j'ai galéré.

J'aurais aussi dû faire les docstrings au fur et à mesure. J'ai tout
fait à la fin pour passer ruff avec la convention Google et c'était
chiant. Petits régrets aussi sur le manque de logs : sans `print` ni
`logging` j'ai débogué un peu à l'aveugle.

## Ce que j'ai appris

- Le test-first c'est pas une perte de temps. La première heure
  c'est lent, mais après ça paye.
- Les fixtures pytest c'est super puissant pour pas répéter le même
  setup. J'ai compris ça un peu tard, du coup mes premiers tests ont
  du code dupliqué.
- Faut pas mocker trop, sinon on teste plus le code mais juste le
  mock. J'essaie de mocker au plus haut niveau (ici le `PointSetClient`)
  et de laisser le reste réel.
- L'archi modulaire avec injection de dépendances ça aide énormément
  pour les tests. C'est pas juste un truc de design pattern, c'est
  vraiment utile.

## État final

Tous les tests unitaires passent (`make unit_test`). `make lint` passe
sans erreur. `make doc` génère bien la doc HTML. Couverture autour de
95% (pas 100%, y'a quelques branches d'erreur réseau que je vois pas
comment tester sans un vrai serveur en panne).

Bilan : projet pas facile mais formateur. Test-first j'y suis maintenant
convaincu. Et l'algo de Delaunay je le re-coderais pas par plaisir.
