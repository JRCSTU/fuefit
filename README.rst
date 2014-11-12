################################################
*fuefit* fits engine-maps on physical parameters
################################################
|dev-status| |build-status| |docs-status| |pypi-status| |downloads-count| |github-issues|

:Release:       |version|
:Home:          https://github.com/ankostis/fuefit
:Documentation: https://fuefit.readthedocs.org/
:PyPI:          https://pypi.python.org/pypi/fuefit
:Copyright:     2014 European Commission (`JRC-IET <http://iet.jrc.ec.europa.eu/>`_)
:License:       `EUPL 1.1+ <https://joinup.ec.europa.eu/software/page/eupl>`_

*Fuefit* is a python package that calculates fitted fuel-maps from measured engine data-points based on coefficients with physical meaning.


.. _before-intro:

Introduction
============

Overview
--------
The *Fuefit* calculator performs the following:

1) Accepts **fuel-consumption engine data points** as input
   (RPM, Power and Fuel-Consumption or equivalent quantities such as CM, PME/Torque and PMF/FC). 
2) Uses those points to **fit the following coefficients**:

  .. math::
  
        a, b, c, a2, b2, loss0, loss2
        
  using the following formula:[#]_

  .. (a + b*cm + c*cm**2)*pmf + (a2 + b2*cm)*pmf**2 + loss0 + loss2*cm**2
  .. math::
   
        \mathbf{pme} = (a + b\times{\mathbf{cm}} + c\times{\mathbf{cm^2}})\times{\mathbf{pmf}} + 
                (a2 + b2\times{\mathbf{cm}})\times{\mathbf{pmf^2}} + loss0 + loss2\times{\mathbf{cm^2}}

3) **Spits-out the input engine-points** according to the fitting, and optionally plots a mesh (grid) 
   with the engine-map.

     
An "execution" or a "run" of a calculation along with the most important pieces of data 
are depicted in the following diagram::


                  .----------------------------.                    .-----------------------------.
                 /        Input-Model         /                    /        Output-Model         /
                /----------------------------/                    /-----------------------------/
               / +--engine                  /                    / +--engine                   /
              /  |  +--...                 /                    /  |  +--fc_map_coeffs        /
             /   +--params                /  ____________      /   +--measured_eng_points    /
            /    |  +--...               /  |            |    /    |    n   p  fc  pme  ... /
           /     +--measured_eng_points /==>| Calculator |==>/     |  ... ... ...  ...     /
          /          n    p    fc      /    |____________|  /      +--fitted_eng_points   /
         /          --  ----  ---     /                    /       |    n    p   fc      /
        /            0   0.0    0    /                    /        |  ...  ...  ...     /
       /           600  42.5   25   /                    /         +--mesh_eng_points  /
      /           ...    ...  ...  /                    /               n    p   fc   /
     /                            /                    /              ...  ...  ...  /
    '----------------------------'                    '-----------------------------'


The *Input & Output Model* are trees of strings and numbers, assembled with:

* sequences,
* dictionaries,
* :class:`pandas.DataFrame`,
* :class:`pandas.Series`, and
* URI-references to other model-trees (TODO).


Apart from various engine-characteristics under ``/engine`` the table-columns such as `capacity` and `p_rated`, 
the table under ``/measured_eng_points`` must contain *at least* one column 
from each of the following categories (column-headers are case-insensitive):

1. Engine-speed::

    N        (1/min)
    N_norm   (1/min)    : normalized against N_idle + (N_rated - N_idle)
    CM       (m/sec)    : Mean Piston speed

2. Work-capability::

    P        (kW)
    P_norm   (kW)       : normalized against P_MAX
    T        (Nm)
    PME      (bar)

3. Fuel-consumption::

    FC       (g/h)
    FC_norm  (g/h)      : normalized against P_MAX
    PMF      (bar)


.. [#] Bastiaan Zuurendonk, Maarten Steinbuch(2005):
        "Advanced Fuel Consumption and Emission Modeling using Willans line scaling techniques for engines",
        *Technische Universiteit Eindhoven*, 2005, 
        Department Mechanical Engineering, Dynamics and Control Technology Group,
        http://alexandria.tue.nl/repository/books/612441.pdf



Quick-start
-----------
On *Windows*/*OS X*, it is recommended to use one of the scientific Python distributions:

* `WinPython <http://winpython.github.io/>`_ (*Windows* only),
* `Anaconda <http://docs.continuum.io/anaconda/>`_ or `miniconda <http://conda.pydata.org/miniconda.html>`_
* `Canopy <https://www.enthought.com/products/canopy/>`_,

as they already include *numpy/scipy*, *pandas* and *win32* native-libraries. 

Assuming you have a working python-environment, open a *command-shell*, 
(in *Windows* use :program:`cmd.exe` BUT ensure :program:`python.exe` is in its :envvar:`PATH`), 
you can try the following commands: 

:Install:
    .. code-block:: console

        $ pip install fuefit
        $ fuefit --winmenus                         ## Adds StartMenu-items, Windows only.
  
    See: :ref:`Install`
    
:Cmd-line:
    .. code-block:: console

        $ fuefit --version
        0.0.5
        
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
Fuefit-|version| runs on Python-3.3+, and it is distributed on `Wheels <https://pypi.python.org/pypi/wheel>`_.

.. Note::
    This project depends on the *numpy/scipy*, *pandas* and *win32* python-packages
    that themselfs require the use of *C* and *Fortran* compilers to build from sources. 
    To avoid this hussle, you can choose instead a self-wrapped python distribution like
    *Anaconda/minoconda*, *Winpython*, or *Canopy*.

    .. Tip::
        * You can try to install the `Anaconda <http://docs.continuum.io/anaconda/>`_ 
          cross-platform distribution (*Windows*, *Linux* and *OS X*), or its lighter-weight alternative, 
          `miniconda <http://conda.pydata.org/miniconda.html>`_.
    
          On this environment you will need to install this project's dependencies manually 
          using a combination of :program:`conda` and :program:`pip` commands.
          See :file:`miniconda_requirements.txt`, and peek at the example script commands in :file:`.travis.yaml`.
        
        * Under *Windows* you can try the self-wrapped `WinPython <http://winpython.github.io/>`_ distribution,
          a higly active project, that can even compile native libraries using an installations of *Visual Studio*, 
          if available (required for instance when upgrading ``numpy/scipy``, ``pandas`` or ``matplotlib`` with :command:`pip`).
                
          Just remember to **Register your WinPython installation** after installation and 
          **add your installation into** :envvar:`PATH` (see :doc:`faq`):
          
            * To register it, go to :menuselection:`Start menu --> All Programs --> WinPython --> WinPython ControlPanel`, and then
              :menuselection:`Options --> Register Distribution` .
            * For the path, add or modify the registry string-key :samp:`[HKEY_CURRENT_USER\Environment] "PATH"`.
      
        * Check for alternative installation instructions on the various python environments and platforms
          at `the pandas site <http://pandas.pydata.org/pandas-docs/stable/install.html>`_.


Before installing it, make sure that there are no older versions left over.  
So run this command until you cannot find any project installed:

.. code-block:: console

    $ pip uninstall fuefit                                      ## Use `pip3` if both python-2 & 3 are in PATH.
    
    
You can install the project directly from the |pypi|_ the "standard" way, 
by typing the :command:`pip` in the console:

.. code-block:: console

    $ pip install fuefit


* If you want to install a *pre-release* version (the version-string is not plain numbers, but 
  ends with ``alpha``, ``beta.2`` or something else), use additionally :option:`--pre`.

* If you want to upgrade an existing instalation along with all its dependencies, 
  add also :option:`--upgrade` (or :option:`-U` equivalently), but then the build might take some 
  considerable time to finish.  Also there is the possibility the upgraded libraries might break 
  existing programs(!) so use it with caution, or from within a |virtualenv|_. 

* To install an older version issue the console command:
  
  .. code-block:: console
  
      $ pip install fuefit=1.1.1                    ## Use `--pre` if version-string has a build-suffix.

* To install it for different Python environments, repeat the procedure using 
  the appropriate :program:`python.exe` interpreter for each environment.

* .. Tip::
    To debug installation problems, you can export a non-empty :envvar:`DISTUTILS_DEBUG` 
    and *distutils* will print detailed information about what it is doing and/or 
    print the whole command line when an external program (like a C compiler) fails.


After a successful installation, it is important that you check which version is visible in your :envvar:`PATH`:

.. code-block:: console

    $ fuefit --version
    0.0.5



Installing from sources
-----------------------
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

    $ pip install -r WinPython_requirements.txt -U .


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

    $ coda install `cat miniconda_requirements.txt`
    $ pip install lmfit             ## Workaround lmfit-py#149 
    $ python setup.py install
    $ fuefit --version
    0.0.5



.. _before-usage:

Usage
=====
.. _excel-usage:

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
    model item (see `Python usage`_ below,).

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
    '0.0.5'

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

Development team
----------------

* Author:
    * Kostis Anagnostopoulos
* Contributing Authors:
    * Giorgos Fontaras for the testing, physics, policy and admin support.




.. _before-indices:

Indices
=======

.. _before-footer:

.. glossary::

    CM
        Mean piston speed (measure for the engines operating speed)
    
    PME
        Mean effective pressure (the engines ability to produce mechanical work)
    
    PMF
        Available mean effective pressure (the maximum mean effective pressure which could be produced if n = 1)
        
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

