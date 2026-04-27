import openmc as mc
from materials_compendium import MaterialsCompendium
from materials_compendium.utils import Material
import pyromat as pm


pm.config['unit_temperature'] = 'K'
pm.config['unit_pressure'] = 'MPa'
pm.config['unit_mass'] = 'g'
pm.config['unit_matter'] = 'g'
pm.config['unit_volume'] = 'cc'

def pm_density(species, T, p):
    return pm.get(f'ig.{species}').d(T=T, p=p)[0]


library = mc.data.DataLibrary.from_xml()


def mc_material_from_compendium(name, register_name):
    mat = Material.from_name(name)

    material = mc.Material()
    material.name = register_name
    material.set_density('g/cc', mat.density)

    for element in mat.elements:
        for nuclide in element.isotopes:
            if library.get_by_material(nuclide.isotope):
                material.add_nuclide(nuclide.isotope, nuclide.atom_fraction, 'ao')

    return material


MATERIALS = {
    'None': None
}

def materials():
    return [value for value in MATERIALS.values() if value != None]

def m(name):
    if name not in MATERIALS:
        raise ValueError(f"{name} not in available materials")
    return MATERIALS[name]

def register_material(material):
    key = material.name
    MATERIALS[key] = material

# - materials
# ===============================================================
def generate_materials(params):
    p = params

    d2o = mc.Material(name='d2o')
    d2o.set_density('g/cc', 1.0)
    d2o.add_nuclide('H2', 2.0)
    d2o.add_nuclide('O16', 1.0)
    register_material(d2o)


    water = mc_material_from_compendium(
        "Water, Liquid", "water")
    register_material(water)


    h2 = mc.Material(name='h2')
    h2.set_density('g/cc', 
                   pm_density('H2', 
                              T=p['cool_temp'],
                              p=p['cool_pres'])
    )
    h2.add_element('H', 2.0)
    register_material(h2)


    molten_salt = mc.Material(name='molten-salt')
    molten_salt.set_density('g/cc', 1.94)
    molten_salt.add_element('Na', 1.0)
    molten_salt.add_element('Cl', 1.0)
    register_material(molten_salt)


    gas = mc.Material(name='gas')
    gas.set_density('g/cc', 1.0e-3)
    gas.add_element('He', 1.0)
    register_material(gas)


    beo = mc.Material(name='beo')
    beo.set_density('g/cc', 3.02)
    beo.add_nuclide('Be9', 1.0)
    beo.add_nuclide('O16', 1.0)
    register_material(beo)


    b4c = mc.Material(name='b4c')
    b4c.set_density('g/cc', 3.02)
    b4c.add_element('B', 4.0)
    b4c.add_element('C', 1.0)
    register_material(b4c)


    lead = mc.Material(name='lead')
    lead.set_density('g/cc', 10.0)
    lead.add_element('Pb', 1.0)
    register_material(lead)


    zirc = mc.Material(name='zircaloy')
    zirc.set_density('g/cc', 6.55)
    zirc.add_element('Zr', 1.0)
    register_material(zirc)


    americium = mc.Material(name='americium')
    americium.set_density('g/cc', 13.6)
    americium.add_nuclide('Am241', 1.0)
    register_material(americium)


    cadmium = mc.Material(name='cadmium')
    cadmium.set_density('g/cc', 8.65)
    cadmium.add_element('Cd', 1.0)
    register_material(cadmium)


    ura_dio = mc.Material(name='ura-dio')
    ura_dio.set_density('g/cc', 10.2)
    ura_dio.add_element('U', 1.0, enrichment=p['fuel_enrich'])
    ura_dio.add_nuclide('O16', 2.0)
    register_material(ura_dio)


    fuel_mox = mc.Material(name='fuel-mox')
    fuel_mox.set_density('g/cc', 10.0)
    fuel_mox.add_nuclide('U238', 0.57)
    fuel_mox.add_nuclide('Pu239', 0.43)
    register_material(fuel_mox)


    lithium = mc.Material(name='lithium')
    lithium.set_density('g/cc', 0.5)
    lithium.add_element('Li', 1.0)
    register_material(lithium)
