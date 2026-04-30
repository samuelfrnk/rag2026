const CATEGORY_MAP = {
    "ai":        "Artificial Intelligence",
    "ao-ph":     "Atmospheric and Oceanic Physics",
    "ce":        "Computational Engineering, Finance & Science",
    "cg":        "Computational Geometry",
    "cl":        "Computation and Language (NLP)",
    "co":        "Computational Complexity",
    "comp-ph":   "Computational Physics",
    "cond-mat":  "Condensed Matter",
    "cr":        "Cryptography and Security",
    "cs":        "Computer Science",
    "cv":        "Computer Vision",
    "cy":        "Computers and Society",
    "data-an":   "Data Analysis, Statistics and Probability",
    "db":        "Databases",
    "ds":        "Data Structures and Algorithms",
    "econ":      "Economics",
    "eess":      "Electrical Engineering and Systems Science",
    "em":        "Econometrics",
    "et":        "Emerging Technologies",
    "geo-ph":    "Geophysics",
    "gn":        "Genomics",
    "gr":        "Graphics",
    "hc":        "Human-Computer Interaction",
    "it":        "Information Theory",
    "iv":        "Image and Video Processing",
    "lg":        "Machine Learning", // UNSURE ???
    "math":      "Mathematics",
    "me":        "Methodology (Statistics)",
    "ml":        "Machine Learning",
    "mm":        "Multimedia",
    "na":        "Numerical Analysis",
    "nc":        "Neural and Evolutionary Computing",
    "ne":        "Neural and Evolutionary Computing",
    "physics":   "Physics",
    "pr":        "Probability",
    "q-bio":     "Quantitative Biology",
    "qm":        "Quantitative Methods (Biology)",
    "ro":        "Robotics",
    "se":        "Software Engineering",
    "st":        "Statistics Theory",
    "stat":      "Statistics",
    "stat-mech": "Statistical Mechanics",
    "sy":        "Systems and Control",
};

/**
 * Takes a list of raw category tags (e.g. ["cs.cv", "stat.ml"]),
 * splits each at ".", looks up every part, and returns a unique
 * set of written-out labels.
 */

export function resolveCategories(rawTags) {
    if (!rawTags) return [];

    const seen = new Set();
    const resolved = [];

    for (const tag of rawTags) {
        const parts = tag.toLowerCase().split(".");
        for (const part of parts) {
            const label = CATEGORY_MAP[part];
            if (label && !seen.has(label)) {
                seen.add(label);
                resolved.push(label);
            }
        }
    }

    return resolved;
}