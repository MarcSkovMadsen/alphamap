# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/Importing.ipynb (unless otherwise specified).

__all__ = ['read_file', 'extract_rawfile_unique_values', 'import_spectronaut_data', 'import_maxquant_data',
           'convert_ap_mq_mod', 'import_alphapept_data', 'convert_diann_mq_mod', 'import_diann_data',
           'convert_fragpipe_mq_mod', 'import_fragpipe_data', 'import_data']

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

    Raises:
        NotImplementedError: if a specified file has not a .csv, .txt or .tsv extension.
        ValueError: if any of the specified columns is not in the file.

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
    else:
        raise NotImplementedError("The selected filetype isn't supported. Please specify a file with a .csv, .txt or .tsv extension.")
    with open(file) as filelines:
        i = 0
        pos = 0
        for l in filelines:
            i += 1
            l = l.split(sep)
            try:
                raw = l.index(column_names[0])
                prot = l.index(column_names[1])
                seq = l.index(column_names[2])
            except:
                raise ValueError('The list of specified column names cannot be extracted from the file.')
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
    """Extract the unique raw file names from "R.FileName" (Spectronaut output), "Raw file" (MaxQuant output),
    "shortname" (AlphaPept output) or "Run" (DIA-NN output) column or from the "Spectral Count" column from the
    combined_peptide.tsv file without modifications for the FragPipe.

    Args:
        file (str): The name of a file.

    Raises:
        ValueError: if a column with the unique raw file names is not in the file.

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
        filename_col_index = None
        filename_data = []

        for l in filelines:
            l = l.split(sep)
            # just do it for the first line
            if i == 0:
                for col in ['R.FileName', 'Raw file', 'Run', 'shortname']:
                    if col in l:
                        filename_col_index = l.index(col)
                        break
                if not isinstance(filename_col_index, int):
                    # to check the case with the FragPipe peptide.tsv file when we don't have the info about the experiment name
                    if ("Assigned Modifications" in "".join(l)) and ("Protein ID" in "".join(l)) and ("Peptide" in "".join(l)):
                        return []
                    # to check the case with the FragPipe combined_peptide.tsv file when the experiment name is included in the "Spectral Count" column
                    elif ("Sequence" in "".join(l)) and ("Assigned Modifications" in "".join(l)) and ("Protein ID" in "".join(l)):
                        return sorted(list(set([col.replace('_', '').replace(' Spectral Count', '') for col in l if 'Spectral Count' in col])))
                    else:
                        raise ValueError('A column with the raw file names is not in the file.')
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
        pd.DataFrame: A pandas dataframe containing information about: all_protein_ids (str), modified_sequence (str), naked_sequence (str)
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
from typing import Union
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
        pd.DataFrame: A pandas dataframe containing information about: all_protein_ids (str), modified_sequence (str), naked_sequence (str)
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
    # TODO: add more AP modifications
    modif_convers_dict = {
        'ox': '[Oxidation ({})]',
        'a': '[Acetyl ({})]',
        'am': '[Amidated ({})]',
        'deam': '[Deamidation ({})]',
        'p': '[Phospho ({})]',
        'pg': '[{}->pyro-Glu]',
        'c': '[Cys-Cys]'
    }
    mods = re.findall('[a-z0-9]+', sequence)
    if mods:
        for mod in mods:
            posit = re.search(mod, sequence)
            i = posit.start()
            if i == 0 and mod == 'a':
                add_aa = 'N-term'
            elif posit.end() == len(sequence) - 1 and mod == 'am':
                add_aa = sequence[posit.end()]
                sequence = sequence.replace(mod + add_aa, add_aa + mod, 1)
                add_aa = 'C-term'
            else:
                add_aa = sequence[posit.end()]
                sequence = sequence.replace(mod + add_aa, add_aa + mod, 1)

            if mod == 'ox':
                if add_aa == 'M':
                    add_aa = 'M'
                elif add_aa in 'MP':
                    add_aa = 'MP'
            elif mod == 'deam':
                if add_aa in 'NQ':
                    add_aa = 'NQ'
            elif mod == 'p':
                if add_aa in 'STY':
                    add_aa = 'STY'
            elif mod == 'pg':
                if add_aa == 'E':
                    add_aa = 'Glu'
                elif add_aa == 'Q':
                    add_aa = 'Gln'

            if mod in modif_convers_dict.keys():
                sequence = sequence.replace(mod, modif_convers_dict.get(mod).format(add_aa), 1)
    return sequence

# Cell
import pandas as pd
from typing import Union

def import_alphapept_data(
    file: str,
    sample: Union[str, list, None] = None
) -> pd.DataFrame:
    """Import peptide level data from AlphaPept.

    Args:
        file (str): The name of a file.
        sample (Union[str, list, None]): The unique raw file name(s) to filter the original file. Defaults to None. In this case data for all raw files will be extracted.

    Returns:
        pd.DataFrame: A pandas dataframe containing information about: all_protein_ids (str), modified_sequence (str), naked_sequence (str)
    """
    ap_columns = ["protein_group", "sequence", "shortname"]

    data = pd.read_csv(file, usecols=ap_columns)
    # TODO: add later the file reading using read_file function. For now it doesn't work for the protein groups that should be split later

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
import re

def convert_diann_mq_mod(
    sequence:str
) -> str:
    """Convert DIA-NN style modifications into MaxQuant style modifications.

    Args:
        sequence (str): The peptide sequence with modification in an AlphaPept style.

    Returns:
        str: The peptide sequence with modification in a similar to DIA-NN style.
    """

    modif_convers_dict = {
        '(UniMod:1)': '[Acetyl ({})]',
        '(UniMod:2)': '[Amidated ({})]',
        '(UniMod:4)': '[Carbamidomethyl ({})]',
        '(UniMod:5)': '[Carbamyl ({})]',
        '(UniMod:7)': '[Deamidation ({})]',
        '(UniMod:21)': '[Phospho ({})]',
        '(UniMod:23)': '[Dehydrated ({})]',
        '(UniMod:26)': '[Pyro-carbamidomethyl ({})]',
        '(UniMod:27)': '[Glu->pyro-Glu]',
        '(UniMod:28)': '[Gln->pyro-Glu]',
        '(UniMod:30)': '[Cation:Na ({})]',
        '(UniMod:34)': '[Methyl ({})]',
        '(UniMod:35)': '[Oxidation ({})]',
        '(UniMod:36)': '[Dimethyl ({})]',
        '(UniMod:37)': '[Trimethyl ({})]',
        '(UniMod:40)': '[Sulfo ({})]',
        '(UniMod:55)': '[Cys-Cys]',
        '(UniMod:121)': '[GlyGly ({})]',
        '(UniMod:254)': '[Delta:H(2)C(2) ({})]',
        '(UniMod:312)': '[Cysteinyl]',
        '(UniMod:345)': '[Trioxidation ({})]',
        '(UniMod:408)': '[Hydroxyproline]',
        '(UniMod:425)': '[Dioxidation ({})]',
        '(UniMod:526)': '[Dethiomethyl ({})]',
        '(UniMod:877)': '[QQTGG ({})]',
    }
    mods = re.findall('\(UniMod:\d+\)', sequence)
    if mods:
        for mod in mods:
            posit = re.search('\(UniMod:\d+\)', sequence)
            i = posit.start()

            if i == 0:
                add_aa = 'N-term'
            elif posit.end() == len(sequence):
                add_aa = 'C-term'
            else:
                add_aa = sequence[i-1]

            if mod == '(UniMod:7)':
                if add_aa in 'NQ':
                    add_aa = 'NQ'
            elif mod == '(UniMod:21)':
                if add_aa in 'STY':
                    add_aa = 'STY'
            elif mod == '(UniMod:23)':
                if add_aa in 'ST':
                    add_aa = 'ST'
            elif mod == '(UniMod:30)':
                if add_aa in 'DE':
                    add_aa = 'DE'
            elif mod == '(UniMod:34)':
                if add_aa in 'KR':
                    add_aa = 'KR'
            elif mod == '(UniMod:36)':
                if add_aa in 'KR':
                    add_aa = 'KR'
            elif mod == '(UniMod:40)':
                if add_aa in 'STY':
                    add_aa = 'STY'
            elif mod == '(UniMod:425)':
                if add_aa in 'MW':
                    add_aa = 'MW'

            if mod in modif_convers_dict.keys():
                sequence = sequence.replace(mod, modif_convers_dict.get(mod).format(add_aa), 1)

    return sequence

# Cell
import pandas as pd
from typing import Union

def import_diann_data(
    file: str,
    sample: Union[str, list, None] = None
) -> pd.DataFrame:
    """Import peptide level data from DIA-NN.

    Args:
        file (str): The name of a file.
        sample (Union[str, list, None]): The unique raw file name(s) to filter the original file. Defaults to None. In this case data for all raw files will be extracted.

    Returns:
        pd.DataFrame: A pandas dataframe containing information about: all_protein_ids (str), modified_sequence (str), naked_sequence (str)
    """
    diann_columns = ["Protein.Ids", "Modified.Sequence", "Run"]

    data = read_file(file, diann_columns)

    if sample:
        if isinstance(sample, list):
            data_sub = data[data["Run"].isin(sample)]
            data_sub = data_sub[["Protein.Ids", "Modified.Sequence"]]
        elif isinstance(sample, str):
            data_sub = data[data["Run"] == sample]
            data_sub = data_sub[["Protein.Ids", "Modified.Sequence"]]
    else:
        data_sub = data[["Protein.Ids", "Modified.Sequence"]]

    # get a list of proteins_id
    data_sub = data_sub.rename(columns={"Protein.Ids": "all_protein_ids"})

    # get modified sequence
    modif_seq = data_sub.apply(lambda row: convert_diann_mq_mod(row["Modified.Sequence"]), axis=1)
    data_sub['modified_sequence'] = modif_seq.values

    # get naked sequence
    nak_seq = data_sub.apply(lambda row: re.sub(r'\[.*?\]', '', row["modified_sequence"]), axis=1)
    data_sub = data_sub.assign(naked_sequence = nak_seq.values)

    input_data = data_sub[["all_protein_ids", "modified_sequence", "naked_sequence"]]
    input_data = input_data.dropna() # remove missing values
    input_data = input_data.drop_duplicates().reset_index(drop=True)
    return input_data

# Cell
import re

def convert_fragpipe_mq_mod(
    sequence:str,
    assigned_modifications: str
) -> str:
    """Convert FragPipe style modifications into MaxQuant style modifications.

    Args:
        sequence (str): The peptide sequence with modification.
        assigned_modifications (str): The string of assigned modifications separated by comma.

    Returns:
        str: The peptide sequence with modification in a similar to DIA-NN style.
    """
    modif_convers_dict = {
        42.0106: '[Acetyl ({})]',
        -0.9840: '[Amidated ({})]',
        57.0215: '[Carbamidomethyl ({})]',
        43.0058: '[Carbamyl ({})]',
        0.9840: '[Deamidation ({})]',
        79.9663: '[Phospho ({})]',
        -18.0106: ['[Dehydrated ({})]', '[Glu->pyro-Glu]'],
        39.9949: '[Pyro-carbamidomethyl ({})]',
        -17.0265: '[Gln->pyro-Glu]',
        21.9819: '[Cation:Na ({})]',
        14.0157: '[Methyl ({})]',
        15.9949: '[Oxidation ({})]',
        28.0313: '[Dimethyl ({})]',
        42.047: '[Trimethyl ({})]',
        79.9568: '[Sulfo ({})]',
        305.0682: '[Cys-Cys]',
        114.0429: '[GlyGly ({})]',
        26.0157: '[Delta:H(2)C(2) ({})]',
        119.0041: '[Cysteinyl]',
        47.9847: '[Trioxidation ({})]',
        148.0372: '[Hydroxyproline]',
        31.9898: '[Dioxidation ({})]',
        -48.0034: '[Dethiomethyl ({})]',
        599.2663: '[QQTGG ({})]',
    }

    if assigned_modifications:
        modifs_posit = [''] * (len(sequence) + 1)
        for mod in assigned_modifications.split(','):
            mod = mod.strip()
            data = mod.replace(')', '').replace('"', '').split('(')
            mod_pos, mod_mass = data[0], float(data[1])
            if mod_pos == 'N-term':
                posit = 0
                add_aa = 'N-term'
            elif mod_pos == 'C-term':
                posit = -1
                add_aa = 'C-term'
            else:
                posit = int(mod_pos[:-1])
                add_aa = mod_pos[-1]
                if mod_mass == 0.9840:
                    if add_aa in 'NQ':
                        add_aa = 'NQ'
                elif mod_mass == 79.9663:
                    if add_aa in 'STY':
                        add_aa = 'STY'
                elif mod_mass == 21.9819:
                    if add_aa in 'DE':
                        add_aa = 'DE'
                elif mod_mass == 14.0157:
                    if add_aa in 'KR':
                        add_aa = 'KR'
                elif mod_mass == 28.0313:
                    if add_aa in 'KR':
                        add_aa = 'KR'
                elif mod_mass == 79.9568:
                    if add_aa in 'STY':
                        add_aa = 'STY'
                elif mod_mass == 31.9898:
                    if add_aa in 'MW':
                        add_aa = 'MW'
            if mod_mass == -18.0106:
                if add_aa == 'E':
                    modifs_posit[posit] = modif_convers_dict[mod_mass][1].format(add_aa)
                else:
                    if add_aa in 'ST':
                        add_aa = 'ST'
                    modifs_posit[posit] = modif_convers_dict[mod_mass][0].format(add_aa)
            else:
                modifs_posit[posit] = modif_convers_dict[mod_mass].format(add_aa)

        modif_sequence = ''.join(["".join(i) for i in zip(' '+ sequence, modifs_posit)]).strip()
        return modif_sequence

    else:
        return sequence

# Cell
import pandas as pd
from typing import Union

def import_fragpipe_data(
    file: str,
    sample: Union[str, list, None] = None
) -> pd.DataFrame:
    """Import peptide level data from FragPipe/MSFragger.

    Args:
        file (str): The name of a file.
        sample (Union[str, list, None]): The unique raw file name(s) to filter the original file. Defaults to None. In this case data for all raw files will be extracted.

    Returns:
        pd.DataFrame: A pandas dataframe containing information about: all_protein_ids (str), modified_sequence (str), naked_sequence (str)
    """
    file_ext = os.path.splitext(file)[-1]
    if file_ext=='.csv':
        sep=','
    elif file_ext=='.tsv':
        sep='\t'
    elif file_ext=='.txt':
        sep='\t'
    if sample:
        if isinstance(sample, list):
            column_names = [each + ' Spectral Count' for each in sample]
            combined_fragpipe_columns = ["Sequence", "Protein ID"] + column_names
            data = pd.read_csv(file, sep=sep, low_memory=False, usecols=combined_fragpipe_columns)
            selected_indices = []
            for column_name in column_names:
                selected_indices.extend(data[data[column_name] > 0].index.tolist())
            data_sub = data.iloc[list(set(selected_indices))]
            data_sub = data_sub[["Sequence", "Protein ID"]]
        elif isinstance(sample, str):
            column_name = sample + ' Spectral Count'
            combined_fragpipe_columns = ["Sequence", "Protein ID", column_name]
            data = pd.read_csv(file, sep=sep, low_memory=False, usecols=combined_fragpipe_columns)
            selected_indices = data[data[column_name] > 0].index.tolist()
            data_sub = data.iloc[selected_indices]
            data_sub = data_sub[["Sequence", "Protein ID"]]

        # rename columns into all_proteins_id and naked sequence
        data_sub = data_sub.rename(columns={"Protein ID": "all_protein_ids", "Sequence": "naked_sequence"})
        data_sub['modified_sequence'] = data_sub.naked_sequence

    else:
        try:
            combined_fragpipe_columns = ["Sequence", "Protein ID"]
            data_sub = pd.read_csv(file, sep=sep, low_memory=False, usecols=combined_fragpipe_columns)

            # rename columns into all_proteins_id and naked sequence
            data_sub = data_sub.rename(columns={"Protein ID": "all_protein_ids", "Sequence": "naked_sequence"})
            data_sub['modified_sequence'] = data_sub.naked_sequence
        except:
            fragpipe_columns = ["Protein ID", "Peptide", "Assigned Modifications"]
            data = read_file(file, fragpipe_columns)
            data_sub = data[["Protein ID", "Peptide", "Assigned Modifications"]]

            # get modified sequence
            modif_seq = data_sub.apply(lambda row: convert_fragpipe_mq_mod(row["Peptide"], row["Assigned Modifications"]), axis=1)
            data_sub['modified_sequence'] = modif_seq.values

            # rename columns into all_proteins_id and naked sequence
            data_sub = data_sub.rename(columns={"Protein ID": "all_protein_ids", "Peptide": "naked_sequence"})

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
        pd.DataFrame: A pandas dataframe containing information about: all_protein_ids (str), modified_sequence (str), naked_sequence (str)
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
            l = l.strip().split(sep)
            if i>0:
                break

        uploaded_data_columns = set(l)
        input_info = file

    if set(["Proteins","Modified sequence","Raw file"]).issubset(uploaded_data_columns):
        if verbose:
            print("Import MaxQuant output")
        data = import_maxquant_data(input_info, sample=sample)
    elif set(["PEP.AllOccurringProteinAccessions","EG.ModifiedSequence","R.FileName"]).issubset(uploaded_data_columns):
        if verbose:
            print("Import Spectronaut output")
        data = import_spectronaut_data(input_info, sample=sample)
    elif set(["protein_group", "sequence", "shortname"]).issubset(uploaded_data_columns):
        if verbose:
            print("Import AlphaPept output")
        data = import_alphapept_data(input_info, sample=sample)
    elif set(["Protein.Ids", "Modified.Sequence", "Run"]).issubset(uploaded_data_columns):
        if verbose:
            print("Import DIA-NN output")
        data = import_diann_data(input_info, sample=sample)
    elif set(["Protein ID", "Assigned Modifications"]).issubset(uploaded_data_columns):
        if verbose:
            print("Import FragPipe output")
        data = import_fragpipe_data(input_info, sample=sample)
    else:
        raise TypeError(f'Input data format for {file} not known.')
    return data