################################################
*fuefit* fits engine-maps on physical parameters
################################################
|dev-status| |build-status| |docs-status| |pypi-status| |downloads-count| |github-issues|

:Release:       |version|
:Documentation: https://fuefit.readthedocs.org/
:Source:        https://github.com/ankostis/fuefit
:PyPI repo:     https://pypi.python.org/pypi/fuefit
:Keywords:      automotive, car, cars, consumption, engine, engine-map, fitting, fuel, vehicle, vehicles
:Copyright:     2014 European Commission (`JRC-IET <http://iet.jrc.ec.europa.eu/>`_)
:License:       `EUPL 1.1+ <https://joinup.ec.europa.eu/software/page/eupl>`_

*Fuefit* is a python package that calculates fitted fuel-maps from measured engine data-points based on coefficients with physical meaning.


.. _before-intro:

Introduction
============

Overview
--------
The *Fuefit* calculator  was developed to apply a statistical fit on measured engine fuel consumption data 
(engine map). This allows the reduction of the information necessary to describe an engine fuel map 
from several hundred points to seven statistically calculated parameters, with limited loss of information. 

More specifically this software works like that:

1) **Accepts engine data as input**, constituting of triplets of RPM, Power and Fuel-Consumption 
   or equivalent quantities eg mean piston speed (CM), brake mean effective pressure (BMEP) or Torque, 
   fuel mean effective pressure (PMF). 

2) **Fits the provided input** to the following formula [#]_ [#]_ [#]_:

  .. BMEP = (a + b*CM + c*CM**2)*PMF + (a2 + b2*CM)*PMF**2 + loss0 + loss2*CM**2
  .. math::
   
        \mathbf{BMEP} = (a + b\times{\mathbf{CM}} + c\times{\mathbf{CM^2}})\times{\mathbf{PMF}} + 
                (a2 + b2\times{\mathbf{CM}})\times{\mathbf{PMF^2}} + loss0 + loss2\times{\mathbf{CM^2}}

3) **Recalculates and (optionally) plots engine-maps** based on the coefficients 
   that describe the fit: 

   .. math::
  
        a, b, c, a2, b2, loss0, loss2


An "execution" or a "run" of a calculation along with the most important pieces of data 
are depicted in the following diagram::


                  .----------------------------.                    .-----------------------------.
                 /        Input-Model         /                    /    Output(Fitted)-Model     /
                /----------------------------/                    /-----------------------------/
               / +--engine                  /                    / +--engine                   /
              /  |  +--...                 /                    /  |  +--fc_map_coeffs        /
             /   +--params                /  ____________      /   +--measured_eng_points    /
            /    |  +--...               /  |            |    /    |    n   p  fc  bmep ... /
           /     +--measured_eng_points /==>| Calculator |==>/     |  ... ... ...  ...     /
          /          n    p    fc      /    |____________|  /      +--fitted_eng_points   /
         /          --  ----  ---     /                    /       |    n    p   fc      /
        /            0   0.0    0    /                    /        |  ...  ...  ...     /
       /           600  42.5   25   /                    /         +--mesh_eng_points  /
      /           ...    ...  ...  /                    /               n    p   fc   /
     /                            /                    /              ...  ...  ...  /
    '----------------------------'                    '-----------------------------'


Apart from various engine-characteristics under ``/engine`` the table-columns such as `capacity` and `p_rated`, 
the table under ``/measured_eng_points`` must contain *at least* one column 
from each of the following categories (column-headers are case-insensitive):

1. Engine-speed::

    N        [1/min]
    N_norm   [-]        : where N_norm = (N – N_idle) / (N_rated-N_idle)
    CM       [m/sec]

2. Load-Power-capability::

    P        [kW]
    P_norm   [-]        : where P_norm = P/P_MAX
    T        [Nm]
    BMEP     [bar]

3. Fuel-consumption::

    FC       [g/h]
    FC_norm  [g/KWh]    : where FC_norm = FC[g/h] / P_MAX [kW]
    PMF      [bar]


The *Input & fitted data-model* described above are trees of strings and numbers, assembled with:

* sequences,
* dictionaries,
* :class:`pandas.DataFrame`,
* :class:`pandas.Series`.


.. [#] Bastiaan Zuurendonk, Maarten Steinbuch(2005):
    "Advanced Fuel Consumption and Emission Modeling using Willans line scaling techniques for engines",
    *Technische Universiteit Eindhoven*, 2005, 
    Department Mechanical Engineering, Dynamics and Control Technology Group,
    http://alexandria.tue.nl/repository/books/612441.pdf
.. [#] Yuan Zou, Dong-ge Li, and Xiao-song Hu (2012): 
    "Optimal Sizing and Control Strategy Design for Heavy Hybrid Electric Truck", 
    *Mathematical Problems in Engineering* Volume 2012, 
    Article ID 404073, 15 pages doi:10.1155/2012/404073
.. [#] Xi Wei (2004): 
    "Modeling and control of a hybrid electric drivetrain for optimum fuel economy, performance and driveability", 
    Dissertation Presented in Partial Fulfillment of the Requirements 
    for the Degree Doctor of Philosophy in the Graduate School of The Ohio State University



Quick-start
-----------
The program runs on **Python-3.3+** and requires *numpy/scipy*, *pandas* and *win32* libraries 
along with their native backends to be installed.
  
On *Windows*/*OS X*, it is recommended to use one of the following "scientific" python-distributions, 
as they already include the native libraries and can install without administrative priviledges: 

* `WinPython <http://winpython.github.io/>`_ (*Windows* only),
* `Anaconda <http://docs.continuum.io/anaconda/>`_,
* `Canopy <https://www.enthought.com/products/canopy/>`_,


Assuming you have a working python-environment, open a *command-shell* 
(in *Windows* use :program:`cmd.exe` BUT ensure :program:`python.exe` is in its :envvar:`PATH`) 
and try the following *console-commands*: 

:Install:
    .. code-block:: console

        $ pip install fuefit
        $ fuefit --winmenus                         ## Adds StartMenu-items, Windows only.
  
    See: :doc:`install`
    
:Cmd-line:
    .. code-block:: console

        $ fuefit --version
        0.0.6
        
        $ fuefit --help
        ...
        
        ## Change-directory into the `fuefit/test/` folder in the  *sources*.
        $ fuefit -I FuelFit_real.csv header+=0 \
            -I ./FuelFit.xlsx sheetname+=0 header@=None names:='["p","n","fc"]' \
            -I ./engine.csv file_frmt=SERIES model_path=/engine header@=None \
            -m /engine/fuel=petrol \
            -m /params/plot_maps@=True \
            -O full_results_model.json \
            -O fit_coeffs.csv model_path=/engine/fc_map_coeffs   index?=false \
            -O t1.csv model_path=/measured_eng_points   index?=false \
            -O t2.csv model_path=/mesh_eng_points       index?=false \

    See: :ref:`cmd-line-usage`
    
:Excel:
    .. code-block:: console

        $ fuefit --excelrun                                             ## Windows & OS X only
    
    See: :ref:`excel-usage`

:Python-code: 
    .. doctest::
    
        >>> import pandas as pd
        >>> from fuefit import datamodel, processor, test
        
        >>> inp_model = datamodel.base_model()
        >>> inp_model.update({...})                                     ## See "Python Usage" below.        # doctest: +SKIP
        >>> inp_model['engine_points'] = pd.read_csv('measured.csv')    ## Pandas can read Excel, matlab, ... # doctest: +SKIP
        >>> datamodel.set_jsonpointer(inp_model, '/params/plot_maps', True)
        
        >>> datamodel.validade_model(inp_model, additional_properties=False)            # doctest: +SKIP 
        
        >>> out_model = processor.run(inp_model)                                        # doctest: +SKIP
        
        >>> print(datamodel.resolve_jsonpointer(out_model, '/engine/fc_map_coeffs'))    # doctest: +SKIP
        a            164.110667
        b           7051.867419
        c          63015.519469
        a2             0.121139
        b2          -493.301306
        loss0      -1637.894603
        loss2   -1047463.140758
        dtype: float64    

    See: :ref:`python-usage`

.. Tip::
    The commands beginning with ``$``, above, imply a *Unix* like operating system with a *POSIX* shell
    (*Linux*, *OS X*). Although the commands are simple and easy to translate in its *Windows* counterparts, 
    it would be worthwile to install `Cygwin <https://www.cygwin.com/>`_ to get the same environment on *Windows*.
    If you choose to do that, include also the following packages in the *Cygwin*'s installation wizard::

        * git, git-completion
        * make, zip, unzip, bzip2
        * openssh, curl, wget

    But do not install/rely on cygwin's outdated python environment.



.. _before-install:

Install
=======
Fuefit-|version| runs on **Python-3.3+**, and it is distributed on `Wheels <https://pypi.python.org/pypi/wheel>`_.

.. Note::
    This project depends on the *numpy/scipy*, *pandas* and *win32* python-packages
    that themselfs require the use of *C* and *Fortran* compilers to build from sources. 
    To avoid this hussle, you can choose instead a self-wrapped python distribution like
    *Anaconda/minoconda*, *Winpython*, or *Canopy*.

    .. Tip::
        * Under *Windows* you can try the self-wrapped `WinPython <http://winpython.github.io/>`_ distribution,
          a higly active project, that can even compile native libraries using an installations of *Visual Studio*, 
          if available (required for instance when upgrading ``numpy/scipy``, ``pandas`` or ``matplotlib`` with :command:`pip`).
                
          Just remember to **Register your WinPython installation** after installation and 
          **add your installation into** :envvar:`PATH` (see :doc:`faq`):
          
            * To register it, go to :menuselection:`Start menu --> All Programs --> WinPython --> WinPython ControlPanel`, and then
              :menuselection:`Options --> Register Distribution` .
            * For the path, add or modify the registry string-key :samp:`[HKEY_CURRENT_USER\Environment] "PATH"`.
      
        * An alternative scientific python-environment is the `Anaconda <http://docs.continuum.io/anaconda/>`_ 
          cross-platform distribution (*Windows*, *Linux* and *OS X*), or its lighter-weight alternative, 
          `miniconda <http://conda.pydata.org/miniconda.html>`_.
    
          On this environment you will need to install this project's dependencies manually 
          using a combination of :program:`conda` and :program:`pip` commands.
          See :file:`requirements/miniconda.txt`, and peek at the example script commands in :file:`.travis.yaml`.
        
        * Check for alternative installation instructions on the various python environments and platforms
          at `the pandas site <http://pandas.pydata.org/pandas-docs/stable/install.html>`_.

    See :doc:`install` for more details

Before installing it, make sure that there are no older versions left over.  
So run this console-command (using :program:`cmd.exe` in windows) until you cannot find 
any project installed:

.. code-block:: console

    $ pip uninstall fuefit                                      ## Use `pip3` if both python-2 & 3 are in PATH.
    
    
You can install the project directly from the |pypi|_ the "standard" way, 
by typing the :command:`pip` in the console:

.. code-block:: console

    $ pip install fuefit


* If you want to install a *pre-release* version (the version-string is not plain numbers, but 
  ends with ``alpha``, ``beta.2`` or something else), use additionally :option:`--pre`.

* If you want to upgrade an existing installation along with all its dependencies, 
  add also :option:`--upgrade` (or :option:`-U` equivalently), but then the build might take some 
  considerable time to finish.  Also there is the possibility the upgraded libraries might break 
  existing programs(!) so use it with caution, or from within a |virtualenv|_. 

* To install an older version issue the console-command:
  
  .. code-block:: console
  
      $ pip install fuefit=1.1.1                    ## Use `--pre` if version-string has a build-suffix.

* To install it for different Python environments, repeat the procedure using 
  the appropriate :program:`python.exe` interpreter for each environment.

* .. Tip::
    To debug installation problems, you can export a non-empty :envvar:`DISTUTILS_DEBUG` 
    and *distutils* will print detailed information about what it is doing and/or 
    print the whole command line when an external program (like a C compiler) fails.


After a successful installation, it is important that you check which version is visible in your :envvar:`PATH`,
so type this console-command:

.. code-block:: console

    $ fuefit --version
    0.0.6



Installing from sources (for advanced users familiar with *git*)
----------------------------------------------------------------
If you download the sources you have more options for installation.
There are various methods to get hold of them:

* Download and extract a `release-snapshot from github <https://github.com/ankostis/fuefit/releases>`_.
* Download and extract a ``sdist`` *source* distribution from |pypi|_.
* Clone the *git-repository* at *github*.  Assuming you have a working installation of `git <http://git-scm.com/>`_
  you can fetch and install the latest version of the project with the following series of commands:
  
  .. code-block:: console
  
      $ git clone "https://github.com/ankostis/fuefit.git" fuefit.git
      $ cd fuefit.git
      $ python setup.py install                                 ## Use `python3` if both python-2 & 3 installed.
  

When working with sources, you need to have installed all libraries that the project depends on. 
Particularly for the latest *WinPython* environments (*Windows* / *OS X*) you can install 
the necessary dependencies with: 

.. code-block:: console

    $ pip install -r requirements/execution.txt .


The previous command installs a "snapshot" of the project as it is found in the sources.
If you wish to link the project's sources with your python environment, install the project 
in `development mode <http://pythonhosted.org/setuptools/setuptools.html#development-mode>`_:

.. code-block:: console

    $ python setup.py develop


.. Note:: This last command installs any missing dependencies inside the project-folder.


Anaconda install
----------------
The installation to *Anaconda* (ie *OS X*) works without any differences from the ``pip`` procedure 
described so far.
 
To install it on *miniconda* environment, you need to install first the project's *native* dependencies 
(numpy/scipy), so you need to download the sources (see above). 
Then open a *bash-shell* inside them and type the following commands: 

.. code-block:: console

    $ coda install `cat requirements/miniconda.txt`
    $ pip install lmfit             ## Workaround lmfit-py#149 
    $ python setup.py install
    $ fuefit --version
    0.0.6



.. _before-usage:

Usage
=====
.. _excel-usage:

Excel usage
-----------
.. Attention:: Excel-integration requires Python 3 and *Windows* or *OS X*!

In *Windows* and *OS X* you may utilize the `xlwings <http://xlwings.org/quickstart/>`_ library 
to use Excel files for providing input and output to the program.

To create the necessary template-files in your current-directory, type this console-command:

.. code-block:: console

     $ fuefit --excel
     

Type :samp:`fuefit --excel {file_path}` if you want to specify a different destination path.

In *windows*/*OS X* you can type ``fuefit --excelrun`` and the files will be created in your home-directory 
and the Excel will immediately open them.


What the above commands do is to create 2 files:

:file:`FuefitExcelRunner{#}.xlsm`
    The python-enabled excel-file where input and output data are written, as seen in the screenshot below:
    
    .. image:: docs/xlwings_screenshot.png
        :scale: 50%
        :alt: Screenshot of the `FuefitExcelRunner.xlsm` file.
    
    After opening it the first tie, enable the macros on the workbook, select the python-code at the left and click 
    the :menuselection:`Run Selection as Pyhon` button; one sheet per vehicle should be created.

    The excel-file contains additionally appropriate *VBA* modules allowing you to invoke *Python code* 
    present in *selected cells* with a click of a button, and python-functions declared in the python-script, below,
    using the `mypy` namespace. 
    
    To add more input-columns, you need to set as column *Headers* the *json-pointers* path of the desired 
    model item (see :ref:`python-usage` below,).

:file:`FuefitExcelRunner{#}.py`   
    Python functions used by the above xls-file for running a batch of experiments.  
    
    The particular functions included reads multiple vehicles from the input table with various  
    vehicle characteristics and/or experiment coefficients, and then it adds a new worksheet containing 
    the cycle-run of each vehicle . 
    Of course you can edit it to further fit your needs.


.. Note:: You may reverse the procedure described above and run the python-script instead:

    .. code-block:: console
    
         $ python FuefitExcelRunner.py
    
    The script will open the excel-file, run the experiments and add the new sheets, but in case any errors occur, 
    this time you can debug them, if you had executed the script through `LiClipse <http://www.liclipse.com/>`__, 
    or *IPython*! 


Some general notes regarding the python-code from excel-cells:

* An elaborate syntax to reference excel *cells*, *rows*, *columns* or *tables* from python code, and 
  to read them as :class:`pandas.DataFrame` is utilized by the Excel .
  Read its syntax at :func:`~fuefit.excel.FuefitExcelRunner.resolve_excel_ref`.
* On each invocation, the predefined VBA module `pandalon` executes a dynamically generated python-script file
  in the same folder where the excel-file resides, which, among others, imports the "sister" python-script file.
  You can read & modify the sister python-script to import libraries such as 'numpy' and 'pandas', 
  or pre-define utility python functions.
* The name of the sister python-script is automatically calculated from the name of the Excel-file,
  and it must be valid as a python module-name.  Therefore:
  * Do not use non-alphanumeric characters such as spaces(` `), dashes(`-`) and dots(`.`) on the Excel-file.
  * If you rename the excel-file, rename also the python-file, or add this python :samp:`import <old_py_file> as mypy``
* On errors, a log-file is written in the same folder where the excel-file resides, 
  for as long as **the message-box is visible, and it is deleted automatically after you click 'ok'!**
* Read http://docs.xlwings.org/quickstart.html


.. _cmd-line-usage:

Cmd-line usage
--------------
Example command:

.. code-block:: console

      fuefit -v\
        -I fuefit/test/FuelFit.xlsx sheetname+=0 header@=None names:='["p","rpm","fc"]' \
        -I fuefit/test/engine.csv file_frmt=SERIES model_path=/engine header@=None \
        -m /engine/fuel=petrol \
        -O ~t2.csv model_path=/fitted_eng_points    index?=false \
        -O ~t2.csv model_path=/mesh_eng_points      index?=false \
        -O ~t.csv model_path= -m /params/plot_maps@=True


.. _python-usage:

Python usage
------------
The most powerful way to interact with the project is through a python :abbr:`REPL (Read-Eval-Print Loop)`.
So fire-up a :command:`python` or :command:`ipython` shell and first try to import the project just to check its version:

.. doctest::

    >>> import fuefit

    >>> fuefit.__version__                ## Check version once more.
    '0.0.6'

    >>> fuefit.__file__                   ## To check where it was installed.         # doctest: +SKIP
    /usr/local/lib/site-package/fuefit-...


.. Tip:
    The use of :program:`ipython` interpreter is preffered over plain :program:`python` since the former 
    provides various user-friendly facilities, such as pressing :kbd:`Tab` for receiving completions on commands, or 
    adding `?` or `??` at the end of commands to view their help *docstrings* and read their source-code.
    
    Additionally you can <b>copy any python listing from this tutorial starting with ``>>>`` and ``...``</b> 
    and paste it directly into the :program:`ipython` interpreter; the prefixes will be removed automatically.  
    But in :command:`python` you have to remove them yourself.


If the version was as expected, take the **base-model** and extend it with your engine-data 
(strings and numbers): 

.. code-block:: pycon

    >>> from fuefit import datamodel, processor

    >>> inp_model = datamodel.base_model()
    >>> inp_model.update({
    ...     "engine": {
    ...         "fuel":     "diesel",
    ...         "p_max":    95,
    ...         "n_idle":   850,
    ...         "n_rated":  6500,
    ...         "stroke":   94.2,
    ...         "capacity": 2000,
    ...         "bore":     None,       ##You do not have to include these,
    ...         "cylinders": None,      ##  they are just for displaying some more engine properties.
    ...     }
    ... })

    >>> import pandas as pd
    >>> df = pd.read_excel('fuefit/test/FuelFit.xlsx', 0, header=None, names=["n","p","fc"])
    >>> inp_model['measured_eng_points'] = df


For information on the accepted model-data, check both its :term:`JSON-schema` at :func:`~fuefit.datamodel.model_schema`,
and the :func:`~fuefit.datamodel.base_model`:

Next you have to *validate* it against its *JSON-schema*:

.. code-block:: pycon

    >>> datamodel.validate_model(inp_model, additional_properties=False)


If validation is successful, you may then feed this model-tree to the :mod:`fuefit.processor`,
to get back the results:

.. code-block:: pycon

    >>> out_model = processor.run(inp_model)

    >>> print(datamodel.resolve_jsonpointer(out_model, '/engine/fc_map_coeffs'))
    a            164.110667
    b           7051.867419
    c          63015.519469
    a2             0.121139
    b2          -493.301306
    loss0      -1637.894603
    loss2   -1047463.140758
    dtype: float64

    >>> print(out_model['fitted_eng_points'].shape)
    (262, 11)


.. Hint::
    You can always check the sample code at the Test-cases and in the cmdline tool :mod:`fuefit.__main__`.


Fitting Parameterization
^^^^^^^^^^^^^^^^^^^^^^^^
The `'lmfit' fitting library <http://lmfit.github.io/lmfit-py/>`_ can be parameterized by 
setting/modifying various input-model properties under ``/params/fitting/``.

In particular under ``/params/fitting/coeffs/`` you can set a dictionary of *coefficient-name* -->
:class:`lmfit.parameters.Parameter` such as ``min/max/value``,
as defined by the *lmfit* library (check the default props under :func:`fuefit.datamodel.base_model()` and the
example columns in the *ExcelRunner*).

.. Seealso::
    http://lmfit.github.io/lmfit-py/parameters.html#Parameters




.. _before-contribute:

Contribute
==========

This project is hosted in **github**. 
To provide feedback about bugs and errors or questions and requests for enhancements,
use `github's Issue-tracker <https://github.com/ankostis/fuefit/issues>`_.



Sources & Dependencies
----------------------
To get involved with development, you need a POSIX environment to fully build it
(*Linux*, *OSX*, or *Cygwin* on *Windows*). 

.. Admonition:: Liclipse IDE
    :class: note

    Within the sources there are two sample files for the comprehensive
    `LiClipse IDE <https://brainwy.github.io/liclipse/>`_:
    
    * :file:`eclipse.project` 
    * :file:`eclipse.pydevproject` 
    
    Remove the `eclipse` prefix, (but leave the dot(``.``)) and import it as "existing project" from 
    Eclipse's `File` menu.
    
    Another issue is due to the fact that LiClipse contains its own implementation of *Git*, *EGit*,
    which badly interacts with unix *symbolic-links*, such as the :file:`docs/docs`, and it detects
    working-directory changes even after a fresh checkout.  To workaround this, Right-click on the above file
    :menuselection:`Properties --> Team --> Advanced --> Assume Unchanged` 


Development team
----------------
* Kostis Anagnostopoulos (software design & implementation)
* Georgios Fontaras (methodology inception, engineering support & validation)

Contributing Authors
^^^^^^^^^^^^^^^^^^^^^
* Stefanos Tsiakmakis
* Biagio Ciuffo
* Alessandro Marotta

Authors would like to thank experts of the SGS group for providing useful feedback.


.. _before-indices:

Indices
=======

.. _before-footer:

.. glossary::

    CM
        `Mean Piston Speed <https://en.wikipedia.org/wiki/Mean_piston_speed>`_, 
        a measure for the engines operating speed [m/sec]
    
    BMEP
        `Brake Mean Effective Pressure <https://en.wikipedia.org/wiki/Mean_effective_pressure>`_, 
        a valuable measure of an engine's capacity to do work that is independent of engine displacement) [bar]
    
    PMF
        *Available Mean Effective Pressure*, the maximum mean effective pressure calculated based on 
        the energy content of the fuel [bar]
        
    JSON-schema
        The `JSON schema <http://json-schema.org/>`_ is an `IETF draft <http://tools.ietf.org/html/draft-zyp-json-schema-03>`_
        that provides a *contract* for what JSON-data is required for a given application and how to interact
        with it.  JSON Schema is intended to define validation, documentation, hyperlink navigation, and
        interaction control of JSON data.
        You can learn more about it from this `excellent guide <http://spacetelescope.github.io/understanding-json-schema/>`_,
        and experiment with this `on-line validator <http://www.jsonschema.net/>`_.

    JSON-pointer
        JSON Pointer(:rfc:`6901`) defines a string syntax for identifying a specific value within
        a JavaScript Object Notation (JSON) document. It aims to serve the same purpose as *XPath* from the XML world,
        but it is much simpler.


.. _before-replacements:

.. |virtualenv| replace::  *virtualenv* (isolated Python environment)
.. _virtualenv: http://docs.python-guide.org/en/latest/dev/virtualenvs/

.. |pypi| replace:: *PyPi* repo
.. _pypi: https://pypi.python.org/pypi/fuefit

.. |build-status| image:: https://travis-ci.org/ankostis/fuefit.svg
    :alt: Integration-build status
    :scale: 100%
    :target: https://travis-ci.org/ankostis/fuefit/builds

.. |docs-status| image:: https://readthedocs.org/projects/fuefit/badge/
    :alt: Documentation status
    :scale: 100%
    :target: https://readthedocs.org/builds/fuefit/

.. |pypi-status| image::  https://pypip.in/v/fuefit/badge.png
    :target: https://pypi.python.org/pypi/fuefit/
    :alt: Latest Version in PyPI

.. |python-ver| image:: https://pypip.in/py_versions/fuefit/badge.svg
    :target: https://pypi.python.org/pypi/fuefit/
    :alt: Supported Python versions

.. |dev-status| image:: https://pypip.in/status/fuefit/badge.svg
    :target: https://pypi.python.org/pypi/fuefit/
    :alt: Development Status

.. |downloads-count| image:: https://pypip.in/download/fuefit/badge.svg?period=week
    :target: https://pypi.python.org/pypi/fuefit/
    :alt: Downloads

.. |github-issues| image:: http://img.shields.io/github/issues/ankostis/fuefit.svg
    :target: https://github.com/ankostis/fuefit/issues
    :alt: Issues count

