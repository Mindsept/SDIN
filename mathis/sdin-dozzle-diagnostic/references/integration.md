# Intégration Dozzle au socle SDIN

Le [Compose partagé](../../../core-platform/podman-compose.yml) déclare
`dozzle.internal`, une interface sur le port hôte `9999`, et monte le socket
Podman du socle. L'app n'ajoute pas un Dozzle par composant et ne monte pas ce
socket dans ses propres conteneurs.

Les [templates applicatifs](../../../core-platform/templates/podman-compose.yml)
prévoient des logs sur stdout/stderr. Vérifier que les conteneurs de l'app sont
visibles depuis le runtime consulté : un processus lancé sur l'hôte hors du
runtime ne devient pas automatiquement visible dans Dozzle.

## Contrat de logs

| Contexte | Champs utiles |
|---|---|
| Commun | `timestamp` UTC, `level`, `app`, `service`, `event`, message court si utile |
| Résumé API | `request_id`, `method`, `route`, `status`, `duration_ms` |
| Travail asynchrone | `job_id`, `state`, `attempt`, `error_code` lorsque pertinent |

Adapter le nom des champs au logger existant si leur sens reste stable. Les
champs worker ne sont pas obligatoires pour un service sans worker. Une ligne
JSON par événement facilite la consultation ; sérialiser les erreurs de manière
bornée et expurgée, plutôt que copier aveuglément un objet d'erreur complet.

Créer un request_id s'il manque, propager celui de confiance entre composants,
et borner les identifiants provenant de l'extérieur. Ils servent à retrouver
une exécution, pas à véhiculer un email, un token ou du contenu libre.

## Logger et runtime

Réutiliser le logger du framework. Un nouveau fichier de logs ou agent d'envoi
ne se justifie pas pour simplement consulter stdout dans Dozzle.

Décrire le driver, la rotation et la conservation réellement actifs. Lire la
configuration effective du runtime avant de proposer des options : les options
de rotation diffèrent selon le driver Podman. Définir taille/durée et responsable
selon le débit mesuré et le besoin de diagnostic ; aucun quota arbitraire commun
à toutes les apps n'est livré ici.

Le socle référence `latest` : relever la version ou l'empreinte réellement
déployée. Utiliser les filtres ou recherches qui existent dans cette version.
Ne pas activer commandes, alertes ou accès au shell pour une simple consultation.

## Debug temporaire

Consigner composant, filtre, niveau, début, échéance et méthode de rétablissement.
Préférer une configuration dynamique existante, sinon le mécanisme de l'app.
Limiter les manipulations au périmètre autorisé ; une consultation n'implique
pas un redémarrage. Vérifier ensuite le niveau effectif et le débit des traces.

## Sources

- [Dozzle](https://dozzle.dev/guide/what-is-dozzle).
- [Mesure p99 du socle](../../../core-platform/templates/p99.ts).
- [Slides, slide 2 et notes](../../../../presentations/sdin-skills-services.html#slide-2).
