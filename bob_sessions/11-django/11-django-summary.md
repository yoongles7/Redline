# 11-django: Model and Views Rewrite

**Task:** Replace the old JSON-based Django model and views with the LangChain pipeline versions.

**Bobcoins used:** 0.963

**Prompt:** 

Read @SPEC.md and @analyzer/core/report.py.

The current analyzer/models.py and analyzer/views.py are for the old JSON-based pipeline. Replace them.

In analyzer/models.py:

Replace the existing Report model with:class Report(models.Model):
    repo_path = models.CharField(max_length=500)
    agent_name = models.CharField(max_length=200)
    intended_purpose = models.TextField(blank=True)
    score = models.IntegerField()
    band = models.CharField(max_length=20)
    metrics = models.JSONField(default=dict)
    impact_paths = models.JSONField(default=list)
    findings = models.JSONField(default=list)
    mitigation_candidates = models.JSONField(default=list)
    graph_dot = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.agent_name} — {self.band} ({self.score})"In analyzer/views.py:

Replace the existing views with:

    index(request) — renders analyzer/index.html. No context.

    analyze(request):

        GET: renders analyzer/analyze.html

        POST: reads request.POST['repo_path'], calls build_report(repo_path) from analyzer.core.report, saves a Report instance, redirects to /report/<id>/

        On any exception (bad path, parse error), re-render analyze.html with error in context

    report_detail(request, report_id):

        Fetches the Report by id

        Renders analyzer/report.html with report in context

        Returns 404 if not found

    compare(request, report_id):

        Fetches the Report

        Renders analyzer/compare.html with report in context (shows before/after mitigation candidates)

In analyzer/urls.py: (create or replace)

    "" → index, name=index

    "analyze/" → analyze, name=analyze

    "report/<int:report_id>/" → report_detail, name=report_detail

    "report/<int:report_id>/compare/" → compare, name=compare

In redline_bob/urls.py: include analyzer URLs at root.

Then run python manage.py makemigrations and python manage.py migrate — but only if the migration succeeds. If there are conflicts, tell me.

Do not create templates yet — that's the next task. Only edit models.py, views.py, urls.py (both files).

**Output:** `analyzer/models.py`, `analyzer/views.py`, `analyzer/urls.py`, `redline_bob/urls.py`, new migration

**Fix applied:** Reset the dev database and regenerated migration to reflect the new schema.

**Test result:** makemigrations and migrate succeed. check passes with no errors.