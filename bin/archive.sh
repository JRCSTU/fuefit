treish=HEAD
ver=`python -m fuefit.cmdline --version | grep .`
prog="fuefit-$ver"
echo Arhives: "dist/${prog}.git.XXX"

rm -f "dist/${prog}.git.tgz" "dist/${prog}.git.zip"
mkdir -p dist
git archive --prefix=$prog/ --output="dist/${prog}.git.tgz" $treish 
git archive --prefix=$prog/ --output="dist/${prog}.git.zip" $treish 

python setup.py sdist 
python setup.py bdist_win32
python setup.py bdist_win64
