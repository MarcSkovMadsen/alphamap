# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/SequencePlot.ipynb (unless otherwise specified).

__all__ = ['format_uniprot_annotation', 'ptm_shape_dict', 'get_plot_data', 'plot_single_peptide_traces',
           'custom_color_palettes', 'uniprot_color_dict', 'aa_color_dict', 'plot_peptide_traces']

# Cell
import pandas as pd

def format_uniprot_annotation(uniprot_ann, uniprot_feature_dict):
    """
    Function to format uniprot annotation for plotting
    """
    uniprot = uniprot_ann.copy(deep=True)
    uniprot.loc[uniprot.feature == "HELIX", "note"] = "Helix"
    uniprot.loc[uniprot.feature == "STRAND", "note"] = "Beta strand"
    uniprot.loc[uniprot.feature == "TURN", "note"] = "Turn"
    uniprot.loc[uniprot.feature.isin(["HELIX","STRAND","TURN"]), "feature"] = "STRUCTURE"

    uniprot_feature_dict_rev = {v: k for k, v in uniprot_feature_dict.items()}

    uniprot['annotation'] = uniprot['note']
    uniprot.loc[uniprot['annotation'].isnull(), 'annotation'] = uniprot['feature']
    uniprot = uniprot.replace({"annotation": uniprot_feature_dict_rev})
    return uniprot


# Cell
#ptm_shape_dict = {'[Phospho (STY)]': 0,
#                '[GlyGly (K)]':2,
#                '[Carbamidomethyl (C)]':3,
#                '[Oxidation (M)]':4,
#                '[Acetyl (Protein N-term)]':5}

# Cell
ptm_shape_dict = {
    '[Acetyl (K)]': 5,
    '[Acetyl (Protein N-term)]': 5,
    '[Carbamidomethyl (C)]': 3,
    '[Oxidation (M)]': 4,
    '[Phospho (STY)]': 0,
    '[GlyGly (K)]': 2,
    '[Methyl (KR)]': 6,
    '[Dimethyl (KR)]': 6,
    '[Trimethyl (K)]': 6,
    '[Pro5]': 9,
    '[Pro6]': 10,
    '[Glu->pyro-Glu]': 11,
    '[Gln->pyro-Glu]': 12,
    '[QQTGG (K)]': 13,
    '[Deamidation (N)]': 14,
    '[Deamidation 18O (N)]': 14,
    '[Deamidation (NQ)]': 14,
    '[Hydroxyproline]': 15,
    '[Carbamyl (N-term)]': 16,
    '[Delta:H(2)C(2) (N-term)]': 19,
    '[Dioxidation (MW)]': 4,
    '[Trioxidation (C)]': 4,
    '[Dethiomethyl (M)]': 20,
    '[Cation:Na (DE)]': 21,
    '[Methyl (E)]': 6,
    '[Dehydrated (ST)]': 23,
    '[Oxidation (P)]': 4,
    '[Dimethyl (K)]': 6,
    '[Amidated (Protein C-term)]': 22,
    '[Sulfo (STY)]': 24,
    '[Acetyl (N-term)]': 5,
    '[Amidated (C-term)]': 22,
    '[Sulfation (Y)]': 25,
    '[Phospho (ST)]': 0,
    '[Cys-Cys]': 26,
    '[Cysteinyl]': 27,
    '[Cysteinyl - carbamidomethyl]': 28,
    '[Oxidation (MP)]': 4
}

# Cell
import numpy as np
import pandas as pd
from pyteomics import fasta

def get_plot_data(protein,df,fasta):
    protein_sequence = fasta[protein].sequence
    df_prot = df[df.unique_protein_id==protein]

    if df_prot.shape[0] == 0:
        df_plot = None
    else:
        df_peps = [np.arange(row['start'], row['end']+1) for _, row in df_prot.iterrows()]
        df_peps  = pd.DataFrame.from_records(data=df_peps)
        df_peps['modified_sequence'] = df_prot['modified_sequence'].values
        df_peps['all_protein_ids'] = df_prot['all_protein_ids'].values
        df_peps = df_peps.melt(id_vars=['modified_sequence','all_protein_ids'])
        df_peps = df_peps[['modified_sequence','all_protein_ids','value']].dropna()
        df_peps = df_peps.rename(columns={"value": "seq_position"})
        df_peps['marker_symbol'] = 1
        df_peps['marker_size'] = 8
        df_peps['PTM'] = np.NaN
        df_peps['PTMtype'] = np.NaN
        df_peps['PTMshape'] = np.NaN
        unique_pep = df_peps.modified_sequence.unique()
        for uid in unique_pep:
            df_peps_uid = df_peps[df_peps.modified_sequence==uid]
            start_uid = np.min(df_peps_uid.seq_position)
            end_uid = np.max(df_peps_uid.seq_position)
            df_peps['marker_symbol'] = np.where(df_peps.seq_position == start_uid, 7, df_peps.marker_symbol)
            df_peps['marker_symbol'] = np.where(df_peps.seq_position == end_uid, 8, df_peps.marker_symbol)
            df_peps['marker_size'] = np.where(df_peps.seq_position == start_uid, 6, df_peps.marker_size)
            df_peps['marker_size'] = np.where(df_peps.seq_position == end_uid, 6, df_peps.marker_size)

            df_PTMs_uid = df_prot[df_prot.modified_sequence==uid]
            PTMsites = df_PTMs_uid.PTMsites.tolist()[0] + start_uid
            PTMtypes = df_PTMs_uid.PTMtypes.tolist()[0]

            for i in range(0,len(PTMsites)):
                df_peps['PTM'] = np.where(df_peps["seq_position"]==PTMsites[i], 1, df_peps.PTM)
                df_peps['PTMtype'] = np.where(df_peps["seq_position"]==PTMsites[i], PTMtypes[i], df_peps.PTMtype)

            df_seq = pd.DataFrame({'seq_position':np.arange(0,len(protein_sequence))})

            df_plot = pd.merge(df_seq, df_peps, how='left', on='seq_position')
            df_plot['height']=0
            df_plot['color']="grey"

            unique_mods = df_plot['PTMtype'].dropna().unique()
            if len(unique_mods) > 0:
                for mod in df_plot['PTMtype'].dropna().unique():
                    if mod != 'nan':
                        #print(mod)
                        if mod not in ptm_shape_dict.keys():
                            ptm_shape_dict.update({mod : 17})

                        df_plot.loc[df_plot.PTMtype == mod, 'PTMshape'] = ptm_shape_dict[mod]
                        #df_plot.loc[df_plot.PTMtype == mod, 'PTMshape'] = 17

    return(df_plot)

# Cell
import plotly.graph_objects as go

def plot_single_peptide_traces(df_plot,protein,fasta):
    protein_sequence = fasta[protein].sequence
    entry_name = fasta[protein].description['GN']
    protein_name = fasta[protein].description['name']

    plot0 = go.Scatter(y=[None],
                       name='',
                       xaxis='x1',
                       showlegend=False)

    ## Peptide backbone
    df_plot_pep = df_plot.dropna(subset=['modified_sequence'])
    plot1 = go.Scatter(x=df_plot_pep.seq_position+1,
                       y=df_plot.height,
                       xaxis='x2',
                       mode='markers',
                       marker_size=df_plot_pep.marker_size,
                       marker_symbol=df_plot_pep.marker_symbol,
                       marker_line_color=df_plot_pep.color,
                       marker_color=df_plot_pep.color,
                       marker_opacity=1,
                       meta=df_plot_pep.modified_sequence,
                       text=df_plot_pep.all_protein_ids,
                       hovertemplate ='Peptide: %{meta}<br>' +
                       'Protein IDs: %{text}',
                       name='',
                       showlegend=False)

    covered_AA = len(df_plot_pep.seq_position.unique())
    percent_AA_coverage = int(np.round(100/len(protein_sequence)*covered_AA))
    #print(percent_AA_coverage)

    ## PTM dots
    df_plot_ptm = df_plot.dropna(subset=['PTM'])
    #print(df_plot_ptm)
    plot2 = go.Scatter(x=df_plot_ptm.seq_position+1,
                       y=df_plot_ptm.height+0.3,
                       xaxis='x2',
                       mode='markers',
                       marker_size=8,
                       marker_symbol=df_plot_ptm.PTMshape,
                       marker_line_color=df_plot_ptm.color,
                       marker_color=df_plot_ptm.color,
                       marker_opacity=1,
                       text=df_plot_ptm.PTMtype,
                       hovertemplate = 'PTM: %{text}',
                       #hoverinfo='text',
                       name='',
                       showlegend=False)

    layout = go.Layout(
            yaxis=dict(
                title = "",
                ticks = None,
                showticklabels=False,
                range=[-1, 2],
                showgrid=False,
                zeroline=False
                ),
            xaxis1=dict(
                title= 'protein sequence',
                tickmode = 'array',
                range=[-10, len(protein_sequence)+10],
                tickvals = np.arange(1,len(protein_sequence)+1),
                ticktext = list(protein_sequence),
                tickangle=0,
                matches="x2",
                type="linear",
                anchor="y",
                showgrid=False,
                zeroline=False
                ),
            xaxis2=dict(
                title= 'AA position',
                tickmode = 'auto',
                range=[-10, len(protein_sequence)+10],
                tickangle=0,
                matches="x1",
                side="top",
                type="linear",
                anchor="y",
                showgrid=False,
                zeroline=False,
                tickformat = '.d'
                ),
        #showlegend=False,
        #height=400,
        #width=1000,
        plot_bgcolor='rgba(0,0,0,0)',
        title=f"Sequence plot for: {protein_name}<br>{entry_name} - {protein}",
        meta=percent_AA_coverage,
        margin = dict(l=20, r=20, t=150, b=20)
        )

    fig = go.Figure(data=[plot1,plot2,plot0], layout=layout)

    #print(fig.layout.meta)

    for i in range(0, df_plot_ptm.shape[0]):
            fig.add_shape(
                    dict(
                        type="line",
                        xref="x2",
                        x0=df_plot_ptm.seq_position.values[i] +1,
                        y0=df_plot_ptm.height.values[i],
                        x1=df_plot_ptm.seq_position.values[i] +1,
                        y1=df_plot_ptm.height.values[i]+0.3,
                        line=dict(
                            color=df_plot_ptm.color.values[i],
                            width=1
                        )
                    )
            )

    return fig

# Cell
custom_color_palettes = {
    'col_greens':["#5C965D","#6AA16B","#77AC78","#84B786","#91C193","#9FCCA1","#B3DCB5","#C6EBC9"],
    'col_ornages':["#ff4800","#ff5400","#ff6000","#ff6d00","#ff7900","#ff8500","#ff9100","#ff9e00","#ffaa00","#ffb600"],
    'col_purples':["#ffa69e","#febaae","#fcb088","#d9f3e2","#b8f2e6","#aed9e0","#9baed9","#9199d5","#8783d1"],
    'col_turquises':["#00a9a5","#4e8098","#90c2e7"],
    'col_darkpinks':["#42033d","#6f0c59","#901468","#7c238c","#924ea6","#9c5eae"],
    'col_browns':["#5a2a27","#5c4742","#8d5b4c","#a5978b","#c4bbaf"]
}


# Cell
uniprot_color_dict = {'CHAIN': custom_color_palettes['col_greens'][0],
                      'INIT_MET': custom_color_palettes['col_greens'][1],
                      'PEPTIDE': custom_color_palettes['col_greens'][2],
                      'PROPEP': custom_color_palettes['col_greens'][3],
                      'SIGNAL': custom_color_palettes['col_greens'][4],
                      'TRANSIT': custom_color_palettes['col_greens'][5],

                      'COILED': custom_color_palettes['col_purples'][0],
                      'COMPBIAS': custom_color_palettes['col_purples'][1],
                      'DOMAIN': custom_color_palettes['col_purples'][2],
                      'MOTIF': custom_color_palettes['col_purples'][3],
                      'REGION': custom_color_palettes['col_purples'][4],
                      'REPEAT': custom_color_palettes['col_purples'][5],
                      'ZN_FING': custom_color_palettes['col_purples'][6],

                      'INTRAMEM': custom_color_palettes['col_turquises'][0],
                      'TOPO_DOM': custom_color_palettes['col_turquises'][1],
                      'TRANSMEM': custom_color_palettes['col_turquises'][2],

                      'STRUCTURE': 'black',
                      # extra structures
                      'Helix': '#5dabe8',
                      'Turn': '#e094bc',
                      'Beta strand': '#8cdbad',

                      'CROSSLNK': custom_color_palettes['col_ornages'][2],
                      'DISULFID': custom_color_palettes['col_ornages'][3],
                      'CARBOHYD': custom_color_palettes['col_ornages'][4],
                      'LIPID': custom_color_palettes['col_ornages'][5],
                      'MOD_RES': custom_color_palettes['col_ornages'][6],

                      'BINDING': custom_color_palettes['col_darkpinks'][0],
                      'CA_BIND': custom_color_palettes['col_darkpinks'][1],
                      'DNA_BIND': custom_color_palettes['col_darkpinks'][2],
                      'METAL': custom_color_palettes['col_darkpinks'][3],
                      'NP_BIND': custom_color_palettes['col_darkpinks'][4],
                      'SITE': custom_color_palettes['col_darkpinks'][5],

                      'NON_STD': custom_color_palettes['col_browns'][0],
                      'NON_CONS': custom_color_palettes['col_browns'][1],
                      'NON_TER': custom_color_palettes['col_browns'][2],
                      'VARIANT': custom_color_palettes['col_browns'][3],
                      'CONFLICT': custom_color_palettes['col_browns'][4],

                      'VAR_SEQ': '#fae7b1',
                      'UNSURE': 'grey',
                      'MUTAGEN': 'darkgrey',
                     }

# Cell
aa_color_dict = {'A':'Alanine',
                 'R':'Arginine',
                 'N':'Asparagine',
                 'D':'Aspartic acid',
                 'C':'Cysteine',
                 'E':'Glutamic acid',
                 'Q':'Glutamine',
                 'G':'Glycine',
                 'H':'Histidine',
                 'I':'Isoleucine',
                 'L':'Leucine',
                 'K':'Lysine',
                 'M':'Methionine',
                 'F':'Phenylalanine',
                 'P':'Proline',
                 'S':'Serine',
                 'T':'Treonine',
                 'W':'Tryptophan',
                 'Y':'Tyrosine',
                 'V':'Valine',
                 'X':'nan',
                 'U':'nan'}

# Cell

import plotly.graph_objects as go
from .proteolytic_cleavage import get_cleavage_sites

def plot_peptide_traces(df,name,protein,fasta,uniprot,selected_features,
                        uniprot_feature_dict,uniprot_color_dict, selected_proteases=[]):

    figure_height = 200

    protein_sequence = fasta[protein].sequence

    # colors for experimental data traces
    colors = ["#023e8a","#0096c7","#90e0ef","#7fd14d","#26a96c"]

    # generation of a reverse uniprot_feature_dict
    uniprot_feature_dict_rev = {v: k for k, v in uniprot_feature_dict.items()}
    #uniprot_feature_dict_rev["STRUCTURE"] = "Secondary structure"

    # subsetting of the uniprot annotation to the selected features
    uniprot_annotation_p = uniprot[uniprot.protein_id==protein]
    # formatting of uniprot annotations
    uniprot_annotation_p_f = format_uniprot_annotation(uniprot_annotation_p, uniprot_feature_dict)
    # subset for selected features
    uniprot_annotation_p_f_f = uniprot_annotation_p_f[uniprot_annotation_p_f.feature.isin(selected_features)]

    if isinstance(df, pd.DataFrame):
        df_plot = get_plot_data(protein=protein,
                              df = df,
                              fasta = fasta)

        df_plot.color = colors[0]

        observed_mods = list(set(df_plot.PTMtype))
        ptm_shape_dict_sub = {key: ptm_shape_dict[key] for key in observed_mods if key in ptm_shape_dict}

        fig = plot_single_peptide_traces(df_plot,protein=protein,fasta = fasta)

        AA_coverage = fig.layout.meta
        trace_name = [name + "<br> (" + str(AA_coverage) + "% coverage)"]

        fig.update_layout(yaxis=dict(showticklabels=True,
                                     tickmode = 'array',
                                     tickvals = [0],
                                     ticktext = [name + "(" + str(AA_coverage) + "%)"],
                                     showgrid=False))

        y_max = 1

    elif isinstance(df, list):

        df_plot = [get_plot_data(protein=protein,
                               df = d,
                               fasta = fasta) for d in df]

        # Subset data and annotations for the samples where the selected protein was detected
        valid_idx = []
        for i in range(len(df_plot)):
            if df_plot[i] is not None:
                valid_idx.append(i)
        df_plot = [df_plot[i] for i in valid_idx]
        name = [name[i] for i in valid_idx]
        colors = [colors[i] for i in valid_idx]
        #observed_mods = set([df_plot[i].PTMtype for i in valid_idx])
        observed_mods = []
        for i in range(len(df_plot)):
            observed_mods.extend(list(set(df_plot[i].PTMtype)))
        observed_mods = list(set(observed_mods))
        ptm_shape_dict_sub = {key: ptm_shape_dict[key] for key in observed_mods if key in ptm_shape_dict}

        for i in range(len(df_plot)):
            df_plot[i].color = colors[i]
            df_plot[i].height = 1+i

        plot_list = [plot_single_peptide_traces(df,protein=protein,fasta = fasta) for df in df_plot]
        new_data = [p.data for p in plot_list]
        new_data = sum(new_data, ())
        new_layout = plot_list[0].layout
        shapes = [p.layout.shapes for p in plot_list]
        shapes = sum(shapes, ())
        new_layout.shapes = new_layout.shapes + tuple(shapes)
        AA_coverage = [p.layout.meta for p in plot_list]
        trace_name = [n + "<br> (" + str(c) + "% coverage)" for n,c in zip(name,AA_coverage)]

        fig = go.Figure(data=new_data, layout=new_layout)
        fig.update_layout(yaxis=dict(range=[0,len(df_plot)+1],
                                     showticklabels=True,
                                     tickmode = 'array',
                                     tickvals = np.arange(0, len(df_plot))+1,
                                     ticktext = np.array(trace_name),
                                     showgrid=False))

        y_max = len(df_plot)+1

        figure_height = figure_height + (len(df_plot)*50)


    ptm_shape_dict_sub = dict(sorted(ptm_shape_dict_sub.items()))
    for i in range(len(ptm_shape_dict_sub)):
        fig.add_trace(go.Scatter(y=[None],
                                 mode='markers',
                                 xaxis='x2',
                                 marker=dict(symbol=list(ptm_shape_dict_sub.values())[i],
                                             color='black'),
                                 name=list(ptm_shape_dict_sub.keys())[i],
                                 showlegend=True))

    all_uniprot_features = list(uniprot_color_dict.keys())
    available_features = list(set(uniprot_annotation_p_f_f.feature))
    unique_features = [x for x in all_uniprot_features if x in available_features]
    if len(unique_features) > 0:

        y_max = y_max+1

        for j in range(0,len(unique_features)):

            figure_height = figure_height + 50

            domain = unique_features[j]
            domain_info_sub = uniprot_annotation_p_f_f[uniprot_annotation_p_f_f.feature==domain].reset_index(drop=True)
            for i in range(0, domain_info_sub.shape[0]):
                start = int(domain_info_sub.start[i])
                end = domain_info_sub.end[i]
                if np.isnan(domain_info_sub.end[i]):
                    end=start #+1
                else:
                    end=int(end)

                if domain_info_sub.feature[i] == "STRUCTURE":
                    marker_col = uniprot_color_dict[domain_info_sub.annotation[i]]
                else:
                    marker_col = uniprot_color_dict[domain_info_sub.feature[i]]

                fig.add_trace(go.Bar(x=list(range(start,end+1)),
                                     y=list(np.repeat(0.2,end-start+1)),
                                     base=list(np.repeat(y_max+(j/2),end-start+1)-0.1),
                                     marker_color=marker_col,
                                     marker_line_width=0,
                                     opacity=0.8,
                                     showlegend=False,
                                     xaxis='x2',
                                     name='',
                                     text=np.repeat(domain_info_sub.annotation[i],len(range(start,end+1))),
                                     hovertemplate ='%{text}'
                                     #hovertext=domain_info_sub.annotation[i],
                                     #hoverinfo='text'
                                    ))
        fig.update_layout(barmode='stack', bargap=0, hovermode='x unified',hoverdistance=1)

    selected_proteases = sorted(selected_proteases)
    if len(selected_proteases) > 0:

        y_max = y_max+1

        for u in range(0,len(selected_proteases)):

            figure_height = figure_height + 50

            protease = selected_proteases[u]
            sites = get_cleavage_sites(protein_sequence,protease)
            for s in sites:
                fig.add_trace(go.Bar(x=list(range(s+1,s+2)),
                                     y=[0.2],
                                     base=y_max+(len(unique_features)/2)+(u/2)-0.1,
                                     marker_color="grey",
                                     opacity=0.8,
                                     showlegend=False,
                                     xaxis='x2',
                                     name='',
                                     text=np.repeat(protease,len(range(s+1,s+2))),
                                     hovertemplate ='%{text}'
                                     #hovertext=protease,
                                     #hoverinfo='text'
                                    ))

    fig.add_trace(go.Scatter(x=np.arange(1,len(protein_sequence)+1,1),
                        y=np.repeat(0,len(protein_sequence)),
                        marker=dict(color='rgba(135, 206, 250, 0)'),
                        name='',
                        mode='markers',
                        xaxis='x2',
                        text=[aa_color_dict[x] for x in list(protein_sequence)],
                        #text=np.arange(1,len(protein_sequence)+1,1),
                        meta=list(protein_sequence),
                        hovertemplate ='<b>%{meta}: %{text}<b>',
                        showlegend=False))

    if figure_height < 500:
        figure_height = 500

    fig.update_layout(barmode='stack', bargap=0, hovermode='x unified',hoverdistance=1,
                      width=1500, height=figure_height)

    mapped_feature_names = [uniprot_feature_dict_rev.get(key) for key in unique_features]
    if isinstance(df, pd.DataFrame):
        fig.update_yaxes(showticklabels=True,
                         #tickvals= np.arange(0, 1+len(unique_features)+len(selected_proteases)),
                         tickvals= np.concatenate((np.array([0]),np.arange(1+1,1+1+(len(unique_features)/2),0.5),np.arange(1+(1*np.min([1,len(unique_features)]))+(len(unique_features)/2)+1,1+(1*np.min([1,len(unique_features)]))+(len(unique_features)/2)+1+(len(selected_proteases)/2),0.5))),
                         ticktext=np.hstack((np.array(trace_name),np.array(mapped_feature_names),np.array(selected_proteases))),
                         automargin=True,
                         range=[-1, y_max+(len(unique_features)/2)+(len(selected_proteases)/2)+0.2],
                         showgrid=False)
    elif isinstance(df, list):
        fig.update_yaxes(showticklabels=True,
                         #tickvals= 1 + np.arange(0, len(df_plot)+len(unique_features)+len(selected_proteases)),
                         tickvals= 1 + np.concatenate((np.array([0]),np.arange(1,len(df_plot),1),np.arange(len(df_plot)+1,len(df_plot)+1+(len(unique_features)/2),0.5),np.arange(len(df_plot)+1+(len(unique_features)/2)+(1*np.min([1,len(unique_features)])),len(df_plot)+1+(len(unique_features)/2)+(1*np.min([1,len(unique_features)]))+(len(selected_proteases)/2),0.5))),
                         ticktext=np.hstack((np.array(trace_name),np.array(mapped_feature_names),selected_proteases)),
                         automargin=True,
                         range=[0, y_max+(len(unique_features)/2)+(len(selected_proteases)/2)+0.2],
                         showgrid=False)

    #config = {'toImageButtonOptions': {'format': 'svg', # one of png, svg, jpeg, webp
    #                                   'filename': 'custom_image',
    #                                   'height': 500,
    #                                   'width': 1500,
    #                                   'scale': 1 # Multiply title/legend/axis/canvas sizes by this factor
    #                                  }
    #         }

    return fig #.show(config=config)