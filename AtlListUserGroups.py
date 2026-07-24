#!/usr/bin/env python3
"""
List Atlassian Cloud groups for a user (by email).

Example:
  python3 AtlListUserGroups.py -s your-site.atlassian.net -a admin@example.com -t ABCDE... -u target@example.com -d dest@example.com
"""
import argparse
import sys
import os

def warn(msg: str):
    """Print a yellow-colored warning to stderr."""
    YELLOW = '\033[33m'
    RESET = '\033[0m'
    print(f"{YELLOW}Warning: {msg}{RESET}", file=sys.stderr)
import requests
from requests.auth import HTTPBasicAuth

def build_base_url(site):
    if site.startswith("http://") or site.startswith("https://"):
        return site.rstrip('/')
    return f"https://{site.rstrip('/')}"

def find_user_account_id(base_url, auth, target_email):
    url = f"{base_url}/rest/api/3/user/search"
    params = {"query": target_email}
    resp = requests.get(url, auth=auth, params=params, timeout=15)
    resp.raise_for_status()
    users = resp.json()
    if not users:
        return None
    # Prefer exact email match if present, otherwise take first result
    for u in users:
        # emailAddress may be omitted depending on instance/privacy; try a few keys
        if u.get("emailAddress") == target_email or u.get("email") == target_email:
            return u.get("accountId")
    return users[0].get("accountId")

def get_user_groups(base_url, auth, account_id):
    url = f"{base_url}/rest/api/3/user/groups"
    params = {"accountId": account_id}
    resp = requests.get(url, auth=auth, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()

def add_user_to_group(base_url, auth, group_name, account_id):
    """Add a user (by accountId) to a group (by group name)."""
    url = f"{base_url}/rest/api/3/group/user"
    params = {"groupname": group_name}
    resp = requests.post(url, auth=auth, params=params, json={"accountId": account_id}, timeout=15)
    resp.raise_for_status()
    return resp.json()

def main():
    p = argparse.ArgumentParser(description="List and optionally copy Atlassian Cloud group memberships from a source user to a destination user")
    p.add_argument("-s", "--site", required=False, help="Your Atlassian site, e.g. my-org.atlassian.net (default: iderawebdev.atlassian.net)")
    p.add_argument("-a", "--admin-email", required=False, help="Admin account email (for API auth). If omitted, uses env JIRA_EMAIL")
    p.add_argument("-t", "--api-token", required=False, help="API token (create at https://id.atlassian.com/manage-profile/security/api-tokens). If omitted, uses env JIRA_PAT")
    p.add_argument("-u", "--user-email", required=True, help="Target user's email to query groups for (domain optional)")
    p.add_argument("-d", "--dest-email", required=False, help="Destination user email to copy group membership to (domain optional)")
    args = p.parse_args()

    # default site if not provided
    site_value = args.site
    if not site_value:
        site_value = 'iderawebdev.atlassian.net'
        warn(f"--site not provided, using default: {site_value}")

    base_url = build_base_url(site_value)

    # admin creds: prefer CLI, fallback to env vars
    admin_email = args.admin_email or os.environ.get('JIRA_EMAIL')
    api_token = args.api_token or os.environ.get('JIRA_PAT')

    # warn if falling back to env vars
    if not args.admin_email and os.environ.get('JIRA_EMAIL'):
        warn("--admin-email not provided, using JIRA_EMAIL from environment")
    if not args.api_token and os.environ.get('JIRA_PAT'):
        warn("--api-token not provided, using JIRA_PAT from environment")

    if not admin_email or not api_token:
        print("Error: admin credentials not provided. Supply --admin-email and --api-token or set JIRA_EMAIL and JIRA_PAT environment variables.", file=sys.stderr)
        sys.exit(1)

    auth = HTTPBasicAuth(admin_email, api_token)
    # if email domain missing, append default and warn
    user_email = args.user_email
    if '@' not in user_email:
        user_email = user_email + '@idera.com'
        warn(f"--user-email domain not provided, using default: {user_email}")

    try:
        account_id = find_user_account_id(base_url, auth, user_email)
    except requests.HTTPError as e:
        print(f"Error searching for user: {e}", file=sys.stderr)
        try:
            print(e.response.text, file=sys.stderr)
        except Exception:
            pass
        sys.exit(2)

    if not account_id:
        print(f"No user found matching email: {args.user_email}", file=sys.stderr)
        sys.exit(3)

    try:
        groups = get_user_groups(base_url, auth, account_id)
    except requests.HTTPError as e:
        print(f"Error fetching groups for accountId {account_id}: {e}", file=sys.stderr)
        try:
            print(e.response.text, file=sys.stderr)
        except Exception:
            pass
        sys.exit(4)

    if not groups:
        print(f"No groups found for user {args.user_email} (accountId {account_id})")
        return

    # print groups and optionally copy membership to destination user
    dest_account_id = None
    if args.dest_email:
        dest_email = args.dest_email
        if '@' not in dest_email:
            dest_email = dest_email + '@idera.com'
            warn(f"--dest-email domain not provided, using default: {dest_email}")
        try:
            dest_account_id = find_user_account_id(base_url, auth, dest_email)
        except requests.HTTPError as e:
            print(f"Error searching for destination user: {e}", file=sys.stderr)
            try:
                print(e.response.text, file=sys.stderr)
            except Exception:
                pass
            sys.exit(5)

        if not dest_account_id:
            print(f"No destination user found matching email: {args.dest_email}", file=sys.stderr)
            sys.exit(6)

    for g in groups:
        # group object typically contains 'name' and 'self' and maybe 'displayName'
        name = g.get("name") or g.get("displayName") or str(g)

        if dest_account_id:
            # copying mode: do not print group names, only print action results
            try:
                add_user_to_group(base_url, auth, name, dest_account_id)
                print(f"Added {dest_email} to group: {name}")
            except requests.HTTPError as e:
                # If already a member or other client error, print and continue
                status = getattr(e.response, 'status_code', None)
                if status in (400, 409):
                    print(f"Destination user may already be a member of '{name}' or bad request (status {status})", file=sys.stderr)
                else:
                    print(f"Error adding user to group {name}: {e}", file=sys.stderr)
                try:
                    print(e.response.text, file=sys.stderr)
                except Exception:
                    pass
                continue
        else:
            # listing mode: print group names
            print(name)

if __name__ == "__main__":
    main()
