## TO BE RUN FROM SELF_DIR
#
## USER_DEFS
ver=0.0.4


mydir=${0%/*}
cd $mydir

if  python -c "import sys; exit('32bit' in sys.executable)"; then  # logic inversed!
    bits=64
else
    bits=32
fi
echo "Building for ${bits}bits..."



## Filenames.
#
declare -A bit_siffixes
bit_suffixes=( ['32']='32' ['64']='-amd64' )
bit_suff="${bit_suffixes[$bits]}"
build_folder="build/exe.win${bit_suff}-3.3"
prog_folder="build/evilometer_exe${bits}-$ver"
prog_tar_folder="evilometer_exe${bits}-$ver"
prog_tar="${prog_folder}.tar"
prog_zip="${prog_tar}.lz"


rm $build_folder
python setup.py build_exe

rm $prog_folder
mv $build_folder $prog_folder
tar -C build -cv $prog_tar_folder -f $prog_tar

#rm $prog_zip
#lzip -vv -9 -k $prog_tar
