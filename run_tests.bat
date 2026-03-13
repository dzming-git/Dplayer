@echo off
cd /d c:\Users\71555\WorkBuddy\Dplayer
python test_all_apis.py > test_results.txt 2>&1
type test_results.txt
