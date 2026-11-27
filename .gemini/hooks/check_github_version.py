import json
import logging
import os
import sys
import urllib.request

# Setup logging
# Script is in .gemini/hooks/
# Log file should be in .gemini/
base_dir = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)  # This is .gemini directory
log_path = os.path.join(base_dir, "check_github_version.log")

# Create logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# File handler (keeps full history)
file_handler = logging.FileHandler(log_path)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
)
logger.addHandler(file_handler)

# Stream handler (only shows warnings and errors to user)
stream_handler = logging.StreamHandler(sys.stderr)
stream_handler.setLevel(logging.WARNING)  # Only show WARNING or higher
stream_handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
)
logger.addHandler(stream_handler)


def get_local_version():
    # gemini-extension.json is in the root directory
    # So we need to go up one more level from .gemini to find gemini-extension.json
    root_dir = os.path.dirname(base_dir)
    json_path = os.path.join(root_dir, "gemini-extension.json")

    try:
        with open(json_path, "r") as f:
            data = json.load(f)
            return data.get("version")
    except Exception as e:
        logging.error(f"Error reading local version: {e}")
        return None


def get_remote_version():
    url = "https://raw.githubusercontent.com/googleads/google-ads-api-developer-assistant/main/gemini-extension.json"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                return data.get("version")
            else:
                logging.error(
                    f"Failed to fetch remote version, status: {response.status}"
                )
                return None
    except Exception as e:
        logging.error(f"Error fetching remote version: {e}")
        return None


def parse_version(v_str):
    return tuple(map(int, v_str.split(".")))


def main():
    logging.info("Checking for extension updates...")
    local_version = get_local_version()
    remote_version = get_remote_version()

    if not local_version or not remote_version:
        logging.info("Could not complete version check.")
        return

    logging.info(
        f"Local version: {local_version}, Remote version: {remote_version}"
    )

    try:
        if parse_version(remote_version) > parse_version(local_version):
            logging.warning(
                f"A new version of the extension is available: {remote_version}"
            )
            logging.warning("Please run `./update.sh` to update.")
        else:
            logging.info("Extension is up to date.")
    except Exception as e:
        logging.error(f"Error comparing versions: {e}")


if __name__ == "__main__":
    main()
