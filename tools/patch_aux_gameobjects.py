"""
Patches a StreetRod3 .aux file with the required $-named game objects.
Computes positions from the model bounding box.

Usage:
    python patch_aux_gameobjects.py <path_to_car.aux>
"""

import struct, sys, os

# -------------------------------------------------------------------------
# Binary helpers
# -------------------------------------------------------------------------

def read_uint(data, offset):
    return struct.unpack_from('<I', data, offset)[0], offset + 4

def read_float(data, offset):
    return struct.unpack_from('<f', data, offset)[0], offset + 4

def read_pascal_string(data, offset):
    length = data[offset]
    s = data[offset+1 : offset+1+length].decode('ascii', errors='replace')
    return s, offset + 1 + length

def write_uint(value):
    return struct.pack('<I', value)

def write_float(value):
    return struct.pack('<f', value)

def write_pascal_string(s):
    enc = s.encode('ascii', errors='replace')[:255]
    return bytes([len(enc)]) + enc

def write_vec3(x, y, z):
    return struct.pack('<3f', x, y, z)

def write_identity_matrix():
    # 3x3 identity in row-major
    return struct.pack('<9f', 1,0,0, 0,1,0, 0,0,1)

def write_game_object(name, x, y, z):
    return write_pascal_string(name) + write_vec3(x, y, z) + write_identity_matrix()

# -------------------------------------------------------------------------
# Parse header
# -------------------------------------------------------------------------
SIG = b'Auxiliary 3D\x1A\x08\x04'
HDR_SIG_LEN      = 15
HDR_VERSION_OFF  = 15  # int32
HDR_NMAT_OFF     = 19  # uint32
HDR_NMESH_OFF    = 23  # uint32
HDR_NLIGHT_OFF   = 27  # uint32
HDR_NGOBJ_OFF    = 31  # uint32  ← we patch this
HDR_NVERTS_OFF   = 35  # uint32
HDR_NUVS_OFF     = 39  # uint32
HDR_NNORMS_OFF   = 43  # uint32
HDR_DATA_START   = 47

def parse_header(data):
    assert data[:HDR_SIG_LEN] == SIG, "Bad signature"
    version, _ = read_uint(data, HDR_VERSION_OFF)
    assert version == 1, f"Unexpected version {version}"
    num_mat,   _ = read_uint(data, HDR_NMAT_OFF)
    num_mesh,  _ = read_uint(data, HDR_NMESH_OFF)
    num_light, _ = read_uint(data, HDR_NLIGHT_OFF)
    num_gobj,  _ = read_uint(data, HDR_NGOBJ_OFF)
    num_verts, _ = read_uint(data, HDR_NVERTS_OFF)
    num_uvs,   _ = read_uint(data, HDR_NUVS_OFF)
    num_norms, _ = read_uint(data, HDR_NNORMS_OFF)
    return dict(num_mat=num_mat, num_mesh=num_mesh, num_light=num_light,
                num_gobj=num_gobj, num_verts=num_verts, num_uvs=num_uvs,
                num_norms=num_norms)

# -------------------------------------------------------------------------
# Read vertices and compute bounding box
# -------------------------------------------------------------------------

def bounding_box(data, num_verts):
    offset = HDR_DATA_START
    mn = [float('inf')] * 3
    mx = [float('-inf')] * 3
    for _ in range(num_verts):
        x, offset = read_float(data, offset)
        y, offset = read_float(data, offset)
        z, offset = read_float(data, offset)
        for i, v in enumerate((x, y, z)):
            if v < mn[i]: mn[i] = v
            if v > mx[i]: mx[i] = v
    return mn, mx

# -------------------------------------------------------------------------
# Estimate game object positions from bounding box
#
# Game coordinate system (after Blender export):
#   X = left(-) / right(+)
#   Y = up (vertical)
#   Z = back(-) / front(+)
#
# Car is centred on X=0.  Wheels are near the bottom (low Y).
# The seat600 is rear-engine but for game purposes $block goes at the engine bay.
# -------------------------------------------------------------------------

def estimate_anchors(mn, mx):
    cx = (mn[0] + mx[0]) / 2  # centre X (should be ~0)
    cy = (mn[1] + mx[1]) / 2  # centre Y
    cz = (mn[2] + mx[2]) / 2  # centre Z

    half_x = (mx[0] - mn[0]) * 0.38   # inset wheels slightly from edge
    front_z = mx[2] * 0.62             # ~62% toward front from centre
    back_z  = mn[2] * 0.62             # ~62% toward rear
    wheel_y = mn[1] + (mx[1] - mn[1]) * 0.12   # ~12% up from bottom
    shock_y = mn[1] + (mx[1] - mn[1]) * 0.30   # ~30% up
    mid_y   = mn[1] + (mx[1] - mn[1]) * 0.40   # mid-height for mechanicals

    anchors = [
        # Wheels
        ("$flwheel",  half_x, wheel_y,  front_z),
        ("$frwheel", -half_x, wheel_y,  front_z),
        ("$brwheel", -half_x, wheel_y,  back_z),
        ("$blwheel",  half_x, wheel_y,  back_z),
        # Shocks
        ("$flshock",  half_x, shock_y,  front_z),
        ("$frshock", -half_x, shock_y,  front_z),
        ("$brshock", -half_x, shock_y,  back_z),
        ("$blshock",  half_x, shock_y,  back_z),
        # Exhaust
        ("$lmuffler",  half_x * 0.6, wheel_y,  back_z * 0.7),
        ("$rmuffler", -half_x * 0.6, wheel_y,  back_z * 0.7),
        # Drivetrain  (seat600 is rear-engine → engine near rear)
        ("$block",  cx, mid_y,  back_z * 0.5),
        ("$diff",   cx, wheel_y, back_z * 0.8),
        ("$trans",  cx, mid_y,   back_z * 0.6),
        # Cockpit camera
        ("$incar_cam", cx, mn[1] + (mx[1] - mn[1]) * 0.75, cz * 0.3),
    ]
    return anchors

# -------------------------------------------------------------------------
# Main
# -------------------------------------------------------------------------

def patch(aux_path):
    with open(aux_path, 'rb') as f:
        data = bytearray(f.read())

    hdr = parse_header(data)
    print(f"Header: {hdr}")

    mn, mx = bounding_box(data, hdr['num_verts'])
    print(f"Bounding box: min={[round(v,3) for v in mn]}  max={[round(v,3) for v in mx]}")

    anchors = estimate_anchors(mn, mx)
    print(f"\nAdding {len(anchors)} game objects:")
    for name, x, y, z in anchors:
        print(f"  {name:15s}  ({x:6.3f}, {y:6.3f}, {z:6.3f})")

    # Append game objects at end of file
    extra = b''
    for name, x, y, z in anchors:
        extra += write_game_object(name, x, y, z)

    # Update NumGameObjects in header
    data[HDR_NGOBJ_OFF:HDR_NGOBJ_OFF+4] = write_uint(len(anchors))

    # Append
    data += extra

    # Write back
    backup = aux_path + '.bak'
    os.rename(aux_path, backup)
    with open(aux_path, 'wb') as f:
        f.write(data)

    print(f"\nDone. Original saved as {backup}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python patch_aux_gameobjects.py <car.aux>")
        sys.exit(1)
    patch(sys.argv[1])
