# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Recompute every number the labs, their reference solutions and the debrief slides quote, from
labs/files, and check the planted problems are where the answer key says.

    uv run labs/solutions/check.py          # all labs
    uv run labs/solutions/check.py 2.1 2.4  # some labs

Standard library only. Writes nothing and calls no model: the model steps of lab 2.1 and the
AI-drafted section of lab 2.4 are scripted (standin.json and files/review/section3_draft.md).
"""
import csv
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = HERE.parent / "files"
SOL = HERE
sys.stdout.reconfigure(encoding="utf-8")
STANDIN = json.loads((HERE / "standin.json").read_text(encoding="utf-8"))
REF = json.loads((HERE / "reference.json").read_text(encoding="utf-8"))


def read_csv(rel):
    with (FILES / rel).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def text(rel):
    return (FILES / rel).read_text(encoding="utf-8")


def e01():
    rows = read_csv("pack/E01_enquiries_by_month.csv")
    total, cat, mins, ch = 0, {}, {}, {}
    for r in rows:
        k, h = int(r["enquiries"]), float(r["avg_handling_minutes"])
        total += k
        cat[r["category_id"]] = cat.get(r["category_id"], 0) + k
        mins[r["category_id"]] = mins.get(r["category_id"], 0.0) + k * h
        ch[r["channel"]] = ch.get(r["channel"], 0) + k
    return total, cat, mins, ch


def options():
    total, cat, mins, ch = e01()
    cpm = float(re.search(r"(\d+\.\d\d) ريال", text("pack/E05_contact_centre_costs.md")).group(1))
    out = {}
    for r in read_csv("pack/E12_options_costs.csv"):
        lo = hi = 0.0
        for part in r["benefit_assumption_share_of_handled_minutes_saved"].split("؛"):
            m = re.match(r"\s*(c\d): (\d+)% إلى (\d+)%", part)
            lo += mins[m.group(1)] * int(m.group(2)) / 100
            hi += mins[m.group(1)] * int(m.group(3)) / 100
        cost3 = int(r["setup_sar"]) + 3 * int(r["annual_sar"]) + int(r["one_off_year2_sar"])
        assert cost3 == int(r["three_year_total_sar"]), r["option"]
        out[r["option"]] = dict(cost3=cost3, min_lo=round(lo), min_hi=round(hi),
                                sar_lo=round(lo * cpm), sar_hi=round(hi * cpm))
    return out, cpm


def lab_1_2():
    t = text("roles/call_sponsor.md")
    for must in ["عشرة أسابيع", "مليون ونصف", "مرزام", "كراسة الطرح"]:
        assert must in t, must
    d = text("roles/call_director.md")
    assert "أوقفته مسؤولة حماية البيانات" in d and "أنمار" in d
    ref = text("start/scope_note_reference.md")
    assert ref.count("## ") == 8, "seven sections and the stakeholder map"
    assert "كراسة الطرح" in ref.split("## 3.")[1].split("## 4.")[0], "the tender stays out of scope"
    rows = [l for l in ref.splitlines() if l.startswith("| ") and "---" not in l][1:]
    assert len(rows) == 6, rows
    print("1.2  reference scope note: 7 sections, tender excluded, 6 stakeholders mapped")


def lab_1_4():
    cards = sorted(p.name for p in (FILES / "roles").glob("w*.md"))
    assert len(cards) == 6, cards
    brief = text("workshop/brief.md")
    for pair in ["w1 (الراعي) وw5", "w2 (خدمات المستفيدين) وw6", "w3 (تقنية المعلومات) وw4"]:
        assert pair in brief, pair
    sheet = text("templates/observer_sheet.md")
    behaviours = [l for l in sheet.splitlines() if re.match(r"\| [1-5] \|", l)]
    assert len(behaviours) == 5
    ref = text("start/decision_record_reference.md")
    weights = [int(x) for x in re.findall(r"^\| K\d \| .+? \| (\d+) \|", ref, re.M)]
    assert weights == [30, 25, 15, 15, 15] and sum(weights) == 100, weights
    assert len(re.findall(r"^\d\. ", ref.split("## الشروط")[1].split("## من")[0], re.M)) == 3
    # The pass mark on the observer sheet: 60% of 20 is 12
    print("1.4  six cards in three pairs, 5 behaviours (max 20, 60% = 12), weights", weights, "sum", sum(weights))


def lab_2_1():
    total, cat, mins, ch = e01()
    o, cpm = options()
    idx = text("pack/pack_index.md")
    public = re.findall(r"^\| (E\d\d) \| .+\| عام", idx, re.M)
    assert public == ["E01", "E02", "E03", "E04", "E10"], public
    weights = REF["weights"]
    scores = REF["reference_scores"]
    weighted = {k: sum(weights[c] * v for c, v in s.items()) / 100 for k, s in scores.items()}
    print(f"2.1  enquiries {total:,}; minutes {round(sum(mins.values())):,}; cost per minute {cpm}")
    for c in sorted(cat):
        print(f"     {c} {cat[c]:,} ({100 * cat[c] / total:.1f}%) minutes {round(mins[c]):,}")
    for k, v in o.items():
        print(f"     option {k}: 3-year {v['cost3']:,} SAR; minutes saved {v['min_lo']:,} to {v['min_hi']:,}; "
              f"SAR {v['sar_lo']:,} to {v['sar_hi']:,} a year; weighted {weighted[k]:.2f}")
    f = {r["service"]: (int(r["started_online"]), int(r["completed_online"])) for r in read_csv("pack/E04_portal_funnel.csv")}
    for s, (a, b) in f.items():
        print(f"     portal {s}: {b:,} of {a:,} ({100 * b / a:.1f}%)")
    kb = read_csv("pack/E03_kb_inventory.csv")
    stale = sum(1 for r in kb if int(r["months_since_review"]) > 12)
    print(f"     KB {len(kb)} articles, restricted {sum(1 for r in kb if r['classification'] == 'مقيد')}, "
          f"over 12 months {stale}, no owner {sum(1 for r in kb if not r['owner'])}")
    ref = (SOL / "D2_1_options_paper.md").read_text(encoding="utf-8")
    for k, v in o.items():
        assert f"{v['cost3']:,}" in ref, (k, "cost")
        assert f"{v['sar_lo']:,}" in ref and f"{v['sar_hi']:,}" in ref, (k, "benefit range")
        assert f"{weighted[k]:.2f}" in ref, (k, "weighted")
    assert weighted["B"] > weighted["C"] > weighted["A"]
    survey = read_csv("pack/E02_resident_survey.csv")
    chat = [r for r in survey if r["question_id"] == "Q1"][0]
    staff = [r for r in survey if r["question_id"] == "Q2"][2]
    for r in (chat, staff):
        share = f"{int(r['respondents']):,} ({100 * int(r['respondents']) / int(r['sample']):.1f}%)"
        assert share in ref, share
        print("     survey", r["question_id"], share)
    for c in ("c3", "c4", "c2", "c1"):
        assert f"{round(mins[c]):,}" in ref, c
    print("     stand-in structure has", len(STANDIN["structure_2_1"]), "headings; reference paper numbers agree")


def lab_2_4():
    total, cat, mins, ch = e01()
    d = text("review/section3_draft.md")
    phone = ch["هاتف"]
    survey = read_csv("pack/E02_resident_survey.csv")
    q4 = [r for r in survey if r["question_id"] == "Q4"]
    sat = int(q4[0]["respondents"]) / int(q4[0]["sample"])
    refund = [r for r in read_csv("pack/E04_portal_funnel.csv") if r["service"].startswith("إلغاء")][0]
    planted = {
        "D1 inconsistent total": f"{total + 5400:,}" in d and f"**{total:,}**" in d,
        "D2 share on the wrong base": f"{100 * cat['c1'] / phone:.1f}%" in d and f"{100 * cat['c1'] / total:.1f}%" not in d,
        "D3 invented citation": "Meridian Service Institute" in d,
        "D4 untraceable target": "إلى 85%" in d,
        "D5 national text misstated": "تسمح مبادئ الذكاء الاصطناعي التوليدي" in d and "المقيدة" in d,
        "D6 no AI-use disclosure": "مسودة أولى من النموذج المستضاف" in d and "الإفصاح" not in d,
    }
    for k, ok in planted.items():
        assert ok, k
    true_claims = {
        "over half by phone": phone / total > 0.5,
        "complaints longest handling": max(mins, key=lambda c: mins[c] / cat[c]) == "c5",
        "complaints minutes": f"{mins['c5'] / cat['c5']:.1f}" in d,
        "refund completion": f"{100 * int(refund['completed_online']) / int(refund['started_online']):.1f}%" in d,
        "satisfaction today": f"{100 * sat:.1f}%" in d,
        "quote excludes integration": "لا يشمل العرض التكامل" in text("pack/E06_vendor_quote.md"),
    }
    for k, ok in true_claims.items():
        assert ok, k
    key = (SOL / "D2_4_review_conduct.md").read_text(encoding="utf-8")
    assert len(re.findall(r"^\| D\d \|", key, re.M)) == 6
    assert len(re.findall(r"^### البطاقة \d", key, re.M)) == 6
    assert "«عدم إدخال أي بيانات تصنف على مستوى مقيد فأعلى (مقيد، وسري، وسري للغاية)»" in key
    print(f"2.4  six planted defects present; six true claims hold (phone {phone:,} of {total:,}, "
          f"c1 share {100 * cat['c1'] / total:.1f}% not {100 * cat['c1'] / phone:.1f}%); six cards keyed")


LABS = {"1.2": lab_1_2, "1.4": lab_1_4, "2.1": lab_2_1, "2.4": lab_2_4}

if __name__ == "__main__":
    wanted = sys.argv[1:] or list(LABS)
    for k in wanted:
        LABS[k]()
    print("PASS", " ".join(wanted))
