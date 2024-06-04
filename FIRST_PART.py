import pandas as pd
global c1genes, c2genes, vim_gene, fqt_genes, hk_genes
c1genes= ['ALDH2', 'APCS', 'APOC4', 'AQP9', 'C1S', 'CYP2E1', 'GHR', 'HPD'] # 8 genes
c2genes = ['AFP', 'BUB1', 'DLG7', 'DUSP9', 'E2F5', 'IGSF1', 'NLE', 'RPL10A'] # 8 genes
vim_gene = 'VIM' # 1 gene
fqt_genes = ['DLK1', 'MEG3'] # 2 genes
hk_genes = ['ACTGA1', 'EEF1A1', 'PNN', 'RHOT2'] # 5 genes
def read_and_prepare_data(file_path):
    # Load the dataset, assuming the first column is 'GENE'
    data_op = pd.read_excel(file_path, engine='openpyxl', index_col=0)
    data = data_op.copy()
    # Separate 'T' and 'NT' columns dynamically
    t_cols = [col for col in data.columns if col.startswith('T')]
    nt_cols = [col for col in data.columns if col.startswith('NT')]

    # Calculate the mean of NT columns
    if nt_cols:
        data['Mean_NT'] = data[nt_cols].mean(axis=1)
        # Normalize T columns by the mean of NT columns
        for col in t_cols:
            data[col] = data[col] / data['Mean_NT']
    # Return:
    # - the normalized data: tumor/mean(non-tumor) ratio
    # - the list of T columns
    return data_op, data, t_cols

def calculate_scores(data, t_cols):
    '''
    Given the expression ratio T/mean(NT), given by columns t_cols in data,
    count the number of upregulated and downregulated genes for C1, C2 classification.
    :param data:
    :param t_cols:
    :param threshold_upper:
    :param threshold_lower:
    :return: scores dictionary with column names as keys and scores as values
    '''
    scores = {}
    for col in t_cols:
        # Count the number of genes that are upregulated and downregulated
        # downregulated: C1-genes with T/mean(NT) <= 0.5
        downregulated = (data[col].loc[c1genes] <= 0.5).sum()
        # upregulated: C2-genes with T/mean(NT) >= 2
        upregulated = (data[col].loc[c2genes] >= 2).sum()
        scores[col] = downregulated + upregulated
    return scores

def classify_c1c2(scores, total_genes, vim_values):
    classifications = {}
    for col, score in scores.items():
        percentage = (score / total_genes) * 100
        if 40 <= percentage <= 60:
            classifications[col] = ('Intermediate', '')
        elif percentage < 40:
            classifications[col] = ('C1-subtype', '')
        else:
            if vim_values[col] > 6.5:
                classifications[col] = ('C2B', '')
            else:
                classifications[col] = ('C2-Pure', '') 
    return classifications

def classify_14q32(data, t_cols):
    classification = {}
    for col in t_cols:
        # Number of 14q32-genes overexpressed: T/NT >=10
        genes_overexpressed = (data[col][fqt_genes] >= 10).sum()
        classification[col] = 'Strong' if genes_overexpressed >= 1 else 'Moderate'
    return classification

def classify_epi_qualu(t_cols,qualu_val):
    classification = {}
    for col in t_cols:
        # When Percentage of UnMethylated Alu (PUMA) > 9.67, then Epi-CB
        if pd.isna(qualu_val[col]):
            classification[col] = pd.NA
        elif qualu_val[col] * 100 > 9.67:
            classification[col] = 'Epi-CB'
        else:
            classification[col] = 'Epi-CA'
    return classification

def classify_epi_cpg(t_cols,cpg_val):
    print('cpg_val:',cpg_val)
    classification = {}
    for col in t_cols:
        # When ((1-mean CpGs T/mean CpGs all the NT)*100) > 6.6, then Epi-CB
        if pd.isna(cpg_val[col]):
            classification[col] = pd.NA
        elif cpg_val[col] * 100 > 6.6:
            classification[col] = 'Epi-CB'
        else:
            classification[col] = 'Epi-CA'
    return classification

def classify_mrs(t_cols, class_14q32, class_epi, class_c1c2):
    classification = {}
    for col in t_cols:
        # Strong 14q32 overexpression
        if pd.isna(class_14q32[col]) or pd.isna(class_epi[col]) or pd.isna(class_c1c2[col]):
            classification[col] = pd.NA
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
            classification[col] = 'MRS-2' if class_epi[col][0] == 'Epi-CB' else 'MRS-1'

    return classification

def process_excel(input_file):
    # Calculate
    data_op, data, t_cols = read_and_prepare_data(input_file)
    scores = calculate_scores(data, t_cols)  # Dynamic split

    # Get VIM values
    vim_values = data.loc[vim_gene].to_dict()
    # Exclude 'VIM' column and non-T columns from vim_values if present
    vim_values = {k: vim_values[k] for k in t_cols if k in vim_values}

    # Get CpG values
    cpg_values = data.loc['CpG_Array'].to_dict()
    cpg_values = {k: cpg_values[k] for k in t_cols if k in cpg_values}
    # Get Qualu values
    qualu_values = data.loc['Qualu'].to_dict()
    qualu_values = {k: qualu_values[k] for k in t_cols if k in qualu_values}

    classifications_c1c2 = classify_c1c2(scores, 16, vim_values)
    classifications_14q32 = classify_14q32(data, t_cols)
    classifications_cpg = classify_epi_cpg(t_cols,cpg_values)
    classifications_qualu = classify_epi_qualu(t_cols,qualu_values)
    classifications_mrs = classify_mrs(t_cols, classifications_14q32, classifications_qualu, classifications_c1c2)
    print('classifications_c1c2:',classifications_c1c2)
    print('classifications_14q32:',classifications_14q32)
    print('classifications_cpg:',classifications_cpg)
    print('classifications_qualu:',classifications_qualu)
    # Merge the classifications with column classifications
    for col in classifications_c1c2:
        classifications_c1c2[col] = (classifications_c1c2[col][0],
                                     classifications_14q32[col],
                                     classifications_cpg[col],
                                     classifications_qualu[col],
                                     classifications_mrs[col])

    classification_df = pd.DataFrame([(col, *vals) for col, vals in classifications_c1c2.items()],
                                     columns=['Sample',
                                              'C1-C2 Classification',
                                              '14q32 Classification',
                                              'CpG Classification',
                                              'Qualu Classification',
                                              'MRS Classification'
                                              ])

    return classification_df