"""Reproducible command-line interface."""
from __future__ import annotations
import argparse
from pathlib import Path
from .build import construct_panel
from .io import read_beneficiaries
from .report import write_outputs
from .toy import make_toy_dataset

def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic Medicare RIF analysis")
    sub = parser.add_subparsers(dest="command", required=True)
    make = sub.add_parser("make-fixture", help="Generate test-only invented data")
    make.add_argument("--dest", type=Path, default=Path("data/toy"))
    make.add_argument("--year", type=int, default=2022)
    run = sub.add_parser("run", help="Build annual synthetic claims utilization analysis")
    run.add_argument("--data-dir", type=Path, required=True)
    run.add_argument("--year", type=int, default=2022)
    run.add_argument("--output-dir", type=Path, default=Path("reports/cms_2022"))
    run.add_argument("--min-age", type=int, default=65)
    run.add_argument("--chunk-size", type=int, default=100_000)
    args = parser.parse_args()
    if args.command == "make-fixture":
        make_toy_dataset(args.dest, year=args.year)
        print(f"Created invented test fixture: {args.dest}; NOT CMS data")
        return
    frame = read_beneficiaries(args.data_dir, args.year)
    panel, qa = construct_panel(
        frame, args.data_dir, args.year, min_age=args.min_age, chunk_size=args.chunk_size
    )
    qa["source_kind"] = (
        "invented_toy_fixture"
        if (args.data_dir / "TOY_NOT_CMS.txt").exists()
        else "unverified_local"
    )
    results = write_outputs(panel, qa, args.output_dir)
    print(f"Analyzed {len(panel):,} synthetic beneficiaries. Reports: {args.output_dir}")
    print("Models:", ", ".join(results["models_fitted"]))
    print("IMPORTANT: Synthetic data do not support real-world health inference.")

if __name__ == "__main__":
    main()
