from pathlib import Path
from core.analysis import Scope
from core.analysis.base import AnalysisBlock


ARTIFACTS_REGISTRY = {}


class Artifact(AnalysisBlock):

    """
    Base class for all artifacts.

    Artifacts consume measurements and produce files
    (plots, NetCDF outputs, reports, etc.).

    They do NOT write to metric.yaml.
    """

    def _generate(self, context):
        """
        Subclasses must implement this.

        Should produce files inside context.path.
        """
        raise NotImplementedError

    def _execute(self, context):
        """
        Unified execution entrypoint.
        """
        return self._generate(context)


def register_artifact(type_name):
    """
    Decorator used by artifacts to register themselves.
    """

    def decorator(cls):
        if type_name in ARTIFACTS_REGISTRY:
            raise ValueError(
                f"Artifact '{type_name}' already registered."
            )

        cls.type_name = type_name
        ARTIFACTS_REGISTRY[type_name] = cls
        return cls

    return decorator


def get_artifact_blocks(entries):

    blocks = []

    for entry in entries:

        # ----------------------------------
        # Case 1: string
        # ----------------------------------
        if isinstance(entry, str):

            type_name = entry
            instance_cfgs = [("", None)]

        # ----------------------------------
        # Case 2: dict
        # ----------------------------------
        elif isinstance(entry, dict):

            if len(entry) != 1:
                raise ValueError(
                    f"Artifact entry must have single key: {entry}"
                )

            type_name, nested = next(iter(entry.items()))

            # ----------------------------------
            # Case 2a: None
            # ----------------------------------
            if nested is None:
                instance_cfgs = [("", None)]

            # ----------------------------------
            # Case 2b: list → simple instances
            # ----------------------------------
            elif isinstance(nested, list):
                instance_cfgs = [(name, None) for name in nested]

            # ----------------------------------
            # Case 2c: dict → base + instances
            # ----------------------------------
            elif isinstance(nested, dict):

                # Split ONLY top-level keys
                if all(isinstance(v, dict) for v in nested.values()):
                    # ALL are instances
                    instance_entries = nested
                    base_cfg = {}
                else:
                    # treat entire dict as config
                    instance_entries = {}
                    base_cfg = nested

                base_cfg = {
                    k: v for k, v in nested.items()
                    if not isinstance(v, dict)
                }

                # ----------------------------------
                # Instances exist → merge base + instance
                # ----------------------------------
                if instance_entries:

                    instance_cfgs = []

                    for name, inst_cfg in instance_entries.items():

                        if inst_cfg is not None and not isinstance(inst_cfg, dict):
                            raise TypeError(
                                f"Instance '{name}' must be dict or None"
                            )

                        merged = {}

                        # base config
                        if base_cfg:
                            merged.update(base_cfg)

                        # instance overrides
                        if inst_cfg:
                            merged.update(inst_cfg)

                        instance_cfgs.append((name, merged))

                # ----------------------------------
                # No instances → pure config
                # ----------------------------------
                else:
                    instance_cfgs = [("", nested)]

            else:
                raise TypeError(
                    f"Invalid artifact config for '{type_name}'"
                )

        else:
            raise TypeError(
                f"Invalid artifact entry: {entry}"
            )

        # ----------------------------------
        # Instantiate blocks
        # ----------------------------------
        if type_name not in ARTIFACTS_REGISTRY:
            available = ", ".join(ARTIFACTS_REGISTRY)
            raise ValueError(
                f"Unknown artifact '{type_name}'. "
                f"Available: {available}"
            )

        artifact_cls = ARTIFACTS_REGISTRY[type_name]

        for instance_name, cfg in instance_cfgs:
            block = artifact_cls()
            block.set_name(instance_name)
            block.merge_config(cfg)
            blocks.append(block)

    return blocks