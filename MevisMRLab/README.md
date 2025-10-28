# MevisMRLab v1.0.2

## Installation
1. MevisMRLab was tested to work with Python 3.11 and above. Please make sure that at least Python 3.11 is installed on your machine. 
2. Several packages must be installed in order to use the software. Therefore, from terminal execute the following pip commands:
```bash
pip install numba 
pip install matplotlib 
pip install mpl-interactions 
pip install mrzerocore 
pip install PyQt5
pip install pypulseq==1.4.2
pip install pyvista
pip install pyvistaqt
```

## Execution
The software is executed using the main file "MevisMrLab_run.py" from within the MevisMRLab folder. Simply execute it with your python interpreter (e.g. from the MevisMRLab directory: python3 MevisMrLab_run.py). Note that the first initilization of MevisMRLab might take a bit as it will download phantom data for the simulation. 

## Authors and acknowledgment
Matthias Guenther (matthias.guenther@mevis.fraunhofer.de)

## Inlcuded Third Party Libraries
The software is based on the following third party libraries which fall under the following licening conditions:
1. MRZero Core (GNU AFFERO GENERAL PUBLIC LICENSE Version 3, 19 November 2007) Link: https://github.com/MRsources/MRzero-Core
2. PyPulseq (GNU AFFERO GENERAL PUBLIC LICENSE Version 3, 19 November 2007) Link: https://github.com/imr-framework/pypulseq
3. PyQt (GNU GENERAL PUBLIC LICENSE Version 3) Link: https://www.riverbankcomputing.com/static/Docs/PyQt5/
4. PyTorch (BSD 3-Clause License) Link: https://github.com/pytorch/pytorch
5. Numba (BSD 2-Clause "Simplified" License) Link: https://github.com/numba/numba/tree/main
6. mpl-interactions (BSD 3-Clause License) Link: https://pypi.org/project/mpl-interactions/ 
7. pyvista (MIT Clause License) Link: https://github.com/pyvista/pyvista
8. pyvistaqt (MIT Clause License) Link: https://github.com/pyvista/pyvistaqt </br>

Detailed information about licenses is given in the third_party_licenses folder. 
