import logging
import os
import sys

import requests

# Disable urllib3 warnings for SSL
import urllib3


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Add the project root to sys.path
sys.path.append(os.getcwd())

from devops_collector.config import settings


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def test_gitlab_token():
    url = settings.gitlab.url.rstrip("/")
    token = settings.gitlab.private_token
    verify = settings.gitlab.verify_ssl

    headers = {"PRIVATE-TOKEN": token}

    logging.info(f"Testing GitLab connection to {url}...")
    logging.info(f"Verify SSL: {verify}")

    try:
        # Test /version
        api_url = f"{url}/api/v4/version"
        resp = requests.get(api_url, headers=headers, verify=verify, timeout=10)
        if resp.status_code == 200:
            logging.info(f"✅ Success! GitLab Version: {resp.json().get('version')}")
        elif resp.status_code == 401:
            logging.error("❌ Unauthorized (401). The token might be invalid or expired.")
        else:
            logging.error(f"❌ Failed with status code {resp.status_code}: {resp.text}")

        # Test /user
        user_url = f"{url}/api/v4/user"
        resp_user = requests.get(user_url, headers=headers, verify=verify, timeout=10)
        if resp_user.status_code == 200:
            user = resp_user.json()
            logging.info(f"✅ Authenticated as user: {user.get('username')} ({user.get('name')})")
            logging.info(f"   Admin: {user.get('is_admin')}")
        else:
            logging.warning(f"⚠️ Could not fetch user info: {resp_user.status_code}")

    except Exception as e:
        logging.error(f"💥 Exception during connection test: {e}")


if __name__ == "__main__":
    test_gitlab_token()
