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


Tested with Python 3.4, supposed to run with 2.7.


Overview:
=========

Fuefit accepts as input data-points for RPM, Power and Fuel-Consumprtion
(or equivalent quantities such as CM, PME/Torwue and PMF) and spits-out
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

Usage:
======

A usage example::

    >> import fuefit

    >> model = {
        "engine": {
            "gear_ratios":      [120.5, 75, 50, 43, 37, 32],
            "resistance_coeffs":[100, 0.5, 0.04],
        }
    }

    >> experiment = fuefit.Experiment(model)

    >> model = experiment.run()

    >> print(model['engine']


For information on the model-data, check the schema::

    print(fuefit.instances.model_schema())



Thanks also to
==============

* Giorgos Fontaras for physics, policy and admin support.
