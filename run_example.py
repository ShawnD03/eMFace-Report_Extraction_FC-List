from pathlib import Path
from emface_extract import run


def main() -> None:
    input_path = Path("MG1CS039MC_05B0_emface_report.txt")
    output_path = run(input_path)
    print(f"Fertig: {output_path}")


if __name__ == "__main__":
    main()
