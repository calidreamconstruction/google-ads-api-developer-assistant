#!/bin/bash

# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Description:
#   Integration tests for update.sh.

set -eu

# --- Environment Setup ---
# Create a temporary directory for tests
TEST_DIR=$(mktemp -d "/tmp/test_update_sh_XXXXXX")
trap 'rm -rf "${TEST_DIR}"' EXIT

echo "Running tests in ${TEST_DIR}"

FAKE_HOME="${TEST_DIR}/fake_home"
FAKE_PROJECT="${TEST_DIR}/fake_project"
mkdir -p "${FAKE_HOME}/bin"
mkdir -p "${FAKE_PROJECT}/.gemini"

# Resolve real script path before mocking git
REAL_UPDATE_SCRIPT="$(git rev-parse --show-toplevel)/update.sh"

# Mock git
cat > "${FAKE_HOME}/bin/git" <<EOF
#!/bin/bash
if [[ "\$1" == "rev-parse" ]]; then
    echo "${FAKE_PROJECT}"
elif [[ "\$1" == "clone" ]]; then
    target="\$3"
    mkdir -p "\$target/.git"
    echo "Mock cloned into \$target"
elif [[ "\$1" == "pull" ]]; then
    echo "Mock pull successful"
elif [[ "\$1" == "ls-files" ]]; then
    # Simulate file is tracked
    exit 0
elif [[ "\$1" == "checkout" ]]; then
    echo "Mock checkout successful"
else
    echo "Mock git: command \$* ignored"
fi
EOF
chmod +x "${FAKE_HOME}/bin/git"

# Mock jq
cat > "${FAKE_HOME}/bin/jq" <<EOF
#!/bin/bash
/usr/bin/jq "\$@"
EOF
chmod +x "${FAKE_HOME}/bin/jq"

# Add fake bin to PATH
export PATH="${FAKE_HOME}/bin:${PATH}"

# Create dummy settings.json
echo '{"context": {"includeDirectories": ["'"${FAKE_PROJECT}"'/client_libs/google-ads-python"]}}' > "${FAKE_PROJECT}/.gemini/settings.json"
mkdir -p "${FAKE_PROJECT}/client_libs/google-ads-python/.git"

# Copy the real update.sh for testing
UPDATE_SCRIPT_PATH="${FAKE_PROJECT}/update.sh"
cp "${REAL_UPDATE_SCRIPT}" "${UPDATE_SCRIPT_PATH}"
chmod +x "${UPDATE_SCRIPT_PATH}"

# --- Test Case 1: Run update.sh (no flags) ---
echo "--- Test Case 1: Default Update ---"
(cd "${FAKE_PROJECT}" && bash update.sh)

# Verify python was "updated"
# (Mock pull output would be in stdout, but the script continues if it works)

# --- Test Case 2: Run update.sh --php (Add new library) ---
echo "--- Test Case 2: Add PHP library ---"
(cd "${FAKE_PROJECT}" && bash update.sh --php)

# Check if php cloned
if [[ ! -d "${FAKE_PROJECT}/client_libs/google-ads-php/.git" ]]; then
    echo "FAIL: google-ads-php was not cloned"
    exit 1
fi

# Check if settings.json updated
if /usr/bin/jq -r '.context.includeDirectories[]' "${FAKE_PROJECT}/.gemini/settings.json" | grep -q "google-ads-php"; then
    echo "PASS: settings.json updated with php path"
else
    echo "FAIL: settings.json missing php path"
    cat "${FAKE_PROJECT}/.gemini/settings.json"
    exit 1
fi

# --- Test Case 3: Run update.sh --php (Already exists) ---
echo "--- Test Case 3: Update existing PHP library ---"
# We just run it again, it should not clone but pull (mock handled)
(cd "${FAKE_PROJECT}" && bash update.sh --php)
echo "PASS: update.sh --php ran successfully with existing lib"

# --- Test Case 4: Run update.sh --context_dir (Valid) ---
echo "--- Test Case 4: Add valid context directory ---"
VALID_DIR="${TEST_DIR}/valid_dir"
mkdir -p "$VALID_DIR"
(cd "${FAKE_PROJECT}" && bash update.sh --context_dir "$VALID_DIR")

# Check if settings.json updated
if /usr/bin/jq -r '.context.includeDirectories[]' "${FAKE_PROJECT}/.gemini/settings.json" | grep -q "valid_dir"; then
    echo "PASS: settings.json updated with valid context_dir"
else
    echo "FAIL: settings.json missing valid context_dir"
    cat "${FAKE_PROJECT}/.gemini/settings.json"
    exit 1
fi

# --- Test Case 5: Run update.sh --context_dir (Invalid) ---
echo "--- Test Case 5: Add invalid context directory ---"
INVALID_DIR="${TEST_DIR}/non_existent_dir"

# We capture stderr to check for error message
(cd "${FAKE_PROJECT}" && bash update.sh --context_dir "$INVALID_DIR" 2> "${TEST_DIR}/stderr.txt")

# Check if error message printed to stderr
if grep -q "ERROR: Directory not found" "${TEST_DIR}/stderr.txt"; then
    echo "PASS: error message printed to stderr for invalid context_dir"
else
    echo "FAIL: missing error message for invalid context_dir"
    cat "${TEST_DIR}/stderr.txt"
    exit 1
fi

# Verify it was NOT added to settings.json
if /usr/bin/jq -r '.context.includeDirectories[]' "${FAKE_PROJECT}/.gemini/settings.json" | grep -q "non_existent_dir"; then
    echo "FAIL: settings.json updated with invalid context_dir"
    exit 1
else
    echo "PASS: settings.json not updated with invalid context_dir"
fi

# --- Test Case 6: Run update.sh --context_dir (Comma separated list with invalid) ---
echo "--- Test Case 6: Multiple context dirs, some valid, some invalid ---"
VALID_DIR2="${TEST_DIR}/valid_dir2"
mkdir -p "$VALID_DIR2"
INVALID_DIR2="${TEST_DIR}/non_existent_dir2"

(cd "${FAKE_PROJECT}" && bash update.sh --context_dir "$VALID_DIR2,$INVALID_DIR2")

# Verify VALID_DIR2 was added
if /usr/bin/jq -r '.context.includeDirectories[]' "${FAKE_PROJECT}/.gemini/settings.json" | grep -q "valid_dir2"; then
    echo "PASS: valid_dir2 added from mixed list"
else
    echo "FAIL: valid_dir2 missing from mixed list"
    exit 1
fi

# Verify INVALID_DIR2 was NOT added
if /usr/bin/jq -r '.context.includeDirectories[]' "${FAKE_PROJECT}/.gemini/settings.json" | grep -q "non_existent_dir2"; then
    echo "FAIL: non_existent_dir2 added from mixed list"
    exit 1
else
    echo "PASS: non_existent_dir2 not added from mixed list"
fi

echo "ALL TESTS PASSED"
