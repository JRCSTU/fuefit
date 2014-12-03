#######
Changes
#######

.. contents::

Releases
========
v0.0.6, X-X-X -- Maintenance release
------------------------------------
* build: Untrack exclipse-project files.
* docs: Improve installation instructions and review of scientific content.
* model: Move /params/is_robust --> ./fitting/is_robust
* model: Rename fit-coefficient PMF --> BMEP.


v0.0.5, 12-Noe-2014 -- 3rd public (Rosetta) release
---------------------------------------------------
* core: Use `lmfit` library for enforcing limits on fitted coefficients, etc.
* data: Updated Excel file with more engines.
* docs: Fix math-formulas and improve instructions.
* WARN: ExcelRunner fails on *OS X*.


v0.0.4, 10-Noe-2014 -- 2nd public (beta) release
------------------------------------------------
* core: FIX calclulations.
* core: Possible to specify whether to Robust-fit or not.
* core: Pin `b0` coefficient to 0.
* excel: Enhance excel-runner code to support any python-code. 
* excel: FIX parsing of ExcelRefs and their syntax documentation.  
* test: Improve tests and Doctest code in README. 
* test, ci: Use TravisCI/Anaconda Continuous-integration to check project health.
* docs: Add "API-reference" section.
* docs: Add some "Anaconda" help.
* NOTE: Various renames of modules, files and model properties.


v0.0.3, 03-Noe-2014 -- 1st public (beta) release
------------------------------------------------
* excel: Add excel-runner for running batch of experiments. 
* cmd: Rename fuefitcmd --> fuefit (back again)
* cmd: Add StartMenu item in *Windows*.
* build: Distribute on Wheels and Docs-archive.
* build: Upload to Github/RTD/PyPi.


v0.0.2, 28-Oct-2014 -- Beta release
-----------------------------------
* Add Excel-UI.
* cmd: Rename fuefit --> fuefitcmd
* core,model: Rename rpm_XXX --> n_XXX, etc.
* docs: Update README with excel capability, copy sections from wltp project.
* build: Stop building as EXE.
* build: Add WinPython-deps as a requirments.txt.
* Add sphinx documentation.
* Relicense from AGPL --> EUPL.


v0.0.1, 25-Jul-2014 -- Alpha release
------------------------------------
* Implemented algorithm using `pdcalc`.
* pdcalc: Implemented library that decides what to calculate with a topological sorting of 
    required calculations from Input --> Output, ala-Excel.
* Packaged as EXE.


v0.0.0, 15-Apr-2014 -- Alpha release
------------------------------------
* Project administerial: README, INSTALL, setup.py mostly transcopied from wtlc
