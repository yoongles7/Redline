from django.db import models


class Report(models.Model):
    agent_name = models.CharField(max_length=200)
    intended_purpose = models.TextField()
    config_text = models.TextField()
    blast_radius = models.CharField(max_length=20)
    attack_paths = models.JSONField(default=list)
    mitigations = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.agent_name} — {self.blast_radius}"
