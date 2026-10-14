# Validation Registry et livraison

Le [modèle de livraison](../assets/livraison.json) contient des digests `null` :
les remplacer par les observations réelles. Les valeurs fictives ne prouvent
aucune publication. Si le registre est arrêté, livrer le protocole non exécuté.

| Scénario | Vérification observable |
|---|---|
| Construire, publier et déployer une version | Provenance connue ; digest enregistré et confronté à l'artefact déployé |
| Modifier uniquement le frontend | Inventaire complet justifiant réutilisation de l'API ; digest API conservé |
| Modifier lockfile/base/entrée partagée | Reconstruction des composants dépendants concernés |
| Réduire les fichiers de l'image | Démarrage et parcours préservés ; taille/transfert relevés |
| Revenir à une version protégée | Image conservée réutilisée ; migrations et traitements compatibles ; parcours valide |
| Préparer un nettoyage avec deux apps | Références actives et rollback des deux apps préservées ; candidats bornés |
| Contrôler les secrets | Aucun secret dans contexte, couches, configuration embarquée ou historique |

Un test de suppression/GC reste distinct du simple inventaire et demande un
périmètre autorisé. Ne pas exécuter une purge du registre pour démontrer la rétention.

## Mesures utiles

Noter séparément durée de préparation/build, images construites/réutilisées,
tailles et transferts observés, stockage logique et espace physique si mesuré.
Les couches partagées empêchent d'assimiler la somme des tailles à l'espace disque.
Une référence supprimée ne démontre pas une libération immédiate de stockage.

## Rapport à fournir

```text
App / build_id / provenance / plateforme :
Entrées comparées et composants reconstruits :
Références publiées et digests observés :
Références effectivement déployées et preuve de correspondance :
Composants réutilisés et justification :
Vérification démarrage / parcours :
Version de rollback, compatibilité et résultat :
Références protégées et inventaire de nettoyage :
Mesures, preuves et limites :
Scénarios non exécutés :
```

Accepter lorsque la version est traçable, le même artefact est utilisé, la
réutilisation est justifiée et les versions de reprise sont protégées. Un rollback
non testé est une limite à déclarer, pas une preuve de conformité.
