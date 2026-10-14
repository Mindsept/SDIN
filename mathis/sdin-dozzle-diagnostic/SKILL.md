---
name: sdin-dozzle-diagnostic
description: "Structurer les logs d'une application SDIN et diagnostiquer un incident avec Dozzle déjà retenu : corrélation des requêtes et travaux, consultation ciblée, debug temporaire et maîtrise du volume."
---

# Dozzle : des logs utiles, un volume maîtrisé

## Résultat attendu

Émettre des traces utiles et retrouver un incident avec un parcours corrélé,
sans imposer un volume de logs disproportionné. Le service est déjà retenu ;
ne pas ajouter de sélection ou d'arbitrage entre services.

User story : « En tant que développeur, je veux retrouver pourquoi un export
a échoué, avec le même identifiant du début à la fin, sans lire toutes les traces
de toutes les applications. »

## Entrées

Identifier app, composants, logger existant, scénario ou incident, période,
identifiants disponibles, volume de trafic/travaux, besoins de conservation
et de mesure. Vérifier version Dozzle et mécanisme de logs du runtime.

## Démarche

1. Pour cadrer l'émission, lire [patterns.md](references/patterns.md) et
   [integration.md](references/integration.md). Réutiliser le logger de l'app ;
   ne pas créer une seconde chaîne de logs pour Dozzle.
2. Adapter [politique-logs.yml](assets/politique-logs.yml) et les
   [exemples JSONL](assets/logs-exemple.jsonl) aux composants présents.
3. Pour un incident, borner app, composant, période et identifiant ; consulter
   les traces puis élargir selon les faits. Consigner observations et hypothèses
   dans le [modèle de diagnostic](assets/rapport-diagnostic.md).
4. Si nécessaire et autorisé, activer un debug ciblé, limité dans le temps,
   avec retour explicite au niveau normal. Un diagnostic ne donne pas à lui
   seul l'autorisation de redémarrer ou purger un composant.
5. Appliquer [validation.md](references/validation.md) : corrélation, absence
   de secrets, volume sur un scénario fixe et retour au niveau normal.

## Contraintes essentielles

- Logs JSON sur stdout/stderr ; champs stables d'horodatage, app, service et niveau.
- API : request_id, méthode, route modèle, statut et duration_ms utiles.
  Worker : job_id, état, tentative et cause des reprises pertinentes.
- Propager les identifiants nécessaires entre composants. Dozzle ne fabrique
  pas une corrélation métier absente des logs.
- Exclure tokens, mots de passe, corps complets et documents produits ; filtrer
  aussi erreurs et stack traces susceptibles de contenir des valeurs sensibles.
- Tracer les changements d'état et reprises significatives ; réduire sondes,
  polling et boucles répétitives, en préservant les erreurs utiles.
- Cadrer rotation et conservation côté runtime ; ne pas supposer qu'ouvrir
  Dozzle garantit la conservation après suppression d'un conteneur.
- Préserver la population nécessaire aux mesures : un p99 calculé uniquement
  sur des traces de requêtes lentes est biaisé.
- Vérifier les fonctions disponibles : le socle déclare Dozzle `latest`.
  Ne pas supposer la présence d'alertes, de requêtes ou de commandes.

## Livraison

Fournir politique de logs, schéma adapté, scénario de corrélation, diagnostic
borné et mesures avec leurs limites. Décrire le statut des scénarios ; ne pas
transformer une hypothèse en cause établie ou un protocole en test exécuté.
