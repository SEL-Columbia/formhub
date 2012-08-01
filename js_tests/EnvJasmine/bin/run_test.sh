#!/usr/bin/env bash

cd "`dirname \"$0\"`"
PWD=$(pwd)

CMD="java -Duser.timezone=\"US/Eastern\" -Dfile.encoding=utf-8 -jar \"$PWD/../lib/rhino/js.jar\" \"$PWD/../lib/envjasmine.js\" --environment=\"UNIX\" --rootDir=\"$PWD/..\" "

for (( i=1 ; i < $#+1 ; i=$i+1 )) do
    CMD="$CMD \"${!i}\""
done

eval $CMD
