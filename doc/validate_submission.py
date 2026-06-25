#!/usr/bin/env python3
"""
Validate submission CSV per challenge rules (sections 2–3).
Row 1 = header. Rows 2–101 = exactly 100 data rows. CSV only.
"""

import csv
import re
import sys
from pathlib import Path

REQUIRED_HEADER = ["candidate_id", "rank", "score", "reasoning"]
CANDIDATE_ID_PATTERN = re.compile(r"^CAND_\d{7}$")
DATA_ROW_START = 2
EXPECTED_DATA_ROWS = 100


def _validate_filename(path: Path) -> list[str]:
    errors = []
    if path.suffix.lower() != ".csv":
        errors.append("Filename must use a .csv extension.")
    elif not path.stem:
        errors.append("Filename must be your registered participant ID (e.g. team_xxx.csv).")
    return errors


def _read_data_rows(path: Path) -> tuple[list[list[str]], list[str]]:
    errors = []
    data_rows = []
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
            except StopIteration:
                errors.append("Row 1 must be the header row; file is empty.")
                return [], errors

            if header != REQUIRED_HEADER:
                errors.append(
                    f"Row 1 (header) must be exactly:\n  {','.join(REQUIRED_HEADER)}\nFound:\n  {','.join(header)}"
                )

            for row in reader:
                if any(cell.strip() for cell in row):
                    data_rows.append(row)
    except UnicodeDecodeError:
        errors.append("File must be UTF-8 encoded.")
    except OSError as e:
        errors.append(f"Cannot read file: {e}")
    
    return data_rows, errors


def _validate_cell_values(row_num: int, row: dict, seen_ids: set, seen_ranks: set) -> tuple[list[str], int | None, float | None, str]:
    errors = []
    cid = row["candidate_id"].strip()
    rank_s = row["rank"].strip()
    score_s = row["score"].strip()

    if not cid:
        errors.append(f"Row {row_num}: candidate_id is required.")
    elif not CANDIDATE_ID_PATTERN.match(cid):
        errors.append(f"Row {row_num}: candidate_id must be CAND_XXXXXXX (7 digits).")
    elif cid in seen_ids:
        errors.append(f"Row {row_num}: duplicate candidate_id '{cid}'.")
    else:
        seen_ids.add(cid)

    rank = None
    try:
        rank = int(rank_s)
        if str(rank) != rank_s:
            raise ValueError
        if not 1 <= rank <= 100:
            errors.append(f"Row {row_num}: rank must be between 1 and 100.")
        elif rank in seen_ranks:
            errors.append(f"Row {row_num}: duplicate rank {rank}.")
        else:
            seen_ranks.add(rank)
    except ValueError:
        errors.append(f"Row {row_num}: rank must be an integer (1–100).")
        rank = None

    score = None
    try:
        score = float(score_s)
    except ValueError:
        errors.append(f"Row {row_num}: score must be a float.")

    return errors, rank, score, cid


def _validate_ordering(by_rank: list[tuple[int, float, str]]) -> list[str]:
    errors = []
    by_rank.sort(key=lambda x: x[0])
    for i in range(len(by_rank) - 1):
        r1, s1, c1 = by_rank[i]
        r2, s2, c2 = by_rank[i + 1]
        if s1 < s2:
            errors.append(f"score must be non-increasing by rank: rank {r1} ({s1}) < rank {r2} ({s2}).")
        if s1 == s2 and c1 > c2:
            errors.append(f"Equal scores at ranks {r1} and {r2}: tie-break requires candidate_id ascending ({c1!r} > {c2!r}).")
    return errors


def validate_submission(csv_path: str) -> list[str]:
    path = Path(csv_path)
    errors = _validate_filename(path)
    
    data_rows, read_errors = _read_data_rows(path)
    errors.extend(read_errors)
    if read_errors:
        return errors

    n = len(data_rows)
    if n != EXPECTED_DATA_ROWS:
        errors.append(f"After the header (row 1), there must be exactly {EXPECTED_DATA_ROWS} data rows; found {n}.")

    seen_ids = set()
    seen_ranks = set()
    by_rank = []

    for i, cells in enumerate(data_rows):
        row_num = DATA_ROW_START + i
        if len(cells) != len(REQUIRED_HEADER):
            errors.append(f"Row {row_num}: expected {len(REQUIRED_HEADER)} columns, got {len(cells)}.")
            continue

        row = dict(zip(REQUIRED_HEADER, cells))
        cell_errors, rank, score, cid = _validate_cell_values(row_num, row, seen_ids, seen_ranks)
        errors.extend(cell_errors)
        
        if rank is not None and score is not None and cid:
            by_rank.append((rank, score, cid))

    missing = set(range(1, 101)) - seen_ranks
    if missing:
        errors.append(f"Each rank 1–100 must appear exactly once; missing: {sorted(missing)}")

    errors.extend(_validate_ordering(by_rank))
    return errors


def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_submission.py <participant_id>.csv")
        sys.exit(1)

    errors = validate_submission(sys.argv[1])
    if errors:
        print(f"Validation failed ({len(errors)} issue(s)):\n")
        for e in errors:
            print(f"- {e}")
        sys.exit(1)

    print("Submission is valid.")


if __name__ == "__main__":
    main()
