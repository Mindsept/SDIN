---
name: apisix-llm
description: "Concevoir, implémenter ou revoir les appels IA des applications du TD via le gateway APISIX fourni : clés virtuelles OpenBao, aliases de modèles, budgets, erreurs et intégration serveur TypeScript/Bun. Utiliser pour les besoins de chat, génération, vision, embeddings ou images et pour prévenir les appels directs aux fournisseurs. Ne pas utiliser pour administrer Casdoor ni pour transformer APISIX en gateway général des API métier."
---

# APISIX : intégrer une IA gouvernée à la plateforme

Construire la fonctionnalité demandée dans le prompt utilisateur en utilisant le gateway IA
fourni. Appliquer les règles ci-dessous aux appels IA de l'application, y compris
les SDK, outils d'agents et bibliothèques RAG qui effectuent eux-mêmes des appels.
Les identifiants de l'agent de code qui construit l'app sont un sujet distinct.

## Avant de choisir une architecture

Lire la demande dans la conversation et les fichiers de l'app concernés.
Le prompt utilisateur est le point d'entrée métier ; ne pas imposer un document
intermédiaire pour y recopier le prompt. Clarifier uniquement
les informations manquantes qui changent réellement l'implémentation.
Déterminer si le besoin exige un LLM : tri, filtres, calculs, recherche exacte et
contenu statique peuvent souvent répondre au besoin sans génération.
Ne pas ajouter un worker, du RAG ou Temporal simplement parce qu'ils existent.

Pour toute intégration, lire [le contrat et ses limites](references/platform-contract.md),
puis vérifier les sources locales indiquées : elles prévalent sur les copies et
sur la documentation d'une autre version d'APISIX.

- Implémentation : lire [les patterns et exemples](references/integration-patterns.md).
- Arbitrage ou explication des règles : lire [leur justification](references/design-rationale.md).
- Exemple réutilisable de client texte serveur : [assets/llm-client.ts](assets/llm-client.ts).
- Lecture du secret au démarrage : [assets/load-llm-config.ts](assets/load-llm-config.ts).

## Règles d'architecture

`MUST` est une exigence du harnais proposé ; `SHOULD` est une préférence à adapter
avec une justification. Ces exigences ne sont pas toutes déjà imposées par
l'infrastructure. Ne pas annoncer une garantie sans preuve.

| ID | Niveau | Instruction |
|---|---|---|
| APX-01 | MUST | Faire passer tous les appels IA externes de l'application par APISIX. Ne créer ni accès direct à un fournisseur, ni champ permettant d'apporter sa propre clé, ni secours direct lorsque le gateway échoue. Une capacité absente impose de revoir le besoin ou de faire évoluer le contrat de plateforme. |
| APX-02 | MUST | Appeler le gateway depuis l'API ou un worker. Garder la clé virtuelle côté serveur ; les clés fournisseur appartiennent au provisioning de la plateforme. Ne pas les lire dans l'app, les mettre dans un bundle, un `VITE_*`, une URL ou les logs. |
| APX-03 | MUST | Exposer une opération métier contrôlée, pas un proxy arbitraire vers `/v1/*`. L'API décide des aliases autorisés, des limites, du prompt système et des données accessibles. Authentifier et autoriser le demandeur selon le produit ; une vkey identifie l'app, pas ses utilisateurs. |
| APX-04 | SHOULD | Isoler le protocole gateway dans un petit adaptateur serveur, et les prompts dans le cas d'usage. Utiliser les aliases `task:*` du contrat ; choisir `task:cheap` d'abord pour une tâche texte simple et justifier tout niveau supérieur par des évaluations métier. |
| APX-05 | MUST | Charger `secret/<app>/llm` depuis OpenBao au démarrage. Valider `base_url` et `virtual_key`, refuser une URL hors liste de gateways approuvés et ne pas suivre les redirections. Une configuration absente rend la fonctionnalité IA indisponible, sans substitution de credentials. |
| APX-06 | MUST | Borner chaque opération : entrée, sortie, durée totale, concurrence et, pour une boucle d'agent, nombre de tours et appels d'outils. `max_tokens` et le quota de tokens/60 s sont deux contrôles différents. Les limites sont décidées côté serveur. |
| APX-07 | MUST | Traiter 401/403 comme un problème d'accès, 429 comme une saturation et 5xx/timeouts comme une indisponibilité. Ne pas relancer automatiquement une génération au résultat inconnu. Si une reprise est nécessaire, une seule couche en est propriétaire, avec tentatives et durée bornées ; aucun contournement du gateway. |
| APX-08 | SHOULD | Répondre directement pour une génération courte ; utiliser une file et un worker pour un traitement long, différable ou repris. Ajouter Temporal seulement si le workflow exige une orchestration durable. Le streaming est un choix d'UX, pas une réduction du coût ni une preuve de succès. |
| APX-09 | MUST | Traiter les entrées et sorties LLM comme non fiables. Minimiser les données envoyées, valider les sorties selon le besoin, autoriser les outils côté serveur et contrôler l'accès aux documents avant le retrieval. Ne pas déléguer les droits d'accès au prompt. |
| APX-10 | MUST | Journaliser les métadonnées utiles : opération, alias, version du prompt, durée, résultat, identifiant de corrélation et tokens lorsqu'ils sont disponibles. Ne pas journaliser les secrets, les prompts ou les réponses brutes par défaut. Ne pas confondre tokens, coût financier et empreinte carbone. |
| APX-11 | MUST | Provisionner via les scripts existants. Garder les routes versionnées comme sources ; ne pas éditer ni committer `apisix/apisix.yaml`, qui contient des clés virtuelles. Le changement de provider est global à cette plateforme, pas un choix du navigateur ou un failover automatique. |
| APX-12 | MUST | Vérifier les règles par des tests négatifs et des preuves adaptées. Une consigne ou un scan de code ne bloque pas les sorties réseau ; déclarer cette limite tant qu'une politique d'egress effective n'interdit pas les accès IA directs. |

## Forme attendue dans l'application

```text
Navigateur → endpoint métier de l'API → adaptateur LLM → APISIX → fournisseur
                                      ↘ worker si traitement différable
OpenBao → configuration serveur        ↗
```

Le gateway possède le routage, les credentials fournisseur et les politiques
transverses. L'app possède l'autorisation métier, ses prompts, sa validation de
sortie et les limites par utilisateur/opération. Garder les calculs ordinaires
et les appels aux autres services hors du gateway IA.

## Vérification et livraison

Adapter les tests aux capacités utilisées : credentials absents, alias interdit,
redirection, quota épuisé, timeout, annulation, sortie tronquée ou invalide.
Revoir les SDK secondaires pour détecter un `baseURL` implicite vers un provider.
Effectuer un appel réel minimal seulement lorsqu'il est nécessaire et autorisé ;
ne pas lancer une campagne qui consomme le budget partagé pour tester un quota.

Pour le livrable, expliquer : besoin couvert, chemin des appels, alias et limites
choisis, provisioning, tests exécutés et garanties encore non établies.
Ne pas modifier automatiquement les services partagés pour masquer un échec.
