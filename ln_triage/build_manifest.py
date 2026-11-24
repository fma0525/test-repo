"""Step 1: build a labelled slide manifest from TCGA (GDC open access).

Label = "does this slide contain lymph node tissue?" Labels are WEAK: GDC stores
anatomic site on the case's diagnosis, not on the slide. So every slide gets a
confidence tier:

  pos_high   metastatic sample (barcode 06) and primary-disease site is a lymph node
  pos_review any other slide whose primary-disease site is a lymph node
             (e.g. SKCM "01" samples recorded at a nodal site, lymphoma DLBC)
  neg_high   slide whose primary-disease site is a reported non-nodal organ
             (includes SKCM skin / soft-tissue metastases = same-source hard negatives)
  neg_low    site not reported, but project is a solid-organ tumour (not SKCM/DLBC)
  exclude    cannot decide (e.g. SKCM metastasis with unreported site)

Training defaults to pos_high + neg_high + neg_low. pos_review goes to
review_sheet.py for a pathologist to confirm.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import gdc_files  # noqa: E402

FIELDS = [
    "file_id", "file_name", "file_size", "md5sum",
    "cases.case_id", "cases.submitter_id", "cases.project.project_id",
    "cases.samples.sample_type",
    "cases.diagnoses.site_of_resection_or_biopsy",
    "cases.diagnoses.diagnosis_is_primary_disease",
    "cases.diagnoses.classification_of_tumor",
]

LYMPHOID_PROJECTS = {"TCGA-DLBC"}       # lymphoma: node replaced by lymphoma -> ambiguous
NODAL_ORIGIN_PROJECTS = {"TCGA-SKCM"}   # project with many nodal metastases


def is_lymph(site: str | None) -> bool:
    return bool(site) and "lymph" in site.lower()


def reported(site: str | None) -> bool:
    return bool(site) and site.lower() not in {"not reported", "unknown", "--"}


def label_slide(hit: dict) -> tuple[str, str]:
    case = hit["cases"][0]
    project = case["project"]["project_id"]
    sample_types = {s.get("sample_type", "").lower() for s in case.get("samples", [])}
    barcode_type = hit["file_name"][13:15]  # TCGA-XX-XXXX-[06]Z-...
    diags = case.get("diagnoses", [])
    prim = [d for d in diags if d.get("diagnosis_is_primary_disease")]
    sites = [d.get("site_of_resection_or_biopsy") for d in (prim or diags)]
    rep = [s for s in sites if reported(s)]
    metastatic = barcode_type == "06" or "metastatic" in sample_types
    any_lymph = any(is_lymph(s) for s in rep)

    if project in LYMPHOID_PROJECTS:
        return "pos_review", "lymphoma (DLBC)"
    if any_lymph and metastatic:
        return "pos_high", "metastatic sample at nodal site"
    if any_lymph:
        return "pos_review", "nodal site recorded but sample not coded metastatic"
    if rep:
        return "neg_high", f"site={rep[0]}"
    if project in NODAL_ORIGIN_PROJECTS:
        return "exclude", "SKCM with unreported site"
    return "neg_low", "site not reported, solid-organ project"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/manifest.csv")
    ap.add_argument("--projects", default="", help="comma list to restrict (debug)")
    args = ap.parse_args()

    filt = [
        {"op": "=", "content": {"field": "data_type", "value": "Slide Image"}},
        {"op": "=", "content": {"field": "experimental_strategy", "value": "Diagnostic Slide"}},
        {"op": "=", "content": {"field": "access", "value": "open"}},
        {"op": "=", "content": {"field": "data_format", "value": "SVS"}},
    ]
    if args.projects:
        filt.append({"op": "in", "content": {"field": "cases.project.project_id",
                                             "value": args.projects.split(",")}})
    hits = gdc_files({"op": "and", "content": filt}, FIELDS)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    counts: dict = {}
    with open(args.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["file_id", "file_name", "file_size", "md5sum", "case_id", "case_submitter_id",
                    "project", "tier", "label", "reason"])
        for h in hits:
            case = h["cases"][0]
            tier, reason = label_slide(h)
            label = 1 if tier.startswith("pos") else (0 if tier.startswith("neg") else "")
            w.writerow([h["file_id"], h["file_name"], h["file_size"], h.get("md5sum", ""),
                        case["case_id"], case["submitter_id"], case["project"]["project_id"],
                        tier, label, reason])
            counts[tier] = counts.get(tier, 0) + 1
    print(json.dumps({"slides": len(hits), "tiers": counts}, indent=1))


if __name__ == "__main__":
    main()
