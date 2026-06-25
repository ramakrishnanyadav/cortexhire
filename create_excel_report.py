import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_excel_report():
    csv_path = Path("outputs/ranked_candidates.csv")
    excel_path = Path("outputs/CortexHire_Ranked_Candidates_FINAL.xlsx")
    
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        return
        
    try:
        # Read the CSV
        df = pd.read_csv(csv_path)
        
        # Create a Pandas Excel writer using XlsxWriter as the engine.
        writer = pd.ExcelWriter(excel_path, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Top 100 Candidates', index=False)
        
        # Get the xlsxwriter workbook and worksheet objects.
        workbook  = writer.book
        worksheet = writer.sheets['Top 100 Candidates']
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#1E3A8A', # Dark blue header
            'font_color': 'white',
            'border': 1
        })
        
        cell_format = workbook.add_format({
            'valign': 'top',
            'border': 1
        })
        
        wrap_format = workbook.add_format({
            'text_wrap': True,
            'valign': 'top',
            'border': 1
        })
        
        score_format = workbook.add_format({
            'num_format': '0.0000',
            'valign': 'top',
            'border': 1
        })
        
        # Write the column headers with the defined format.
        for col_num, value in enumerate(df.columns.values):
            # Capitalize and format header names (e.g., candidate_id -> Candidate ID)
            display_name = str(value).replace('_', ' ').title()
            worksheet.write(0, col_num, display_name, header_format)
            
        # Format the columns
        # Candidate ID
        worksheet.set_column('A:A', 20, cell_format)
        # Rank
        worksheet.set_column('B:B', 10, cell_format)
        # Score
        worksheet.set_column('C:C', 15, score_format)
        # Reasoning
        worksheet.set_column('D:D', 100, wrap_format)
        
        # Add a light alternating row color
        row_format = workbook.add_format({'bg_color': '#F3F4F6', 'border': 1, 'valign': 'top'})
        row_format_wrap = workbook.add_format({'bg_color': '#F3F4F6', 'border': 1, 'text_wrap': True, 'valign': 'top'})
        
        for row in range(1, len(df) + 1):
            if row % 2 == 0: # Apply alternate color to even rows
                worksheet.set_row(row, cell_format=row_format)
                # Ensure the reasoning column still wraps in alternate rows
                worksheet.write(row, 3, df.iloc[row-1, 3], row_format_wrap)

        writer.close()
        logger.info(f"Successfully generated professional Excel report at: {excel_path.absolute()}")
        
    except ImportError:
        logger.error("Please install pandas and xlsxwriter: pip install pandas xlsxwriter")
    except Exception as e:
        logger.error(f"Failed to generate Excel report: {e}")

if __name__ == "__main__":
    create_excel_report()
