@echo off
echo Running ChanTheory Visualizer...
python main.py
echo.
echo Execution finished.
echo Opening generated charts...
start chan_chart_1m.png
start chan_chart_5m.png
start chan_chart_30m.png
pause
