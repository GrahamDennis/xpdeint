#!/bin/bash
# Exit if anything fails
set -o errexit

# Run by typing ./create_release_version.sh in admin/ directory
cd ..
XMDS_VERSION=`python setup.py --version`

# Create Version.py with subversion revision information
cd xpdeint
./version.sh
cd ..

if [ -d admin/staging ]; then 
	rm -rf admin/staging;
fi

mkdir -p admin/staging/

# Create a clean checkout
svn export . admin/staging/xmds-${XMDS_VERSION}
# Copy Version.py with revision information
cp xpdeint/Version.py admin/staging/xmds-${XMDS_VERSION}/xpdeint

cd admin/staging/xmds-${XMDS_VERSION}
cd admin/userdoc-source
# Build html docs
make html
# Copy built HTML docs into staging/ dir for later transfer to website
cp -r ../../documentation ../../../
# Build LaTeX docs
make latex
cd ../../documentation/latex
# Actually make the PDF
make all-pdf
cd ../..

# Compile Cheetah templates
make

# Clean up after waf
make distclean

# Before we put everything into the tarball, remove files and
# directories that don't need to be distributed to the user.

# Don't need admin/ folder. It's just for developers, who will
# use the SVN repo and can get it from there.
rm -rf admin/

# There may be an FFTW directory if the linux installer was used
rm -rf fftw*

# debian/ and bin/ directories are not needed by the end user
rm -rf debian/
rm -rf bin/

# The html docs have been built, so don't need the doctrees or _sources
rm -rf documentation/doctrees/
rm -rf documentation/_sources/

# Finally package everything up into the tarball
cd ..
tar -czf xmds-${XMDS_VERSION}.tar.gz xmds-${XMDS_VERSION}

echo
echo To release to sourceforge, execute the following commands.
echo scp staging/xmds-${XMDS_VERSION}.tar.gz username@frs.sf.net:/home/frs/project/x/xm/xmds/
echo "cd staging; scp -r documentation/* username@web.sf.net:/home/project-web/xmds/htdocs/"
echo

