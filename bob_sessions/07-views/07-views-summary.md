# 07-views: Django Views and URL Routing

**Task:** Build index, analyze, and report_detail views plus URL routing.

**Bobcoins used:** 0.436

**Prompt:** 

Read @SPEC.md, @analyzer/models.py, @analyzer/core/parser.py, @analyzer/core/classifier.py, @analyzer/core/paths.py, and @analyzer/core/report.py.

Build the views and URL routing for Redline.

In analyzer/views.py, create three views:
1. index(request) -- renders the landing page (analyzer/index.html). No context needed.
2. analyze(request):
   - GET: renders the analyze form (analyzer/analyze.html)   
   - POST: reads the submitted JSON from request.POST['config_text'], runs it through the full pipeline (parser -> classifier -> paths -> report), saves a Report instance, then redirects to /report/<id>/   
   - If parsing fails (invalid jSON or missing field), re-render the analyze page with an error message in context
3. report_detail(request, report_id):
   - Fetches the Report by id   
   - Renders anlayzer/report.html with the report in context    
   - Returns 404 if not found

In analyzer/urs.py (create this file), define:
- "" -> index, name=index
- "analyze/" -> analyze, name=analyze
- "report/<int:report_id>/" -> report_detail, name=report_detail

In redline_bob/urls.py, include the analyzer URLs at the root path.

Do not create templates yet -- that's the next task. Just views and URLs.

**Output:** `analyzer/views.py`, `analyzer/urls.py`, `redline_bob/urls.py`

**Check:** `python manage.py check` passes with no errors.
