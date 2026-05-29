# Media Time Guard – Guide utilisateur (Français)

Media Time Guard limite le temps multimédia quotidien d'une personne sur ses lecteurs
(par ex. Sonos One) et applique la limite de façon fiable, même quand les enfants tentent
de la contourner.

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
Une entrée est créée par personne. L'assistant comporte quatre étapes :

1. **Personne et lecteurs**
   - **Nom** : par ex. `Luke`. (Les enfants n'ont souvent pas d'entité `person` : saisissez le nom.)
   - **Entité personne** (facultatif) : si elle existe.
   - **Lecteurs multimédias** : un ou plusieurs. Un lecteur ne peut appartenir qu'à **une** personne.
2. **Budgets quotidiens** : minutes du lundi au dimanche. `0` = bloqué toute la journée.
3. **Avertissement** (facultatif) : activé/désactivé, seuil de temps restant (minutes), méthode :
   - **TTS** : choisissez un moteur TTS + texte d'annonce. `{minutes}` est remplacé par les minutes restantes.
   - **Multimédia** : une URL / un ID de contenu à lire.
4. **Réinitialisation** : heure à laquelle le compteur est remis à zéro (par défaut `00:00`).

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
| `number.media_time_<personne>_extend` | minutes supplémentaires aujourd'hui (valeur absolue) |
| `button.media_time_<personne>_extend_15` / `_extend_30` | +15 / +30 minutes |

Attributs du capteur : `budget_minutes`, `used_minutes`, `remaining_minutes`, `is_locked`,
`is_suspended`, `extra_minutes_today`, `warned_today`.

## 5. Tâches courantes

- **Accorder plus de temps :** appuyez sur le bouton +15/+30, réglez l'entité number ou appelez
  `media_time_guard.extend_time` avec `person` et `minutes`.
- **Aucune limite aujourd'hui (enfant malade) :** activez l'interrupteur *Suspend Today* ou appelez
  `media_time_guard.suspend_today` avec `suspended: true`.
- **Réinitialiser manuellement :** appelez `media_time_guard.reset_person`.

## 6. Limitation connue

Le comptage repose sur l'état `playing`. **La lecture en sourdine ou très basse compte quand
même**, car le lecteur « lit » toujours.
