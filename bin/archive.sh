treish=HEAD
ver=`python -m fuefit.__main__ --version | grep .`
prog="fuefit.git_$ver"
echo Arhives: "dist/${prog}.XXX"

rm -f "dist/${prog}.zip"
mkdir -p dist
git archive --prefix=$prog/ --output="dist/${prog}.zip" $treish 

python setup.py sdist bdist_wheel 
