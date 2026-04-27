import openmc as mc
import numpy as np
import xarray as xr
from core.utils.energy_bins import resolve_energy_bins
from .registry import register_tally, MeshTally


@register_tally("openmc-tally")
class ConfigurableOpenMCTally(MeshTally):

    name = "openmc-tally"

    default_config = {
        "score": "flux",
        "filters": []
    }

    @property
    def mesh_metadata(self):

        if not hasattr(self, "_mesh"):
            return None

        mesh = self._mesh

        # -------------------------
        # Rectilinear
        # -------------------------
        if isinstance(mesh, mc.RectilinearMesh):

            return {
                "type": "rectilinear",
                "dims": ["x", "y", "z"],
                "edges": {
                    "x": list(mesh.x_grid),
                    "y": list(mesh.y_grid),
                    "z": list(mesh.z_grid),
                },
            }

        # -------------------------
        # Cylindrical
        # -------------------------
        elif isinstance(mesh, mc.CylindricalMesh):

            return {
                "type": "cylindrical",
                "dims": ["r", "phi", "z"],
                "edges": {
                    "r": list(mesh.r_grid),
                    "phi": list(mesh.phi_grid),
                    "z": list(mesh.z_grid),
                },
                "origin": list(mesh.origin),
            }

        # -------------------------
        # Spherical
        # -------------------------
        elif isinstance(mesh, mc.SphericalMesh):

            return {
                "type": "spherical",
                "dims": ["r", "theta", "phi"],
                "edges": {
                    "r": list(mesh.r_grid),
                    "theta": list(mesh.theta_grid),
                    "phi": list(mesh.phi_grid),
                },
                "origin": list(mesh.origin),
            }

        return None

    def build(self):

        cfg = self.cfg

        score = cfg["score"]
        filter_configs = cfg.get("filters", [])

        filters = []


        for f in filter_configs:
            ftype, fcfg = next(iter(f)), f[next(iter(f))]

            if ftype == "energy":
                bins = fcfg["bins"]
                bins = resolve_energy_bins(
                    bins)
                
                filters.append(mc.EnergyFilter(bins))

            elif ftype == "cell":
                filters.append(mc.CellFilter(fcfg["bins"]))

            elif ftype == "material":
                filters.append(mc.MaterialFilter(fcfg["bins"]))

            elif ftype == "particle":
                filters.append(mc.ParticleFilter(fcfg["bins"]))

            elif ftype == "mesh":

                mesh_cfg = fcfg
                mesh_type = mesh_cfg.get("type", "rectilinear")

                if mesh_type == "rectilinear":

                    mesh = mc.RectilinearMesh()

                    mesh.x_grid = np.linspace(
                        mesh_cfg["lower_left"][0],
                        mesh_cfg["upper_right"][0],
                        mesh_cfg["dimension"][0] + 1,
                    )

                    mesh.y_grid = np.linspace(
                        mesh_cfg["lower_left"][1],
                        mesh_cfg["upper_right"][1],
                        mesh_cfg["dimension"][1] + 1,
                    )

                    mesh.z_grid = np.linspace(
                        mesh_cfg["lower_left"][2],
                        mesh_cfg["upper_right"][2],
                        mesh_cfg["dimension"][2] + 1,
                    )

                elif mesh_type == "cylindrical":

                    mesh = mc.CylindricalMesh(
                        r_grid=np.linspace(
                            mesh_cfg["r_min"],
                            mesh_cfg["r_max"],
                            mesh_cfg["nr"] + 1,
                        ),
                        z_grid=np.linspace(
                            mesh_cfg["z_min"],
                            mesh_cfg["z_max"],
                            mesh_cfg["nz"] + 1,
                        ),
                        phi_grid=np.linspace(
                            mesh_cfg.get("phi_min", 0.0),
                            mesh_cfg.get("phi_max", 2 * np.pi),
                            mesh_cfg.get("nphi", 1) + 1,
                        ),
                        origin=mesh_cfg.get("origin", (0.0, 0.0, 0.0)),
                    )

                elif mesh_type == "spherical":

                    mesh = mc.SphericalMesh(
                        r_grid=np.linspace(
                            mesh_cfg["r_min"],
                            mesh_cfg["r_max"],
                            mesh_cfg["nr"] + 1,
                        ),
                        theta_grid=np.linspace(
                            mesh_cfg.get("theta_min", 0.0),
                            mesh_cfg.get("theta_max", np.pi),
                            mesh_cfg["ntheta"] + 1,
                        ),
                        phi_grid=np.linspace(
                            mesh_cfg.get("phi_min", 0.0),
                            mesh_cfg.get("phi_max", 2 * np.pi),
                            mesh_cfg["nphi"] + 1,
                        ),
                        origin=mesh_cfg.get("origin", (0.0, 0.0, 0.0)),
                    )

                else:
                    raise ValueError(f"Unsupported mesh type: {mesh_type}")

                self._mesh = mesh

                filters.append(mc.MeshFilter(mesh))

            else:
                raise ValueError(f"Unsupported filter type: {ftype}")

        tally = mc.Tally(name=self.name)
        tally.scores = [score]
        tally.filters = filters

        return [tally]


    def _extract(self, statepoint):

        tally = statepoint.get_tally(name=self.name)
        ds = self._to_xarray(tally)
        return ds


    def _to_xarray(self, tally):

        if len(tally.scores) != 1:
            raise ValueError("Multiple scores not supported")

        if len(tally.nuclides) != 1:
            raise ValueError("Multiple nuclides not supported")

        mean = tally.mean[:, 0, 0]
        std = tally.std_dev[:, 0, 0]

        dims = []
        coords = {}
        shape = []

        for f in tally.filters:

            if isinstance(f, mc.EnergyFilter):

                dims.append("energy")
                shape.append(f.num_bins)

                edges = np.array(f.bins)
                coords["energy"] = 0.5 * (edges[:, 0] + edges[:, 1])

                coords["energy_low"]  = ("energy", edges[:, 0])
                coords["energy_high"] = ("energy", edges[:, 1])

            elif isinstance(f, mc.MeshFilter):

                mesh = f.mesh

                if isinstance(mesh, mc.RectilinearMesh):

                    nx, ny, nz = mesh.dimension

                    dims.extend(["x", "y", "z"])
                    shape.extend([nx, ny, nz])

                    x_edges = mesh.x_grid
                    coords["x"] = 0.5 * (x_edges[:-1] + x_edges[1:])

                    y_edges = mesh.y_grid
                    coords["y"] = 0.5 * (y_edges[:-1] + y_edges[1:])

                    z_edges = mesh.z_grid
                    coords["z"] = 0.5 * (z_edges[:-1] + z_edges[1:])

                elif isinstance(mesh, mc.CylindricalMesh):

                    nr, nphi, nz = mesh.dimension

                    dims.extend(["r", "phi", "z"])
                    shape.extend([nr, nphi, nz])

                    r_edges = mesh.r_grid
                    coords["r"] = 0.5 * (r_edges[:-1] + r_edges[1:])

                    phi_edges = mesh.phi_grid
                    coords["phi"] = 0.5 * (phi_edges[:-1] + phi_edges[1:])

                    z_edges = mesh.z_grid
                    coords["z"] = 0.5 * (z_edges[:-1] + z_edges[1:])

                elif isinstance(mesh, mc.SphericalMesh):

                    nr, ntheta, nphi = mesh.dimension

                    dims.extend(["r", "theta", "phi"])
                    shape.extend([nr, ntheta, nphi])

                    r_edges = mesh.r_grid
                    coords["r"] = 0.5 * (r_edges[:-1] + r_edges[1:])

                    theta_edges = mesh.theta_grid
                    coords["theta"] = 0.5 * (theta_edges[:-1] + theta_edges[1:])

                    phi_edges = mesh.phi_grid
                    coords["phi"] = 0.5 * (phi_edges[:-1] + phi_edges[1:])

                else:
                    raise ValueError(f"Unsupported mesh class: {type(mesh)}")

            else:

                name = type(f).__name__.replace("Filter", "").lower()
                dims.append(name)
                shape.append(f.num_bins)
                coords[name] = np.array(f.bins)

        values = mean.reshape(shape)
        std_values = std.reshape(shape)

        ds = xr.Dataset(
            {
                "mean": (dims, values),
                "std_dev": (dims, std_values),
            },
            coords=coords,
        )

        return ds