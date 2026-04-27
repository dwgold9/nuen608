

DEFAULTS = {
    'active_height': 200,
    'active_diameter': 225,
    'cool_temp': 1000,        # Coolant Temperature (K)
    'cool_pres': 7,           # Coolant Pressure (MPa)
    'refl_thck': 20,
    'fuel_enrich': 19.75,
    'lat_pitch': 4.5,
    'fuel_rad': 1.5,
    'gap_thck': 0.01,
    'clad_thck': 0.2,
    'cool_rad': 10,
    'mat_fuel': 'ura-dio',
    'mat_gap': 'gas',
    'mat_clad': 'zircaloy',
    'mat_cool': 'h2',
    'mat_cntl': 'b4c',
    'mat_refl': 'lead',
    'mat_drum': 'beo',
    'drum_rad': 10,
    'drum_rot': 180,
    'num_drums': 6,
    'seed': 1,
    'batches': 100,
    'inactive': 30,
    'particles': 1000,
}

def resolve(config, model_default={}):
    if config is None:
        config = {}
    return {**DEFAULTS, **model_default, **config}

