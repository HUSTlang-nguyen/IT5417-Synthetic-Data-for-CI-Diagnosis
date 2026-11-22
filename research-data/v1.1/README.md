# CI diagnosis pilot v1.1 portable

351marked-silver records:175real train,37validation,38test,101synthetic train.

Input and reference/assessment are separate. Never supply held-out references, assessments or provenance repair patches to retrieval/model prompts. Labels are not expert gold. This derived snapshot does not replace the original training lock or enable checkpoint resume on another machine.

Run `python -m ci_demo.portable_dataset --check research-data/v1.1`. No raw runs, Docker or model required.

See attribution.json and LICENSES/NOTICES for original licenses, copyright notices, source revisions and synthetic changes. Generic /home/user/root_dir strings in pytest9064 are upstream expected diagnostic fixtures, retained verbatim; local Ollama Modelfile paths were omitted only from derived metadata with original hashes preserved. Raw evidence remains in external archives and is not reproduced by this package.
