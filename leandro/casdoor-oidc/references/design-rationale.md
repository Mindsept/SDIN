# Pourquoi ces règles Casdoor ?

## IDP-01 et IDP-02 — Une identité commune, un client propre à chaque app

Créer un second magasin de mots de passe oblige l'app à gérer stockage,
récupération, MFA et cycles de compte. Casdoor fournit déjà l'identité partagée.
L'app peut garder un profil métier sans répliquer le mot de passe. `(iss, sub)`
évite de prendre l'email ou le nom affiché, modifiables, pour une clé stable.

Un client par app rend le callback, les scopes et la rotation attribuables.
Le client de provisioning a des pouvoirs d'administration ; le fournir au
runtime élargirait une faille de l'app à l'IdP. OpenBao livre donc le client app,
tandis que les scripts disposent du client bootstrap dans leur périmètre.
Un produit public sans ressources privées n'exige pas de login artificiel.

## IDP-03 — Choisir le flux selon la capacité à garder un secret

Une app web avec API peut garder les tokens et le secret client sur le serveur.
Le navigateur reçoit un ID de session opaque : il ne devient pas un magasin de
refresh tokens. Cette préférence s'accorde avec les templates frontend/API du
TD et évite de faire dépendre la sécurité d'un secret de bundle.

Une app native ou une SPA sans backend ne peut garder un secret client. Elle
demande un client public et PKCE, avec un provisioning et un modèle de stockage
de tokens spécifiques. La skill ne prétend pas que le client confidentiel créé
par le script est réutilisable tel quel dans cette architecture.

## IDP-04 — Une transaction plutôt qu'un callback isolé

Le callback doit correspondre au navigateur qui a demandé la connexion.
Le state lie la réponse à sa transaction, PKCE lie le code à un verifier et le
nonce lie l'identité reçue à la tentative. Le harnais choisit les trois pour
rendre explicite la protection et éviter des simplifications fragiles.

TTL, binding et consommation atomique empêchent de réutiliser une transaction
ou de mélanger des connexions simultanées. Une map globale contenant un unique
state échouerait dès deux utilisateurs ; un delete non atomique permettrait
deux traitements concurrents. Le grant de code évite aussi de faire circuler
des mots de passe dans l'app ou des tokens dans un implicit flow.

## IDP-05 et IDP-06 — Un token est une preuve pour un usage précis

Décoder un JWT montre des champs, sans établir qui les a signés ni pour quel
destinataire. Le harnais demande une bibliothèque, les vérifications de claims
et de signature selon son API, pas une cryptographie maison. Les accès JWKS
doivent venir de l'IdP approuvé et les algorithmes du contrat du client.

Le mélange d'URLs du TD est un piège concret : une URL accessible au backend
peut ne pas être l'issuer du token. Supprimer la validation réglerait le symptôme
en perdant la preuve d'identité. On corrige la configuration réseau/canonique
en gardant les comparaisons exactes.

Un ID token établit une connexion au client OIDC ; un access token vise une
ressource ; un credential machine établit une identité de workload. Les accepter
indifféremment permettrait d'utiliser un token destiné à une autre app ou de
confondre une machine avec un utilisateur. Une vkey APISIX n'a pas ces usages.

## IDP-07 — La session réduit l'exposition mais crée une frontière CSRF

HttpOnly évite que le JavaScript lise le cookie, mais le navigateur l'envoie
automatiquement. Une mutation doit donc vérifier une protection CSRF et l'origine
attendue. SameSite et CORS contribuent à la politique ; ils ne sont pas une preuve
universelle que la requête traduit l'intention de l'utilisateur.

Un ID de session frais après login ou élévation de droits empêche de conserver
un identifiant pré-auth fixé par un attaquant. L'expiration et l'invalidation se
gèrent côté serveur, pas seulement en cachant le cookie. Le mode HTTP local doit
être une exception explicitement nommée pour ne pas se propager en production.

## IDP-08 — Savoir qui est connecté ne dit pas ce qu'il peut lire

Un utilisateur connecté peut encore demander le document d'un autre via un ID
deviné. Chaque ressource exige donc tenant, propriété ou permission métier.
Les groupes sont mappés par leur identifiant exact : un groupe d'une autre app
ou un booléen `isAdmin` reçu du navigateur ne doit pas autoriser l'action.

L'exemple de policy illustre ce découpage sans faire des rôles lecteur/rédacteur
une convention obligatoire. Il faut aussi choisir comment les changements de
droits invalident les sessions/caches : garder pour toujours les droits du jour
du login ferait persister un accès supprimé.

## IDP-09 et IDP-10 — URLs et durée font partie du modèle de confiance

Un callback ou returnTo libre permettrait de rediriger des codes ou l'utilisateur
vers un site externe. Une configuration dérivée de headers proxy non validés
peut déplacer la même frontière. Les URLs approuvées doivent être définies par
le serveur et les retours limités à des routes métier internes.

Logout local, logout SSO et révocation de tokens sont des opérations distinctes.
Le harnais force leur explication pour éviter une déconnexion cosmétique.
L'IdP indisponible refuse les nouveaux logins ; les sessions déjà établies suivent
une politique de durée et de fraîcheur des droits, plutôt que tomber toutes
immédiatement ou devenir valables sans limite. Le refresh n'est ajouté que si
nécessaire et effectivement provisionné.

## IDP-11 et IDP-12 — Tester les droits par de vrais parcours

Un bypass e2e pourrait devenir un endpoint de production. Les personas du seed
permettent de tester la connexion et les groupes réels sans utiliser un compte
administratif. Leur mot de passe partagé est réservé à la démo ; on documente
les scénarios et l'accès local aux credentials, pas leurs valeurs dans Git.

Les tests de guards doivent savoir refuser inter-tenant, droits insuffisants et
retours externes. Ils ne prouvent pas le flux OIDC complet : celui-ci demande une
instance Casdoor, ses clés et un navigateur. Les références distinguent ces
preuves pour ne pas annoncer une sécurité que les tests n'ont pas exercée.
