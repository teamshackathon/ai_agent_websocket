#!/bin/bash

# 現在のGitブランチ名を取得
CURRENT_BRANCH=$(git branch --show-current)

# Pull Requestを作成
gh pr create --base stg --title "$CURRENT_BRANCH" --body ""