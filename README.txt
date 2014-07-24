==============================================
fuefit: fue-consumption engine maps calculator
==============================================

Install:
========

To install it, assuming you have download the sources,
do the usual::

    python setup.py install

Or get it directly from the PIP repository::

    pip3 install wltc


Tested with Python 3.4.


Overview:
=========

Fuefit accepts as input data-points for RPM, Power and Fuel-Consumprtion
(or equivalent quantities such as CM, PME/Torque and PMF) and spits-out
fitted fuel-maps according to the formula:

   (a + b*cm + c*cm**2)*pmf + (a2 + b2*cm)*pmf**2 + loss0 + loss2*cm**2\n",

An "execution" or a "run" of an experiment is depicted in the following diagram::

                           _______________
         .----------.     |               |      .------------------.
        /   Model  /  ==> |   Experiment  | ==> / Model(augmented) /
       /----------/       |_______________|    '------------------'
      /  fuefit  /
     /  consts  /
    '----------'

Cmd-line usage:
===============
python -m fuefit.main -d off \
    -I fuefit/test/FuelFit.xlsx sheetname+=0 header@=None names@='["rpm","p","fc"]' \
    -I fuefit/test/engine.csv file_frmt=SERIES model_path=/engine header@=None \
    -m /engine/fuel=petrol \
    -O ~t1.csv model_path=/engine_points index?=false \
    -O ~t2.csv model_path=/engine_map index?=false \
    -O ~t.csv model_path= -m /params/plot_maps@=True


A usage example::

    >> import fuefit

    >> model = {
        "engine": {
            "gear_ratios":      [120.5, 75, 50, 43, 37, 32],
            "resistance_coeffs":[100, 0.5, 0.04],
        }
    }

    >> experiment = fuefit.Experiment()

    >> model = experiment.run(model)

    >> print(model['engine'])


For information on the model-data, check the schema::

    print(fuefit.model.model_schema())



Thanks also to
==============

* Giorgos Fontaras for physics, policy and admin support.
