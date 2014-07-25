./build/exe.win-amd64-3.3/fuefit.exe \
    -I fuefit/test/FuelFit.xlsx sheetname+=0 header@=None names:='["p","rpm","fc"]' \
    -I fuefit/test/engine.csv file_frmt=SERIES model_path=/engine header@=None \
    -m /engine/fuel=petrol \
    -O ~t1.csv model_path=/engine_points index?=false \
    -O ~t2.csv model_path=/engine_map index?=false \
    -O ~t.csv model_path= -m /params/plot_maps@=True

