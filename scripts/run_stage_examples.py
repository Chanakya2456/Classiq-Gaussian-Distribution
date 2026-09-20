#!/usr/bin/env python3

import argparse

from classiq_gaussian_state_preparation import create_qprog, create_solution


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Gaussian state-preparation qprogs.")
    parser.add_argument("--stage", type=int, default=1, choices=[1, 2], help="Execution stage to synthesize.")
    parser.add_argument("--resolution", type=int, default=8, help="Resolution to use for the Gaussian state.")
    args = parser.parse_args()

    qprog = create_qprog(create_solution(args.resolution), args.resolution, stage=args.stage)
    print(f"Generated stage {args.stage} qprog for resolution {args.resolution}")
    print(qprog)


if __name__ == "__main__":
    main()
