# CHANGELOG

Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.1.0/).
Versionado: `17.0.MAYOR.MENOR.PARCHE`.

Cada entrada de version incluye el **prompt** que motivo los cambios
y las **discusiones de diseno** relevantes que influyeron en las decisiones,
para trazabilidad completa del razonamiento de agentes de IA.

---

## [17.0.1.2.1] - 2026-08-26

### Prompt

> Necesito que dentro del dropdown de item works del systray cada item work
> tenga un ícono (flecha a la derecha) que al tocarlo redirija el backend al
> registro del item. O sea, quiero poder inspeccionar la tarea incluso antes
> de empezar a trabajar en ella.
>
> Consulta, hay una forma que se habra en un popup y no abriendo en una
> nueva pestaña.

### Discusión de diseño

Cada `DropdownItem` de las listas "Hoy"/"Resto" ya disparaba
`onSelectWorkItem` (cambia el work item activo) al hacer click en cualquier
parte del ítem — no había forma de solo mirar el registro sin switchear.
Se agregó un ícono `fa-chevron-right` dentro de cada ítem con
`t-on-click.stop`, que aprovecha que el `onClick` de `DropdownItem` está
bindeado con `t-on-click.stop` en su elemento raíz (`web.DropdownItem`
template): al frenar la propagación desde el ícono, el click nunca llega al
listener del ítem y no dispara el switch, solo abre el registro.

Para abrir el registro se descartó `window.open(...)` a `/web#id=...` (abre
una pestaña nueva del navegador) en favor de `this.action.doAction(...)`
con `target: 'new'` — el mismo mecanismo que usan los smart buttons de
Odoo para abrir un formulario como diálogo modal dentro de la misma
pestaña, que es lo que pidió el usuario. Se extrajo `onOpenWorkItem()`
(botón "Abrir" del work item activo, ya existente) a un método genérico
`openWorkItemRecord(model, resId)` para no duplicar la lógica entre el
botón y el ícono nuevo.

### Added

- Ícono de flecha (`fa-chevron-right`) en cada work item de las listas
  "Hoy"/"Resto" del dropdown del systray, que abre su registro como
  diálogo modal sin cambiar el work item activo.

### Changed

- `onOpenWorkItem()` ahora delega en el nuevo método genérico
  `openWorkItemRecord(model, resId)`, que abre el registro vía
  `action.doAction({..., target: 'new'})` en vez de `window.open`.
