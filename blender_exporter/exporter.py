"""
Core export logic: Blender scene data  →  AUXModel.

Coordinate system
-----------------
Blender uses a right-handed, Z-up system (X right, Y forward, Z up).
SR3 appears to use a Y-up system (X right, Z forward, Y up), which is
typical for OpenGL games of that era.

The default conversion applied here is:
    game_x =  blender_x
    game_y =  blender_z       (Blender up → game up)
    game_z = -blender_y       (Blender forward → game -forward)

This can be disabled by passing axis_conversion=False.

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


def _convert_pos(v, convert: bool):
    """Blender position vector → game position vector."""
    x, y, z = float(v[0]), float(v[1]), float(v[2])
    if convert:
        return (x, z, -y)
    return (x, y, z)


def _convert_matrix(rot3x3, convert: bool):
    """Convert a Blender 3×3 rotation matrix to game space.

    Applies the same axis permutation as _convert_pos to each basis vector.
    Returns a list-of-rows suitable for GameObjectData.matrix.
    """
    if not convert:
        return [[float(rot3x3[r][c]) for c in range(3)] for r in range(3)]

    # Basis vectors in Blender space
    bx = (rot3x3[0][0], rot3x3[1][0], rot3x3[2][0])
    by = (rot3x3[0][1], rot3x3[1][1], rot3x3[2][1])
    bz = (rot3x3[0][2], rot3x3[1][2], rot3x3[2][2])

    def cvt(bv):
        bvx, bvy, bvz = bv
        return (bvx, bvz, -bvy)

    gx, gy, gz = cvt(bx), cvt(by), cvt(bz)

    # Reconstruct rows (row i = column i of the basis-column matrix)
    return [
        [gx[0], gy[0], gz[0]],
        [gx[1], gy[1], gz[1]],
        [gx[2], gy[2], gz[2]],
    ]


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

        # Ensure split normals are available
        me.calc_normals_split()
        me.calc_loop_triangles()

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

                # Split normal (set by calc_normals_split)
                wn = (normal_mat @ loop.normal).normalized()
                gn = _convert_pos(wn, convert)
                poly.normal_idx[i] = _collect(model.normals, _r(gn))

            # UV channels (one entry per UV map)
            for uv_layer in uv_layers:
                ch = []
                for loop_idx in tri.loops:
                    uv = uv_layer.data[loop_idx].uv
                    # Flip V: Blender V=0 bottom → OpenGL V=0 top
                    entry = (round(float(uv.x), _ROUND),
                             round(1.0 - float(uv.y), _ROUND))
                    ch.append(_collect(model.uvcoords, entry))
                poly.uv_channels.append(ch)

            # Guarantee at least one UV channel (zero UVs)
            if not uv_layers:
                zero = _collect(model.uvcoords, (0.0, 0.0))
                poly.uv_channels.append([zero, zero, zero])

            mesh_data.polygons.append(poly)

    finally:
        obj_eval.to_mesh_clear()

    return mesh_data


def _process_light(obj, convert: bool) -> LightData:
    light = LightData()
    pos = obj.matrix_world.translation
    light.position = _convert_pos(pos, convert)

    bl = obj.data
    light.colour = (float(bl.color[0]),
                    float(bl.color[1]),
                    float(bl.color[2]))
    # energy → brightness heuristic (game expects 0-1 range roughly)
    light.brightness = min(float(bl.energy) / 100.0, 1.0)
    light.radius = float(getattr(bl, 'shadow_soft_size', 1.0))
    return light


def _process_empty(obj, convert: bool) -> GameObjectData:
    pos  = obj.matrix_world.translation
    gpos = _convert_pos(pos, convert)
    rot  = obj.matrix_world.to_3x3()
    mat  = _convert_matrix(rot, convert)
    return GameObjectData(obj.name, gpos, mat)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def export_scene(context,
                 filepath: str,
                 export_selected: bool,
                 axis_conversion: bool) -> set:
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
        md = _process_mesh(obj, model, depsgraph, axis_conversion)
        model.meshes.append(md)

    for obj in light_objs:
        model.lights.append(_process_light(obj, axis_conversion))

    for obj in empty_objs:
        model.game_objects.append(_process_empty(obj, axis_conversion))

    base = os.path.splitext(filepath)[0]
    write_aux(filepath, model)
    write_mat(base + '.mat', model)

    return {'FINISHED'}
