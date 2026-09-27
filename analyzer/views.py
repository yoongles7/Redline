import os
import shutil
import tempfile
import zipfile

from django.shortcuts import render, get_object_or_404, redirect

from .models import Report
from .core.report import build_report

_MAX_EXTRACT_BYTES = 50 * 1024 * 1024  # 50 MB


def index(request):
    return render(request, "analyzer/index.html")


def analyze(request):
    if request.method == "POST":
        uploaded = request.FILES.get("repo_zip")
        if not uploaded:
            return render(request, "analyzer/analyze.html", {"error": "Please select a ZIP file."})

        filename = uploaded.name or ""
        content_type = uploaded.content_type or ""
        if not (filename.endswith(".zip") or content_type == "application/zip"):
            return render(
                request,
                "analyzer/analyze.html",
                {"error": "Invalid file type. Please upload a .zip archive."},
            )

        tmpdir = tempfile.mkdtemp(prefix="redline_")
        try:
            try:
                zf = zipfile.ZipFile(uploaded)
            except zipfile.BadZipFile:
                return render(
                    request,
                    "analyzer/analyze.html",
                    {"error": "The uploaded file is not a valid ZIP archive."},
                )

            with zf:
                total_size = 0
                for entry in zf.infolist():
                    name = entry.filename
                    # Path traversal protection
                    if ".." in name or name.startswith("/"):
                        return render(
                            request,
                            "analyzer/analyze.html",
                            {"error": "ZIP archive contains unsafe paths and was rejected."},
                        )
                    total_size += entry.file_size
                    if total_size > _MAX_EXTRACT_BYTES:
                        return render(
                            request,
                            "analyzer/analyze.html",
                            {"error": "ZIP archive exceeds the 50 MB extraction limit."},
                        )
                zf.extractall(tmpdir)

            # Detect effective repo root (unwrap single-subdir wrappers)
            top_entries = os.listdir(tmpdir)
            top_dirs = [e for e in top_entries if os.path.isdir(os.path.join(tmpdir, e))]
            top_files = [e for e in top_entries if os.path.isfile(os.path.join(tmpdir, e))]
            if len(top_dirs) == 1 and not top_files:
                effective_root = os.path.join(tmpdir, top_dirs[0])
            else:
                effective_root = tmpdir

            # Require at least one .py file
            has_py = any(
                fname.endswith(".py")
                for _, _, files in os.walk(effective_root)
                for fname in files
            )
            if not has_py:
                return render(
                    request,
                    "analyzer/analyze.html",
                    {"error": "No Python files found in the uploaded archive."},
                )

            try:
                result = build_report(effective_root)
            except Exception as exc:
                return render(request, "analyzer/analyze.html", {"error": str(exc)})

            instance = Report.objects.create(
                repo_path=filename,
                agent_name=result["agent_name"],
                intended_purpose=result["intended_purpose"],
                score=result["blast_radius"]["score"],
                band=result["blast_radius"]["band"],
                metrics=result["blast_radius"]["metrics"],
                impact_paths=result["impact_paths"],
                findings=result["findings"],
                mitigation_candidates=result["mitigation"]["candidates"],
                graph_dot=result["graph"]["dot"],
            )
            return redirect("report_detail", report_id=instance.id)

        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    return render(request, "analyzer/analyze.html")


def report_detail(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    return render(request, "analyzer/report.html", {"report": report})


def compare(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    return render(request, "analyzer/compare.html", {"report": report})
