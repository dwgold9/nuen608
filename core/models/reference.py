import openmc as mc
import numpy as np

from .defaults import *
from .registry import register_model
from .materials import m, materials, generate_materials


@register_model("reference")
def build_model(config):
    p = resolve(config)

    mc.reset_auto_ids()
    model = mc.Model()
    model.parameters = p

    # ============================================================
    # Materials
    # ============================================================
    generate_materials(p)
    model.materials = materials()

    # ============================================================
    # Geometry: Global boundaries
    # ============================================================
    act_top = mc.ZPlane(z0=p['active_height'] / 2)
    act_bot = mc.ZPlane(z0=-p['active_height'] / 2)
    act_cyl = mc.ZCylinder(r=p['active_diameter'] / 2)

    refl_top = mc.ZPlane(
        z0=p['active_height'] / 2 + p['refl_thck'],
        boundary_type='vacuum'
    )
    refl_bot = mc.ZPlane(
        z0=-p['active_height'] / 2 - p['refl_thck'],
        boundary_type='vacuum'
    )
    refl_cyl = mc.ZCylinder(
        r=p['active_diameter'] / 2 + p['refl_thck'],
        boundary_type='vacuum'
    )

    # ============================================================
    # Pin cell construction
    # ============================================================
    pin_cells = []

    pin = ['fuel', 'gap', 'clad', 'cool']
    p['gap_rad'] = p['fuel_rad'] + p['gap_thck']
    p['clad_rad'] = p['gap_rad'] + p['clad_thck']

    for i in range(len(pin)):
        inn = pin[i - 1]
        out = pin[i % len(pin)]

        cyl_inn = mc.ZCylinder(r=p[f'{inn}_rad'])
        cyl_out = mc.ZCylinder(r=p[f'{out}_rad'])

        cell = mc.Cell()
        cell.fill = m(p[f'mat_{out}'])

        if i == 0:
            cell.region = (
                -cyl_out
                & +act_bot & -act_top
            )
        elif i == len(pin) - 1:
            cell.region = (
                +cyl_inn
                & +act_bot & -act_top
            )
        else:
            cell.region = (
                +cyl_inn & -cyl_out
                & +act_bot & -act_top
            )

        pin_cells.append(cell)

    pin_univ = mc.Universe(cells=pin_cells)

    # ============================================================
    # Hexagonal fuel lattice
    # ============================================================
    num_rings = 20

    def universe_ring(num_rings, universes):
        rings = []
        for i in range(num_rings):
            n = 1 if i == 0 else 6 * i
            rings.append([universes[i]] * n)
        return rings[::-1]

    # Outside lattice
    outer_cell = mc.Cell()
    outer_cell.fill = m(p['mat_refl'])
    outer_univ = mc.Universe(cells=[outer_cell])

    hex_lat = mc.HexLattice()
    hex_lat.outer = outer_univ
    hex_lat.pitch = (p['lat_pitch'],)
    hex_lat.center = (0, 0)
    hex_lat.universes = universe_ring(num_rings, [pin_univ] * num_rings)

    monolith_cell = mc.Cell()
    monolith_cell.fill = hex_lat
    monolith_cell.region = +act_bot & -act_top & -act_cyl

    # ============================================================
    # Control drums
    # ============================================================
    R_cntl = (p['active_diameter'] / 2 - p['drum_rad']) * 1
    num_drums = p['num_drums']

    cntl_cells = []
    cntl_thck = p['drum_rad'] * 0.1
    drum_rot = p['drum_rot']

    cntl_cyl = mc.ZCylinder(r=p['drum_rad'] - cntl_thck)
    drum_cyl = mc.ZCylinder(r=p['drum_rad'])

    theta_azm = 120
    cntl_azm_ccw = mc.YPlane().rotate((0, 0, theta_azm / 2))
    cntl_azm_clw = mc.YPlane().rotate((0, 0, -theta_azm / 2))

    drum_cntl_cell = mc.Cell()
    drum_cntl_cell.fill = m(p['mat_cntl'])
    drum_cntl_cell.region = (
        -drum_cyl & +cntl_cyl
        & +act_bot & -act_top
        & -cntl_azm_ccw & +cntl_azm_clw
    )

    drum_refl_cell = mc.Cell()
    drum_refl_cell.fill = m(p['mat_drum'])
    drum_refl_cell.region = -drum_cyl & ~drum_cntl_cell.region

    drum_univ = mc.Universe(cells=[drum_refl_cell, drum_cntl_cell])

    for i in range(num_drums):
        theta = i / num_drums * 2 * np.pi + 1 / num_drums * np.pi * 0
        x0 = R_cntl * np.cos(theta)
        y0 = R_cntl * np.sin(theta)

        cntl_cyl = mc.ZCylinder(r=p['drum_rad'], x0=x0, y0=y0)

        cell = mc.Cell()
        cell.fill = drum_univ
        cell.region = +act_bot & -act_top & -cntl_cyl

        cell.id = (i + 1) * 100
        cell.translation = (x0, y0, 0)
        cell.rotation = (0, 0, theta / np.pi * 180 + drum_rot)

        cntl_cells.append(cell)

    cntl_region = mc.Union([c.region for c in cntl_cells])
    active_region = +act_bot & -act_top & -act_cyl

    monolith_cell.region = monolith_cell.region & ~cntl_region

    refl_cell = mc.Cell()
    refl_cell.fill = m(p['mat_refl'])
    refl_cell.region = (
        +refl_bot & -refl_top & -refl_cyl
        & ~active_region
    )

    root_univ = mc.Universe(
        cells=[refl_cell, monolith_cell, *cntl_cells]
    )

    model.geometry = mc.Geometry(root=root_univ)

    # ============================================================
    # Settings
    # ============================================================
    src_init = mc.IndependentSource()
    src_init.space = mc.stats.Point([0, 0, 0])

    settings = mc.Settings()
    settings.particles = p['particles']
    settings.batches = p['batches']
    settings.inactive = p['inactive']
    settings.seed = p['seed']
    settings.run_mode = 'eigenvalue'
    settings.source = [src_init]
    settings.verbosity = 7

    model.settings = settings

    return model