#################################################################################
fuefit: Fit fuel-consumption engine-maps on a physical formula with 6 parameters.
#################################################################################
:Copyright:   2014 European Commission (JRC)
:License:     AGPL


Overview:
=========

Fuefit accepts as input data-points for RPM, Power and Fuel-Consumprtion
(or equivalent quantities such as CM, PME/Torque and PMF) and spits-out
fitted fuel-maps according to the "normalized formula [1]_:

   (a + b*cm + c*cm**2)*pmf + (a2 + b2*cm)*pmf**2 + loss0 + loss2*cm**2

The input and output models are JSON structures build with the help of pandas
(so specific subtrees can be DataFrames or Series).
An "execution" or a "run" can be depicted with the following diagram::


         .-------------------.                        .-------------------.
        /        Model      /     ___________        / Model(augmented)  /
       /-------------------/     |           |      /-------------------/
      / +--engine         /  ==> |  program  | ==> / +...              /
     /  +--engine_points /       |___________|    /  +--engine_map    /
    /   +--params       /                        /                   /
    '------------------'                        '-------------------'



Cmd-line usage:
===============

    python fuefit -v\
        -I fuefit/test/FuelFit.xlsx sheetname+=0 header@=None names:='["p","rpm","fc"]' \
        -I fuefit/test/engine.csv file_frmt=SERIES model_path=/engine header@=None \
        -m /engine/fuel=petrol \
        -O ~t1.csv model_path=/engine_points index?=false \
        -O ~t2.csv model_path=/engine_map index?=false \
        -O ~t.csv model_path= -m /params/plot_maps@=True


Python usage:
=============

    >> from fuefit import model, processor

    >> model = {
        "engine": {
            "fuel": "diesel",
            "p_max": 95,
            "rpm_idle": 850,
            "rpm_rated": 150,
            "stroke": 94.2,
            "capacity": 2000,
            "bore": null,
            "cylinders": null,
        }
    }

    >> experiment = fuefit.Experiment()

    >> model = processor.run(model)

    >> print(model['engine'])


For information on the model-data, check the schema::

    print(fuefit.model.model_schema())



Thanks also to
==============

* Giorgos Fontaras for the physics, policy and admin support.


Footnotes:
==========

.. [1] Bastiaan Zuurendonk, Maarten Steinbuch(2005):
        "Advanced Fuel Consumption and Emission Modeling using Willans line scaling techniques for engines",
        Technische Universiteit Eindhoven, Department Mechanical Engineering, Dynamics and Control Technology Group
