echo off

set PWD=%cd%
cd %~f0\..
set ROOT=%cd%\..
set dirList = dir /b/r/s %ROOT%\specs
java -Duser.timezone="US/Eastern" -jar "%ROOT%\lib\rhino\js.jar" "%ROOT%\lib\envjasmine.js" --environment="WIN" --rootDir="%ROOT%" %dirList%
cd %PWD%
