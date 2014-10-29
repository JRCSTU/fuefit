treish=HEAD
ver=`python -m fuefit.cmdline --version | grep .`
prog="fuefit.git-$ver"
echo Arhives: "dist/${prog}.XXX"

rm -f "dist/${prog}.tgz" "dist/${prog}.zip"
mkdir -p dist
git archive --prefix=$prog/ --output="dist/${prog}.tgz" $treish 
git archive --prefix=$prog/ --output="dist/${prog}.zip" $treish 

python setup.py sdist bdist_wheel 
