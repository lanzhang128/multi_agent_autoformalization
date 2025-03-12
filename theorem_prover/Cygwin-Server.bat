@echo off

set HOME=%HOMEDRIVE%%HOMEPATH%
set PATH=%ISABELLE_DIRPATH%\bin;%PATH%
set LANG=en_US.UTF-8
set CHERE_INVOKING=true
set args=%*

"%ISABELLE_DIRPATH%\contrib\cygwin\bin\bash" --login -c 'isabelle %args%'
