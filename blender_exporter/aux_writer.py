"""
StreetRod3 Auxiliary 3D binary format (.aux) writer.

Binary layout (all values little-endian):

  [15 bytes]  Signature: b'Auxiliary 3D' + 0x1A 0x08 0x04
  [4  bytes]  Version: int32 = 1
  --- Counts (all uint32) ---
  [4  bytes]  NumMaterials
  [4  bytes]  NumMeshes
  [4  bytes]  NumLights
  [4  bytes]  NumGameObjects
  [4  bytes]  NumVertices
  [4  bytes]  NumTexCoords
  [4  bytes]  NumVertexNormals
  --- Shared lists ---
  [N * 12]    Vertex list:       X, Y, Z  (float32 each)
  [N * 8]     TexCoord list:     U, V     (float32 each)
  [N * 12]    VertexNormal list: X, Y, Z  (float32 each)
  --- Material names ---
  [N * ?]     Pascal-string per material: 1 byte length + N bytes text
  --- Meshes ---
  [N * ?]     Per mesh:
                Pascal-string name
                uint32 NumPolygons
                Per polygon:
                  uint8  NumChannels
                  Per channel: 3 * uint32 UV indices (one per triangle vertex)
                  Per vertex (x3): uint32 NormalIdx, uint32 VertexIdx
                  uint16 LightMapID  (always 0)
                  uint32 TextureID   (material index)
  --- Lights ---
  [N * 32]    Per light: Position(3f) + Colour(3f) + Radius(f) + Brightness(f)
  --- Game Objects ---
  [N * ?]     Per game object:
                Pascal-string name  (e.g. "$flwheel")
                Position: X, Y, Z  (float32 each)
                Matrix:   9 * float32 in row-major order
                          (CMatrix::Load reads mat[j][i] for i-outer/j-inner,
                           then Transpose() is applied, so row-major = correct)
"""

import struct

AUX_SIGNATURE = b'Auxiliary 3D\x1A\x08\x04'
AUX_VERSION = 1


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _write_pascal_string(fp, s: str) -> None:
    """1-byte length prefix + raw ASCII bytes (no null terminator)."""
    encoded = s.encode('ascii', errors='replace')
    length = min(len(encoded), 255)
    fp.write(struct.pack('<B', length))
    fp.write(encoded[:length])


def _write_vec3(fp, x: float, y: float, z: float) -> None:
    fp.write(struct.pack('<3f', x, y, z))


def _write_uint(fp, n: int) -> None:
    fp.write(struct.pack('<I', n))


def _write_ushort(fp, n: int) -> None:
    fp.write(struct.pack('<H', n))


def _write_uchar(fp, n: int) -> None:
    fp.write(struct.pack('<B', n))


def _write_int32(fp, n: int) -> None:
    fp.write(struct.pack('<i', n))


def _write_float(fp, f: float) -> None:
    fp.write(struct.pack('<f', f))


def _write_matrix_row_major(fp, matrix_3x3) -> None:
    """Write a 3x3 matrix in row-major order.

    CMatrix::Load reads mat[j][i] for (i outer, j inner), then calls
    Transpose().  The net effect is that the file stores the matrix in
    row-major order of the desired final matrix.  So we simply write
    row 0, row 1, row 2.

    matrix_3x3: sequence of 3 rows, each a sequence of 3 floats.
    """
    for row in matrix_3x3:
        for val in row:
            _write_float(fp, float(val))


# ---------------------------------------------------------------------------
# Intermediate data model
# ---------------------------------------------------------------------------

class PolygonData:
    """One triangle in the .aux format."""
    __slots__ = ('mat_idx', 'vertex_idx', 'normal_idx', 'uv_channels')

    def __init__(self):
        self.mat_idx: int = 0
        self.vertex_idx = [0, 0, 0]    # indices into AUXModel.vertices
        self.normal_idx = [0, 0, 0]    # indices into AUXModel.normals
        # One entry per UV channel, each a list of 3 UV indices
        self.uv_channels: list = []


class MeshData:
    """One named mesh."""
    __slots__ = ('name', 'polygons')

    def __init__(self, name: str):
        self.name: str = name
        self.polygons: list = []   # list of PolygonData


class LightData:
    """Point light."""
    __slots__ = ('position', 'colour', 'radius', 'brightness')

    def __init__(self):
        self.position = (0.0, 0.0, 0.0)
        self.colour   = (1.0, 1.0, 1.0)
        self.radius   = 1.0
        self.brightness = 1.0


class GameObjectData:
    """Named anchor point ($flwheel, $block, $incar_cam, etc.)"""
    __slots__ = ('name', 'position', 'matrix')

    def __init__(self, name: str,
                 position=(0.0, 0.0, 0.0),
                 matrix=None):
        self.name: str = name
        self.position = position
        # Identity matrix if not provided
        self.matrix = matrix or [[1.0, 0.0, 0.0],
                                  [0.0, 1.0, 0.0],
                                  [0.0, 0.0, 1.0]]


class AUXModel:
    """Complete intermediate representation of an .aux model."""

    def __init__(self):
        self.vertices:       list = []   # (x, y, z)
        self.uvcoords:       list = []   # (u, v)
        self.normals:        list = []   # (nx, ny, nz)
        self.material_names: list = []   # str
        self.meshes:         list = []   # MeshData
        self.lights:         list = []   # LightData
        self.game_objects:   list = []   # GameObjectData


# ---------------------------------------------------------------------------
# Main writer
# ---------------------------------------------------------------------------

def write_aux(filepath: str, model: AUXModel) -> None:
    """Serialise *model* to *filepath* in the Auxiliary 3D binary format."""
    with open(filepath, 'wb') as fp:

        # ---- Header -------------------------------------------------------
        fp.write(AUX_SIGNATURE)
        _write_int32(fp, AUX_VERSION)

        # ---- Counts -------------------------------------------------------
        _write_uint(fp, len(model.material_names))
        _write_uint(fp, len(model.meshes))
        _write_uint(fp, len(model.lights))
        _write_uint(fp, len(model.game_objects))
        _write_uint(fp, len(model.vertices))
        _write_uint(fp, len(model.uvcoords))
        _write_uint(fp, len(model.normals))

        # ---- Shared lists -------------------------------------------------
        for x, y, z in model.vertices:
            _write_vec3(fp, x, y, z)

        for u, v in model.uvcoords:
            fp.write(struct.pack('<2f', u, v))

        for nx, ny, nz in model.normals:
            _write_vec3(fp, nx, ny, nz)

        # ---- Material names -----------------------------------------------
        for name in model.material_names:
            _write_pascal_string(fp, name)

        # ---- Meshes -------------------------------------------------------
        for mesh in model.meshes:
            _write_pascal_string(fp, mesh.name)
            _write_uint(fp, len(mesh.polygons))

            for poly in mesh.polygons:
                num_ch = len(poly.uv_channels)
                _write_uchar(fp, num_ch)

                for ch in poly.uv_channels:
                    for uv_idx in ch:          # 3 UV indices per channel
                        _write_uint(fp, uv_idx)

                for i in range(3):             # per vertex: normal then position
                    _write_uint(fp, poly.normal_idx[i])
                    _write_uint(fp, poly.vertex_idx[i])

                _write_ushort(fp, 0)           # LightMapID = 0
                _write_uint(fp, poly.mat_idx)

        # ---- Lights -------------------------------------------------------
        for light in model.lights:
            _write_vec3(fp, *light.position)
            fp.write(struct.pack('<3f', *light.colour))
            _write_float(fp, light.radius)
            _write_float(fp, light.brightness)

        # ---- Game Objects -------------------------------------------------
        for gobj in model.game_objects:
            _write_pascal_string(fp, gobj.name)
            _write_vec3(fp, *gobj.position)
            _write_matrix_row_major(fp, gobj.matrix)
