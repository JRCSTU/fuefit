REM The `fuefit` package must have been installed (ie ``pip install fuefit -U --pre``)
REM   and python must be in your PATH for the `fuefit.exe` program to run, below. 

fuefit \
    -I .\FuelFit.xlsx sheetname+=0 header@=None names:='["p","rpm","fc"]' \
    -I .\engine.csv file_frmt=SERIES model_path=\engine header@=None \
    -m \engine\fuel=petrol \
    -O ~t1.csv model_path=\engine_points index?=false \
    -O ~t2.csv model_path=\engine_map index?=false \
    -O ~t.csv model_path= -m \params\plot_maps@=True

