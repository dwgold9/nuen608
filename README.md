# NUEN-608 Design Project

## Software
1. OpenMC


## Summary
This repository contains the neutronics simulation and analysis for a NUEN-608 design project. The course is for fast-spectra nuclear reactors. The aim is to devise a space reactor with fast characteristics. 

## Status
> Work-in-Progress

## Setup
### Create Environment
```bash
conda env create -f environment.yml --platform osx-64     # Mac Silicon
```

### Compile OpenMC4d
```bash
cd $HOME/Documents/research/developer/openmc4d 
rm -rf build && mkdir build && cd build 
cmake .. -DCMAKE_INSTALL_PREFIX=$CONDA_PREFIX
make -j4 
make install   

python -m pip install -e /Users/davisgolden/Documents/research/developer/openmc4d
```

## Tutorial

### Execute Simulation
>>> python simulate.py foo_study

To overwrite:

>>> python simulate.py foo_study --force

To resume:

>>> python simulate.py foo_study --resume

# Post-Process
>>> python analyze.py foo_study