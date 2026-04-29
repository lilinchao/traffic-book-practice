# AI Engineering Book Practice

This repository contains the open-source practice materials for a programming, AI, data, and engineering practice book.

## What Is Inside

- Chapter practice guides
- Starter projects and reference solutions
- Datasets and experiment notes
- Engineering checklists
- Extra reading and errata

## Dataset Catalog

Traffic data sources for chapters 4-8 are listed in:

- `datasets.html`
- `DATASETS.md`

Small downloaded case datasets are stored in `data/raw/`.

To refresh them:

```bash
bash scripts/download_case_data.sh
```

## Notebooks

Chapter notebooks are stored in `notebooks/`.

Install dependencies:

```bash
pip install -r requirements.txt
```

Run chapter 4:

```bash
jupyter notebook notebooks/chapter-04/traffic_accident_panel_analysis.ipynb
```

## Website

This repository is designed to work directly with GitHub Pages.

After pushing to GitHub:

1. Open the repository on GitHub.
2. Go to `Settings` -> `Pages`.
3. Under `Build and deployment`, choose `Deploy from a branch`.
4. Select the `main` branch and `/root`.
5. Save the setting.

Your site will be available at:

```text
https://<your-github-username>.github.io/<repository-name>/
```

## Local Preview

Open `index.html` in your browser, or run a simple local server:

```bash
python3 -m http.server 8000
```

Then visit:

```text
http://localhost:8000
```

## Suggested Structure

```text
chapters/
  01-getting-started/
    README.md
    exercises.md
    starter/
    solution/
assets/
  datasets/
  images/
templates/
  chapter/
```

## License

Code examples are released under the MIT License.

Text and learning materials are released under CC BY 4.0 unless otherwise noted.
