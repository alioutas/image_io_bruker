# Read and write .dat files produced by Bruker Vutara352 and VXL microscopes

This code allows to read .dat files from Bruker Super-Resolution microscopes (Vutara352 and VXL), perform custom analysis in python (not part of this repo), and finally transform a pandas dataframe back to a .dat file format that can be read and visualize with Bruker SRX software.

## Explanation of available Functions:

### Loading the read and write functions

```{python}
from image_io_functions import readParticleFile, writeParticleFile
```

### Read a dat binary file as a pandas dataframe

*how to run example*

```{python}
df = readParticleFile("PATH/TO/particles.dat")
```

### Save a pandas dataframe as a binary .dat

*how to run example*

```{python}
writeParticleFile(df, "PATH/TO/particles.dat", file_ext=".dat")
```

