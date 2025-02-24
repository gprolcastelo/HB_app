import pandas as pd
global c1genes, c2genes, vim_gene, fqt_genes, hk_genes
t_starts = 'T_'
nt_starts = 'NT_'
cpg_row_name = 'Mean_beta-value'
# cpg_row_name = 'CpG_Array'
c1genes= ['ALDH2', 'APCS', 'APOC4', 'AQP9', 'C1S', 'CYP2E1', 'GHR', 'HPD'] # 8 genes
# ALDH2, APCS, APOC4, AQP9, C1S, CYP2E1, GHR, HPD
c2genes = ['AFP', 'BUB1', 'DLG7', 'DUSP9', 'E2F5', 'IGSF1', 'NLE', 'RPL10A'] # 8 genes
# AFP, BUB1 , DLG7, DUSP9, E2F5, IGSF1, NLE, RPL10A
vim_gene = 'VIM' # 1 gene
fqt_genes = ['DLK1', 'MEG3'] # 2 genes
hk_genes = ['ACTGA1', 'EEF1A1', 'PNN', 'RHOT2'] # 5 genes

def read_and_prepare_data(file_path):
    # Load the dataset, assuming the first column is 'GENE'
    data_op = pd.read_excel(file_path, engine='openpyxl', index_col=0)
    # Separate 'T' and 'NT' columns dynamically
    t_cols = [col for col in data_op.columns if col.startswith(t_starts)]
    nt_cols = [col for col in data_op.columns if col.startswith(nt_starts)]
    data = pd.DataFrame([], index=data_op.index, columns=data_op[t_cols].columns.tolist()+['Mean_NT'])

    # Calculate the mean of NT columns
    if nt_cols:
        mean_nt = data_op[nt_cols].mean(axis=1)
        data['Mean_NT'] = mean_nt
    else:
        raise ValueError('No NT columns found in the dataset')
    # Normalize T columns by the mean of NT columns
    for col in t_cols:
        data[col] = data_op[col] / mean_nt
    # For the CpG_Array row formula is different: [1-(T/mean NT)]:
    data.loc[cpg_row_name] = 1 - data_op.loc[cpg_row_name][t_cols]/mean_nt.loc[cpg_row_name]

    # Return:
    # - the normalized data: tumor/mean(non-tumor) ratio
    # - the list of T columns
    return data_op, data, t_cols, nt_cols

def calculate_scores(data, t_cols,rnaseq_analysis=True):
    """
    Given the expression ratio T/mean(NT), given by columns t_cols in data,
    count the number of upregulated and downregulated genes for C1, C2 classification.
    :param data:
    :param t_cols:
    :param rnaseq_analysis:
    :return: scores dictionary with column names as keys and scores as values
    """
    cutoff_c1 = 0.25 if rnaseq_analysis else 0.5
    cutoff_c2 = 4 if rnaseq_analysis else 2
    scores = {}
    for col in t_cols:
        # Count the number of genes that are upregulated and downregulated
        # downregulated: C1-genes with T/mean(NT) <= cutoff_c1
        downregulated = (data[col].loc[c1genes] <= cutoff_c1).sum()
        # upregulated: C2-genes with T/mean(NT) >= cutoff_c2
        upregulated = (data[col].loc[c2genes] >= cutoff_c2).sum()
        scores[col] = downregulated + upregulated
    return scores

def classify_c1c2(scores, total_genes, vim_values):
    """
    Classify the samples based on the C2 score and VIM value.
    :param scores:
    :param total_genes:
    :param vim_values:
    :return: classifications dictionary with column names as keys and classification as values, and
                percentages dictionary with column names as keys and percentages as values
    """
    classifications = {}
    percentages = {}
    for col, score in scores.items():
        percentage = (score / total_genes) * 100
        percentages[col] = percentage
        if 40 <= percentage <= 60:
            classifications[col] = ('Intermediate', '')
        elif percentage < 40:
            classifications[col] = ('C1-subtype', '')
        else:
            if vim_values[col] > 6.5:
                classifications[col] = ('C2B', '')
            else:
                classifications[col] = ('C2-Pure', '')
    return classifications, percentages

def classify_14q32(data, t_cols):
    """
    Classify the samples based on the number of 14q32 genes overexpressed.
    :param data:
    :param t_cols:
    :return: classification dictionary with column names as keys and classification as values
    """
    classification = {}
    for col in t_cols:
        # Number of 14q32-genes overexpressed: T/NT >=10
        genes_overexpressed = (data[col][fqt_genes] >= 10).sum()
        classification[col] = 'Strong' if genes_overexpressed >= 1 else 'Moderate'
    return classification

def classify_epi_qualu(t_cols,qualu_val,mean_nt_puma):
    """
    Epigenetic classification based on the Percentage of UnMethylated Alu (PUMA) values.
    :param t_cols:
    :param qualu_val:
    :param mean_nt_puma:
    :return: classification dictionary with column names as keys and classification as values
    """
    classification = {}
    for col in t_cols:
        # When Percentage of UnMethylated Alu (PUMA) > 7.17+ mean NT, then Epi-CB
        if pd.isna(qualu_val[col]):
            classification[col] = pd.NA
        elif qualu_val[col] > 7.17 + mean_nt_puma:
            classification[col] = 'Epi-CB'
        else:
            classification[col] = 'Non-Epi-CB'
    return classification

def classify_epi_cpg(t_cols,cpg_val):
    """
    Epigenetic classification based on the Mean beta-values.
    :param t_cols:
    :param cpg_val:
    :return: classification dictionary with column names as keys and classification as values
    """

    classification = {}
    for col in t_cols:
        # When ((1-mean CpGs T/mean CpGs all the NT)*100) > 6.64, then Epi-CB
        if pd.isna(cpg_val[col]):
            classification[col] = pd.NA
        elif cpg_val[col] * 100 > 6.6:
            classification[col] = 'Epi-CB'
        else:
            classification[col] = 'Epi-CA'
    return classification

def classify_mrs(t_cols, class_14q32, class_cpg, class_qualu, class_c1c2):
    """
    Compare the classifications of 14q32, CpG, Qualu, and C1-C2 to get the MRS classification.
    :param t_cols:
    :param class_14q32:
    :param class_cpg:
    :param class_qualu:
    :param class_c1c2:
    :return: classification dictionary with column names as keys and classification as values
    """
    classification = {}
    for col in t_cols:
        class_epi = class_cpg if pd.isna(class_qualu[col]) else class_qualu
        # If any of the classifications is missing, then the final classification is missing
        if pd.isna(class_14q32[col]) or pd.isna(class_epi[col]) or pd.isna(class_c1c2[col]):
            classification[col] = pd.NA
        # Strong 14q32 overexpression
        elif class_14q32[col] == 'Strong':
            # Epi-CB
            if class_epi[col] == 'Epi-CB':
                # MRS-3
                classification[col] = 'MRS-3b' if class_c1c2[col][0] == 'C2-Pure' else 'MRS-3a'
            # Epi-CA
            else:
                classification[col] = 'MRS-2'
        # Moderate 14q32 overexpression
        else:
            classification[col] = 'MRS-2' if class_epi[col] == 'Epi-CB' else 'MRS-1'
    return classification

def process_excel(input_file,rnaseq_analysis):
    """
    Process the input file, perform classifications, and return the classification results.
    :param input_file:
    :param rnaseq_analysis:
    :return: classification dataframe with results from the classifications
    """
    # Calculate
    data_op, data, t_cols, nt_cols = read_and_prepare_data(input_file)
    scores = calculate_scores(data, t_cols,rnaseq_analysis)  # Dynamic split
    # Get VIM values
    vim_values = data.loc[vim_gene].to_dict()
    # Exclude 'VIM' column and non-T columns from vim_values if present
    vim_values = {k: vim_values[k] for k in t_cols if k in vim_values}

    # Get CpG values
    cpg_values = data.loc[cpg_row_name].to_dict()
    cpg_values = {k: cpg_values[k] for k in t_cols if k in cpg_values}
    # Get Qualu values
    qualu_values = data_op.loc['PUMA_value'].to_dict()
    qualu_values = {k: qualu_values[k] for k in t_cols if k in qualu_values}

    classifications_c1c2, percentages_c1c2 = classify_c1c2(scores, 16, vim_values)
    classifications_14q32 = classify_14q32(data, t_cols)
    classifications_cpg = classify_epi_cpg(t_cols,cpg_values)
    classifications_qualu = classify_epi_qualu(t_cols,qualu_values,data['Mean_NT']['PUMA_value'])

    classifications_mrs = classify_mrs(t_cols=t_cols,
                                       class_14q32=classifications_14q32,
                                       class_cpg=classifications_cpg,
                                       class_qualu=classifications_qualu,
                                       class_c1c2=classifications_c1c2)

    # Choose the epigenetic classification between CpG and Qualu, that is not missing data:
    classifications_epi = {col: classifications_cpg[col] if pd.isna(classifications_qualu[col]) else classifications_qualu[col]
                           for col in t_cols}

    # Merge the classifications with column classifications
    for col in classifications_c1c2:
        classifications_c1c2[col] = (classifications_c1c2[col][0],
                                     percentages_c1c2[col],
                                     classifications_14q32[col],
                                     classifications_epi[col],
                                     classifications_mrs[col])

    classification_df = pd.DataFrame([(col, *vals) for col, vals in classifications_c1c2.items()],
                                     columns=['Sample',
                                              'C2 Score',
                                              '% of C2 Score',
                                              '14q32 Classification',
                                              'Epigenetic Classification',
                                              'MRS Classification'
                                              ])

    return classification_df