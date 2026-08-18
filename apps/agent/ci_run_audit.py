#!/usr/bin/env python
"""CLI entrypoint for both GitHub Actions (`python ci_run_audit.py <audit_id>`)
and local testing. On any failure, marks the audit as errored in Convex
rather than leaving it stuck at "running" forever.
"""
import os
import sys

from dotenv import load_dotenv

from convex import ConvexClient
from pipeline import run_audit


def main() -> None:
    load_dotenv()
    if len(sys.argv) != 2:
        print("Usage: python ci_run_audit.py <audit_id>", file=sys.stderr)
        sys.exit(1)

    audit_id = sys.argv[1]
    try:
        run_audit(audit_id)
        print(f"Audit {audit_id} completed.")
    except Exception as e:
        print(f"Audit {audit_id} failed: {e}", file=sys.stderr)
        try:
            ConvexClient(os.environ["CONVEX_URL"]).mutation(
                "audits:markError", {"id": audit_id, "message": str(e)}
            )
        except Exception as inner:
            print(f"Also failed to report the error to Convex: {inner}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
