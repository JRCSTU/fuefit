################################################
*fuefit* fits engine-maps on physical parameters
################################################
:Release:       |version|
:Copyright:     2014 European Commission (`JRC-IET <http://iet.jrc.ec.europa.eu/>`_)
:License:       `EUPL 1.1+ <https://joinup.ec.europa.eu/software/page/eupl>`_

The *fuefit* is a python package that calculates fitted fuel-maps from measured engine data-points 
based on parameters with physical meaning.


.. _before-intro:

Introduction
============

Overview
--------
The *Fuefit* calculator accepts engine data-points for as Input,
(RPM, Power and Fuel-Consumption or equivalent quantities such as CM, PME/Torque and PMF) 
and spits-out fitted fuel-maps according to the following formula [#]_:

.. math::

   (a + b*cm + c*cm**2)*pmf + (a2 + b2*cm)*pmf**2 + loss0 + loss2*cm**2


An "execution" or a "run" of a calculation along with the most important pieces of data 
are depicted in the following diagram::


          .-------------------.                         .--------------------------.
         /    Input-Model    /     ____________        /       Output-Model       /
        /-------------------/     |            |      /--------------------------/
       / +--engine         /  ==> | Calculator | ==> / +--engine                /
      /  +--engine_points /       |____________|    /  | +--fc_map_params      /
     /   +--params       /                         /   +--engine_map          /
    /                   /                         /    +--fitted_eng_points  /
   '-------------------'                         '--------------------------'

The *Input & Output Model* are trees of strings and numbers, assembled with:

* sequences,
* dictionaries,
* :class:`pandas.DataFrame`,
* :class:`pandas.Series`, and
* URI-references to other model-trees (TODO).


Quick-start
-----------
Assuming a working python-environment, open a *command-shell* inside the sources of the project 
(ie in *Windows* use :program:`cmd.exe` BUT with with Python in its :envvar:`PATH`)
and try the following commands 

:Installation:  ``$ pip install fuefit-|version|-py3-none-any.whl``  
:Start-menu:    ``$ fuefit --winmenu`` 
:Excel:         ``$ fuefit --excelrun``                          *Windows*/*OS X* only
:Cmd-line:      ``$ fuefit --help`` 
:Python-code: 
    .. code-block:: python
    
        import pandas as pd
        from fuefit import model, processor
        
        input_model = mdl = model.base_model()
        input_model.update({...})                                     ## See "Python Usage" below.
        input_model['engine_points'] = pd.read_csv('measured.csv')    ## Can also read Excel, matlab, ...
        mdl = model.validate_model(mdl, additional_props) 
        
        output_model = processor.run(input_model)
        
        print(model.resolve_jsonpointer(output_model, '/engine/fc_map_params'))
        print(output_model['fitted_eng_points'])


.. Tip::
    The commands above beginning with ``$`` imply a *Unix* like operating system with a *POSIX* shell
    (*Linux*, *OS X*). If you're using *Windows*, you'll have to run their counterparts
    in the *windows command shell* :program:`cmd.exe`.
    
    Although the commands are simple and easy to translate , it would be worthwile to install
    `Cygwin <https://www.cygwin.com/>`_ to get the same environment on *Windows*.
    If you choose to do that, include also the following packages in the *Cygwin*'s installation wizard::

        * git, git-completion
        * make, zip, unzip, bzip2
        * openssh, curl, wget

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
      

.. _before-install:

Install
=======
Current |version| runs on Python-3.3+ and is distributed on `Wheels <https://pypi.python.org/pypi/wheel>`_.

You can install (or upgrade) the project the "standard" way by using :command:`pip`.

.. code-block:: console

    $ pip install fuefit-0.0.2_beta3-py3-none-any.whl           ## Use `pip3` if both python-2 & 3 in PATH.


Check that installation has worked:

.. code-block:: console

    $ fuefit --version
    0.0.2.beta2

.. Tip:
    To debug the installation, you can export a non-empty :envvar:`DISTUTILS_DEBUG` 
    and *distutils* will print detailed information about what it is doing and/or 
    print the whole command line when an external program (like a C compiler) fails.


You may upgrade all dependencies to their latest version with :option:`--upgrade` (or :option:`-U` equivalently) 
but then the build might take some considerable time to finish.

To install it for different Python versions, repeat step 3 for every required version.

Particularly for the latest *WinPython* environments (*Windows* / *OS X*) you can install dependencies with: 

.. code-block:: console

    $ pip install -r WinPython_requirements.txt -U .


The previous command install dependencies in the system's folders.
If you want to avoid that (because, for instance, you do not have *admin-rights*), but 
you do not want to use a `virtualenv <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_, 
you can install dependencies inside the project-folder with this command:

.. code-block:: console

    $ python setup.py install                       ## Use `python3` if you have installed both python-2 & 3.
    

The previous command install just the latest version of the project.
If you wish to link the project's sources with your python environment, install the project 
in `development mode <http://pythonhosted.org/setuptools/setuptools.html#development-mode>`_:

.. code-block:: console

    $ python setup.py develop



.. _before-usage:

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
     

You could type instead :samp:`fuefit --excel {file_path}` to specify a different destination path.

In *windows*/*OS X* you can type ``fuefit --excelrun`` and the files will be created in your home-directory 
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

:file:`fuefit_excel_runner{#}.py`   
    Python functions used by the above xls-file for running a batch of experiments.  
    
    The particular functions included reads multiple vehicles from the input table with various  
    vehicle characteristics and/or experiment parameters, and then it adds a new worksheet containing 
    the cycle-run of each vehicle . 
    Of course you can edit it to further fit your needs.


.. Note:: You may reverse the procedure described above and run the python-script instead:

    .. code-block:: console
    
         $ python fuefit_excel_runner.py
    
    The script will open the excel-file, run the experiments and add the new sheets, but in case any errors occur, 
    this time you can debug them, if you had executed the script through `LiClipse <http://www.liclipse.com/>`__, 
    or *IPython*! 


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

    fuefit -v\
        -I fuefit/test/FuelFit.xlsx sheetname+=0 header@=None names:='["p","rpm","fc"]' \
        -I fuefit/test/engine.csv file_frmt=SERIES model_path=/engine header@=None \
        -m /engine/fuel=petrol \
        -O ~t1.csv model_path=/engine_points index?=false \
        -O ~t2.csv model_path=/engine_map index?=false \
        -O ~t.csv model_path= -m /params/plot_maps@=True


Python usage
------------
Example code:

.. code-block:: pycon

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


For information on the model-data, check the schema:

.. code-block:: pycon

    >> print(fuefit.model.model_schema())


You can always check the Test-cases and the :mod:`fuefit.cmdline` for sample code.
You explore documentation in Html by serving it with a web-server:



.. _before-contribute:

Contribute
==========
[TBD]

Development team
----------------

* Author:
    * Kostis Anagnostopoulos
* Contributing Authors:
    * Giorgos Fontaras for the physics, policy and admin support.




.. _before-indices:

Footnotes
=========

.. _before-footer:

.. [#] Bastiaan Zuurendonk, Maarten Steinbuch(2005):
        "Advanced Fuel Consumption and Emission Modeling using Willans line scaling techniques for engines",
        *Technische Universiteit Eindhoven*, 2005, 
        Department Mechanical Engineering, Dynamics and Control Technology Group,
        http://alexandria.tue.nl/repository/books/612441.pdf

