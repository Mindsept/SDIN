# Pourquoi ces règles OpenBao ?

## BAO-01 — Un store de secrets garde une mission précise

Déplacer toutes les données vers OpenBao ferait de sa disponibilité une
dépendance de chaque écran et multiplierait les lectures privilégiées. Les
credentials sont nécessaires pour joindre une ressource ; les documents,
sessions et préférences sont des données de l'application. Les séparer permet
d'appliquer à chacun une rétention, un débit et des droits adaptés.

## BAO-02 et BAO-03 — Deux phases, deux niveaux de privilèges

Créer une base ou un client OIDC nécessite plus de droits que les utiliser.
Donner les droits de provisioning au backend permettrait à une faille métier
de toucher les autres ressources. Une identité par app, voire par processus,
limite cette portée. La policy nomme les chemins nécessaires pour rendre le
besoin explicite et testable ; un nom de dossier n'est pas une permission.

Le TD utilise un token root commun. La skill explique cette limite au lieu de
faire croire qu'une lecture sous `secret/mon-app/` empêche une autre lecture.
Le lecteur restreint les chemins côté code, mais une vraie séparation exige
un token effectivement lié aux policies minimales.

## BAO-04 — Centraliser les secrets ne protège pas leurs copies

Un secret récupéré depuis OpenBao puis loggé ou exporté vers le frontend redevient
accessible hors du store. La règle couvre toute sa circulation, y compris les
erreurs, les fixtures et les arguments de scripts. Une suppression du fichier
committé ne suffit pas : l'ancien credential peut toujours fonctionner et être
présent dans l'historique. La réponse est une révocation/rotation vérifiée.

## BAO-05 et BAO-06 — Des dépendances validées avant les requêtes métier

Relire un mot de passe à chaque requête ajoute latence, charge et couplage sans
actualiser automatiquement un pool de connexion déjà ouvert. Charger, valider
et injecter un client configuré est plus simple. Ce choix exige toutefois un
refresh lors des rotations : le cache de démarrage ne doit pas être présenté
comme une rotation instantanée.

Un 403 révèle un accès refusé ; un 404 une donnée absente ou inaccessible selon
le contrat ; une erreur réseau ne dit rien sur l'existence du secret. Les traiter
tous comme « pas encore créé » peut changer un mot de passe persistant ou
écraser une map. L'échec explicite conserve l'état et permet un diagnostic.
Si une dépendance est optionnelle, on peut désactiver sa fonctionnalité sans
faire tomber une app dont le reste fonctionne.

## BAO-07 — Versionnement et concurrence sont des contrats différents

KV v2 permet de conserver des versions, mais un `put` sans CAS peut écraser la
mise à jour simultanée d'un autre processus. Les maps de budgets et de vkeys sont
partagées : perdre un champ affecterait une autre application. Le CAS compare
la version de l'objet ; sur conflit, il faut relire et fusionner avant une
nouvelle tentative. Le versionnement facilite le diagnostic, il ne résout pas
automatiquement le conflit.

## BAO-08 — Il reste toujours une identité initiale

Dire « tous les secrets sont dans OpenBao » ne résout pas l'accès initial à
OpenBao. Un workload a besoin d'une identité ou d'un credential livré depuis
un canal de confiance. AppRole est une option, mais son SecretID doit lui aussi
être délivré et protégé. Selon le déploiement, une identité native ou un agent
de secrets peut réduire les credentials statiques ; la skill ne les impose
pas dans le workshop ni ne les prétend déjà configurés.

## BAO-09 et BAO-10 — La rotation doit toucher le service qui accepte le secret

Changer la valeur KV n'invalide pas le mot de passe d'une base, une clé S3 ou un
secret client Casdoor. Les deux états doivent être coordonnés, puis les clients
rechargés et l'ancien accès refusé. La vérification côté ressource est la preuve
utile, pas seulement le numéro de version KV.

Un token OpenBao, un mot de passe KV et un credential dynamique n'ont pas le
même cycle de vie. Leur confondre TTL et rotation conduirait à des renouvellements
inutiles ou des credentials expirés. Le dépôt fournit des valeurs statiques et
un token de dev ; la skill réserve les patterns de leases aux moteurs réellement
configurés et nécessaires.

## BAO-11 et BAO-12 — Un audit observable et des tests qui savent échouer

Le device est déjà déclaré dans la plateforme. Ajouter une seconde procédure
ou désactiver l'audit pendant un incident créerait de la dérive et détruirait
une preuve utile. Même HMACé, l'audit révèle des chemins et identités : il mérite
une politique d'accès et de rétention propre.

Un test local prouve que le client refuse un chemin, pas que le serveur refuse
un token. Les tests négatifs d'ACL doivent employer une identité réellement
limitée. Les exemples restent des assets adaptables, sans imposer un nouveau
service ou une bibliothèque pour le seul plaisir de généraliser.
