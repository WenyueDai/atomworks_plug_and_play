# run_metadata.py
from pathlib import Path
from atw_pp.run import build_metadata
from atw_pp.config import MetadataConfig

cfg = MetadataConfig()

build_metadata(
    cif_dir=Path("/home/eva/20260202_atomworks_plug_play/atw_pp/atw_pp/examples/default_input/antibody_antigen_pdb"),
    out_dir=Path("/home/eva/20260202_atomworks_plug_play/atw_pp/atw_pp/examples/default_output/antibody_antigen_pdb"),
    cfg=cfg,
    param_csvs=None,
    paragraph_preds=None,
)

# python run_metadata.py