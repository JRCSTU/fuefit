treish=HEAD
ver=`python -m fuefit.cmdline --version | grep .`
prog="fuefit-$ver"
rm -f "${prog}.tgz" "${prog}.zip"
git archive --prefix=$prog/ --output="${prog}.tgz" $treish 
git archive --prefix=$prog/ --output="${prog}.zip" $treish 
