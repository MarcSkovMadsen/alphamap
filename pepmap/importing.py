# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/Importing.ipynb (unless otherwise specified).

__all__ = ['import_spectronaut_data', 'import_maxquant_data', 'import_data']

# Cell
import pandas as pd
import re

def import_spectronaut_data(file, sample=None):
    """
    Function to import peptide level data from Spectronaut
    """
    spectronaut_columns = ["PEP.AllOccurringProteinAccessions","EG.ModifiedSequence","R.FileName"]
    data = pd.read_csv(file, sep=None, engine='python', usecols=spectronaut_columns)

    if sample:
        if isinstance(sample, list):
            data_sub = data[data["R.FileName"].isin(sample)]
            data_sub = data_sub[["PEP.AllOccurringProteinAccessions","EG.ModifiedSequence"]]
        elif isinstance(sample, str):
            data_sub = data[data["R.FileName"] == sample]
            data_sub = data_sub[["PEP.AllOccurringProteinAccessions","EG.ModifiedSequence"]]
    else:
        data_sub = data[["PEP.AllOccurringProteinAccessions","EG.ModifiedSequence"]]

    # get modified sequence
    mod_seq = data_sub.apply(lambda row: re.sub('_','',row["EG.ModifiedSequence"]), axis=1)
    data_sub = data_sub.assign(modified_sequence=mod_seq.values)
    # get naked sequence
    nak_seq = data_sub.apply(lambda row: re.sub(r'\[.*?\]','',row["modified_sequence"]), axis=1)
    data_sub = data_sub.assign(naked_sequence=nak_seq.values)
    data_sub = data_sub.rename(columns={"PEP.AllOccurringProteinAccessions": "all_protein_ids"})
    input_data = data_sub[["all_protein_ids","modified_sequence","naked_sequence"]]
    input_data = input_data.drop_duplicates().reset_index(drop=True)
    return input_data

# Cell
import pandas as pd
import re

def import_maxquant_data(file, sample=None):
    """
    Function to import peptide level data from MaxQuant
    """
    mq_columns = ["Proteins","Modified sequence","Raw file"]
    data = pd.read_csv(file, sep='\t', usecols=mq_columns)

    if sample:
        if isinstance(sample, list):
            data_sub = data[data["Raw file"].isin(sample)]
            data_sub = data_sub[["Proteins","Modified sequence"]]
        elif isinstance(sample, str):
            data_sub = data[data["Raw file"] == sample]
            data_sub = data_sub[["Proteins","Modified sequence"]]
    else:
        data_sub = data[["Proteins","Modified sequence"]]
    # get modified sequence
    mod_seq = data_sub.apply(lambda row: re.sub('_','',row["Modified sequence"]), axis=1)
    data_sub = data_sub.assign(modified_sequence=mod_seq.values)

    # replace outer () with []
    mod_seq_replaced = data_sub.apply(lambda row: re.sub(r'\((.*?\(.*?\))\)',r'[\1]',row["modified_sequence"]), axis=1)
    data_sub = data_sub.assign(modified_sequence=mod_seq_replaced.values)

    # get naked sequence
    nak_seq = data_sub.apply(lambda row: re.sub(r'\[.*?\]','',row["modified_sequence"]), axis=1)
    data_sub = data_sub.assign(naked_sequence=nak_seq.values)
    data_sub = data_sub.rename(columns={"Proteins": "all_protein_ids"})
    input_data = data_sub[["all_protein_ids","modified_sequence","naked_sequence"]]
    input_data = input_data.drop_duplicates().reset_index(drop=True)
    return input_data

# Cell
import pandas as pd
import re
from io import StringIO

def import_data(file, sample=None, verbose=True, dashboard=False):
    if dashboard:
        uploaded_data_columns = set(pd.read_csv(StringIO(str(file, "utf-8")), nrows=0, sep=None, engine='python').columns)
        input_info = StringIO(str(file, "utf-8"))
    else:
        uploaded_data_columns = set(pd.read_csv(file, nrows=0, sep=None, engine='python').columns)
        input_info = file
    if set(["Proteins","Modified sequence","Raw file"]).issubset(uploaded_data_columns):
        if verbose:
            print("Import MaxQuant input")
        data = import_maxquant_data(input_info)
    elif set(["PEP.AllOccurringProteinAccessions","EG.ModifiedSequence","R.FileName"]).issubset(uploaded_data_columns):
        if verbose:
            print("Import Spectronaut input")
        data = import_spectronaut_data(input_info, sample=sample)
    else:
        raise TypeError(f'Input data format for {file} not known.')
    return data