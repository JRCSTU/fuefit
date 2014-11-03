files=`find . -name '*.py' -o -name '*.txt' -o -name '*.sh' |grep -v /build/ |grep -v /wltc.egg |grep -v /tmp`
wc $files
