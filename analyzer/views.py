from django.shortcuts import render, get_object_or_404, redirect

from .models import Report
from .core.report import build_report


def index(request):
    return render(request, "analyzer/index.html")


def analyze(request):
    if request.method == "POST":
        repo_path = request.POST.get("repo_path", "")
        try:
            result = build_report(repo_path)
        except Exception as exc:
            return render(request, "analyzer/analyze.html", {"error": str(exc)})

        instance = Report.objects.create(
            repo_path=repo_path,
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

    return render(request, "analyzer/analyze.html")


def report_detail(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    return render(request, "analyzer/report.html", {"report": report})


def compare(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    return render(request, "analyzer/compare.html", {"report": report})
