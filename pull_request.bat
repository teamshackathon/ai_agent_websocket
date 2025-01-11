@echo off

rem 現在のGitブランチ名を取得
for /f "delims=" %%a in ('git branch --show-current') do set CURRENT_BRANCH=%%a

rem Pull Requestを作成
gh pr create --base stg --title "%CURRENT_BRANCH%" --body ""