> 🇬🇧 [English](README.md) · 🇩🇪 [Deutsch](README.de.md) · 🇪🇸 Español (this page)

<p align="center">
  <img src="icon.png" alt="Media Time Guard" width="160" height="160">
</p>

<h1 align="center">Media Time Guard</h1>

<p align="center">
  <b>Tiempo de pantalla y audio para niños — configúralo una vez y se mantiene.</b>
</p>

## Se acabó la negociación de "solo cinco minutos más"

**Media Time Guard** asigna a cada niño un **presupuesto diario de tiempo multimedia** y lo
aplica **de forma automática y a prueba de manipulaciones** — en Sonos One y en **cualquier**
otro `media_player` de Home Assistant. Cuando se agota el tiempo, la reproducción se detiene.
¿Apagar y encender el altavoz? No sirve. ¿Reiniciar? Tampoco. Ese es justo el objetivo:
**los niños ponen a prueba los límites; esta integración los mantiene.**

### Por qué les encanta a los padres

- ⏱️ **Un presupuesto por día de la semana** – corto entre semana, generoso el fin de semana (`0` = bloqueado ese día).
- 🛡️ **Realmente a prueba de manipulaciones** – cuenta la reproducción real y sobrevive a reinicios, cortes de luz y trucos de apagar/encender.
- 🔀 **Sin doble conteo** – el mismo niño en varios altavoces gasta el tiempo una sola vez.
- 🔔 **Un aviso justo** – un **anuncio TTS** amable ("quedan 10 minutos…") o tu propio sonido antes de terminar.
- ➕ **Recompensar es fácil** – minutos extra con botones (+15/+30), un control deslizante o un servicio.
- 🤒 **Excepciones** – ¿el niño está enfermo? Suspende el control por hoy con un interruptor.
- 🌍 **Multilingüe** – interfaz **y entidades** en español, inglés, alemán, francés (+ noruego, griego, japonés).
- 🧩 **100 % configurable desde la interfaz, totalmente local** – sin YAML, sin automatizaciones, sin nube.

Una entrada de configuración por niño: vincúlala a una entidad `person` (o simplemente
introduce un nombre) y asigna las entidades `media_player` de esa persona. La integración
cuenta el tiempo multimedia en esos reproductores y, cuando se agota el presupuesto del día,
mantiene detenidos los reproductores asignados.

## Instalación

### HACS (recomendado)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Jo-Highness&repository=media_time_guard&category=integration)

1. En **HACS** → **⋮ → Repositorios personalizados** → añade `https://github.com/Jo-Highness/media_time_guard` con la categoría **Integración** (no es necesario cuando la integración esté en la tienda por defecto: usa el botón de arriba).
2. Busca *Media Time Guard* en HACS y **descárgalo**.
3. **Reinicia** Home Assistant.
4. *Ajustes → Dispositivos y servicios → Añadir integración → "Media Time Guard"*.

### Manual

1. Copia `custom_components/media_time_guard/` en tu carpeta `<config>/custom_components/`.
2. **Reinicia** Home Assistant.
3. Añade la integración desde *Ajustes → Dispositivos y servicios*.

## Configuración (una integración por niño)

La configuración inicial y la edición posterior usan los mismos cuatro pasos del asistente.
Todo se puede editar después con *Configurar* (Opciones).

| Paso | Qué defines |
|---|---|
| **1 · Persona** | Un **nombre** (p. ej. `Luke`), una entidad **`person`** opcional y los **reproductores** asignados. Cada reproductor pertenece a una sola persona. |
| **2 · Presupuestos diarios** | Minutos por día de la semana **lun–dom**. `0` bloquea el multimedia ese día por completo. |
| **3 · Aviso** | Activado/desactivado, el **umbral de minutos restantes** (predeterminado `10`) y el **método**: un anuncio **TTS** (elige un motor TTS + un mensaje, donde `{minutes}` se sustituye) **o** reproducir un **medio** por su content id (con su tipo de contenido). |
| **4 · Reinicio** | La hora del **reinicio diario** (predeterminado `00:00:00`) a la que se reinician los contadores y el aviso único. |

## Entidades

Cada persona configurada obtiene su propio **dispositivo** con estas entidades
(`<person>` = el slug del nombre):

| Entidad | Tipo | Propósito |
|---|---|---|
| `sensor.media_time_<person>_remaining` | sensor (medición, minutos) | Minutos multimedia restantes hoy, con atributos detallados (presupuesto, usado, día, bloqueado/suspendido, minutos extra, último reinicio). |
| `switch.media_time_<person>_suspend_today` | interruptor | **Suspender hoy** – pausa el control por el resto del día (p. ej. el niño está enfermo). |
| `number.media_time_<person>_extend` | número (0–600, paso 5) | **Minutos extra** para el presupuesto de hoy. |
| `button.media_time_<person>_extend_15` | botón | Añadir rápido **+15 minutos**. |
| `button.media_time_<person>_extend_30` | botón | Añadir rápido **+30 minutos**. |

## Servicios

Todos los servicios aceptan el **nombre o slug** de la persona.

| Servicio | Campos | Descripción |
|---|---|---|
| `media_time_guard.extend_time` | `person`, `minutes` (1–600) | Añade minutos multimedia extra para hoy (aumenta el presupuesto efectivo). |
| `media_time_guard.suspend_today` | `person`, `suspended` (bool) | Suspende o reanuda el control por hoy. |
| `media_time_guard.reset_person` | `person` | Reinicia manualmente los contadores de hoy de una persona. |

## Ejemplos de automatización

**Recompensar 15 minutos cuando se terminan los deberes:**

```yaml
automation:
  - alias: "Media reward when homework done"
    trigger:
      - platform: state
        entity_id: input_boolean.luke_homework_done
        to: "on"
    action:
      - service: media_time_guard.extend_time
        data:
          person: Luke
          minutes: 15
```

**Suspender el control automáticamente un día de enfermedad:**

```yaml
automation:
  - alias: "Suspend media limit when sick"
    trigger:
      - platform: state
        entity_id: input_boolean.luke_sick
        to: "on"
    action:
      - service: media_time_guard.suspend_today
        data:
          person: Luke
          suspended: true
```

## Solución de problemas / Preguntas frecuentes

**La reproducción no se detiene aunque el presupuesto esté agotado.**
Comprueba que las entidades `media_player` del niño están realmente asignadas a esa persona
en el asistente y que el presupuesto del día actual no esté demasiado alto. `0` significa
"bloqueado todo el día".

**Se cuenta tiempo aunque (audiblemente) no suene nada.**
El conteo se basa en el estado `playing` del reproductor, así que la reproducción silenciada
o muy baja también cuenta. Es intencional y mantiene el control a prueba de manipulaciones.

**El mismo niño usa dos altavoces, ¿se cuenta doble?**
No. El tiempo multimedia de una persona se cuenta una sola vez, sin importar cuántos de sus
reproductores asignados suenen a la vez.

**Activar el registro de depuración** para ver cómo se cuenta y se aplica el tiempo:

```yaml
logger:
  logs:
    custom_components.media_time_guard: debug
```

Más detalles: guías completas de usuario en [`docs/user/`](docs/user) (de, en, es, fr, nb, el, ja)
y la arquitectura en [`docs/TECHNICAL.md`](docs/TECHNICAL.md).

## Contribuir

Las contribuciones son bienvenidas. Lee [`CONTRIBUTING.md`](CONTRIBUTING.md) y abre una issue
o un pull request en [GitHub](https://github.com/Jo-Highness/media_time_guard).

## Licencia

Publicado bajo la [Licencia MIT](LICENSE).
