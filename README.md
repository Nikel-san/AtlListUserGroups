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
	- -s, --site SITE       Atlassian site, e.g. my-org.atlassian.net (or set ATLASSIAN_SITE env var)
	- -a, --admin-email     Admin email for API auth (or set JIRA_EMAIL)
	- -t, --api-token       API token (or set JIRA_PAT)
	- -u, --user-email      Source user's email (domain optional; @idera.com appended with a warning if missing)
	- -d, --dest-email      Destination user email to copy group membership to (domain optional)
  - Usage examples:
	- List groups:
	  python AtlListUserGroups.py -s your-site.atlassian.net -a admin@example.com -t API_TOKEN -u target@example.com
	- Copy groups to another user:
	  python AtlListUserGroups.py -s your-site.atlassian.net -a admin@example.com -t API_TOKEN -u source@example.com -d dest@example.com
  - Behavior notes:
	- If --site is omitted the script uses the ATLASSIAN_SITE environment variable if set; otherwise a default site is used and a warning is printed.
	- If --user-email or --dest-email is provided without a domain, @idera.com is appended and a warning is printed.
	- Warnings are printed in yellow ANSI color; Windows terminals may require ANSI support or enabling VT100 sequences.

Behavior and safety
- The script supports a dry-run style by not having an explicit mutate mode; copying group memberships performs live POSTs when --dest-email is provided.
- Review and test in a non-production environment before running operations that modify user group membership.

License
- No license is provided. Use at your own risk.

Contact
- Review the scripts and adjust to your environment before running in production.
