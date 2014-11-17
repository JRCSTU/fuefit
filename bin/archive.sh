#!bash
mydir="${0%/*}"
treish=HEAD
ver=`python -m fuefit.__main__ --version | grep .`
gitpack="fuefit_${ver}-git"
docpack="fuefit_${ver}-doc"

cd $mydir/..

python setup.py build_sphinx

rm -f \
    "dist/${gitpack}.zip" \
    "dist/${docpack}.zip"
mkdir -p dist
echo "Creating arhive: dist/${gitpack}.zip"
git archive -9 --prefix="$gitpack/" --output="dist/${gitpack}.zip"  ${treish} 

echo "Creating arhive: dist/${docpack}.zip"
( 
    cd docs/_build &&
    ln -sf html "${docpack}" && 
    zip -9 -r  "../../dist/${docpack}.zip"  "${docpack}" 
) 

python setup.py sdist bdist_wheel 
