@ECHO OFF
REM The `fuefit` package must have been installed (ie ``pip install fuefit``)
REM   and python must be in your PATH for the `fuefit.exe` program to run, below. 

fuefit ^
    -I ./FuelFit.xlsx sheetname+=0 header@=None names:="[""p"",""n"",""fc""]" ^
    -I ./engine.csv file_frmt=SERIES model_path=/engine header@=None ^
    -m /params/fitting/coeffs/b2/vary?=off ^
    -m /engine/fuel=petrol ^
    -m /params/plot_maps@=True ^
    -O eng_coeffs.csv  model_path=/engine/fc_map_coeffs ^
    -O ~t.json ^
    -O ~t1.csv model_path=/measured_eng_points  index?=false ^
    -O ~t2.csv model_path=/mesh_eng_points      index?=false ^
    %1 %2 %3 %4 %5 %6 %7

IF errorlevel 1 (
    echo Invoke script with `-v -d` for more verbose output.
)