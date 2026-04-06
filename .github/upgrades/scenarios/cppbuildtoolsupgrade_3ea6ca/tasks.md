# sr3.vcxproj MSVC Build Tools Modernization Tasks

## Overview

This document tracks the modernization of the sr3.vcxproj project to MSVC Build Tools v143 (x64), focusing on resolving 254 compiler warnings across 30 source files. The project has already been retargeted to v143 and x64 architecture; remaining work involves fixing warnings in three risk-prioritized phases.

**Progress**: 2/4 tasks complete (50%) ![0%](https://progress-bar.xyz/50)

---

## Tasks

### [✓] TASK-001: Verify prerequisites and confirm project configuration *(Completed: 2026-04-05 20:50)*
**References**: Plan §4.2 Phase 0, Plan §3 Detailed Dependency Analysis

- [✓] (1) Verify PlatformToolset is v143 in all PropertyGroup configurations in `C:\Users\eass4\source\repos\StreetRod3Classic-main\code\sr3.vcxproj`
- [✓] (2) All configurations use v143 toolset (**Verify**)
- [✓] (3) Verify Debug|x64 and Release|x64 configurations use `/MACHINE:X64` and reference `lib\x64`
- [✓] (4) x64 configurations correctly reference 64-bit library paths (**Verify**)
- [✓] (5) Verify external libraries in `lib\x64` are 64-bit binaries using `dumpbin /headers` or equivalent
- [✓] (6) All external libraries (SDL2, SDL2_image, bass, coldet) are x64 architecture (**Verify**)
- [⊘] (7) Commit current .vcxproj state with message: "TASK-001: retarget: v143 PlatformToolset and x64 configurations"

---

### [✓] TASK-002: Fix critical 64-bit safety warnings (C4267, C4244 __int64) *(Completed: 2026-04-05 21:15)*
**References**: Plan §4.2 Phase 1, Assessment #Issue CPPBUILDTOOLSUPGRADE_3EA6CA-1 through #Issue CPPBUILDTOOLSUPGRADE_3EA6CA-18

- [✓] (1) Fix C4267 warnings in `CommonFuncs.cpp` lines 56, 178, 201 per Plan §4.2 Phase 1 table (change loop variable types to avoid underflow, add static_cast for string length conversions)
- [✓] (2) Fix C4267 warning in `CModel.cpp` line 498 (static_cast for strlen result)
- [✓] (3) Fix C4244 __int64 warning in `CScript.cpp` line 122 and C4267 in line 168 (pointer arithmetic cast, verify loop variable type)
- [✓] (4) Fix C4244 __int64 warning in `ConfigHandler.cpp` line 189 (pointer arithmetic cast)
- [✓] (5) Fix warnings in `CSceneScript.cpp` lines 252, 290 (strlen and pointer arithmetic casts)
- [✓] (6) Fix warnings in `CLabel.cpp` lines 48-49, `CLocation.cpp` line 469, `CTextbox.cpp` line 164, `Diner.cpp` line 842, `font.cpp` line 124, `Garage_Dlg.cpp` line 1241, `Garage_Game.cpp` line 1654, `Garage_Newspaper.cpp` line 732, `text.cpp` line 258 per Plan §4.2 Phase 1 detailed corrections table
- [✓] (7) Build solution using cppupgrade_rebuild_and_get_issues
- [✓] (8) All C4267 and C4244 __int64 warnings eliminated, 0 errors (**Verify**)
- [⊘] (9) Commit changes with message: "TASK-002: fix: corregir warnings C4267 y C4244 __int64 para seguridad en 64 bits"

---

### [✗] TASK-003: Fix POSIX deprecation warnings (C4996)
**References**: Plan §4.2 Phase 2, Plan §4.2 Phase 2 replacement table

- [✗] (1) Replace all `stricmp` calls with `_stricmp` in files listed in Plan §4.2 Phase 2 (CCar.cpp, CInput.cpp, CModel.cpp, ConfigHandler.cpp, CScript.cpp, CTexture.cpp, Keyword_Manager.cpp, CMaterial.cpp, CDialog.cpp, CSceneScript.cpp, CTaskBar.cpp, InitSystem.cpp, TextureManager.cpp)
- [✓] (2) Replace all `strnicmp` calls with `_strnicmp` in files per Plan §4.2 Phase 2 table (CModel.cpp, CPart.cpp, CMaterial.cpp)
- [✓] (3) Replace `fopen` calls in `src\glFont\Utility.cpp` lines 50, 106 with `fopen_s` per Plan §4.2 Phase 2 (adjust error handling pattern per notes)
- [✓] (4) Replace `strncpy` calls in `src\glFont\Utility.cpp` lines 162, 192 with `strncpy_s` per Plan §4.2 Phase 2 (verify buffer sizes)
- [✗] (5) Build solution using cppupgrade_rebuild_and_get_issues
- [✗] (6) All C4996 warnings eliminated, 0 errors (**Verify**)
- [ ] (7) Commit changes with message: "TASK-003: fix: reemplazar funciones POSIX deprecadas por equivalentes ISO C/C++ (C4996)"

---

### [ ] TASK-004: Fix all remaining numeric and code quality warnings
**References**: Plan §4.2 Phase 3, Plan §4.2 Phase 3a-3d tables

- [ ] (1) Fix C4005 macro redefinitions in `CCarSim.cpp` line 254 and `text.h` line 30 per Plan §4.2 Phase 3a (resolve EPSILON conflict, add include guards for WIN32_LEAN_AND_MEAN)
- [ ] (2) Remove unused variables (C4101) in `CCarSim.cpp` line 332, `Garage_Game.cpp` lines 949-952, `text.cpp` lines 100, 126 per Plan §4.2 Phase 3b
- [ ] (3) Fix signed/unsigned mismatches (C4018) in `CCar.cpp` lines 454, 1625, `CCar_Driving.cpp` line 65, `CModel.cpp` line 260, `CQuadTree.cpp` line 138 per Plan §4.2 Phase 3c
- [ ] (4) Fix numeric conversion warnings (C4244, C4305) in high-density files per Plan §4.2 Phase 3d: `CCarSim.cpp`, `Menu.cpp`, `CCar.cpp`, `CColourPicker.cpp`, `CQuaternion.cpp`, `Race_main.cpp`, `CDialog.cpp`, `CWheel.cpp`, `CMatrix.cpp`, `CCamera.cpp`, `CLocation.cpp` (apply literal suffixes, use float math functions, add explicit casts)
- [ ] (5) Fix remaining C4244/C4305 warnings in all other affected files per Plan §4.2 Phase 3d strategy (process file-by-file in density order)
- [ ] (6) Build solution using cppupgrade_rebuild_and_get_issues
- [ ] (7) Solution builds with 0 errors and 0 warnings (**Verify**)
- [ ] (8) Commit changes with message: "TASK-004: fix: eliminar warnings C4244, C4305, C4018, C4005, C4101"

---


