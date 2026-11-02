# Media Time Guard – Guide utilisateur (Français)

Media Time Guard limite le temps multimédia quotidien d'une personne sur ses lecteurs
(par ex. Sonos One) et les arrête une fois le budget quotidien épuisé. Seul l'état `playing` des lecteurs
attribués est compté ; les autres appareils et applications ne sont pas couverts.

## 1. Installation

**Via HACS (recommandé)**
1. Ouvrez HACS → menu ⋮ → *Dépôts personnalisés*.
2. Ajoutez l'URL du dépôt, catégorie **Intégration**.
3. Recherchez *Media Time Guard* et téléchargez-le.
4. Redémarrez Home Assistant.

**Manuel :** copiez le dossier `custom_components/media_time_guard/` dans
`<config>/custom_components/` et redémarrez HA.

## 2. Configurer une personne

*Paramètres → Appareils et services → Ajouter une intégration → « Media Time Guard ».*
Une entrée est créée par personne. L'assistant comporte cinq étapes :

1. **Personne et lecteurs**
   - **Nom** : par ex. `Luke` (doit être unique).
   - **Lecteurs multimédias** : un ou plusieurs. Un lecteur ne peut appartenir qu'à **une** personne.
2. **Budgets quotidiens** : minutes du lundi au dimanche. `0` = bloqué toute la journée.
3. **Avertissement** (facultatif) : activé/désactivé, seuil de temps restant (minutes), méthode :
   - **TTS** : choisissez un moteur TTS + texte d'annonce. `{minutes}` est remplacé par les minutes restantes.
   - **Multimédia** : une URL / un ID de contenu à lire.
4. **Réinitialisation** : heure à laquelle le compteur est remis à zéro (par défaut `00:00`).
5. **Accès** : *Seuls les administrateurs et les utilisateurs choisis peuvent modifier* (désactivé par défaut) et, en option, des utilisateurs non administrateurs autorisés en plus.

Modifiez-le plus tard via le bouton **Configurer** de l'entrée.

## 3. Ce qui se passe

- Le temps ne compte que lorsqu'au moins un lecteur attribué **lit** (`playing`).
- La lecture simultanée sur plusieurs enceintes n'est **pas** comptée deux fois.
- Quand le budget est épuisé, tous les lecteurs sont **arrêtés** et verrouillés pour le reste
  de la journée. Éteindre/rallumer une enceinte ou redémarrer HA ne lève **pas** le verrou.
- Peu avant la fin, un avertissement unique est émis (si activé).

## 4. Entités par personne

| Entité | Signification |
|---|---|
| `sensor.media_time_<personne>_remaining` | minutes restantes aujourd'hui |
| `switch.media_time_<personne>_suspend_today` | suspendre l'application aujourd'hui (par ex. malade) |
| `switch.media_time_<personne>_blocked` | bloquer toutes les enceintes de la personne jusqu'à nouvel ordre |
| `number.media_time_<personne>_extend` | minutes supplémentaires aujourd'hui (valeur absolue) |
| `button.media_time_<personne>_extend_15` / `_extend_30` | +15 / +30 minutes |

Attributs du capteur : `budget_minutes`, `used_minutes`, `remaining_minutes`, `is_locked`,
`is_suspended`, `is_blocked`, `extra_minutes_today`, `warned_today`.

## 5. Tâches courantes

- **Accorder plus de temps :** appuyez sur le bouton +15/+30, réglez l'entité number ou appelez
  `media_time_guard.extend_time` avec `person` et `minutes`.
- **Aucune limite aujourd'hui (enfant malade) :** activez l'interrupteur *Suspend Today* ou appelez
  `media_time_guard.suspend_today` avec `suspended: true`.
- **Bloquer les enceintes jusqu'à nouvel ordre :** activez l'interrupteur *Bloqué* ou appelez
  `media_time_guard.set_blocked` avec `blocked: true`. Toute lecture est arrêtée immédiatement,
  même après minuit et un redémarrage, jusqu'à ce que l'interrupteur soit désactivé.
- **Réinitialiser manuellement :** appelez `media_time_guard.reset_person`.

## 6. Limitation connue

Le comptage repose sur l'état `playing`. **La lecture en sourdine ou très basse compte quand
même**, car le lecteur « lit » toujours.

## 7. Qui peut modifier ?

Si la restriction est activée à l'étape **Accès**, seuls les **administrateurs**, les **utilisateurs
choisis** et les **automatisations** peuvent modifier le temps multimédia de cette personne (prolonger,
minutes supplémentaires, suspendre aujourd'hui, bloquer/débloquer, réinitialiser). Tous les autres – p. ex.
le compte d'une tablette murale utilisée par les enfants – reçoivent « Unauthorized », que ce soit via le
tableau de bord, Assist ou l'API. Le temps restant reste visible pour tous.

Important : les automatisations s'exécutent sans utilisateur et sont donc toujours autorisées. Ne crée pas
d'automatisation qu'un enfant peut déclencher (p. ex. via un assistant ou un bouton) et qui prolonge le
temps. N'expose pas les entités aux satellites vocaux ni à HomeKit.
