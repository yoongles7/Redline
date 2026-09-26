import json

from django.shortcuts import render, get_object_or_404, redirect

from .models import Report
from .core import parser, classifier, paths, report as report_module


def index(request):
    return render(request, "analyzer/index.html")


def analyze(request):
    if request.method == "POST":
        config_text = request.POST.get("config_text", "")
        try:
            parsed = parser.parse(config_text)
        except (json.JSONDecodeError, ValueError, FileNotFoundError) as exc:
            return render(request, "analyzer/analyze.html", {"error": str(exc)})

        classified = classifier.classify(parsed)
        attack_paths = paths.detect(classified)
        result = report_module.generate(parsed, classified, attack_paths)

        instance = Report.objects.create(
            agent_name=result["agent_name"],
            intended_purpose=result["intended_purpose"],
            config_text=config_text,
            blast_radius=result["blast_radius"],
            attack_paths=result["attack_paths"],
            mitigations=result["mitigations"],
        )
        return redirect("report_detail", report_id=instance.id)

    return render(request, "analyzer/analyze.html")


def report_detail(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    return render(request, "analyzer/report.html", {"report": report})
