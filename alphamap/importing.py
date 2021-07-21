# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/Importing.ipynb (unless otherwise specified).

__all__ = ['read_file', 'extract_rawfile_unique_values', 'import_spectronaut_data', 'import_maxquant_data',
           'convert_ap_mq_mod', 'import_alphapept_data', 'import_data']

# Cell
import os
import pandas as pd

def read_file(
    file: str,
    column_names: list
) -> pd.DataFrame:
    """Load a specified columns of the file as a pandas dataframe.

    Args:
        file (str): The name of a file.
        column_names (list): The list of three columns that should be extracted from the file.

    Returns:
        pd.DataFrame: A pandas dataframe with all the data stored in the specified columns.
    """
    file_ext = os.path.splitext(file)[-1]
    if file_ext=='.csv':
        sep=','
    elif file_ext=='.tsv':
        sep='\t'
    elif file_ext=='.txt':
        sep='\t'

    with open(file) as filelines:
        i = 0
        pos = 0
        for l in filelines:
            i += 1
            l = l.split(sep)
            raw = l.index(column_names[0])
            prot = l.index(column_names[1])
            seq = l.index(column_names[2])
            if i>0:
                break

    with open(file) as filelines:
        raws = []
        prots = []
        seqs = []
        for l in filelines:
            l = l.split(sep)
            raws.append(l[raw])
            prots.append(l[prot])
            seqs.append(l[seq])

    res = pd.DataFrame({column_names[0]:raws[1:],
             column_names[1]:prots[1:],
             column_names[2]:seqs[1:]})

    return res


def extract_rawfile_unique_values(
    file: str
) -> list:
    """Extract the unique raw file names either from "R.FileName" (Spectronaut output) or "Raw file" (MaxQuant output) column.

    Args:
        file (str): The name of a file.

    Returns:
        list: A sorted list of unique raw file names from the file.
    """
    file_ext = os.path.splitext(file)[-1]
    if file_ext == '.csv':
        sep = ','
    elif file_ext in ['.tsv', '.txt']:
        sep = '\t'

    with open(file) as filelines:
        i = 0
        filename_col_index = int()
        filename_data = []

        for l in filelines:
            l = l.split(sep)
            # just do it for the first line
            if i == 0:
                try:
                    filename_col_index = l.index('R.FileName')
                except ValueError as err:
                    filename_col_index = l.index('Raw file')
            else:
                filename_data.append(l[filename_col_index])
            i += 1

        unique_filenames = set(filename_data)

    sorted_unique_filenames = sorted(list(unique_filenames))
    return sorted_unique_filenames

# Cell
import pandas as pd
import re
from typing import Union

def import_spectronaut_data(
    file: str,
    sample: Union[str, list, None] = None
) -> pd.DataFrame:
    """Import peptide level data from Spectronaut.

    Args:
        file (str): The name of a file.
        sample (Union[str, list, None]): The unique raw file name(s) to filter the original file. Defaults to None. In this case data for all raw files will be extracted.

    Returns:
        pd.DataFrame: A pandas dataframe containing information about:
            - all_protein_ids (str)
            - modified_sequence (str)
            - naked_sequence (str)
    """
    spectronaut_columns = ["PEP.AllOccurringProteinAccessions","EG.ModifiedSequence","R.FileName"]

    data = read_file(file, spectronaut_columns)

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
    input_data = input_data.dropna()
    input_data = input_data.drop_duplicates().reset_index(drop=True)
    return input_data

# Cell
import pandas as pd
import re

def import_maxquant_data(
    file: str,
    sample: Union[str, list, None] = None
) -> pd.DataFrame:
    """Import peptide level data from MaxQuant.

    Args:
        file (str): The name of a file.
        sample (Union[str, list, None]): The unique raw file name(s) to filter the original file. Defaults to None. In this case data for all raw files will be extracted.

    Returns:
        pd.DataFrame: A pandas dataframe containing information about:
            - all_protein_ids (str)
            - modified_sequence (str)
            - naked_sequence (str)
    """
    mq_columns = ["Proteins","Modified sequence","Raw file"]

    data = read_file(file, mq_columns)

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
    input_data = input_data.dropna() # remove missing values
    input_data = input_data.drop_duplicates().reset_index(drop=True)
    return input_data

# Cell
import re

def convert_ap_mq_mod(
    sequence:str
) -> str:
    """Convert AlphaPept style modifications into MaxQuant style modifications.

    Args:
        sequence (str): The peptide sequence with modification in an AlphaPept style.

    Returns:
        str: The peptide sequence with modification in a similar to MaxQuant style.
    """
    modif_convers_dict = {
        '[oxM]': '[Oxidation (M)]', '[oxP]': '[Oxidation (P)]', '[oxMP]': '[Oxidation (MP)]',
        '[a]': '[Acetyl (Protein N-term)]', '[aK]': '[Acetyl (K)]',
        '[am]': '[Amidated (C-term)]', '[deamN]': '[Deamidation (N)]', '[deamNQ]': '[Deamidation (NQ)]',
        '[p]': '[Phospho (STY)]',
        '[pgE]': '[Glu->pyro-Glu]', '[pgQ]': '[Gln->pyro-Glu]',
        '[c]': '[Cys-Cys]'
    }
    mods = re.findall('[a-z0-9]+', sequence)
    if mods:
        for mod in mods:
            i = sequence.index(mod)
            sequence = sequence.replace(mod, '')
            if mod == 'ox':
                if sequence[i:i+2] == 'MP':
                    add_aa = 'MP'
                    sequence = sequence[:i+2] + f'[{mod}{add_aa}]' + sequence[i+2:]
                else:
                    add_aa = sequence[i]
                    sequence = sequence[:i+1] + f'[{mod}{add_aa}]' + sequence[i+1:]
            elif mod == 'a':
                if i == 0:
                    sequence = f'[{mod}]' + sequence[i:]
                elif sequence[i] == 'K':
                    sequence = sequence[:i+1] + f'[{mod}{sequence[i]}]' + sequence[i+1:]
            elif mod == 'am':
                if i == len(sequence)-1:
                    sequence = sequence + f'[{mod}]'
            elif mod == 'deam':
                if sequence[i:i+2] == 'NQ':
                    add_aa = 'NQ'
                    sequence = sequence[:i+2] + f'[{mod}{add_aa}]' + sequence[i+2:]
                else:
                    add_aa = sequence[i]
                    sequence = sequence[:i+1] + f'[{mod}{add_aa}]' + sequence[i+1:]
            elif mod == 'p':
                sequence = sequence[:i+1] + f'[{mod}]' + sequence[i+1:]
            elif mod == 'pg':
                add_aa = sequence[i]
                sequence = sequence[:i+1] + f'[{mod}{add_aa}]' + sequence[i+1:]
            elif mod == 'c':
                sequence = sequence[:i+1] + f'[{mod}]' + sequence[i+1:]
        for k,v in modif_convers_dict.items():
            if k in sequence:
                sequence = sequence.replace(k, v)
    return sequence

# Cell
import pandas as pd

def import_alphapept_data(
    file: str,
    sample: Union[str, list, None] = None
) -> pd.DataFrame:
    """Import peptide level data from AlphaPept.

    Args:
        file (str): The name of a file.
        sample (Union[str, list, None]): The unique raw file name(s) to filter the original file. Defaults to None. In this case data for all raw files will be extracted.

    Returns:
        pd.DataFrame: A pandas dataframe containing information about:
            - all_protein_ids (str)
            - modified_sequence (str)
            - naked_sequence (str)
    """
    ap_columns = ["protein_group", "sequence", "shortname"]

    data = pd.read_csv(file, usecols=ap_columns)
    # TO DO: add later the file reading using read_file function. For now it doesn't work for the protein groups that should be split later

    if sample:
        if isinstance(sample, list):
            data_sub = data[data["shortname"].isin(sample)]
            data_sub = data_sub[["protein_group", "sequence"]]
        elif isinstance(sample, str):
            data_sub = data[data["shortname"] == sample]
            data_sub = data_sub[["protein_group", "sequence"]]
    else:
        data_sub = data[["protein_group", "sequence"]]

    data_sub = data_sub[~data_sub.sequence.str.contains('_decoy')]

    # get modified sequence
    modif_seq = data_sub.apply(lambda row: convert_ap_mq_mod(row.sequence), axis=1)
    data_sub['modified_sequence'] = modif_seq.values

    # get a list of proteins_id
    proteins = data_sub.apply(lambda row: ";".join([_.split('|')[1] for _ in row.protein_group.split(',')]), axis=1)
    data_sub['all_protein_ids'] = proteins.values

    # get naked sequence
    nak_seq = data_sub.apply(lambda row: ''.join([_ for _ in row.sequence if _.isupper()]), axis=1)
    data_sub['naked_sequence'] = nak_seq.values

    input_data = data_sub[["all_protein_ids", "modified_sequence", "naked_sequence"]]
    input_data = input_data.dropna() # remove missing values
    input_data = input_data.drop_duplicates().reset_index(drop=True)
    return input_data

# Cell
import pandas as pd
import re
from io import StringIO
import os

def import_data(
    file :str,
    sample: Union[str, list, None] = None,
    verbose: bool = True,
    dashboard: bool = False
) -> pd.DataFrame:
    """Import peptide level data. Depending on available columns in the provided file, the function calls other specific functions for each tool.

    Args:
        file (str): The name of a file.
        sample (Union[str, list, None]): The unique raw file name(s) to filter the original file. Defaults to None. In this case data for all raw files will be extracted.
        verbose (bool): if True, print the type of input that is used. Defaults to True.
        dashboard (bool): If True, the function is used for the dashboard output (StringIO object). Defaults to False.

    Raises:
        TypeError: If the input data format is unknown.

    Returns:
        pd.DataFrame: A pandas dataframe containing information about:
            - all_protein_ids (str)
            - modified_sequence (str)
            - naked_sequence (str)
    """
    if dashboard:
        file = StringIO(str(file, "utf-8"))

    file_ext = os.path.splitext(file)[-1]
    if file_ext=='.csv':
        sep=','
    elif file_ext=='.tsv':
        sep='\t'
    elif file_ext=='.txt':
        sep='\t'

    with open(file) as filelines:
        i = 0
        pos = 0
        for l in filelines:
            i += 1
            l = l.split(sep)
            if i>0:
                break

        uploaded_data_columns = set(l)
        input_info = file
    if set(["Proteins","Modified sequence","Raw file"]).issubset(uploaded_data_columns):
        if verbose:
            print("Import MaxQuant input")
        data = import_maxquant_data(input_info, sample=sample)
    elif set(["PEP.AllOccurringProteinAccessions","EG.ModifiedSequence","R.FileName"]).issubset(uploaded_data_columns):
        if verbose:
            print("Import Spectronaut input")
        data = import_spectronaut_data(input_info, sample=sample)
    elif set(["protein_group", "sequence", "shortname"]).issubset(uploaded_data_columns):
        if verbose:
            print("Import AlphaPept input")
        data = import_alphapept_data(input_info, sample=sample)
    else:
        raise TypeError(f'Input data format for {file} not known.')
    return data