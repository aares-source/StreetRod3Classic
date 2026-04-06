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
from bpy.props import BoolProperty, EnumProperty
from bpy_extras.io_utils import ExportHelper


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

    def execute(self, context):
        from . import exporter
        result = exporter.export_scene(
            context,
            filepath=self.filepath,
            export_selected=self.export_selected,
            axis_conversion=self.axis_conversion,
        )
        if 'FINISHED' in result:
            self.report({'INFO'},
                        f"Exported to {self.filepath!r}")
        else:
            self.report({'WARNING'},
                        "No exportable objects found (need MESH / LIGHT / $-EMPTY).")
        return result

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(self, "export_selected")
        layout.prop(self, "axis_conversion")

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
    bpy.utils.register_class(SR3_OT_ExportAUX)
    bpy.types.TOPBAR_MT_file_export.append(_menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(_menu_func_export)
    bpy.utils.unregister_class(SR3_OT_ExportAUX)
