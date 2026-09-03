AtlListUserGroups
=================

Utility to list Atlassian Cloud groups for a user and optionally copy group membership from one user to another.

Requirements
- Python 3.8+
- pip install requests

Script
- AtlListUserGroups.py
  - Purpose: list groups for a specific Atlassian Cloud user (by email) and optionally copy those group memberships to another user.
  - Authentication:
	- Preferred: HTTP Basic using admin email + API token passed via CLI --admin-email / -a and --api-token / -t.
	- If CLI options omitted, falls back to environment variables JIRA_EMAIL and JIRA_PAT (prints a yellow warning when used).
  - CLI options (short and long forms):
	- -s, --site SITE       Atlassian site, e.g. my-company.atlassian.net (env: ATLASSIAN_SITE)
	- -a, --admin-email     Admin email for API auth (env: JIRA_EMAIL)
	- -t, --api-token       API token (env: JIRA_PAT)
	- -u, --user-email      Source user's full email, e.g. target@example.com
	- -d, --dest-email      Destination user's full email, e.g. dest@example.com
	- -f, --file            CSV file containing source and destination email pairs
  - Usage examples:
	- List groups:
	  python AtlListUserGroups.py -s my-company.atlassian.net -a admin@example.com -t API_TOKEN -u target@example.com
	- Copy groups to another user:
	  python AtlListUserGroups.py -s my-company.atlassian.net -a admin@example.com -t API_TOKEN -u source@example.com -d dest@example.com
	- Copy groups for CSV pairs:
	  python AtlListUserGroups.py -s my-company.atlassian.net -a admin@example.com -t API_TOKEN -f users.csv
	  CSV format: source@example.com,dest@example.com
  - Behavior notes:
	- If --site is omitted the script uses the ATLASSIAN_SITE environment variable if set; otherwise it exits with a clear error.
	- Full email addresses should be provided for --user-email and --dest-email.
	- Warnings are printed in yellow ANSI color; Windows terminals may require ANSI support or enabling VT100 sequences.

Behavior and safety
- The script supports a dry-run style by not having an explicit mutate mode; copying group memberships performs live POSTs when --dest-email is provided.
- Review and test in a non-production environment before running operations that modify user group membership.

License
- No license is provided. Use at your own risk.

Contact
- Review the scripts and adjust to your environment before running in production.
