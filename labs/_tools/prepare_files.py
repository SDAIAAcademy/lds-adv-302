# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Write the synthetic file pack of the Shawt case into labs/files/.

    uv run labs/_tools/prepare_files.py

Standard library only, seed 302: the same bytes on every run. Every organisation, person,
figure and document is invented. The texts live in texts.py beside this file; the numbers are
drawn here and pushed into the texts, so the pack, the seeded section and the solutions agree.
"""
import csv
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import texts as T  # noqa: E402

FILES = HERE.parent / "files"
SEED = 302
sys.stdout.reconfigure(encoding="utf-8")

CATS = [
    ("c1", "مواعيد العمل والأسعار والقواعد", 0.31, 3.2),
    ("c2", "المساعدة في حجز الملاعب والقاعات", 0.19, 6.5),
    ("c3", "إلغاء الحجز واسترداد المبلغ", 0.15, 9.8),
    ("c4", "التسجيل في أكاديميات الناشئين", 0.14, 8.4),
    ("c5", "الشكاوى والبلاغات", 0.10, 11.5),
    ("c6", "المفقودات", 0.05, 4.0),
    ("c7", "أخرى", 0.06, 5.0),
]
SEASON = [1.35, 1.25, 1.0, 0.9, 0.85, 0.8, 0.8, 1.15, 1.05, 0.95, 0.95, 0.95]
CHANNELS = [("هاتف", 0.58), ("بريد إلكتروني", 0.17), ("نموذج الموقع", 0.18), ("حضوري", 0.07)]
COST_PER_MINUTE = 2.10  # SAR per handled agent minute, fully loaded (E05)


def write(rel, text):
    p = FILES / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text.strip() + "\n", encoding="utf-8", newline="\n")


def write_csv(rel, header, rows):
    p = FILES / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def enquiries(rng):
    base = 41800 / sum(SEASON)
    rows = []
    for m in range(12):
        for cid, name, share, handle in CATS:
            mult = SEASON[m] * (1.6 if cid == "c4" and m in (7, 8) else 1.0)
            n = base * share * mult * rng.uniform(0.93, 1.07)
            for ch, p in CHANNELS:
                count = round(n * p * rng.uniform(0.9, 1.1))
                h = round(handle * rng.uniform(0.92, 1.08), 1)
                rows.append([m + 1, cid, name, ch, count, h])
    return rows


def survey(rng):
    n = 1240
    blocks = []
    q1 = [("محادثة على الموقع أو التطبيق", 0.34), ("الهاتف", 0.29), ("الخدمة الذاتية في البوابة", 0.26),
          ("البريد الإلكتروني", 0.07), ("الحضور إلى المرفق", 0.04)]
    q2 = [("أثق بها", 0.18), ("أثق بها إن عُرض علي مصدرها", 0.27), ("أفضّل موظفًا", 0.49), ("لا أعرف", 0.06)]
    q3 = [("نعم", 0.61), ("لا", 0.39)]
    q4 = [("راضٍ أو راضٍ جدًا", 0.58), ("محايد", 0.17), ("غير راضٍ", 0.25)]
    qs = [
        ("Q1", "أي قناة تفضّل لسؤال سريع عن المواعيد أو الأسعار؟", q1),
        ("Q2", "هل تثق بإجابة آلية عن استرداد المبلغ؟", q2),
        ("Q3", "هل حاولت إلغاء حجز أو طلب استرداد عبر البوابة في آخر سنة؟", q3),
        ("Q4", "ما رضاك عن آخر تواصل مع خدمة المستفيدين؟", q4),
    ]
    rows = []
    for qid, text, opts in qs:
        counts = [round(n * s * rng.uniform(0.97, 1.03)) for _, s in opts]
        counts[-1] += n - sum(counts)
        for (label, _), c in zip(opts, counts):
            rows.append([qid, text, label, c, n])
        blocks.append((qid, dict(zip([o[0] for o in opts], counts))))
    return rows, dict(blocks), n


def kb(rng):
    topics = ["مواعيد", "أسعار", "قواعد الاستخدام", "الحجز", "الإلغاء والاسترداد", "الأكاديميات", "المسابح",
              "الصالات", "المفقودات", "الشكاوى", "إجراءات داخلية"]
    rows = []
    for i in range(1, 121):
        t = topics[(i - 1) % len(topics)]
        internal = t == "إجراءات داخلية" or rng.random() < 0.10
        cls = "مقيد" if internal else "عام"
        months = rng.choice([2, 3, 5, 7, 9, 11, 14, 18, 22, 27]) if rng.random() < 0.75 else rng.randint(1, 11)
        owner = "" if rng.random() < 0.14 else rng.choice(["خدمة المستفيدين", "إدارة المرافق", "الأكاديميات", "المالية"])
        rows.append([f"KB-{i:03d}", f"{t}: مقال {i}", t, cls, months, owner])
    return rows


def funnel():
    return [
        ["حجز ملعب أو قاعة", 18640, 15287],
        ["إلغاء حجز وطلب استرداد", 4120, 906],
        ["تسجيل في أكاديمية", 3380, 1386],
        ["تحديث بيانات ولي الأمر", 1210, 1102],
    ]


def main():
    rng = random.Random(SEED)
    FILES.mkdir(parents=True, exist_ok=True)

    e01 = enquiries(rng)
    write_csv("pack/E01_enquiries_by_month.csv",
              ["month", "category_id", "category", "channel", "enquiries", "avg_handling_minutes"], e01)
    total = sum(r[4] for r in e01)
    by_cat = {c[0]: 0 for c in CATS}
    mins_cat = {c[0]: 0.0 for c in CATS}
    by_ch = {}
    for r in e01:
        by_cat[r[1]] += r[4]
        mins_cat[r[1]] += r[4] * r[5]
        by_ch[r[3]] = by_ch.get(r[3], 0) + r[4]
    phone = by_ch["هاتف"]

    s_rows, s, n_survey = survey(rng)
    write_csv("pack/E02_resident_survey.csv", ["question_id", "question", "answer", "respondents", "sample"], s_rows)

    k = kb(rng)
    write_csv("pack/E03_kb_inventory.csv",
              ["article_id", "title", "topic", "classification", "months_since_review", "owner"], k)

    f = funnel()
    write_csv("pack/E04_portal_funnel.csv", ["service", "started_online", "completed_online"], f)

    facts = {
        "total": total,
        "by_cat": by_cat,
        "minutes_by_cat": {c: round(v) for c, v in mins_cat.items()},
        "by_channel": by_ch,
        "phone": phone,
        "survey": s,
        "survey_n": n_survey,
        "kb_total": len(k),
        "kb_restricted": sum(1 for r in k if r[3] == "مقيد"),
        "kb_stale": sum(1 for r in k if r[4] > 12),
        "kb_no_owner": sum(1 for r in k if not r[5]),
        "funnel": {r[0]: [r[1], r[2]] for r in f},
        "cost_per_minute": COST_PER_MINUTE,
    }

    for rel, text in T.files(facts).items():
        write(rel, text)
    for rel, (header, rows) in T.tables(facts).items():
        write_csv(rel, header, rows)

    print("total enquiries", total, "| phone", phone)
    for c in CATS:
        print(c[0], by_cat[c[0]], round(100 * by_cat[c[0]] / total, 1), "% | minutes", round(mins_cat[c[0]]))
    print("survey", s)
    print("kb", facts["kb_total"], "restricted", facts["kb_restricted"], "stale", facts["kb_stale"], "no owner", facts["kb_no_owner"])


if __name__ == "__main__":
    main()
