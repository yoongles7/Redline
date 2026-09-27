from django.db import models


class Report(models.Model):
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
        return f"{self.agent_name} — {self.band} ({self.score})"
