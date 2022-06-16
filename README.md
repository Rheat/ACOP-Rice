# ACOP-Rice
> A modified version of the AquaCrop-OSPy specific to rice simulation
> 
> There are two main modification.
> 1. Adding a new irrigation method specific to paddy rice.
    IrrMethod=6: Irrigation is triggered if water depth drops below a specified threshold (or several thresholds representing different major crop growth stages).
     `TDcriteria` : `pandas.DataFrame` : DataFrame containing time and depth criteria
> 2. Making the height of bunds changeable.
     `zBund` : `pandas.DataFrame` : DataFrame containing dates and Bund height(m)
    

## Install

`pip install aquacrop`

If you encounter this error:

`“ModuleNotFoundError: No module named ‘aquacrop.solution_aot’”`

then you must also run 

`python -m aquacrop.solution` 

after installation to compile the internal aquacrop functions.

## Quickstart

A number of tutorials has been created (more to be added in future) to help users jump straight in and run their first simulation. Run these tutorials instantly on Google Colab:


1.   <a href=https://colab.research.google.com/github/aquacropos/aquacrop/blob/master/docs/notebooks/AquaCrop_OSPy_Notebook_1.ipynb>Running an AquaCrop-OSPy model</a>
2.   <a href=https://colab.research.google.com/github/aquacropos/aquacrop/blob/master/docs/notebooks/AquaCrop_OSPy_Notebook_2.ipynb>Estimation of irrigation water demands</a>
3.   <a href=https://colab.research.google.com/github/aquacropos/aquacrop/blob/master/docs/notebooks/AquaCrop_OSPy_Notebook_3.ipynb>Optimisation of irrigation management strategies</a>
4.  <a href=https://colab.research.google.com/github/aquacropos/aquacrop/blob/master/docs/notebooks/AquaCrop_OSPy_Notebook_4.ipynb>Projection of climate change impacts</a>

