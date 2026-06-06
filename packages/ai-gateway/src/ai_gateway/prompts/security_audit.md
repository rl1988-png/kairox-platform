# Security Audit Prompt

Review admin audit logs, failed logins, and trade anomalies for the last 24 hours.

Respond JSON:
- report_markdown: Markdown findings list
- findings: array of { severity: LOW|MED|HIGH, title, detail }
- confidence: 0-1

Focus on privilege escalation, unusual withdraw approvals, and repeated failed auth.
