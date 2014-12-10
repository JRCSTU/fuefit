==========================
Frequently Asked Questions
==========================

General
=======


Can I copy/extend it?  What is its License, in practical terms?
---------------------------------------------------------------
I'm not a lawyer, but in a broad view, the core algorithm of the project is "copylefted" with
the *EUPL-1.1+ license*, and it includes files from other "non-copyleft" open source licenses like
*MIT MIT License* and *Apache License*, appropriately marked as such.  So in an nutshell, you can study it,
copy it, modify or extend it, and distrbute it, as long as you always distribute the sources of your changes.


Technical
=========

I followed the instructions but i still cannot install/run/get *X*.  What now?
------------------------------------------------------------------------------
If you have no previous experience in python, setting up your environment and installing a new project
is a demanding, but manageable, task.  Here is a checklist of things that might go wrong:

* Did you send each command to the **appropriate shell/interpreter**?

  You should enter sample commands starting ``$`` into your *shell* (:program:`cmd` or :program:`bash`),
  and those starting with ``>>>`` into the *python-interpreter*
  (but don't include the previous symbols and/or the *output* of the commands).


* Is **python contained in your PATH** ?

  To check it, type `python` in your console/command-shell prompt and press :kbd:`[Enter]`.
  If nothing happens, you have to inspect :envvar:`PATH` and modify it accordingly to include your 
  python-installation. 
  
  * Under *Windows* type ``path`` in your command-shell prompt.
    To change it, run :program:`regedit.exe` and  modify (or add if not already there) the `PATH` string-value 
    inside the following *registry-setting*::
    
      HKEY_CURRENT_USER\Environment\
    
    You need to logoff and logon to see the changes.

    Note that *WinPython* **does not modify your path!** if you have registed it, so you definetely have to 
    perform the the above procedure yourself.
  
    
  * Under *Unix* type ``echo $PATH$`` in your console. 
    To change it, modify your "rc' files, ie: :file:`~/.bashrc` or :file:`~/.profile`.
  

* Is the correct **version of python** running? Of **fuefit**??

  Certain commands such as :command:`pip` come in 2 different versions *python-2 & 3*
  (:command:`pip2` and :command:`pip3`, respectively).  Most programs report their version-infos
  with :option:`--version`.
  Use :option:`--help` if this does not work.


* Have you **upgraded/downgraded the project** into a more recent/older version?

  This project is still in development, so the names of data and functions often differ from version to version.
  Check the :doc:`CHANGES` for point that you have to be aware of when upgrading.


* Did you try **verbose reporting** for the command-line tool?

    * Use :option:`-v` of :option:`--vv` to receive log-messages.
    * Use :option:`-d` to enable debug-checks.


* Did you `search <https://github.com/ankostis/fuefit/issues>`_ whether **a similar issue** has already been reported?

* Did you **ask google** for an answer??

* If the above suggestions still do not work, feel free to **open a new issue** and ask for help.
  Write down your platform (Windows, OS X, Linux), your exact python distribution
  and version, and include the *print-out of the failed command along with its error-message.*

  This last step will improve the documentation and help others as well.


Discussion
==========
.. raw:: html

    <div id="disqus_thread"></div>
    <script type="text/javascript">
        /* * * CONFIGURATION VARIABLES: EDIT BEFORE PASTING INTO YOUR WEBPAGE * * */
        var disqus_shortname = 'fuefit';
        var disqus_identifier = 'site.faq';
        var disqus_title = 'fuefit: Frequently Asked Questions';

        /* * * DON'T EDIT BELOW THIS LINE * * */
        (function() {
            var dsq = document.createElement('script'); dsq.type = 'text/javascript'; dsq.async = true;
            dsq.src = '//' + disqus_shortname + '.disqus.com/embed.js';
            (document.getElementsByTagName('head')[0] || document.getElementsByTagName('body')[0]).appendChild(dsq);
        })();
    </script>
    <noscript>Please enable JavaScript to view the <a href="http://disqus.com/?ref_noscript">comments powered by Disqus.</a></noscript>
