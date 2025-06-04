import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import PatternFill

def chain_ladder_to_excel(input_csv, output_excel):
    """
    Process insurance fraud data using Chain Ladder method with dynamic link ratios
    and export results to an Excel file with two sheets:
    1. Link Ratios - All calculated development factors
    2. Forecasted - Complete run-off triangle with extrapolated values
    """
    
    # =============================================
    # PART 1: LOAD AND PREPARE DATA
    # =============================================
    try:
        df = pd.read_csv(input_csv)
        print("Data loaded successfully")
        
        # Clean column names and set index
        df.columns = df.columns.str.strip()
        if 'FraudMonth' in df.columns:
            df = df.set_index('FraudMonth')
        
        # Identify numeric columns as lag periods (excluding non-numeric columns)
        lag_cols = [col for col in df.columns if str(col).isdigit()]
        if not lag_cols:
            raise ValueError("No numeric lag columns found")
            
        # Sort lag columns numerically
        lag_cols = sorted(lag_cols, key=lambda x: int(x))
        print(f"Identified lag periods: {lag_cols}")
            
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return

    # =============================================
    # PART 2: DYNAMIC CHAIN LADDER PROCESSING
    # =============================================
    forecast_df = df.copy()
    lr_history = []
    
    # Process each development period
    for i in range(len(lag_cols)-1):
        current_lag = str(lag_cols[i])  # Ensure string type
        next_lag = str(lag_cols[i+1])   # Ensure string type
        
        # Calculate initial link ratio
        valid_pairs = forecast_df[[current_lag, next_lag]].dropna()
        if len(valid_pairs) < 2:
            print(f"Insufficient data to calculate {current_lag}→{next_lag} ratio")
            continue
            
        numerator = valid_pairs[next_lag].sum()
        denominator = valid_pairs[current_lag].sum()
        lr = numerator / denominator
        lr_history.append({
            'From Lag': current_lag,
            'To Lag': next_lag,
            'Ratio': lr,
            'Note': 'Initial calculation'
        })
        
        # Extrapolate missing values
        mask = forecast_df[current_lag].notna() & forecast_df[next_lag].isna()
        forecast_df.loc[mask, next_lag] = forecast_df.loc[mask, current_lag] * lr
        
        # Recalculate ratio with new data
        new_numerator = forecast_df[next_lag].sum()
        new_denominator = forecast_df[current_lag].sum()
        new_lr = new_numerator / new_denominator
        lr_history.append({
            'From Lag': current_lag,
            'To Lag': next_lag,
            'Ratio': new_lr,
            'Note': 'After extrapolation'
        })
        
        # Update forecasts with refined ratio
        forecast_df.loc[mask, next_lag] = forecast_df.loc[mask, current_lag] * new_lr

    # =============================================
    # PART 3: CREATE EXCEL OUTPUT
    # =============================================
    try:
        # Create workbook and sheets
        wb = Workbook()
        wb.remove(wb.active)  # Remove default sheet
        
        # Sheet 1: Link Ratio History / Development factor
        ws_lr = wb.create_sheet("Link Ratios")
        lr_df = pd.DataFrame(lr_history)
        for r in dataframe_to_rows(lr_df, index=False, header=True):
            ws_lr.append(r)
        
        # Sheet 2: Forecasted Triangle
        ws_fc = wb.create_sheet("Forecasted")
        
        # Highlight extrapolated cells
        fill = PatternFill(start_color='FFFF00', end_color='FFFF00', fill_type='solid')
        
        for r in dataframe_to_rows(forecast_df.reset_index(), index=False, header=True):
            ws_fc.append(r)
        
        # Apply formatting to header row
        for cell in ws_fc[1]:
            cell.fill = PatternFill(start_color='D3D3D3', fill_type='solid')
        
        # Identify and highlight extrapolated cells
        original_df = df.copy()
        for col in lag_cols:
            col_idx = forecast_df.columns.get_loc(col) + 2  # +2 for index and header offset
            for row_idx in range(2, len(forecast_df)+2):
                original_val = original_df.iloc[row_idx-2, original_df.columns.get_loc(col)] if col in original_df.columns else None
                current_val = forecast_df.iloc[row_idx-2, forecast_df.columns.get_loc(col)]
                if pd.isna(original_val) and not pd.isna(current_val):
                    ws_fc.cell(row=row_idx, column=col_idx).fill = fill
        
        # Save the workbook
        wb.save(output_excel)
        print(f"Results saved to {output_excel}")
        
    except Exception as e:
        print(f"Error saving Excel file: {str(e)}")

chain_ladder_to_excel(
    input_csv="insurance_fraud_chain_ladder_data.csv",
    output_excel="chain_ladder_results.xlsx"
)
