"""
3D RAC advantage-space figure (n=3) rendered with PyVista.

  * Quantum boundary  : unit sphere  c0^2 + c1^2 + c2^2 = 1
  * Classical polytope: cuboctahedron with 14 vertices
        - 6 axis points (+-1,0,0) etc.  -> lie ON the sphere
        - 8 cube corners (+-1/2,...)    -> lie INSIDE, at radius sqrt(3)/2
  * majority strategy : the cube corner (1/2,1/2,1/2), win rate 0.75 each index
  * quantum-in-(1,1,1): (1/sqrt3)(1,1,1), win rate ~0.789  -> strictly beyond majority

Renders ONE image to OUT_PATH using the CAMERA / LIGHTING settings below.

Headless note: if running without a display, start a virtual one first, e.g.
    Xvfb :99 -screen 0 1024x768x24 &   then   DISPLAY=:99 python rac_polytope_pyvista.py
"""
import numpy as np
import pyvista as pv
from scipy.spatial import ConvexHull

# =====================================================================
#  TUNABLE SETTINGS  --  edit these
# =====================================================================
OUT_PATH   = "rac_polytope.png"
IMG_SIZE   = (1400, 1400)          # output resolution (px)

# ---- camera ----
CAM_AZIMUTH   = 20.0               # horizontal orbit angle (deg)
CAM_ELEVATION = 10.0               # vertical angle (deg)
CAM_ROLL      = 0.0                # roll about view axis (deg)
CAM_ZOOM      = 1.15               # >1 zooms in
CAM_PARALLEL  = True               # True = orthographic (sphere outline is a true circle)

# ---- lighting ----
LIGHT_AZIMUTH   = 40.0             # light direction, horizontal (deg)
LIGHT_ELEVATION = 55.0             # light direction, vertical (deg)
LIGHT_INTENSITY = 0.9
AMBIENT         = 0.15             # base fill so shadowed faces aren't black
SPECULAR        = 0.15             # highlight strength on the polytope
BACKGROUND      = "white"

# ---- colours ----
C_SPHERE   = "#F5C543"             # quantum sphere / circle (yellow)
C_GREATCIRCLE = "#8A7B26"             # great circle (dark yellow)
C_POLY     = "#3D7EC4"             # classical polytope (blue)
C_EDGE     = "white"              # polytope edges
C_AXIS     = "#1A1A1A"             # axes / ink
C_MAJORITY = "#E05B49"             # majority point (red)
C_QUANTUM  = "#B8901E"             # quantum-in-(1,1,1) point (gold)

SPHERE_STYLE = "surface"         # "wireframe" | "surface" | "silhouette"
SPHERE_OPACITY = 0.25              # used when SPHERE_STYLE == "surface"

SHOW_MAJORITY = True
SHOW_QUANTUM  = True
SHOW_GREAT_CIRCLE = True           # great circle in the c0 = 0 plane
AXIS_LEN = 1.5                     # how far axes extend past the sphere

ADD_TEXT = False
# =====================================================================


def build_polytope():
    axis_v = [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]
    cube_v = [(sx*0.5, sy*0.5, sz*0.5)
              for sx in (1,-1) for sy in (1,-1) for sz in (1,-1)]
    V = np.array(axis_v + cube_v, float)
    hull = ConvexHull(V)
    faces = []
    for s in hull.simplices:
        faces.append([3, *s])
    poly = pv.PolyData(V, np.hstack(faces))
    return poly, np.array(axis_v, float)


def light_direction(az_deg, el_deg):
    az, el = np.radians(az_deg), np.radians(el_deg)
    return np.array([np.cos(el)*np.cos(az),
                     np.cos(el)*np.sin(az),
                     np.sin(el)])


def main():
    poly, axis_pts = build_polytope()

    p = pv.Plotter(off_screen=True, window_size=list(IMG_SIZE))
    p.set_background(BACKGROUND)

    # --- classical polytope: solid shaded faces + edges ---
    # --- real rhombic-dodecahedron edges: axis <-> cube, built explicitly ---
    def rd_edges(V):
        axis_idx = [i for i,v in enumerate(V) if abs(np.linalg.norm(v)-1) < 1e-6]
        cube_idx = [i for i,v in enumerate(V) if abs(np.linalg.norm(v)-1) > 1e-6]
        lines = []
        for a in axis_idx:
            for c in cube_idx:
                # rhombus edge: cube corner touches the 3 axis faces whose axis
                # shares its sign; edge exists when they are adjacent on the hull
                if abs(np.dot(V[a], V[c]) - 0.5) < 1e-6:   # axis·cube = 1/2
                    lines.append([2, a, c])
        return np.hstack(lines)

    edge_mesh = pv.PolyData(poly.points, lines=rd_edges(poly.points))

    p.add_mesh(poly, color=C_POLY, opacity=1.0, show_edges=False,
               ambient=AMBIENT, diffuse=0.9, specular=SPECULAR,
               specular_power=15, smooth_shading=False)
    p.add_mesh(edge_mesh, color=C_EDGE, line_width=2)

    # --- quantum sphere ---
    sph = pv.Sphere(radius=1.0, theta_resolution=60, phi_resolution=60)
    if SPHERE_STYLE == "surface":
        p.add_mesh(sph, color=C_SPHERE, opacity=SPHERE_OPACITY, specular=0.2)
    elif SPHERE_STYLE == "wireframe":
        p.add_mesh(sph, color=C_SPHERE, style="wireframe",
                   line_width=1.0, opacity=SPHERE_OPACITY)
    elif SPHERE_STYLE == "silhouette":
        p.add_silhouette(sph, color=C_SPHERE, line_width=3)

    # --- great circle in the c0 = 0 plane ---
    if SHOW_GREAT_CIRCLE:
        t = np.linspace(0, 2*np.pi, 200)
        gc = np.column_stack([np.zeros_like(t), np.cos(t), np.sin(t)])
        p.add_mesh(pv.lines_from_points(gc), color=C_GREATCIRCLE,
                   line_width=4, opacity=0.7)

        gc = np.column_stack([np.cos(t), np.sin(t), np.zeros_like(t)])
        p.add_mesh(pv.lines_from_points(gc), color=C_GREATCIRCLE,
                           line_width=4, opacity=0.7)

        gc = np.column_stack([np.cos(t), np.zeros_like(t), np.sin(t)])
        p.add_mesh(pv.lines_from_points(gc), color=C_GREATCIRCLE,
                           line_width=4, opacity=0.7)

        amplitude = 1/np.sqrt(3)

        gc = np.column_stack([np.sqrt(2)*amplitude*np.cos(t), amplitude*np.ones_like(t), np.sqrt(2)*amplitude*np.sin(t)])
        p.add_mesh(pv.lines_from_points(gc), color=C_GREATCIRCLE,
                           line_width=2, opacity=0.7)

        gc = np.column_stack([np.sqrt(2)*amplitude*np.cos(t), -1*amplitude*np.ones_like(t), np.sqrt(2)*amplitude*np.sin(t)])
        p.add_mesh(pv.lines_from_points(gc), color=C_GREATCIRCLE,
                           line_width=2, opacity=0.7)       

        gc = np.column_stack([np.sqrt(1/2)*np.cos(t), np.sin(t), np.sqrt(1/2)*np.cos(t)])
        p.add_mesh(pv.lines_from_points(gc), color=C_GREATCIRCLE,
                           line_width=2, opacity=0.7)

        gc = np.column_stack([np.sqrt(1/2)*np.cos(t), np.sin(t), -1*np.sqrt(1/2)*np.cos(t)])
        p.add_mesh(pv.lines_from_points(gc), color=C_GREATCIRCLE,
                           line_width=2, opacity=0.7)

    # --- axes through origin, extended beyond the sphere ---
    for u, lab in [((1,0,0), "index_0"), ((0,1,0), "index_1"), ((0,0,1), "index_2")]:
        u = np.array(u, float)
        line = pv.Line(-AXIS_LEN*u, AXIS_LEN*u)
        p.add_mesh(line, color=C_AXIS, line_width=3)
        p.add_point_labels([1.6*u], [lab], font_size=28,
                           text_color=C_AXIS, shape=None,
                           show_points=False, always_visible=True)

    diagonal = pv.Line(np.array((0,0,0), float), AXIS_LEN*np.array((1,1,1), float))
    p.add_mesh(diagonal, color=C_AXIS, line_width=3)
    p.add_point_labels([1.6*np.array((1,1,1), float)], ['(1,1,1) Diagnonal'], font_size=28,
                               text_color=C_AXIS, shape=None,
                               show_points=False, always_visible=True)
    # --- key points ---
    p.add_mesh(pv.PolyData(axis_pts), color=C_AXIS,
               point_size=12, render_points_as_spheres=True)
    if SHOW_MAJORITY:
        p.add_mesh(pv.PolyData(np.array([[0.5,0.5,0.5]])), color=C_MAJORITY,
                   point_size=22, render_points_as_spheres=True)
        if ADD_TEXT:
            p.add_point_labels([[0.5,0.5,0.62]], ["majority"], font_size=24,
                            text_color=C_MAJORITY, shape=None,
                            show_points=False, always_visible=True)
    if SHOW_QUANTUM:
        q = 1/np.sqrt(3)
        p.add_mesh(pv.PolyData(np.array([[q,q,q]])), color=C_QUANTUM,
                   point_size=18, render_points_as_spheres=True)
        if ADD_TEXT:
            p.add_point_labels([[q,q,q+0.15]], ["quantum"], font_size=24,
                            text_color=C_QUANTUM, shape=None,
                            show_points=False, always_visible=True)

    # --- lighting ---
    p.remove_all_lights()
    Ld = light_direction(LIGHT_AZIMUTH, LIGHT_ELEVATION)
    key = pv.Light(position=tuple(Ld*5), focal_point=(0,0,0),
                   intensity=LIGHT_INTENSITY, light_type='scene light')
    p.add_light(key)
    fill = pv.Light(position=tuple(-Ld*5 + np.array([0,0,2])),
                    focal_point=(0,0,0), intensity=0.3,
                    light_type='scene light')
    p.add_light(fill)

    # --- camera ---
    if CAM_PARALLEL:
        p.enable_parallel_projection()
    p.camera_position = 'xy'
    p.camera.azimuth = CAM_AZIMUTH
    p.camera.elevation = CAM_ELEVATION
    p.camera.roll += CAM_ROLL
    p.camera.zoom(CAM_ZOOM)

    p.screenshot(OUT_PATH)
    p.close()
    print("saved", OUT_PATH)


if __name__ == "__main__":
    main()