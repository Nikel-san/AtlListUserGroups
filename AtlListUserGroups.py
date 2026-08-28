#!/usr/bin/env python3
"""
List Atlassian Cloud groups for a user (by email).

Example:
  python3 AtlListUserGroups.py -s my-company.atlassian.net -a admin@example.com -t API_TOKEN -u target@example.com -d dest@example.com
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
    for u in users:
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
    try:
        return resp.json()
    except Exception:
        return {}

def main():
    p = argparse.ArgumentParser(description="List and optionally copy Atlassian Cloud group memberships from a source user to a destination user")
    p.add_argument("-s", "--site", required=False, help="Your Atlassian site, e.g. my-company.atlassian.net (env: ATLASSIAN_SITE)")
    p.add_argument("-a", "--admin-email", required=False, help="Admin account email for API auth (env: JIRA_EMAIL)")
    p.add_argument("-t", "--api-token", required=False, help="API token (env: JIRA_PAT)")
    p.add_argument("-u", "--user-email", required=True, help="Target user's full email to query groups for (e.g. target@example.com)")
    p.add_argument("-d", "--dest-email", required=False, help="Destination user's full email to copy group membership to (e.g. dest@example.com)")
    args = p.parse_args()

    site_value = args.site or os.environ.get('ATLASSIAN_SITE')
    if not site_value:
        print("Error: site not provided. Supply --site or set ATLASSIAN_SITE environment variable.", file=sys.stderr)
        sys.exit(1)

    base_url = build_base_url(site_value)

    admin_email = args.admin_email or os.environ.get('JIRA_EMAIL')
    api_token = args.api_token or os.environ.get('JIRA_PAT')

    if not args.admin_email and os.environ.get('JIRA_EMAIL'):
        warn("--admin-email not provided, using JIRA_EMAIL from environment")
    if not args.api_token and os.environ.get('JIRA_PAT'):
        warn("--api-token not provided, using JIRA_PAT from environment")

    if not admin_email or not api_token:
        print("Error: admin credentials not provided. Supply --admin-email and --api-token or set JIRA_EMAIL and JIRA_PAT environment variables.", file=sys.stderr)
        sys.exit(1)

    auth = HTTPBasicAuth(admin_email, api_token)
    user_email = args.user_email

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

    dest_account_id = None
    if args.dest_email:
        dest_email = args.dest_email
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

    added = 0
    skipped = 0
    failed = 0

    for g in groups:
        name = g.get("name") or g.get("displayName") or str(g)

        if dest_account_id:
            try:
                add_user_to_group(base_url, auth, name, dest_account_id)
                print(f"Added {dest_email} to group: {name}")
                added += 1
            except requests.HTTPError as e:
                status = getattr(e.response, 'status_code', None)
                if status in (400, 409):
                    print(f"Skipped '{name}': user already a member or bad request (status {status})", file=sys.stderr)
                    skipped += 1
                elif status == 403:
                    print(f"Skipped '{name}': forbidden — managed group or insufficient permissions (status 403)", file=sys.stderr)
                    skipped += 1
                else:
                    print(f"Error adding user to group '{name}': {e}", file=sys.stderr)
                    failed += 1
                try:
                    print(e.response.text, file=sys.stderr)
                except Exception:
                    pass
                continue
            except Exception as e:
                print(f"Error adding user to group '{name}': {e}", file=sys.stderr)
                failed += 1
                continue
        else:
            print(name)

    if dest_account_id:
        print(f"\nDone. added={added} skipped={skipped} failed={failed}", file=sys.stderr)

if __name__ == "__main__":
    main()