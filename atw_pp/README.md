# atomworks plug-and-play

A small, **role + plugin** based metadata builder for large-scale structural datasets.
It parses CIFs, builds **chains** and flexible **roles** (e.g. antigen / vh / vl / antibody / helper), runs **plugins**, and writes:

- `structures_metadata.parquet`
- `chains_metadata.parquet`
- `roles_metadata.parquet`
- `interfaces_metadata.parquet`
- `all_metadata.parquet` (wide/pivoted aggregation for easy ranking/filtering)
- `bad_files.csv`

Designed for stable schema, configurable role selection, and “drop-in” plugins.

---
## Key ideas

### Roles (the core abstraction)
The define *roles* as chain-id sets:

- `antigen = A + D` (multi-chain antigen)
- `binder = B`
- `antibody = H + L`
- `helper = X`

Plugins operate on `ctx.roles` (merged AtomArrays), so the same plugin works across:

- multi-chain antigens
- multi-binder systems

### Plugin system
A plugin is `ctx -> rows`. Plugins:
- read from `Context` (`aa`, `chains`, `roles`, `cfg`, `params`)
- emit rows to one of four tables: `structures / chains / roles / interfaces`
- automatically get column namespaced via `prefix__...`

---

## Package layout

```

atw_pp/
__init__.py
config.py
cli.py
run.py

io/
cif.py
params.py
paragraph.py

core/
annotations.py
epitope.py
selection.py
contacts.py

plugins/
base.py
identity.py
chain_continuity.py
paragraph_paratope.py
interface_contacts.py

tables/
wide.py

````

---

## Installation

This package is intended to be run inside an environment that already has:

- `atomworks`
- `biotite`
- `numpy`
- `pandas`
- `scipy` (for `cKDTree`)
- `pyarrow` (recommended for parquet)

```bash
conda create -n atw_pp python=3.12
conda activate atw_pp

# cd correct atw_pp folder
python3 -m pip install --user -U pip setuptools wheel

python3 -m pip install -e ".[ml]"

# sometimes atomworks not installed
python -m pip install "atomworks[ml]"

# atomworks: https://github.com/RosettaCommons/atomworks
````

---

## Input expectations

### CIFs

Provide a directory containing `.cif` files (recursively discovered).

### Optional: params CSV

One or more CSVs with a required `path` column (absolute path to CIF), plus any additional columns.
These will be attached to every emitted row as `param__<colname>` by default.

### Optional: Paragraph predictions CSV

You can run paragraph to obtain csv with header:

Required columns:

* `pdb` (defaults to `Path(cif).stem`)
* `chain_id`
* `IMGT`
* `pred`
* `x, y, z`

If you prefer strict matching by absolute file path, add a `path` column and run with `--paragraph_id_mode path`.

---

## Quick start

### 1) Default (A/B/C: antigen/vh/vl)

```bash
python -m atw_pp.cli \
  --cif_dir /data/cifs \
  --out_dir out_default
```

### 2) VHH-only (H chain) + paragraph paratope

```bash
python -m atw_pp.cli \
  --cif_dir /data/vhh_cifs \
  --out_dir out_vhh \
  --vh_chains H \
  --antigen_chains \
  --paragraph_preds /data/paragraph_predictions.csv \
  --plugins identity chain_continuity paragraph_paratope
```

Expected outputs:

* chain-level paratope summaries into `chains_metadata.parquet`
* role-level paratope summaries into `roles_metadata.parquet` (for roles in `cfg.role_paratope_summaries`)

### 3) Multi-chain antigen (A+D) + Fab (H+L) + multiple interface pairs

```bash
python -m atw_pp.cli \
  --cif_dir /data/complex_cifs \
  --out_dir out_multichain \
  --antigen_chains A D \
  --vh_chains H \
  --vl_chains L \
  --iface_pair antibody antigen \
  --iface_pair vh antigen \
  --iface_pair vl antigen \
  --plugins identity interface_contacts
```

This writes `interfaces_metadata.parquet` with one row per `(pair, structure)`.

### 4) Custom roles via `--role` (arbitrary systems)

```bash
python -m atw_pp.cli \
  --cif_dir /data/weird_cifs \
  --out_dir out_roles \
  --role antigen A B C \
  --role vh H \
  --role vl L \
  --role antibody H L \
  --role helper X \
  --iface_pair antibody antigen \
  --iface_pair helper antigen \
  --plugins identity interface_contacts
```

---

## Outputs

### `structures_metadata.parquet`

One row per structure. Typical columns:

* `path`, `assembly_id`
* `id__n_atoms_total`, `id__n_chains`, ...

### `chains_metadata.parquet`

One row per chain per structure. Typical columns:

* `path`, `assembly_id`, `chain_id`
* `id__n_atoms`, `qc__has_break`, ...
* `paragraph__paratope_size`, `paragraph__paratope_rg`, ...

### `roles_metadata.parquet`

One row per role per structure. Typical columns:

* `path`, `assembly_id`, `role`
* `id__n_atoms`, ...
* `paragraph__paratope_size` (if role-level summaries enabled)

### `interfaces_metadata.parquet`

One row per interface pair per structure. Typical columns:

* `path`, `assembly_id`, `pair`, `role_left`, `role_right`
* `iface__n_contact_atoms`, `iface__n_clash_atoms`, `iface__min_dist`

### `all_metadata.parquet` (wide table)

One row per structure, with:

* chain features pivoted: `chain_<chain_id>__<feature>`
* role features pivoted: `role_<role>__<feature>`
* interface features pivoted: `iface_<left__right>__<feature>`

Great for ranking:

* `iface_antibody__antigen__iface__n_contact_atoms`
* `role_antibody__paragraph__paratope_size`
* `param__...` columns

### `bad_files.csv`

Parse failures, with optional attached params.

---

## Configuration knobs

### Roles

Via CLI shortcuts:

* `--antigen_chains A D`
* `--vh_chains H`
* `--vl_chains L`

Or explicit:

* `--role antigen A D`
* `--role helper X`

### Interface pairs

Repeatable:

```bash
--iface_pair antibody antigen --iface_pair vh antigen
```

### Role-level paragraph summaries

Default: `vh vl antibody`. Override:

```bash
--role_paratope_summaries antibody
```

Or disable entirely:

```bash
--role_paratope_summaries
```

### Params attachment

* `--param_prefix param__`
* `--param_on_conflict keep_row|overwrite`
* `--csv_mode merge|append`

---

## Writing a new plugin

Create `atw_pp/plugins/my_plugin.py`:

```python
from __future__ import annotations
from .base import Context

class MyPlugin:
    name = "my_plugin"
    prefix = "my"
    table = "roles"  # structures|chains|roles|interfaces

    def run(self, ctx: Context):
        ab = ctx.roles.get("antibody")
        if ab is None or len(ab) == 0:
            return
        yield {
            "__table__": "roles",
            "path": ctx.path,
            "assembly_id": ctx.assembly_id,
            "role": "antibody",
            "my_metric": 123.0,
        }
```

Register in `atw_pp/plugins/__init__.py`:

```python
from .my_plugin import MyPlugin
BUILTIN_PLUGINS["my_plugin"] = MyPlugin()
```

Then run:

```bash
python -m atw_pp.cli --plugins identity my_plugin ...
```

Notes:

* Only include identity columns (`path`, `assembly_id`, `chain_id`, `role`, `pair`, etc.) at top-level.
* Everything else will be namespaced as `<prefix>__<key>` automatically.

---

## Common troubleshooting

* **No interface rows produced**

  * Ensure both roles exist and are non-empty (e.g. `antigen` and `antibody`).
  * Confirm `--iface_pair left right` matches role names.

* **Paragraph results missing**

  * Confirm `pdb` matches `Path(cif).stem`, or use `--paragraph_id_mode path` with a `path` column.
  * Ensure `chain_id` in CSV matches structure chain IDs.

* **Param CSV not attaching**

  * Must contain `path` column, and values must match `str(Path(cif).resolve())`.

---

## License

MIT license.

## Citation
* AtomWorks
* Biotite
* SciPy

