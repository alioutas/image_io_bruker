#%%
# import packages
import os
import numpy as np
import json
import csv
import tifffile as tif
import struct
import gzip
import pandas as pd

# From Bruker
#############################################################
# Read a particle.dat or particle.dat.gz file and return
# the column names and data table
# -----------------------------------------------------------
def readParticleFile(file_path):
    if not os.path.exists(file_path):
        print("Error: Could not find file " + file_path)
        return [],[]

    file_name, file_ext = os.path.splitext(file_path)
    file_content = None
    
    if file_ext == ".dat":
        with open(file_path, 'rb') as f:
            file_content = f.read()
    elif file_ext == ".gz":
        with gzip.open(file_path, 'rb') as f:
            file_content = f.read()
    else:
        print("Error: Invalid file format!")
        return [],[]

    if file_content is None or len(file_content) == 0:
        print("Error: Empty file!")
        return [],[]

    # read header

    # first 4 bytes is the number of columns
    num_cols = struct.unpack("<i", file_content[:4])[0]
    print("Found ", num_cols, " columns")
    byte_curr = 4
    
    column_names = []
    column_bytes = []
    column_types = []
    # For each column we process header info
    # 4 byte int entry for the name string length
    # variable bytes for the name string
    # 4 byte int for the number of bytes in the particle data for this column
    for c in range(num_cols):
        # get length of name string in bytes
        col_len = struct.unpack("<i", file_content[byte_curr:(byte_curr+4)])[0]
        byte_curr = byte_curr + 4

        # get name string
        col_name = struct.unpack("<"+str(col_len)+"s", file_content[byte_curr:(byte_curr+col_len)])[0]
        column_names.append(col_name)
        byte_curr = byte_curr + col_len

        # get particle data byte count
        col_bytes = struct.unpack("<i", file_content[byte_curr:(byte_curr+4)])[0]
        column_bytes.append(col_bytes)
        byte_curr = byte_curr + 4
        
        # infer type from number of bytes and name
        if col_bytes == 1: # 1 byte is always a boolean
            column_types.append("<?")
        elif col_bytes == 4: # 4 bytes is always an int
            column_types.append("<i")
        elif col_bytes == 8 and col_name == b'frame-timestamp': #b'frame-timestamp': # 8 bytes can be a int64 if it is a timestamp
            column_types.append("<q")
        elif col_bytes == 8: # typically 8 bytes is a double
            column_types.append("<d")
        else:
            print("Error: Detected unknown byte length for column ", col_name, "!")  # colName -- col_name
            return [],[]

    # read particles
    print("Reading particles...")
    # collect data in one large 2D array
    point_data = [[] for i in range(num_cols)]

    # Go until we run out of lines
    while byte_curr < len(file_content):
        for c in range(num_cols):
            val = struct.unpack(column_types[c], file_content[byte_curr:(byte_curr+column_bytes[c])])[0]
            point_data[c].append(val)
            byte_curr = byte_curr + column_bytes[c]

    num_points = len(point_data[0])
    print("Read ", num_points, " points")

    dff = pd.DataFrame(point_data).transpose()
    dff.columns = column_names
    dff.columns = [x.decode('utf-8').replace("b'", "'" ) for x in dff.columns.values.tolist()]
    dff = dff.infer_objects()

    return dff


def writeParticleFile(df, file_path, file_ext=".dat"):

    #############################################################
    # Save a dataframe (df) to the file_path 
    # as a binary particle.dat or particle.dat.gz file
    # Author: Antonios Lioutas
    # -----------------------------------------------------------

    num_cols = len(df.columns)
    file_content = bytearray()

    # Add number of columns to file content
    file_content.extend(struct.pack("<i", num_cols))

    column_types = []

    # Add header info for each column
    for column in df.columns:
        # Convert column name to bytes
        col_name = column.encode('utf-8')

        # Add length of column name to file content
        col_len = len(col_name)
        file_content.extend(struct.pack("<i", col_len))

        # Add column name to file content
        file_content.extend(col_name)

        # Get column type and determine number of bytes and struct format string
        col_type = df[column].dtype
        if col_type == np.bool:
            col_bytes = 1
            col_type_str = "<?"
        elif col_type == np.int32 or col_type == np.int64:
            col_bytes = 4
            col_type_str = "<i"
        elif col_type == np.float64:
            col_bytes = 8
            col_type_str = "<d"
        else:
            raise ValueError("Unsupported data type!")

        # Add number of bytes to file content
        file_content.extend(struct.pack("<i", col_bytes))

        # Store column type string for later use
        column_types.append(col_type_str)

    # Add particle data
    for _, row in df.iterrows():
        for column, col_type_str in zip(df.columns, column_types):
            file_content.extend(struct.pack(col_type_str, row[column]))

    # Write to disk as .dat or .dat.gz
    if file_ext == ".dat":
        with open(file_path, 'wb') as f:
            f.write(file_content)
    elif file_ext == ".gz":
        with gzip.open(file_path, 'wb') as f:
            f.write(file_content)
    else:
        print("Error: Invalid file format!")

