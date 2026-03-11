# eMFace-Report_Extraction_FC-List

Generate a FC-list from the eMFace-Report to trigger Docu-Workflow.

## EMFace Extract

Small tool that reads an eMFace report text file and outputs the required information as HTML.

## Requirements
- Python 3.10+ (tested with 3.12)

## Usage

```powershell
python .\emface_extract.py .\<<eMFace-Report.txt>>
```

Optional with a custom output file:

```powershell
python .\emface_extract.py .\<<eMFace-Report.txt>> -o .\<<output.html>>
```

Additionally, a JSON file with the same base name is generated (e.g., `<<output.json>>`).

Example runner:

```powershell
python .\run_example.py
```
