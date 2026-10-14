# Pourquoi ces règles et ces patterns ?

Ce document explique le raisonnement derrière les règles `APX-01` à `APX-12`.
Il sert à discuter et faire évoluer le harnais. L'agent ne doit pas charger toute
cette justification pour un simple appel : les instructions essentielles sont
dans `SKILL.md`, les détails conditionnels dans les autres références.

## APX-01 — Un point de passage pour les appels IA

Un vibecoder demande une fonctionnalité. Un agent peut la réaliser en installant
le SDK d'un fournisseur, en lui donnant une clé dans `.env` et en appelant son
API. La fonctionnalité marche, mais ses consommations, ses destinations de
données et ses credentials échappent alors à la politique de plateforme.

La règle de passage obligatoire par APISIX empêche cette décision dans le code
généré. Elle couvre aussi les embeddings, la génération d'image et les appels
cachés dans une bibliothèque d'agents : limiter la règle au chat laisserait
précisément des chemins de shadow IA.

Il faut distinguer cette exigence applicative de son enforcement réseau. Une
skill influence les décisions ; elle ne peut empêcher un processus compromis
ou un SDK non détecté d'accéder à Internet. La garantie forte demande une
politique d'egress où les backends applicatifs ne peuvent contacter les services
IA que via le gateway, avec les sorties nécessaires aux autres services
explicitement autorisées. Le Compose fourni n'établit pas cette garantie.

L'interdiction du secours direct est essentielle : sinon, une erreur de quota
devient précisément le déclencheur d'un contournement. Le comportement attendu
est une attente, une indisponibilité contrôlée ou une évolution de plateforme.
Cette règle concerne les appels de l'application, pas le compte du coding agent.

## APX-02 — Deux credentials pour deux responsabilités

La clé fournisseur donne accès à un compte externe. La vkey identifie un consumer
de la plateforme et permet d'attribuer les appels à une app. Séparer ces clés
permet de changer le fournisseur ou sa clé sans réécrire les applications, et de
révoquer une app sans redistribuer la clé commune aux autres équipes.

La vkey doit rester secrète malgré son nom « virtuelle ». Dans un navigateur,
elle est accessible dans le bundle ou les requêtes. Toute personne qui la
récupère pourrait consommer le budget de l'app en dehors du parcours métier.
Le serveur conserve donc la vkey et traduit une action utilisateur en appel IA.

OpenBao fournit le secret runtime ; l'app lit son chemin, pas la map de toutes
les vkeys ni la clé fournisseur. Ce découpage facilite une future ACL minimale.
Dans le TD, le token root public reste une simplification de dev : la séparation
par chemin exprime une intention d'architecture, pas une sécurité déjà imposée.

## APX-03 — L'API protège le produit, APISIX protège l'accès partagé

Un endpoint qui transmet sans contrôle le body du navigateur au gateway laisse
l'utilisateur choisir un modèle coûteux, une sortie énorme, des outils ou un
prompt système inattendu. Même avec la vkey côté serveur, ce serait un accès
générique au compte IA de l'application.

L'API doit exposer une opération métier comme « résumer ce document », vérifier
que l'utilisateur peut lire le document et fixer les paramètres autorisés.
Pour un produit qui permet réellement de discuter librement, la conversation
reste autorisée, bornée et isolée entre utilisateurs ; le browser ne choisit
toujours pas la destination ni les credentials.

Cette séparation évite aussi de confondre les identités : Casdoor authentifie
éventuellement l'utilisateur ; la vkey authentifie l'app auprès d'APISIX. Le quota
de l'app ne fournit pas un quota par utilisateur. Si l'app est publique, une
politique anti-abus doit être définie selon ce contexte plutôt que supposer
qu'une authentification inexistante protège les appels.

## APX-04 — Une dépendance petite et des modèles choisis par capacité

Un adaptateur réduit le couplage entre la logique métier et le protocole HTTP.
On peut tester le cas d'usage avec un double, remplacer un SDK et traduire les
erreurs sans répéter cette mécanique dans chaque endpoint. Pour une app simple,
un module suffit : une interface, plusieurs factories ou un framework d'agents
ne sont pas requis.

Les aliases donnent à la plateforme la responsabilité du mapping fournisseur.
Le code métier exprime un niveau de capacité, pas une version de modèle.
Mais l'indépendance n'est pas absolue : les fonctionnalités avancées et la qualité
des sorties doivent être évaluées à chaque changement de mapping/provider.

Le point de départ `task:cheap` évite de sélectionner une offre supérieure « au
cas où ». Si une évaluation métier montre des erreurs inacceptables, on augmente
le niveau en documentant qualité, latence et consommation. Un alias bon marché
qui nécessite plusieurs corrections peut coûter davantage qu'un appel mieux
adapté. Le raisonnement se mesure sur la tâche complète.

## APX-05 — Refuser une configuration dangereuse avant l'appel

Les SDK ont souvent une URL fournisseur par défaut. Une configuration incomplète
ne doit pas réactiver silencieusement cette destination. Le client fourni n'a
aucune clé fournisseur ni URL de secours ; il refuse les gateways non approuvés.
La liste fermée limite aussi l'exfiltration d'une vkey vers une URL injectée.

Refuser les redirections ferme un autre chemin où une destination initialement
approuvée pourrait mener à un autre hôte. Ces mesures protègent les appels de ce
client ; elles ne remplacent pas le filtrage réseau ou la sécurité d'OpenBao.

Le chargement au démarrage rend la dépendance visible et évite de relire OpenBao
à chaque génération. Après rotation, il faut cependant recharger la configuration
ou redémarrer le backend. Pour une app dont l'IA est optionnelle, seule la
fonctionnalité concernée peut être indisponible ; faire tomber toute l'app sans
examiner le produit serait disproportionné.

## APX-06 — Plusieurs limites pour plusieurs formes de dépense

La limite tokens/60 s protège un usage partagé sur une fenêtre ; la limite de
sortie borne une génération ; la taille d'entrée évite des prompts démesurés ;
la concurrence borne les requêtes simultanées ; la deadline borne l'attente
locale ; le nombre de tours arrête une boucle d'agent. Aucun de ces mécanismes
ne remplace les autres.

Le plugin APISIX observe l'usage après les réponses. Il ne réserve donc pas un
budget financier ferme avant chaque génération. Les images ont en plus un
chemin différent qui n'active pas ce plugin dans le dépôt. Il faut explicitement
refuser de présenter une fenêtre de tokens comme une protection universelle
contre les dépassements de coût.

Les seuils des snippets décrivent un résumé court. Les transformer en constantes
universelles ferait échouer un besoin légitime de document long ou une tâche
nécessitant du raisonnement. Le harnais exige des limites justifiées, pas des
valeurs arbitraires identiques pour tous les produits.

## APX-07 — Les reprises ne sont pas gratuites

Un appel LLM est généralement une génération POST : après un timeout, on ne
sait pas toujours si l'amont l'a traité. Le relancer peut produire une nouvelle
facturation et une réponse différente. Relancer en plus au niveau du SDK, du
handler et du worker multiplie les tentatives.

Le client d'exemple ne relance rien. Pour un traitement différable, un worker
peut appliquer une politique unique et bornée, vérifier les résultats persistés
et respecter une attente imposée. Une clé d'idempotence métier protège les
effets dans votre base ; elle ne garantit pas que le fournisseur ne calculera
qu'une fois. Les effets d'un outil doivent être autorisés et dédupliqués à part.

401/403 demandent un diagnostic d'accès ; répéter la même requête ne répare pas
une vkey absente. 429 signale une saturation ; basculer vers une clé personnelle
violerait la politique. Une sortie invalide n'autorise pas non plus une boucle
illimitée de « réparation ». Chaque correction est une nouvelle dépense.

## APX-08 — Déployer le bon type de traitement

Un résumé rapide peut se faire dans l'API. Ajouter une file et un worker impose
des états, des opérations et du support qui ne répondent pas forcément au besoin.
Un lot de documents, au contraire, gagne à être traité en arrière-plan : la page
n'attend pas, la concurrence peut être contrôlée et l'état du job est consultable.

Temporal devient pertinent pour des étapes durables, timers ou validations
humaines. Un appel LLM doit alors être dans une activité, jamais dans un workflow
qui rejoue son historique. Le simple fait qu'une génération prenne quelques
secondes ne justifie pas Temporal.

Le streaming accélère la perception de la réponse, pas nécessairement son
calcul total. Un HTTP 200 suivi d'une coupure peut contenir un résultat partiel.
Il faut vérifier la terminaison du protocole et éviter de considérer cette
réponse comme complète. L'annulation côté client réduit le travail local mais
ne prouve pas que la facturation amont a cessé.

## APX-09 — Une passerelle ne comprend pas vos permissions métier

APISIX sait router et contrôler l'accès au service IA. Il ne sait pas si Alice
peut lire le document de Bob ni si une instruction contenue dans un PDF est
légitime. Les droits sont vérifiés avant le retrieval et avant un effet métier.
Ne pas envoyer tous les documents au LLM puis lui demander de filtrer les droits.

Les réponses sont des propositions non fiables : valider un schéma, une catégorie
ou des références avant leur utilisation. Pour des outils, le serveur conserve
une liste d'opérations autorisées et contrôle chaque appel avec le contexte
utilisateur. Une phrase dans le prompt n'est pas un mécanisme d'autorisation.

La minimisation évite de transmettre des secrets et données sans utilité. Elle
réduit aussi la taille du contexte. Le cache et le RAG restent conditionnels :
un cache partagé mal isolé peut restituer des informations privées ; réindexer
tout un corpus sans changement de contenu consomme du calcul inutile.

## APX-10 — Mesurer sans créer une deuxième base de données sensibles

Les tokens, la durée, l'alias et la version du prompt permettent de comparer des
implémentations et diagnostiquer une saturation. Les prompts et réponses brutes
peuvent contenir des documents privés ou des secrets : les copier dans Dozzle
étend inutilement leur surface d'accès et leur durée de conservation.

Une erreur réseau ou amont peut également inclure des détails sensibles. Le
client renvoie des erreurs typées et un statut, sans incorporer le corps brut
ni l'exception réseau. Les logs de gateway doivent conserver le niveau prévu
dans la configuration locale, qui documente un risque de fuite à `info`.

Enfin, nombre de tokens, facture et émissions sont des mesures différentes.
Calculer une facture exige les tarifs et le détail de consommation applicables ;
calculer une empreinte demande d'autres données. L'outil `p99.ts` du dépôt mesure
des latences API, pas l'impact carbone des générations. Pour un job LLM, mesurer
aussi délai de file et durée totale plutôt que lui appliquer aveuglément un
objectif de latence destiné aux endpoints ordinaires.

## APX-11 — Respecter la source de vérité et le périmètre partagé

Le dépôt a déjà un modèle d'exploitation : les secrets sont dans OpenBao, les
routes dans des fichiers versionnés et les consumers dans un fichier généré.
Installer un Admin API ou modifier le YAML runtime introduirait un second chemin
de configuration ; le prochain seed pourrait écraser ces modifications.

Les scripts existants réduisent le nombre de décisions que l'agent doit inventer.
Il faut toutefois lire leur comportement réel : un budget existant est conservé
par `onboard-app.sh`, et le bootstrap qui publie une vkey ne re-seede pas à lui
seul le gateway. Une bonne instruction nomme ces détails qui font échouer une
intégration, plutôt que seulement dire « utiliser les bonnes pratiques ».

Le choix de provider est global ici. Une app ne doit pas changer le provider
de toutes les autres apps pour résoudre son seul incident. Les opérations
partagées se préparent dans le périmètre demandé et sont accompagnées d'une
vérification de leurs effets.

## APX-12 — Faire la différence entre règle, contrôle et garantie

Un résultat fonctionnel ne prouve pas que l'app respecte le harnais. Les tests
négatifs montrent qu'un alias interdit, une destination non approuvée ou une
réponse tronquée sont effectivement refusés. Les tests avec doubles évitent de
consommer des tokens pour vérifier ces invariants applicatifs.

Ils ne prouvent ni le quota du gateway ni l'absence d'egress direct. Ces points
exigent des tests d'intégration séparés dans un environnement adapté. La skill
liste les limites observées pour empêcher l'agent de transformer une intention
de documentation en garantie de sécurité.

Le dossier `assets/` contient des exemples réutilisables, pas un nouveau service
obligatoire. La description de skill est ciblée sur les besoins IA de l'app.
Les procédures et cette justification sont chargées à la demande pour conserver
un contexte utile. Cette skill ne remplace pas le futur `AGENTS.md` : celui-ci
devra orienter les besoins IA vers elle, et la CI devra vérifier les règles dont
vous voulez rendre le respect obligatoire.
