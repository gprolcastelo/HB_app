import pandas as pd
global c1genes, c2genes, vim_gene, fqt_genes, hk_genes
c1genes= ['ALDH2', 'APCS', 'APOC4', 'AQP9', 'C1S', 'CYP2E1', 'GHR', 'HPD'] # 8 genes
c2genes = ['AFP', 'BUB1', 'DLG7', 'DUSP9', 'E2F5', 'IGSF1', 'NLE', 'RPL10A'] # 8 genes
vim_gene = 'VIM' # 1 gene
fqt_genes = ['DLK1', 'MEG3'] # 2 genes
hk_genes = ['ACTGA1', 'EEF1A1', 'PNN', 'RHOT2'] # 5 genes
def read_and_prepare_data(file_path):
    # Load the dataset, assuming the first column is 'GENE'
    data = pd.read_excel(file_path, engine='openpyxl', index_col=0)

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
    return data, t_cols

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
        # print('col:', col)
        # Count the number of genes that are upregulated and downregulated
        # downregulated: C1-genes with T/mean(NT) <= 0.5
        downregulated = (data[col].loc[c1genes] <= 0.5).sum()
        # upregulated: C2-genes with T/mean(NT) >= 2
        upregulated = (data[col].loc[c2genes] >= 2).sum()
        # print('downregulated:', downregulated)
        # print('upregulated:', upregulated)
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
    threshold = 10
    num_rows = 4
    classification = {}
    for col in t_cols:
        # Number of 14q32-genes overexpressed: T/NT >=10
        genes_overexpressed = (data[col][fqt_genes] >= threshold).sum()
        classification[col] = 'Strong' if genes_overexpressed >= 1 else 'Moderate'
    return classification

def process_excel(input_file):
    # Calculate
    data, t_cols = read_and_prepare_data(input_file)
    scores = calculate_scores(data, t_cols)  # Dynamic split
    
    # Assume last row of data contains VIM values
    vim_values = data.loc[vim_gene].to_dict()
    # Exclude 'VIM' column and non-T columns from vim_values if present
    vim_values = {k: vim_values[k] for k in t_cols if k in vim_values}
    
    classifications = classify_c1c2(scores, 16, vim_values)
    column_classifications = classify_14q32(data, t_cols)
    
    # Merge the classifications with column classifications
    for col in classifications:
        classifications[col] = (classifications[col][0], column_classifications[col])
    
    classification_df = pd.DataFrame([(col, *vals) for col, vals in classifications.items()],
                                     columns=['Sample', 'C1-C2 Classification', '14q32 Classification'])
    
    return classification_df