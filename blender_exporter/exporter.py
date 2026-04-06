"""
Core export logic: Blender scene data  →  AUXModel.

Coordinate system
-----------------
SR3 uses the same Z-up, Y-forward coordinate system as Blender:
    game_x = blender_x   (X right)
    game_y = blender_y   (Y forward / car length)
    game_z = blender_z   (Z up / car height)

No axis conversion is required.  The ``axis_conversion`` parameter is
retained in the API for backwards compatibility but no longer performs
an axis swap.

Scale
-----
Existing SR3 car models use approximately 4.9 game units per real metre.
If your Blender model is built at 1:1 metre scale, pass ``scale=4.9``
(or set the Scale field in the export dialog).

Object conventions
------------------
  - MESH objects    → meshes in the .aux
  - LIGHT objects   → point lights in the .aux
  - EMPTY objects whose name starts with '$' → game objects (anchors)

    Required car anchors:
      $flwheel  $frwheel  $brwheel  $blwheel   (wheel positions)
      $flshock  $frshock  $brshock  $blshock   (shock positions)
      $lmuffler  $rmuffler                     (exhaust positions)
      $block                                   (engine block)
      $diff                                    (differential)
      $trans                                   (transmission)
      $incar_cam                               (cockpit camera)
      $hlite01, $hlite02, ...                  (headlights, sequential)
      $tlite01, $tlite02, ...                  (tail lights, sequential)

UV coordinates
--------------
Blender stores V=0 at the bottom; OpenGL/SR3 expects V=0 at the top,
so V is flipped (v_out = 1.0 - v_in) during export.
"""

import bpy
import bmesh
import os

from .aux_writer import (AUXModel, MeshData, PolygonData,
                         LightData, GameObjectData)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ROUND = 6   # decimal places used when deduplicating floats


def _r(v):
    return tuple(round(x, _ROUND) for x in v)


def _collect(lst: list, item: tuple) -> int:
    """Return the index of *item* in *lst*, appending it if not present."""
    try:
        return lst.index(item)
    except ValueError:
        lst.append(item)
        return len(lst) - 1


def _convert_pos(v, convert: bool = True, scale: float = 1.0):
    """Blender position vector → game position vector.

    SR3 uses the same coordinate system as Blender (Z-up, Y-forward),
    so no axis conversion is applied.  The *convert* flag is kept for
    API compatibility.  *scale* multiplies all three components.
    """
    x, y, z = float(v[0]), float(v[1]), float(v[2])
    return (x * scale, y * scale, z * scale)


def _convert_matrix(rot3x3, convert: bool = True):
    """Return a 3×3 rotation matrix as a list-of-rows.

    SR3 uses Blender's coordinate system so no remapping is applied.
    The *convert* flag is kept for API compatibility.
    """
    return [[float(rot3x3[r][c]) for c in range(3)] for r in range(3)]


# ---------------------------------------------------------------------------
# Per-object processing
# ---------------------------------------------------------------------------

def _process_mesh(obj, model: AUXModel,
                  depsgraph, convert: bool) -> MeshData:
    """Triangulate *obj* and append its geometry into the shared lists."""
    mesh_data = MeshData(obj.name)

    # Apply modifiers via evaluated object
    obj_eval = obj.evaluated_get(depsgraph)
    me = obj_eval.to_mesh()

    try:
        # Triangulate with bmesh so we always work with tris
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bm.to_mesh(me)
        bm.free()

        # Ensure split normals are available.
        # calc_normals_split() was removed in Blender 4.1; in 4.1+ split
        # normals are always computed and accessible via me.corner_normals.
        if hasattr(me, 'calc_normals_split'):
            me.calc_normals_split()
        me.calc_loop_triangles()

        # Choose the normal accessor once, outside the loop
        _use_corner_normals = hasattr(me, 'corner_normals')

        world_mat   = obj.matrix_world
        normal_mat  = world_mat.to_3x3().inverted_safe().transposed()
        uv_layers   = me.uv_layers

        # Map material slots → indices in model.material_names
        local_mat_idx = []
        for slot in obj.material_slots:
            if slot.material:
                name = slot.material.name
                if name not in model.material_names:
                    model.material_names.append(name)
                local_mat_idx.append(model.material_names.index(name))
            else:
                local_mat_idx.append(0)

        # Pre-cache UV data as flat [u0,v0, u1,v1, ...] buffers before the
        # triangle loop.  foreach_get is stable across all Blender versions;
        # the per-loop .data[i].uv access broke in Blender 5.x.
        uv_buf = []
        for uv_layer in uv_layers:
            buf = [0.0] * (len(me.loops) * 2)
            try:
                uv_layer.data.foreach_get('uv', buf)      # Blender <= 4.x
            except (AttributeError, TypeError):
                try:
                    uv_layer.data.foreach_get('vector', buf)  # Blender 5.x
                except (AttributeError, TypeError):
                    pass
            uv_buf.append(buf)

        for tri in me.loop_triangles:
            poly = PolygonData()

            # Material index (clamp for safety)
            slot_idx = min(tri.material_index, len(local_mat_idx) - 1) \
                       if local_mat_idx else 0
            poly.mat_idx = local_mat_idx[slot_idx] if local_mat_idx else 0

            # Vertices, normals, UVs
            for i, loop_idx in enumerate(tri.loops):
                loop = me.loops[loop_idx]
                vert = me.vertices[loop.vertex_index]

                # Position
                wp = world_mat @ vert.co
                gp = _convert_pos(wp, convert)
                poly.vertex_idx[i] = _collect(model.vertices, _r(gp))

                # Split normal: Blender 4.1+ uses corner_normals[loop_idx]
                if _use_corner_normals:
                    raw_normal = me.corner_normals[loop_idx].vector
                else:
                    raw_normal = loop.normal
                wn = (normal_mat @ raw_normal).normalized()
                gn = _convert_pos(wn, convert)
                poly.normal_idx[i] = _collect(model.normals, _r(gn))

            # UV channels (one per UV map, from pre-cached flat buffers)
            for buf in uv_buf:
                ch = []
                for loop_idx in tri.loops:
                    u = buf[loop_idx * 2]
                    v = buf[loop_idx * 2 + 1]
                    entry = (round(float(u), _ROUND),
                             round(1.0 - float(v), _ROUND))
                    ch.append(_collect(model.uvcoords, entry))
                poly.uv_channels.append(ch)

            # Guarantee at least one UV channel (zero UVs)
            if not uv_buf:
                zero = _collect(model.uvcoords, (0.0, 0.0))
                poly.uv_channels.append([zero, zero, zero])

            mesh_data.polygons.append(poly)

    finally:
        obj_eval.to_mesh_clear()

    return mesh_data


def _process_light(obj, convert: bool, scale: float = 1.0) -> LightData:
    light = LightData()
    pos = obj.matrix_world.translation
    light.position = _convert_pos(pos, convert, scale)

    bl = obj.data
    light.colour = (float(bl.color[0]),
                    float(bl.color[1]),
                    float(bl.color[2]))
    # energy → brightness heuristic (game expects 0-1 range roughly)
    light.brightness = min(float(bl.energy) / 100.0, 1.0)
    light.radius = float(getattr(bl, 'shadow_soft_size', 1.0))
    return light


def _process_empty(obj, convert: bool, scale: float = 1.0) -> GameObjectData:
    pos  = obj.matrix_world.translation
    gpos = _convert_pos(pos, convert, scale)
    rot  = obj.matrix_world.to_3x3()
    mat  = _convert_matrix(rot, convert)
    return GameObjectData(obj.name, gpos, mat)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def export_scene(context,
                 filepath: str,
                 export_selected: bool,
                 axis_conversion: bool,
                 scale: float = 1.0) -> set:
    """Export the current scene (or selection) to *filepath* (.aux + .mat).

    Returns a Blender operator result set: {'FINISHED'} or {'CANCELLED'}.
    """
    from .mat_writer import write_mat
    from .aux_writer import write_aux

    objects = (list(context.selected_objects)
               if export_selected else list(context.scene.objects))

    mesh_objs  = [o for o in objects if o.type == 'MESH']
    light_objs = [o for o in objects if o.type == 'LIGHT']
    empty_objs = [o for o in objects
                  if o.type == 'EMPTY' and o.name.startswith('$')]

    if not mesh_objs and not empty_objs:
        return {'CANCELLED'}

    model = AUXModel()
    depsgraph = context.evaluated_depsgraph_get()

    for obj in mesh_objs:
        md = _process_mesh(obj, model, depsgraph, axis_conversion, scale)
        model.meshes.append(md)

    for obj in light_objs:
        model.lights.append(_process_light(obj, axis_conversion, scale))

    for obj in empty_objs:
        model.game_objects.append(_process_empty(obj, axis_conversion, scale))

    base = os.path.splitext(filepath)[0]
    write_aux(filepath, model)
    write_mat(base + '.mat', model)

    return {'FINISHED'}
