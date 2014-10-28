#################################################################################
fuefit: Fit fuel-consumption engine-maps on a physical formula with 6 parameters.
#################################################################################
:Release:       |version|
:Copyright:   2014 European Commission (JRC)
:License:     AGPL


Introduction
============
Overview
--------

Fuefit accepts as input data-points for RPM, Power and Fuel-Consumprtion
(or equivalent quantities such as CM, PME/Torque and PMF) and spits-out
fitted fuel-maps according to the "normalized formula [1]_:

   (a + b*cm + c*cm**2)*pmf + (a2 + b2*cm)*pmf**2 + loss0 + loss2*cm**2

The input and output models are JSON structures build with the help of pandas
(so specific subtrees can be DataFrames or Series).
An "execution" or a "run" can be depicted with the following diagram::


          .-------------------.                         .-------------------.
         /        Model      /     ____________        / Model(augmented)  /
        /-------------------/     |            |      /-------------------/
       / +--engine         /  ==> | Experiment | ==> / +...              /
      /  +--engine_points /       |____________|    /  +--engine_map    /
     /   +--params       /                         /                   /
    '-------------------'                         '-------------------'



Quick-start
-----------
Assuming a working python-environment, you can `cd` to the downloaded sources of the project and 
use the following commands in a console:

:Installation: ``$ pip install -r WinPython_requirments.txt -U .``
:Cmd-line: ``$ fuefitcmd --help`` 
:Excel: ``$ fuefitcmd --excelrun`` (*Windows*/*OS X* only)
:Python-code:
    .. code-block:: python
    
    import pandas as pd
    from fuefit import model, processor
    
    input_model = mdl = model.base_model()
    input_model.update({...})                                       ## See "Python Usage" for model contents.
    input_model['engine_points'] = pd.read_csv('measured.csv')      ## Pandas can also read Excel, matlab, ...
    mdl = model.validate_model(mdl, additional_props) 
    
    output_model = processor.run(input_model)
    
    print(model.resolve_jsonpointer(output_model, '/engine/fc_map_params'))
    print(output_model['fitted_eng_points'])


.. Tip:: 
    To install *python*, you can try the free (as in beer) distribution
    `Anaconda <http://docs.continuum.io/anaconda/pkg-docs.html>`_ for *Windows* and *OS X*, or
    the totally free `WinPython <http://winpython.sourceforge.net/>`_ distribution, but only for *Windows*:

    * For *Anaconda* you may need to install project's dependencies manually (see :file:`setup.py`)
      using :command:`conda`.
    * The most recent version of *WinPython* (python-3.4) although it has just 
      `changed maintainer  <http://sourceforge.net/projects/stonebig.u/files/>`_,
      it remains a higly active project, and it can even compile native libraries using an installations of 
      *Visual Studio*, if available
      (required for instance when upgrading ``numpy/scipy``, ``pandas`` or ``matplotlib`` with :command:`pip`).
      
      Remember also to *Register your WinPython installation* from 
      :menuselection:`Start menu --> All Programs --> WinPython --> WinPython ControlPanel`, and then
      :menuselection:`Options --> Register Ditribution`.
      
.. Tip::
    The commands above beginning with ``$`` work on an *unix* like operating system with a *POSIX* shell
    (*Linux*, *OS X*). If you're using *Windows*, you'll have to run their *windows command shell* counterparts.
    The same is true for the rest of this documentation.

    Although the commands are simple and easy to translate , it would be worthwile to install
    `cygwin <https://www.cygwin.com/>`_ to get the same environment on *Windows* machines.
    If you choose to do that, make sure that in the *cygwin*'s installation wizard the following packages
    are also included::

        * git, git-completion
        * make
        * openssh, curl, wget



Install
=======
Current |version| runs on Python-3.3+ .

You can install (or upgrade) the project the "standard" way using :command:`pip`.
Just `cd` to the project's folder and enter:

.. code-block:: console

    $ pip install --upgrade .                       ## Use `pip3` if both python-2 & 3 installed.

To install for different Python versions, repeat step 3 for every required version.

Particularly for the latest *WinPython* environments (*Windows* / *OS X*) you can install dependencies with: 

.. code-block:: console

    $ pip install -r WinPython_requirements.txt -U .


The previous command install dependencies in the system's folders.
If you want to avoid that (because, for instance, you do not have *admin-rights*), but 
you do not want to use a |virtualenv|_, you can install dependencies inside the project-folder 
with this command:

.. code-block:: console

    $ python setup.py install                       ## Use `python3` if you have installed both python-2 & 3.
    

The previous command install just the latest version of the project.
If you wish to link the project's sources with your python environment, install the project 
in `development mode <http://pythonhosted.org/setuptools/setuptools.html#development-mode>`_:

.. code-block:: console

    $ python setup.py develop




Usage
=====
Excel usage
-----------
.. Attention:: Excel-integration requires Python 3 and *Windows* or *OS X*!

In *Windows* and *OS X* you may utilize the excellent `xlwings <http://xlwings.org/quickstart/>`_ library 
to use Excel files for providing input and output to the processor.

To create the necessary template-files in your current-directory you should enter:

.. code-block:: console

     $ fuefit --excel
     

You could type instead :samp:`fuefitcmd --excel {file_path}` to specify a different destination path.

In *windows*/*OS X* you can type ``fuefitcmd --excelrun`` and the files will be created in your home-directory 
and the excel will open them in one-shot.

All the above commands creates two files:

:file:`fuefit_excel_runner.xlsm`
    The python-enabled excel-file where input and output data are written, as seen in the screenshot below:
    
    .. image:: docs/xlwings_screenshot.png
        :scale: 50%
        :alt: Screenshot of the `fuefit_excel_runner.xlsm` file.
        
    After opening it the first tie, enable the macros on the workbook, select the python-code at the left and click 
    the :menuselection:`Run Selection as Pyhon` button; one sheet per vehicle should be created.

    The excel-file contains additionally appropriate *VBA* modules allowing you to invoke *Python code* 
    present in *selected cells* with a click of a button, and python-functions declared in the python-script, below,
    using the `mypy` namespace. 
    
    To add more input-columns, you need to set as column *Headers* the *json-pointers* path of the desired 
    model item (see `Python usage`_ below,).

:file:`fuefit_excel_runner.py`   
    Utility python functions used by the above xls-file for running a batch of experiments.  
     
    The particular functions included reads multiple vehicles from the input table with various  
    vehicle characteristics and/or experiment parameters, and then it adds a new worksheet containing 
    the cycle-run of each vehicle . 
    Of course you can edit it to further fit your needs.


.. Note:: You may reverse the procedure described above and run the python-script instead.
    The script will open the excel-file, run the experiments and add the new sheets, but in case any errors occur, 
    this time you can debug them, if you had executed the script through *LiClipse*, or *IPython*! 

Some general notes regarding the python-code in excel-cells:

* The *VBA* `xlwings` module contains the code from the respective library; do not edit, but you may replace it 
  with a latest version. 
* You can read & modify the *VBA* `xlwings_ext` module with code that will run on each invocation 
  to import libraries such as 'numpy' and 'pandas', or pre-define utility python functions.
* The name of the python-module to import is automatically calculated from the name of the Excel-file,
  and it must be valid as a python module-name.  Therefore do not use non-alphanumeric characters such as 
  spaces(` `), dashes(`-`) and dots(`.`) on the Excel-file.
* Double-quotes(") do not work for denoting python-strings in the cells; use single-quotes(') instead.
* You cannot enter multiline or indentated python-code such as functions and/or  ```if-then-else`` expressions; 
  move such code into the python-file. 
* There are two pre-defined python variables on each cell, `cr` and `cc`, refering to "cell_row" and 
  "cell_column" coordinates of the cell, respectively.  For instance, to use the right-side column as 
  a poor-man's debugging aid, you may use this statement in a cell:

  .. code-block:: python
    
    Range((cr, cc+1)).value = 'Some string or number'

* On errors, the log-file is written in :file:`{userdir}/AppData/Roaming/Microsoft/Excel/XLSTART/xlwings_log.txt` 
  for as long as **the message-box is visible, and it is deleted automatically after you click 'ok'!**
* Read http://docs.xlwings.org/quickstart.html

    
.. Tip:: 
    You can permanently enable your Excel installation to support *xlwings* by copying
    the *VBA* modules of the demo-excel file ``xlwings`` and ``xlwings-ext`` into 
    your :file:`PERSONAL.XLSB` workbook, as explaine here: 
    http://office.microsoft.com/en-001/excel-help/copy-your-macros-to-a-personal-macro-workbook-HA102174076.aspx.
    
    You can even `add a new Ribbon-button <http://msdn.microsoft.com/en-us/library/bb386104.aspx>`_ 
    to execute the selected cells as python-code.  Set this new button to invoke the ``RunSelectionAsPython()``
    *VBA* function.

    If you do the above, remember that *VBA*-code in your personal-workbook takes precedance over any code
    present in your currently open workbook.


Cmd-line usage
--------------

    fuefitcmd -v\
        -I fuefit/test/FuelFit.xlsx sheetname+=0 header@=None names:='["p","rpm","fc"]' \
        -I fuefit/test/engine.csv file_frmt=SERIES model_path=/engine header@=None \
        -m /engine/fuel=petrol \
        -O ~t1.csv model_path=/engine_points index?=false \
        -O ~t2.csv model_path=/engine_map index?=false \
        -O ~t.csv model_path= -m /params/plot_maps@=True


Python usage
------------

    >> from fuefit import model, processor

    >> input_model = model.base_model()
    >> input_model.update({
        "engine": {
            "fuel": "diesel",
            "p_max": 95,
            "n_idle": 850,
            "n_rated": 6500,
            "stroke": 94.2,
            "capacity": 2000,
            "bore": null,
            "cylinders": null,
        }
    })

    >> model.validate_model(input_model)

    >> output_model = processor.run(input_model)

    >> print(output_model['engine'])
    >> print(output_model['fitted_eng_maps'])


For information on the model-data, check the schema::

    >> print(fuefit.model.model_schema())


You can always check the Test-cases and the :mod:`fuefit.cmdline` for sample code.



Thanks also to
==============

* Giorgos Fontaras for the physics, policy and admin support.



Footnotes:
==========

.. [1] Bastiaan Zuurendonk, Maarten Steinbuch(2005):
        "Advanced Fuel Consumption and Emission Modeling using Willans line scaling techniques for engines",
        Technische Universiteit Eindhoven, Department Mechanical Engineering, Dynamics and Control Technology Group
