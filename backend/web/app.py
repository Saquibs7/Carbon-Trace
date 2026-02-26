from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
    flash,
)


# Ensure project root is on sys.path so `src` is importable when running
# this file directly with `python web/app.py`.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.web_pipeline import run_web_pipeline


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("CARBON_TRACE_SECRET", "dev-secret-key")

    project_root = Path(__file__).resolve().parents[1]
    uploads_dir = project_root / "uploads"
    outputs_dir = project_root / "web_outputs"
    uploads_dir.mkdir(exist_ok=True)
    outputs_dir.mkdir(exist_ok=True)

    @app.route("/", methods=["GET"])
    def index():
        return render_template("index.html")

    @app.route("/upload", methods=["POST"])
    def upload():
        # two possible uploads: OWID CSV (required) and optional factory data
        owid_file = request.files.get("owid_csv")
        prod_file = request.files.get("production_csv")

        if not owid_file or owid_file.filename == "":
            flash("Please select an OWID CO₂ CSV file to upload.")
            return redirect(url_for("index"))
        if not owid_file.filename.lower().endswith(".csv"):
            flash("Only CSV files are supported for the OWID dataset.")
            return redirect(url_for("index"))

        session_id = uuid.uuid4().hex[:8]
        upload_path = uploads_dir / f"owid_{session_id}.csv"
        owid_file.save(upload_path)

        production_path = None
        if prod_file and prod_file.filename:
            if not prod_file.filename.lower().endswith(".csv"):
                flash("Only CSV files are supported for the production dataset.")
                return redirect(url_for("index"))
            production_path = uploads_dir / f"prod_{session_id}.csv"
            prod_file.save(production_path)

        output_root = outputs_dir / session_id
        output_root.mkdir(parents=True, exist_ok=True)

        try:
            result = run_web_pipeline(
                str(upload_path),
                str(output_root),
                production_csv=str(production_path) if production_path else None,
            )
        except Exception as exc:  # noqa: BLE001
            flash(f"Processing failed: {exc}")
            return redirect(url_for("index"))

        cleaned_csv_rel = os.path.relpath(result["cleaned_csv"], project_root)
        audit_summary_rel = os.path.relpath(result["audit_summary_csv"], project_root)
        chart_rel = result["emissions_chart"]

        # read first few rows of the audit summary for inline display
        try:
            import pandas as pd

            audit_preview = pd.read_csv(result["audit_summary_csv"]).head(10).to_dict(
                orient="records"
            )
        except Exception:  # pragma: no cover - optional feature
            audit_preview = []

        return render_template(
            "result.html",
            session_id=session_id,
            cleaned_csv_path=cleaned_csv_rel,
            summary=result["summary"],
            audit_summary_path=audit_summary_rel,
            audit_preview=audit_preview,
            emissions_chart=chart_rel,
            violators=result.get("violators", []),
        )

    @app.route("/download/<path:filename>", methods=["GET"])
    def download(filename: str):
        project_root_str = str(project_root)
        file_path = Path(project_root_str) / filename
        if not file_path.exists():
            flash("Requested file not found.")
            return redirect(url_for("index"))
        return send_from_directory(
            directory=file_path.parent,
            path=file_path.name,
            as_attachment=True,
        )

    return app


if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(host="0.0.0.0", port=8000, debug=True)

