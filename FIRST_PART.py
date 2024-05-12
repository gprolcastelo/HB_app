import pandas as pd

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
    return data, t_cols

def calculate_scores(data, t_cols, threshold_upper=2, threshold_lower=0.5, index_split=8):
    scores = {}
    for col in t_cols:
        above_threshold = (data[col][:index_split] > threshold_upper).sum()
        below_threshold = (data[col][index_split:] < threshold_lower).sum()
        scores[col] = above_threshold + below_threshold
    return scores

def classify_scores(scores, total_genes, vim_values):
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

def classify_columns(data, t_cols):
    threshold = 10
    num_rows = 4
    classification = {}
    for col in t_cols:
        count_above_threshold = (data[col][:num_rows] > threshold).sum()
        classification[col] = 'Strong' if count_above_threshold >= 3 else 'Moderate'
    return classification

def process_excel(input_file):
    data, t_cols = read_and_prepare_data(input_file)
    scores = calculate_scores(data, t_cols, index_split=len(data.index)//2)  # Dynamic split
    
    # Assume last row of data contains VIM values
    vim_values = data.iloc[-1].to_dict()
    # Exclude 'VIM' column and non-T columns from vim_values if present
    vim_values = {k: vim_values[k] for k in t_cols if k in vim_values}
    
    classifications = classify_scores(scores, len(data.index), vim_values)
    column_classifications = classify_columns(data, t_cols)
    
    # Merge the classifications with column classifications
    for col in classifications:
        classifications[col] = (classifications[col][0], column_classifications[col])
    
    classification_df = pd.DataFrame([(col, *vals) for col, vals in classifications.items()], columns=['Sample', 'Classification', '14q32 OE'])
    
    return classification_df