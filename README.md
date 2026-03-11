# eMFace-Report_Extraction_FC-List

Generate a FC-list from the eMFace-Report to trigger Docu-Workflow.

## EMFace Extract

Kleines Tool, das eine EMFace-Report-Textdatei einliest und die geforderten Informationen als HTML ausgibt.

## Voraussetzungen
- Python 3.10+ (getestet mit 3.12)

## Nutzung

```powershell
python .\emface_extract.py .\<<eMFace-Report.txt>>
```

Optional mit eigener Ausgabedatei:

```powershell
python .\emface_extract.py .\<<eMFace-Report.txt>> -o .\<<output.html>>
```

Zusätzlich wird eine JSON-Datei mit gleichem Namen erzeugt (z.B. `<<output.json>>`).

Beispiel-Runner:

```powershell
python .\run_example.py
```
