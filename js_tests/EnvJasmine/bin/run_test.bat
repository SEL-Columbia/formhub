echo off

set PWD=%cd%
set SPEC=%~f1
cd %~f0\..
set ROOT=%cd%\..
java -Duser.timezone="US/Eastern" -Dfile.encoding=utf-8 -jar "%ROOT%\lib\rhino\js.jar" "%ROOT%\lib\envjasmine.js" --environment="WIN" --rootDir="%ROOT%" "%SPEC%"
cd %PWD%
