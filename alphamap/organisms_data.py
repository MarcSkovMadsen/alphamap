# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/organisms_data.ipynb (unless otherwise specified).

__all__ = ['all_organisms', 'import_fasta', 'import_uniprot_annotation']

# Cell
all_organisms = {
    'Human': {'fasta_name': 'human.fasta',
               'uniprot_name': 'preprocessed_uniprot_human.csv'
              },
    'Mouse': {'fasta_name': 'mouse.fasta',
               'uniprot_name': 'preprocessed_uniprot_mouse.csv'
              },
    'Rat': {'fasta_name': 'rat_[10116].fasta',
               'uniprot_name': 'preprocessed_uniprot_rat.csv'
              },
    'Cow': {'fasta_name': 'bovine_[9913].fasta',
               'uniprot_name': 'preprocessed_uniprot_bovine.csv'
              },
    'Zebrafish': {'fasta_name': 'zebrafish_[7955].fasta',
               'uniprot_name': 'preprocessed_uniprot_zebrafish.csv'
              },
    'Drosophila': {'fasta_name': 'drosophila_[7227].fasta',
               'uniprot_name': 'preprocessed_uniprot_drosophila.csv'
              },
    'Caenorhabditis elegans': {'fasta_name': 'celegans_[6239].fasta',
               'uniprot_name': 'preprocessed_uniprot_human.csv'
              },
    'Slime mold': {'fasta_name': 'slimemold_[44689].fasta',
               'uniprot_name': 'preprocessed_uniprot_slimemold.csv'
              },
    'Arabidopsis thaliana': {'fasta_name': 'arabidopsis_thaliana.fasta',
               'uniprot_name': 'preprocessed_uniprot_arabidopsis.csv'
              },
    'Rice': {'fasta_name': 'rice_[39947].fasta',
               'uniprot_name': 'preprocessed_uniprot_rice.csv'
              },
    'Escherichia coli': {'fasta_name': 'ecoli_[83333].fasta',
               'uniprot_name': 'preprocessed_uniprot_ecoli.csv'
              },
    'Bacillus subtilis': {'fasta_name': 'bsubtilis_[224308].fasta',
               'uniprot_name': 'preprocessed_uniprot_bsubtilis.csv'
              },
    'Saccharomyces cerevisiae': {'fasta_name': 'yeast_[559292].fasta',
               'uniprot_name': 'preprocessed_uniprot_yeast.csv'
              },
    'SARS-CoV': {'fasta_name': 'cov.fasta',
               'uniprot_name': 'preprocessed_uniprot_cov.csv'
              },
    'SARS-CoV2': {'fasta_name': 'cov2.fasta',
               'uniprot_name': 'preprocessed_uniprot_cov2.csv'
              }
}

# Cell
import os
import urllib.request
import shutil
import imp
from pyteomics import fasta
def import_fasta(organism: str):
    """
    Import fasta file for the selected organism.
    This downloads the file from github if not present.

    Args:
        organism (str): Organism for which the fasta file should be imported.
    Returns:
        fasta: Fasta file imported by pyteomics 'fasta.IndexedUniProt' for the selected organism.
    """
    if not organism in all_organisms.keys():
        raise ValueError(f"Organism {organism} is not available. Please select one of the following: {list(all_organisms.keys())}")


    BASE_PATH = imp.find_module("alphamap")[1] #os.path.abspath('')
    INI_PATH = os.path.join(BASE_PATH, '..')
    FUNCT_PATH = os.path.join(INI_PATH, 'alphamap')
    DATA_PATH = os.path.join(FUNCT_PATH, 'data')

    fasta_name = all_organisms[organism]['fasta_name']

    if not os.path.exists(os.path.join(DATA_PATH, fasta_name)):
        print(f"The fasta file for {organism} is downloaded from github.")
        github_url_data_folder = 'https://github.com/MannLabs/alphamap/blob/master/alphamap/data/'

        github_file = os.path.join(
            github_url_data_folder,
            os.path.basename(os.path.join(DATA_PATH, fasta_name))) + '/?raw=true'

        with urllib.request.urlopen(github_file) as response, open(os.path.join(DATA_PATH, fasta_name), 'wb') as out_file:
            shutil.copyfileobj(response, out_file)

    fasta_file = fasta.IndexedUniProt(os.path.join(DATA_PATH, fasta_name))

    return fasta_file

# Cell
import os
import urllib.request
import shutil
import imp
import pandas as pd
def import_uniprot_annotation(organism: str):
    """
    Import uniprot annotation file for the selected organism.
    This downloads the file from github if not present.

    Args:
        organism (str): Organism for which the uniprot annotation should be imported.
    Returns:
        pd.DataFrame: Dataframe with the uniprot annotations for the selected organism.

    """
    if not organism in all_organisms.keys():
        raise ValueError(f"Organism {organism} is not available. Please select one of the following: {list(all_organisms.keys())}")


    BASE_PATH = imp.find_module("alphamap")[1] #os.path.abspath('')
    INI_PATH = os.path.join(BASE_PATH, '..')
    FUNCT_PATH = os.path.join(INI_PATH, 'alphamap')
    DATA_PATH = os.path.join(FUNCT_PATH, 'data')

    uniprot_name = all_organisms[organism]['uniprot_name']

    if not os.path.exists(os.path.join(DATA_PATH, uniprot_name)):
        print(f"The uniprot annotation file for {organism} is downloaded from github.")
        github_url_data_folder = 'https://github.com/MannLabs/alphamap/blob/master/alphamap/data/'

        github_file = os.path.join(
            github_url_data_folder,
            os.path.basename(os.path.join(DATA_PATH, uniprot_name))) + '/?raw=true'

        with urllib.request.urlopen(github_file) as response, open(os.path.join(DATA_PATH, uniprot_name), 'wb') as out_file:
            shutil.copyfileobj(response, out_file)

    uniprot_file = pd.read_csv(os.path.join(DATA_PATH, uniprot_name))

    return uniprot_file