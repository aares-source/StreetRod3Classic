"""
StreetRod3 AUX Exporter — Blender Add-on
=========================================
Exports the selected mesh/light/empty objects to the proprietary binary
Auxiliary 3D format (.aux) used by StreetRod3Classic, together with a
companion text material file (.mat).

Installation
------------
1. Zip the entire *blender_exporter* folder.
2. In Blender: Edit > Preferences > Add-ons > Install… → select the zip.
3. Enable "Import-Export: StreetRod3 AUX Exporter".

Usage
-----
File > Export > StreetRod3 Model (.aux)

Object naming conventions
--------------------------
  MESH objects   → 3D meshes written to the .aux
  LIGHT objects  → point lights in the .aux
  EMPTY objects  → game-object anchors; the object name MUST start with '$'
                   (e.g. "$flwheel", "$block", "$incar_cam")

See exporter.py for the full list of required anchor names.
"""

bl_info = {
    "name":        "StreetRod3 AUX Exporter",
    "author":      "StreetRod3Classic contributors",
    "version":     (1, 0, 0),
    "blender":     (3, 6, 0),
    "location":    "File > Export > StreetRod3 Model (.aux)",
    "description": "Export to StreetRod3 Auxiliary 3D binary format (.aux + .mat)",
    "category":    "Import-Export",
}

import bpy
import os
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy_extras.io_utils import ExportHelper


# ---------------------------------------------------------------------------
# Deploy helpers
# ---------------------------------------------------------------------------

def _write_default_sr3(path: str, car_folder: str) -> None:
    """Write a minimal newspaper .sr3 file with standard parts."""
    display_name = car_folder.replace('_', ' ').replace('-', ' ').title()
    parts = [
        ("Block",      "ford_block_v6"),
        ("Fan",        "standard_fan"),
        ("Alternator", "standard_alt"),
        ("Intake",     "ford_v6_2brl_manifold"),
        ("Starter",    "starter_stock"),
        ("Carb1",      "ford_2brl_carby"),
        ("Airfilter",  "standard_airfilter"),
        ("LMuffler",   "standard_lmuffler"),
        ("RMuffler",   "standard_rmuffler"),
        ("Diff",       "ford_diff"),
        ("Trans",      "ford_3spd_trans"),
    ]
    with open(path, 'w', encoding='ascii', errors='replace') as f:
        f.write(f"// {display_name}\n\n")
        f.write(f"[Car]\nCar = {car_folder}\nName = {display_name}\n")
        f.write("Description = \\nRuns good\nManufacturer = MAN_ford\n\n")
        f.write("[Price]\nMinPrice = 100\nMaxPrice = 300\nSellingPrice = 800\n")
        for i in range(1, 5):
            f.write(f"\n[Tire{i}]\nPart = Chrome_Smoothie_Wheel\nDamage = 0\n")
        for section, part in parts:
            f.write(f"\n[{section}]\nPart = {part}\nDamage = 0\n")
        for i in range(1, 5):
            f.write(f"\n[Shock{i}]\nPart = shock_stock\nDamage = 0\n")


def _deploy_car(game_root: str, car_folder: str,
                aux_path: str, mat_path: str) -> None:
    """Copy car.aux + car.mat to the game and create .sr3 if missing."""
    import shutil
    car_dir = os.path.join(game_root, 'data', 'cars', car_folder)
    os.makedirs(car_dir, exist_ok=True)
    shutil.copy2(aux_path, os.path.join(car_dir, 'car.aux'))
    shutil.copy2(mat_path, os.path.join(car_dir, 'car.mat'))
    sr3_path = os.path.join(game_root, 'data', 'newspaper', car_folder + '.sr3')
    if not os.path.exists(sr3_path):
        _write_default_sr3(sr3_path, car_folder)


# ---------------------------------------------------------------------------
# Addon preferences
# ---------------------------------------------------------------------------

class SR3_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    game_root: bpy.props.StringProperty(
        name="Game Root Directory",
        description="Folder that contains the 'data' subfolder of StreetRod3Classic",
        subtype='DIR_PATH',
        default="",
    )

    def draw(self, context):
        self.layout.prop(self, "game_root")


# ---------------------------------------------------------------------------
# Export operator
# ---------------------------------------------------------------------------

class SR3_OT_ExportAUX(bpy.types.Operator, ExportHelper):
    """Export selected objects to StreetRod3 .aux + .mat"""

    bl_idname  = "export_scene.sr3_aux"
    bl_label   = "Export SR3 Model"
    bl_options = {'PRESET'}

    # ExportHelper sets this as the default extension
    filename_ext = ".aux"

    filter_glob: bpy.props.StringProperty(
        default="*.aux",
        options={'HIDDEN'},
    )

    export_selected: BoolProperty(
        name="Selected Only",
        description="Export only selected objects (mesh, light, $-empties)",
        default=True,
    )

    axis_conversion: BoolProperty(
        name="Axis Conversion (Z-up → Y-up)",
        description=(
            "Convert from Blender Z-up to game Y-up coordinate system.\n"
            "Blender (X right, Y forward, Z up) →\n"
            "Game   (X right, Z forward, Y up).\n"
            "Disable if your model is already oriented for the game."
        ),
        default=True,
    )

    deploy_to_game: BoolProperty(
        name="Deploy to Game",
        description=(
            "After export, copy car.aux + car.mat to data/cars/<name>/ and\n"
            "create data/newspaper/<name>.sr3 (only if it does not exist yet).\n"
            "Set the game root path in Add-on Preferences."
        ),
        default=False,
    )

    car_folder: StringProperty(
        name="Car Folder",
        description="Subfolder under data/cars/ (leave blank to use the export filename)",
        default="",
    )

    def execute(self, context):
        import traceback
        from . import exporter
        try:
            result = exporter.export_scene(
                context,
                filepath=self.filepath,
                export_selected=self.export_selected,
                axis_conversion=self.axis_conversion,
            )
        except Exception:
            tb = traceback.format_exc()
            print(tb)  # visible in Window > Toggle System Console
            log_path = os.path.splitext(self.filepath)[0] + '_export_error.log'
            with open(log_path, 'w', encoding='utf-8') as log_f:
                log_f.write(tb)
            self.report({'ERROR'},
                        f"Export failed — full traceback saved to: {log_path}")
            return {'CANCELLED'}

        if 'FINISHED' not in result:
            self.report({'WARNING'},
                        "No exportable objects found (need MESH / LIGHT / $-EMPTY).")
            return result

        if self.deploy_to_game:
            prefs = context.preferences.addons[__name__].preferences
            game_root = prefs.game_root.rstrip('/\\')
            if not game_root:
                self.report({'WARNING'},
                            "Deploy skipped — set Game Root in Add-on Preferences.")
            else:
                folder = (self.car_folder.strip() or
                          os.path.splitext(os.path.basename(self.filepath))[0])
                try:
                    _deploy_car(game_root, folder, self.filepath,
                                os.path.splitext(self.filepath)[0] + '.mat')
                    self.report({'INFO'},
                                f"Exported and deployed → {game_root}\\data\\cars\\{folder}\\")
                except Exception as e:
                    self.report({'WARNING'}, f"Export OK but deploy failed: {e}")
        else:
            self.report({'INFO'}, f"Exported to {self.filepath!r}")

        return result

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(self, "export_selected")
        layout.prop(self, "axis_conversion")

        layout.separator()
        layout.prop(self, "deploy_to_game")
        if self.deploy_to_game:
            col = layout.column(align=True)
            col.prop(self, "car_folder")
            prefs = context.preferences.addons[__name__].preferences
            if prefs.game_root:
                col.label(text=prefs.game_root, icon='FILE_FOLDER')
            else:
                col.label(text="Set Game Root in Add-on Preferences", icon='ERROR')

        layout.separator()
        layout.label(text="EMPTY objects named $xxx → anchors", icon='EMPTY_AXIS')
        layout.label(text="Required: $flwheel, $frwheel, $brwheel, $blwheel")
        layout.label(text="          $flshock, $frshock, $brshock, $blshock")
        layout.label(text="          $block, $diff, $trans, $incar_cam")
        layout.label(text="          $lmuffler, $rmuffler")
        layout.label(text="          $hlite01…, $tlite01…")


# ---------------------------------------------------------------------------
# Menu hook
# ---------------------------------------------------------------------------

def _menu_func_export(self, context):
    self.layout.operator(SR3_OT_ExportAUX.bl_idname,
                         text="StreetRod3 Model (.aux)")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register():
    bpy.utils.register_class(SR3_AddonPreferences)
    bpy.utils.register_class(SR3_OT_ExportAUX)
    bpy.types.TOPBAR_MT_file_export.append(_menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(_menu_func_export)
    bpy.utils.unregister_class(SR3_OT_ExportAUX)
    bpy.utils.unregister_class(SR3_AddonPreferences)
