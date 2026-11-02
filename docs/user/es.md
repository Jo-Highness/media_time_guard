# Media Time Guard – Guía de usuario (Español)

Media Time Guard limita el tiempo diario de medios de una persona en sus reproductores
(p. ej. Sonos One) y los detiene cuando se agota el presupuesto diario. Solo cuenta el estado `playing` de
los reproductores asignados; otros dispositivos y apps no quedan cubiertos.

## 1. Instalación

**Con HACS (recomendado)**
1. Abre HACS → menú ⋮ → *Repositorios personalizados*.
2. Añade la URL del repositorio, categoría **Integración**.
3. Busca *Media Time Guard* y descárgalo.
4. Reinicia Home Assistant.

**Manual:** copia la carpeta `custom_components/media_time_guard/` en
`<config>/custom_components/` y reinicia HA.

## 2. Configurar una persona

*Ajustes → Dispositivos y servicios → Añadir integración → "Media Time Guard".*
Se crea una entrada por persona. El asistente tiene cinco pasos:

1. **Persona y reproductores**
   - **Nombre**: p. ej. `Luke` (debe ser único).
   - **Reproductores**: uno o varios. Un reproductor solo puede pertenecer a **una** persona.
2. **Presupuestos diarios**: minutos de lunes a domingo. `0` = bloqueado todo el día.
3. **Aviso** (opcional): activado/desactivado, umbral de tiempo restante (minutos), método:
   - **TTS**: elige un motor TTS + texto del anuncio. `{minutes}` se reemplaza por los minutos restantes.
   - **Multimedia**: una URL / ID de contenido para reproducir.
4. **Reinicio**: hora a la que se reinicia el contador (por defecto `00:00`).
5. **Acceso**: *Solo administradores y usuarios seleccionados pueden cambiar* (desactivado por defecto) y, opcionalmente, usuarios sin derechos de administrador permitidos adicionalmente.

Cámbialo más tarde con el botón **Configurar** de la entrada.

## 3. Qué ocurre

- El tiempo cuenta solo mientras al menos un reproductor asignado está **reproduciendo**.
- Reproducir en varios altavoces a la vez **no** se cuenta dos veces.
- Cuando se agota el presupuesto, todos los reproductores se **detienen** y se bloquean el
  resto del día. Apagar y encender un altavoz o reiniciar HA **no** levanta el bloqueo.
- Poco antes del final se emite un aviso único (si está activado).

## 4. Entidades por persona

| Entidad | Significado |
|---|---|
| `sensor.media_time_<persona>_remaining` | minutos restantes hoy |
| `switch.media_time_<persona>_suspend_today` | suspender la aplicación hoy (p. ej. enfermo) |
| `switch.media_time_<persona>_blocked` | bloquear todos los altavoces de la persona hasta nuevo aviso |
| `number.media_time_<persona>_extend` | minutos extra hoy (valor absoluto) |
| `button.media_time_<persona>_extend_15` / `_extend_30` | +15 / +30 minutos |

Atributos del sensor: `budget_minutes`, `used_minutes`, `remaining_minutes`, `is_locked`,
`is_suspended`, `is_blocked`, `extra_minutes_today`, `warned_today`.

## 5. Tareas habituales

- **Dar más tiempo:** pulsa el botón +15/+30, ajusta la entidad number o llama a
  `media_time_guard.extend_time` con `person` y `minutes`.
- **Sin límite hoy (niño enfermo):** activa el interruptor *Suspend Today* o llama a
  `media_time_guard.suspend_today` con `suspended: true`.
- **Bloquear los altavoces hasta nuevo aviso:** activa el interruptor *Bloqueado* o llama a
  `media_time_guard.set_blocked` con `blocked: true`. Toda reproducción se detiene al instante,
  también tras la medianoche y reinicios, hasta que vuelvas a apagarlo.
- **Reiniciar manualmente:** llama a `media_time_guard.reset_person`.

## 6. Limitación conocida

El recuento se basa en el estado `playing`. **La reproducción silenciada o muy baja también
cuenta**, porque el reproductor sigue "reproduciendo".

## 7. ¿Quién puede cambiarlo?

Con la restricción activada en el paso **Acceso**, solo los **administradores**, los **usuarios
seleccionados** y las **automatizaciones** pueden cambiar el tiempo multimedia de esta persona (ampliar,
minutos extra, suspender hoy, bloquear/desbloquear, reiniciar). Los demás – p. ej. la cuenta de una tableta
de pared que usan los niños – reciben "Unauthorized", ya sea desde el panel, Assist o la API. El tiempo
restante sigue visible para todos.

Importante: las automatizaciones se ejecutan sin usuario y por eso siempre están permitidas. No crees una
automatización que un niño pueda activar (p. ej. con un ayudante o un pulsador) y que amplíe el tiempo. No
expongas las entidades a satélites de voz ni a HomeKit.
