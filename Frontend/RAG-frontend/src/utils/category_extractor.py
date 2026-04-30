import csv
import ast
from pathlib import Path

#########################################################################################################
ARXIV_TERMS = {
    "ai":           "Artificial Intelligence",
    "ao-ph":        "Atmospheric and Oceanic Physics",
    "ce":           "Computational Engineering, Finance, and Science",
    "cg":           "Computational Geometry",
    "cl":           "Computation and Language (NLP)",
    "co":           "Computational Complexity",
    "comp-ph":      "Computational Physics",
    "cond-mat":     "Condensed Matter",
    "cr":           "Cryptography and Security",
    "cs":           "Computer Science",
    "cv":           "Computer Vision and Pattern Recognition",
    "cy":           "Computers and Society",
    "data-an":      "Data Analysis, Statistics and Probability",
    "db":           "Databases",
    "ds":           "Data Structures and Algorithms",
    "econ":         "Economics",
    "eess":         "Electrical Engineering and Systems Science",
    "em":           "Econometrics",
    "et":           "Emerging Technologies",
    "geo-ph":       "Geophysics",
    "gn":           "Genomics",
    "gr":           "Graphics",
    "hc":           "Human-Computer Interaction",
    "it":           "Information Theory",
    "iv":           "Image and Video Processing",
    "lg":           "Machine Learning", # UNSURE ?
    "math":         "Mathematics",
    "me":           "Methodology (Statistics)",
    "ml":           "Machine Learning",
    "mm":           "Multimedia",
    "na":           "Numerical Analysis",
    "nc":           "Neural and Evolutionary Computing",
    "ne":           "Neural and Evolutionary Computing",
    "physics":      "Physics",
    "pr":           "Probability",
    "q-bio":        "Quantitative Biology",
    "qm":           "Quantitative Methods (Biology)",
    "ro":           "Robotics",
    "se":           "Software Engineering",
    "st":           "Statistics Theory",
    "stat":         "Statistics",
    "stat-mech":    "Statistical Mechanics",
    "sy":           "Systems and Control"
}
###############################################################################################################################

def extract_unique_terms(input_path: str, output_path: str) -> None:
    input_file = Path(input_path)
    output_file = Path(output_path)

    unique_terms = set()

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(input_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw = row["terms"].strip()
            try:
                # Parse the list string e.g. "['cs.cv', 'cs.ai']"
                terms_list = ast.literal_eval(raw)
                for term in terms_list:
                    if "." in term:
                        terms = term.split(".")
                        for t in terms:
                            unique_terms.add(t.strip())
                    else:
                        unique_terms.add(term.strip())
            except (ValueError, SyntaxError):
                # Fallback: treat the cell as a plain single term
                if raw:
                    unique_terms.add(raw)

    sorted_terms = sorted(unique_terms)

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["term"])
        for term in sorted_terms:
            writer.writerow([term])

    # Terminal statistics
    print("=" * 50)
    print("  Unique Terms Extraction — Summary")
    print("=" * 50)
    print(f"  Input file  : {input_file.resolve()}")
    print(f"  Output file : {output_file.resolve()}")
    print(f"  Unique terms: {len(sorted_terms)}")
    print("-" * 50)
    print("  Terms found:")
    for term in sorted_terms:
        print(f"    • {term}")
    print("=" * 50)


def map_terms_to_categories(terms: list) -> dict:
    category_mapping = {}
    for term in terms:
        category_mapping[term] = ARXIV_TERMS.get(term, "Unknown Category")
    return category_mapping

def write_mapped_terms(terms: list, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mapping = map_terms_to_categories(terms)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["term", "full_name"])
        for term, full_name in sorted(mapping.items()):
            writer.writerow([term, full_name])

    unknown = [t for t, v in mapping.items() if v == "Unknown Category"]
    print(f"\n  Mapped terms saved to : {output_path.resolve()}")
    print(f"  Successfully mapped   : {len(mapping) - len(unknown)}/{len(mapping)}")
    if unknown:
        print(f"  ⚠ Unknown (not in dict): {', '.join(sorted(unknown))}")


if __name__ == "__main__":
    BASE_DIR    = Path(__file__).parent         
    INPUT_PATH  = BASE_DIR / "../../data/category/arxiv_scrape_1_cleaned.csv"       
    OUTPUT_PATH = BASE_DIR / "../../data/category/unique_terms_undefined.csv"    
    OUTPUT_PATH_MAPPED = BASE_DIR / "../../data/category/unique_terms_mapped.csv"

    extract_unique_terms(INPUT_PATH, OUTPUT_PATH)

    # Read back the extracted terms and write the mapped version
    sorted_terms = [row["term"] for row in csv.DictReader(open(OUTPUT_PATH, encoding="utf-8"))]
    write_mapped_terms(sorted_terms, OUTPUT_PATH_MAPPED)