#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Export a genealogy branch (all descendants of a given member) to CSV backup files.

Uses recursive SQL queries to find all descendants of a root member,
then exports the related data (members, family_links, marriages) as CSV files.

Usage:
  # Export all members of genealogy_id=1
  python scripts/export_branch.py --genealogy 1

  # Export only descendants of member_id=100 (a specific branch)
  python scripts/export_branch.py --genealogy 1 --root-member 100

  # Specify output directory
  python scripts/export_branch.py --genealogy 1 --output data/export/wang_branch
"""

import argparse
import csv
import os
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import mysql.connector
from config import DATABASE_CONFIG


def get_connection():
    """Create MySQL connection."""
    return mysql.connector.connect(**DATABASE_CONFIG)


def get_genealogy_info(conn, genealogy_id):
    """Get genealogy name and surname."""
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT genealogy_id, name, surname FROM genealogies WHERE genealogy_id = %s",
        (genealogy_id,)
    )
    info = cursor.fetchone()
    cursor.close()
    return info


def get_all_member_ids(conn, genealogy_id):
    """Get all member_ids in a genealogy."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT member_id FROM members WHERE genealogy_id = %s",
        (genealogy_id,)
    )
    ids = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return ids


def get_descendant_ids(conn, root_member_id):
    """Recursively find all descendants of a member using a CTE.

    Returns a set of member_ids (including the root member).
    """
    cursor = conn.cursor()
    cursor.execute("""
        WITH RECURSIVE descendants AS (
            -- Base case: the root member
            SELECT member_id FROM members WHERE member_id = %s
            UNION
            -- Recursive: children of current level
            SELECT fl.child_id
            FROM family_links fl
            INNER JOIN descendants d ON fl.parent_id = d.member_id
        )
        SELECT member_id FROM descendants
    """, (root_member_id,))
    ids = set(row[0] for row in cursor.fetchall())
    cursor.close()
    return ids


def export_members(conn, member_ids, output_path):
    """Export member records to CSV."""
    if not member_ids:
        return 0

    cursor = conn.cursor(dictionary=True)
    placeholders = ",".join(["%s"] * len(member_ids))
    cursor.execute(f"""
        SELECT member_id, genealogy_id, name, gender,
               birth_year, death_year, bio
        FROM members
        WHERE member_id IN ({placeholders})
        ORDER BY member_id
    """, list(member_ids))

    rows = cursor.fetchall()
    cursor.close()

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "member_id", "genealogy_id", "name", "gender",
            "birth_year", "death_year", "bio"
        ])
        writer.writeheader()
        # Convert None to empty string
        for row in rows:
            for k, v in row.items():
                if v is None:
                    row[k] = ""
            writer.writerow(row)

    return len(rows)


def export_family_links(conn, member_ids, output_path):
    """Export family_links where both child and parent are in the member set."""
    if not member_ids:
        return 0

    cursor = conn.cursor(dictionary=True)
    placeholders = ",".join(["%s"] * len(member_ids))
    cursor.execute(f"""
        SELECT child_id, parent_id, relation_type
        FROM family_links
        WHERE child_id IN ({placeholders})
          AND parent_id IN ({placeholders})
    """, list(member_ids) * 2)

    rows = cursor.fetchall()
    cursor.close()

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "child_id", "parent_id", "relation_type"
        ])
        writer.writeheader()
        for row in rows:
            for k, v in row.items():
                if v is None:
                    row[k] = ""
            writer.writerow(row)

    return len(rows)


def export_marriages(conn, member_ids, output_path):
    """Export marriages where both members are in the member set."""
    if not member_ids:
        return 0

    cursor = conn.cursor(dictionary=True)
    placeholders = ",".join(["%s"] * len(member_ids))
    cursor.execute(f"""
        SELECT member_id1, member_id2, marriage_year, divorce_year
        FROM marriages
        WHERE member_id1 IN ({placeholders})
          AND member_id2 IN ({placeholders})
    """, list(member_ids) * 2)

    rows = cursor.fetchall()
    cursor.close()

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "member_id1", "member_id2", "marriage_year", "divorce_year"
        ])
        writer.writeheader()
        for row in rows:
            for k, v in row.items():
                if v is None:
                    row[k] = ""
            writer.writerow(row)

    return len(rows)


def export_genealogy_info(conn, genealogy_id, output_path):
    """Export genealogy metadata to CSV."""
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT genealogy_id, name, surname, created_by FROM genealogies WHERE genealogy_id = %s",
        (genealogy_id,)
    )
    row = cursor.fetchone()
    cursor.close()

    if not row:
        return 0

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "genealogy_id", "name", "surname", "created_by"
        ])
        writer.writeheader()
        for k, v in row.items():
            if v is None:
                row[k] = ""
        writer.writerow(row)

    return 1


def main():
    parser = argparse.ArgumentParser(
        description="Export a genealogy branch to CSV backup files"
    )
    parser.add_argument("--genealogy", type=int, required=True,
                        help="Genealogy ID to export")
    parser.add_argument("--root-member", type=int, default=None,
                        help="Root member ID for branch export (default: export entire genealogy)")
    parser.add_argument("--output", type=str, default=None,
                        help="Output directory path (default: data/export/<genealogy_name>)")
    args = parser.parse_args()

    print("=" * 60)
    print("Branch Export Tool for Genecloud")
    print("=" * 60)

    # Connect
    print("\nConnecting to MySQL...")
    try:
        conn = get_connection()
    except mysql.connector.Error as e:
        print(f"ERROR: Cannot connect to MySQL: {e}")
        sys.exit(1)

    try:
        # Get genealogy info
        info = get_genealogy_info(conn, args.genealogy)
        if not info:
            print(f"ERROR: Genealogy {args.genealogy} not found")
            sys.exit(1)

        print(f"\nGenealogy: {info['name']} (ID: {info['genealogy_id']})")

        # Determine member IDs to export
        if args.root_member:
            print(f"Exporting branch rooted at member_id={args.root_member}...")
            member_ids = get_descendant_ids(conn, args.root_member)
            if not member_ids:
                print(f"ERROR: Member {args.root_member} not found or has no descendants")
                sys.exit(1)
            branch_label = f"branch_{args.root_member}"
        else:
            print("Exporting entire genealogy...")
            member_ids = set(get_all_member_ids(conn, args.genealogy))
            branch_label = "full"

        print(f"  Found {len(member_ids):,} members to export")

        # Determine output directory
        if args.output:
            output_dir = args.output
        else:
            safe_name = info['name'].replace(" ", "_")
            output_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "data", "export",
                f"{safe_name}_{branch_label}"
            )

        os.makedirs(output_dir, exist_ok=True)
        print(f"  Output directory: {output_dir}")

        # Export
        t0 = time.time()

        print("\n[1/4] Exporting genealogy info...")
        n = export_genealogy_info(conn, args.genealogy,
                                  os.path.join(output_dir, "genealogy.csv"))
        print(f"  {n} genealogy record")

        print("[2/4] Exporting members...")
        n = export_members(conn, member_ids,
                           os.path.join(output_dir, "members.csv"))
        print(f"  {n} members")

        print("[3/4] Exporting family_links...")
        n = export_family_links(conn, member_ids,
                                 os.path.join(output_dir, "family_links.csv"))
        print(f"  {n} family_links")

        print("[4/4] Exporting marriages...")
        n = export_marriages(conn, member_ids,
                             os.path.join(output_dir, "marriages.csv"))
        print(f"  {n} marriages")

        elapsed = time.time() - t0
        print(f"\nExport completed in {elapsed:.1f}s")
        print(f"Files saved to: {output_dir}")

        # List exported files
        print("\n--- Exported Files ---")
        for fname in sorted(os.listdir(output_dir)):
            fpath = os.path.join(output_dir, fname)
            size = os.path.getsize(fpath)
            print(f"  {fname:25s}  {size:>10,} bytes")

    finally:
        conn.close()
        print("\nConnection closed.")


if __name__ == "__main__":
    main()