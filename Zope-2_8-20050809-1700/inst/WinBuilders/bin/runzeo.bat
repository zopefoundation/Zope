@set PYTHON=C:\Program Files\Zope-2.7.0-b1+\bin\python.exe
@set ZOPE_HOME=C:\Program Files\Zope-2.7.0-b1+\lib\python
@set INSTANCE_HOME=C:\ZEO-Instance
@set CONFIG_FILE=%INSTANCE_HOME%\etc\zeo.conf
@set PYTHONPATH=%ZOPE_HOME%
@set ZEO_RUN=%ZOPE_HOME%\ZEO\runzeo.py
"%PYTHON%" "%ZEO_RUN%" -C "%CONFIG_FILE%" %1 %2 %3 %4 %5
