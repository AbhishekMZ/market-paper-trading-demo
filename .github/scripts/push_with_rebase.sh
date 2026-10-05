#!/usr/bin/env bash
# Push the commit already created in this job. Another scheduled job may have
# moved main while this one was running (analyze vs observe). Rebase onto the
# new tip and retry. On a conflict, keep this job's generated files: during
# rebase, "theirs" is the commit being replayed.
set -euo pipefail

if git push origin HEAD:main; then
  exit 0
fi

echo "Push rejected; fetching full history so the rebase has a common base."
git fetch --unshallow origin || true
git fetch origin main

for attempt in 1 2 3 4 5; do
  echo "Rebasing onto origin/main (attempt ${attempt})."
  git rebase -X theirs origin/main
  if git push origin HEAD:main; then
    exit 0
  fi
  echo "Push rejected again."
  git fetch origin main
done

echo "Push failed after retries."
exit 1
