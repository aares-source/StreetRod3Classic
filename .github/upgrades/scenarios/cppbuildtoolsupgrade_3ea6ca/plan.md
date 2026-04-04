# Plan: Actualización / Retarget MSVC Build Tools (cppbuildtoolsupgrade_3ea6ca)

**TOC**

- [1. Executive Summary](#1-executive-summary)
- [2. Migration Strategy](#2-migration-strategy)
- [3. Detailed Dependency Analysis](#3-detailed-dependency-analysis)
- [4. Project-by-Project Plans](#4-project-by-project-plans)
- [5. Risk Management](#5-risk-management)
- [6. Testing & Validation Strategy](#6-testing--validation-strategy)
- [7. Complexity & Effort Assessment](#7-complexity--effort-assessment)
- [8. Source Control Strategy](#8-source-control-strategy)
- [9. Success Criteria](#9-success-criteria)
- [Appendix A: Commands & Tools](#appendix-a-commands--tools)

---

## 1. Executive Summary

- Escenario: El proyecto `sr3.vcxproj` requiere el Platform Toolset `v180` que no está instalado en la máquina (error MSB8020).  
- Alcance: `C:\Users\eass4\OneDrive\Desktop\StreetRod3Classic-main\code\sr3.sln` (1 proyecto afectado: `sr3.vcxproj`).  
- Descubrimiento clave: build reportó 1 error crítico (MSB8020) y 0 warnings.  
- Clasificación de complejidad: Medium — 1 proyecto afectado, 1 high-risk toolset issue (<=2 high-risk → Phase-based).  
- Estrategia recomendada (elegida por el usuario): Retargetear el proyecto a un toolset instalado y compatible (opción 1).  
- Bloqueante restante: Inventario del/los toolset(s) instalados en la máquina (p.ej. `v143`, `v142`) — requerido para elegir el valor exacto de `<PlatformToolset>` a aplicar.

---

## 2. Migration Strategy

Objetivo: Retargetear `sr3.vcxproj` desde `<PlatformToolset>v180</PlatformToolset>` a un toolset instalado y soportado por la instalación de Visual Studio en la máquina.

Seleccionado: Estrategia faseada (Phase-based). Justificación: único proyecto con un problema de tooling; aplicar cambio al proyecto primero y validar reconstrucción antes de cualquier cambio adicional.

Decisiones principales:
- No cambiar código fuente salvo que la validación muestre incompatibilidades tras retarget.
- Cambios en `.vcxproj` se harán en una rama nueva y siguiendo el orden: unload → editar → validar → reload → rebuild.
- Validación automatizada con `cppupgrade_validate_vcxproj_file` y `cppupgrade_rebuild_and_get_issues`.

Requisitos previos (obligatorios antes de aplicar cambios):
1. Inventario de toolsets instalados en la máquina. Acción: el Executor debe ejecutar el listado de toolsets instalados o confirmar la versión objetivo (p.ej. `v143`).  
2. Políticas del equipo sobre edición automática de `.vcxproj`.  

Decisiones de paralelismo: trabajo secuencial en este repositorio (un solo proyecto afectado) — no hay paralelismo operativo necesario.

---

## 3. Detailed Dependency Analysis

Resumen del grafo de dependencias:
- Proyectos en solución: 1 → `C:\Users\eass4\OneDrive\Desktop\StreetRod3Classic-main\code\sr3.vcxproj` (leaf project).  
- Dependencias externas (linker/libs observadas en build report): `SDL.lib`, `SDLmain.lib`, `SDL_image.lib`, `coldet.lib`, `bass.lib`, `opengl32.lib`, `glu32.lib` y librerías de sistema (kernel32, user32, gdi32, advapi32, shell32, ole32, oleaut32, uuid, odbc32, odbccp32, winspool, comdlg32). Estas son dependencias binario/linker, no referencias a otros proyectos de la solución.

Camino crítico: `sr3.vcxproj` es el único nodo; retarget exitoso y rebuild exitoso son la ruta crítica para resolver MSB8020.

Dependencias circulares: Ninguna detectada (solución con un solo proyecto).

---

## 4. Project-by-Project Plans

- `C:\Users\eass4\OneDrive\Desktop\StreetRod3Classic-main\code\sr3.vcxproj`
  - Current State:
    - `<PlatformToolset>`: `v180` (según build report).  
    - WindowsTargetPlatformVersion: `10.0`.  
    - Build result: Error MSB8020 (toolset no encontrado).  
    - Dependencias de enlace: ver sección 3.  
  - Target State:
    - `<PlatformToolset>`: `<TARGET_TOOLSET>` (p. ej. `v143`) — EXACT target debe confirmarse con inventario de toolsets instalados.
    - Proyecto compila sin MSB8020 y sin nuevos errores introducidos por el cambio de toolset.
  - Migration Steps:
    1. Prerequisitos — Confirmar target toolset disponible en la máquina. ⚠️ Requerido: inventario de toolsets.
    2. Crear rama git para los cambios: `upgrade/cppbuildtools-retarget-v180-to-<TARGET_TOOLSET>`.
    3. Unload project: `upgrade_unload_project` en `C:\Users\eass4\OneDrive\Desktop\StreetRod3Classic-main\code\sr3.vcxproj`.
    4. Editar `.vcxproj`: reemplazar la línea `<PlatformToolset>v180</PlatformToolset>` por `<PlatformToolset><TARGET_TOOLSET></PlatformToolset>`.
       - Nota: usar la cadena exacta del toolset devuelta por el inventario (p.ej. `v143`).
    5. Validar `.vcxproj` editado con `cppupgrade_validate_vcxproj_file` (usar ruta completa del archivo) — no recargar si la validación falla.
    6. Reload project: `upgrade_reload_project` para recargar `sr3.vcxproj` en la solución.
    7. Rebuild y validar: `cppupgrade_rebuild_and_get_issues` para obtener errores y warnings actuales.
    8. Si build muestra errores relacionados con flags incompatibles (p.ej. /ZW, coroutines, cambiado language standard), seguir la ruta de mitigación (ver sección 5).  
    9. Commit en la rama creada con mensaje claro: "Retarget sr3.vcxproj: v180 -> <TARGET_TOOLSET>".

  - Expected Breaking Changes:
    - Posibles errores de compilación por incompatibilidades en flags o uso de extensiones desactualizadas.
    - Posibles diferencias en comportamiento por cambios en optimización o defines (raro, pero documentar si aparece).

  - Testing Strategy (por proyecto):
    - Rebuild completo de la solución tras reload.
    - Ejecutar cualquier test unitario/integración disponible (si aplica).  
    - Validación manual básica: ejecutar la aplicación para comprobar que arranca (si el entorno lo permite).  

  - Validation Checklist:
    - [ ] `.vcxproj` validado por `cppupgrade_validate_vcxproj_file`.
    - [ ] `cppupgrade_rebuild_and_get_issues` muestra 0 errores (o solo los out-of-scope que se acordaron).
    - [ ] Commit en nueva rama con cambios y PR abierto para revisión.

---

## 5. Risk Management

| Risk Description | Likelihood | Impact | Mitigation Strategy |
|------------------|------------|--------|---------------------|
| MSB8020 (missing toolset `v180`) | High | Critical | Retarget in branch with review and validation; keep backup of original `.vcxproj`. |
| Incompatible flags or language features after retarget | Medium | High | 1. Document exact errors. 2. Revert or adapt flags in `.vcxproj` with dedicated change and validation. 3. If code requires language features not available, change `LanguageStandard` or refactor code paths; escalate to developer for manual fixes. |
| Deprecated API or missing includes errors | Low | Medium | Open issue for code fix and proceed per developer guidance. |
| Missing third-party libs (e.g., SDL) | Low | High | Verify `LIBPATH` and presence of .lib files in `lib` folder; if missing, restore or update paths. |

High-risk items:
- MSB8020 (missing toolset `v180`) — riesgo crítico hasta resolver. Mitigación: retarget en rama con revisión y validación; mantener respaldo del `.vcxproj` original.

Potential incompatibilities after retarget:
- Flags such as `/ZW`, coroutine-related flags, or older language feature usage might be incompatible with newer toolsets. Mitigation steps:
  1. If compiler errors reference incompatible flags, document exact errors and revert or adapt flags in `.vcxproj` with a dedicated change and validation.
  2. If code requires language features not available in the target toolset, consider changing `LanguageStandard` or refactoring the code paths; escalate to developer for manual fixes.

Remediation decision tree (summary):
- If `cppupgrade_rebuild_and_get_issues` shows only linker errors for missing third-party libs: verify `LIBPATH` and presence of .lib files in `lib` folder; if missing, restore or update paths.
- If compiler errors show deprecated API or missing includes: open issue for code fix and proceed per developer guidance.

Out-of-scope items (must be listed explicitly):
- Cambios a terceros o libraries binarios (e.g., recompilar SDL) — se informarán como bloqueos si aparecen.
- Actualización de Visual Studio o instalación de `v180` (si se opta por instalar en lugar de retargetear), a menos que el usuario lo solicite.

---

## 6. Testing & Validation Strategy

Phase-by-phase validation:
- Phase 0 (Pre-change): Confirmar inventario de toolsets instalados.
- Phase 1 (Retarget): After edit+reload, run `cppupgrade_rebuild_and_get_issues`.
  - Success: No MSB8020 and no new errors introduced.
  - If errors appear: classify them as (A) build-tooling related (flags, platform SDK mismatch) or (B) code incompatibility. Address per mitigation table.

Smoke tests:
- Rebuild must succeed.
- Application starts (manual smoke) if possible.

Comprehensive validation:
- Run test suite (if any) and validate basic runtime scenarios.

Test artifacts to capture:
- `cppupgrade_rebuild_and_get_issues` output before and after change.
- `cppupgrade_validate_vcxproj_file` result.
- Commit/PR references and reviewer sign-off.

---

## 7. Complexity & Effort Assessment

- Project `sr3.vcxproj` — Complexity: Medium (tooling change may cascade to small code edits).  
- Dependencies: External libs present (linker), but they are not project references.  
- Parallel capacity: Single project; single-threaded execution recommended.

---

## 8. Source Control Strategy

- Create a feature branch for the retarget change: `upgrade/cppbuildtools-retarget-v180-to-<TARGET_TOOLSET>`.
- Commit atomic change: only edit to `.vcxproj` (and any minimal changes required to restore build, each in separate commits with clear messages).
- PR checklist: include build output before and after, mention validation steps executed, and request review from a maintainer who understands platform toolset implications.

Changelog template for the PR:
- Summary: "Retarget sr3.vcxproj from v180 to <TARGET_TOOLSET>."
- Files changed: list full path to `.vcxproj`.
- Build validation: attach `cppupgrade_rebuild_and_get_issues` output.

---

## 9. Success Criteria

- Technical:
  - `cppupgrade_rebuild_and_get_issues` returns 0 errors for `sr3.sln` after retarget.
  - No MSB8020 reported.
  - Any introduced build errors are addressed and documented before merging.
- Quality:
  - No regressions in runtime smoke tests documented.
  - Changes limited to `.vcxproj` and necessary follow-ups; code changes are minimal and reviewed.
- Process:
  - Changes made on feature branch with PR and validation artifacts attached.

---

## Appendix A: Commands & Tools

Planned tool usage (executor must run these in sequence):
1. Inventory installed toolsets (manual step or using Visual Studio Installer output).  
2. `upgrade_unload_project` for `C:\Users\eass4\OneDrive\Desktop\StreetRod3Classic-main\code\sr3.vcxproj`.
3. Edit the `.vcxproj` file: replace `<PlatformToolset>v180</PlatformToolset>` with `<PlatformToolset><TARGET_TOOLSET></PlatformToolset>` (use exact string from inventory).
4. `cppupgrade_validate_vcxproj_file` on the edited file (use absolute path).
5. `upgrade_reload_project` for the project file.
6. `cppupgrade_rebuild_and_get_issues` to validate build.

Notes & conditional flows:
- If `cppupgrade_validate_vcxproj_file` fails: do NOT reload; inspect errors, fix `.vcxproj` accordingly, re-validate.
- If rebuild shows flag incompatibilities, follow mitigation section in Risks to address them in source or project settings.

---

⚠️ Requerimientos pendientes (bloqueantes para ejecución):
- Confirmar el toolset objetivo instalado (`<TARGET_TOOLSET>`).  
- Confirmar permiso para crear ramas y editar `.vcxproj` automáticamente.

---

Change Log:
- 2026-04-01: Plan creado basado en assessment.md y salida de `cppupgrade_rebuild_and_get_issues`.
