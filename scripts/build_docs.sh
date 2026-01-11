#!/bin/bash
# Build Sphinx documentation

set -e

cd docs

# Clean previous builds
make clean

# Build HTML documentation
make html

echo "Documentation built successfully!"
echo "Open docs/_build/html/index.html in your browser to view"
