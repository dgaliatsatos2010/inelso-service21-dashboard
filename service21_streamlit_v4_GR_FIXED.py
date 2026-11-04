import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="INELSO Service 21 — Πίνακας Ποιότητας Αξιολόγησης",
    page_icon="📊",
    layout="wide",
)

# Ελληνικοποίηση του κουμπιού μεταφόρτωσης του Streamlit.
# Η αλλαγή είναι μόνο οπτική και δεν επηρεάζει τη λειτουργία του file uploader.
st.markdown(
    """
    <style>
    [data-testid="stFileUploaderDropzone"] button {
        font-size: 0 !important;
    }
    [data-testid="stFileUploaderDropzone"] button::after {
        content: "Μεταφόρτωση";
        font-size: 14px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("INELSO Service 21 — Πίνακας Ποιότητας Αξιολόγησης")
st.caption(
    "Επίπεδο ψυχομετρικής ανάλυσης μόνο για ανάγνωση, για στατιστικά κουίζ του Moodle. "
    "Μεταφορτώστε το αρχείο CSV από Αποτελέσματα → Στατιστικά στο Moodle."
)

st.info(
    "Σχεδιασμένο για σύνδεση από το Moodle ως εξωτερικός πίνακας Service 21. "
    "Το Moodle παραμένει το σημείο εκκίνησης, ενώ η ανάλυση και οι αναφορές εμφανίζονται εδώ."
)

with st.sidebar:
    st.header("Πηγή δεδομένων")
    uploaded = st.file_uploader("Μεταφόρτωση CSV στατιστικών κουίζ Moodle", type=["csv"])
    st.markdown("---")
    st.subheader("Κανόνες ταξινόμησης")
    st.write(
        "Όρια του δείκτη διάκρισης που χρησιμοποιεί ο πίνακας:\n\n"
        "- **ΙΣΧΥΡΗ**: ≥ 40%\n"
        "- **ΙΚΑΝΟΠΟΙΗΤΙΚΗ**: 20–39.99%\n"
        "- **ΕΛΕΓΧΟΣ**: 0–19.99%\n"
        "- **ΚΡΙΣΙΜΗ**: < 0%"
    )
    st.info("Η εφαρμογή είναι μόνο για ανάγνωση. Δεν καταχωρίζει βαθμούς και δεν τροποποιεί δεδομένα του Moodle.")

def normalize_colname(c):
    return (
        str(c)
        .strip()
        .lower()
        .replace("\n", " ")
        .replace("_", " ")
        .replace("-", " ")
    )

def find_col(df, candidates):
    normalized = {normalize_colname(c): c for c in df.columns}
    for cand in candidates:
        candn = normalize_colname(cand)
        for norm, original in normalized.items():
            if candn == norm or candn in norm:
                return original
    return None

def pct_to_float(v):
    if pd.isna(v):
        return np.nan
    if isinstance(v, (int, float, np.number)):
        return float(v)
    s = str(v).strip()
    if s.lower() in {"none", "nan", ""}:
        return np.nan
    s = s.replace("%", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return np.nan

def classify_discrimination(x):
    if pd.isna(x):
        return "N/A"
    if x < 0:
        return "ΚΡΙΣΙΜΗ"
    if x < 20:
        return "ΕΛΕΓΧΟΣ"
    if x < 40:
        return "ΙΚΑΝΟΠΟΙΗΤΙΚΗ"
    return "ΙΣΧΥΡΗ"

def classify_facility(x):
    if pd.isna(x):
        return "N/A"
    if x < 20:
        return "Πολύ δύσκολη"
    if x < 40:
        return "Δύσκολη"
    if x <= 80:
        return "Ισορροπημένη"
    return "Εύκολη"



def review_reason(row):
    disc = row.get("Discrimination index", np.nan)
    facility = row.get("Facility index", np.nan)
    status = row.get("Status", "N/A")

    if pd.isna(disc):
        return "Ο δείκτης διάκρισης δεν ήταν δυνατό να εκτιμηθεί από τα διαθέσιμα δεδομένα."
    if status == "ΚΡΙΣΙΜΗ":
        return (
            "Αρνητικός δείκτης διάκρισης: οι μαθητές με υψηλότερη συνολική επίδοση δεν είχαν μεγαλύτερη πιθανότητα σωστής απάντησης. "
            "Αυτό μπορεί να υποδηλώνει λανθασμένο κλειδί απάντησης, ασαφή διατύπωση, αντίστροφη κωδικοποίηση, ασυμφωνία περιεχομένου ή προβληματική λειτουργία της ερώτησης."
        )
    if status == "ΕΛΕΓΧΟΣ":
        if pd.notna(facility) and facility < 20:
            return (
                "Ασθενής διάκριση σε συνδυασμό με πολύ υψηλή δυσκολία. Η ερώτηση μπορεί να είναι υπερβολικά δύσκολη ή να μην ευθυγραμμίζεται καλά "
                "με τη διδασκαλία ή να εξαρτάται από ασαφή διατύπωση."
            )
        if pd.notna(facility) and facility > 80:
            return (
                "Ασθενής διάκριση σε συνδυασμό με πολύ εύκολη ερώτηση. Οι περισσότεροι εκπαιδευόμενοι ενδέχεται να απαντούν σωστά, "
                "με αποτέλεσμα να περιορίζεται η δυνατότητα διάκρισης μεταξύ υψηλότερης και χαμηλότερης επίδοσης."
            )
        return (
            "Ασθενής διάκριση παρά τον μη ακραίο δείκτη ευκολίας. Η ερώτηση πρέπει να ελεγχθεί ως προς τη διατύπωση, "
            "την ποιότητα των παραπλανητικών επιλογών, την ευθυγράμμιση με το περιεχόμενο και τη ρύθμιση βαθμολόγησης."
        )
    if status == "ΙΚΑΝΟΠΟΙΗΤΙΚΗ":
        return (
            "Ικανοποιητική διάκριση. Η ερώτηση συμβάλλει χρήσιμα στη διαφοροποίηση των επιδόσεων, αλλά δεν ανήκει στις ισχυρότερες "
            "ερωτήσεις και μπορεί να παρακολουθείται σε επόμενες ομάδες εκπαιδευομένων."
        )
    return (
        "Ισχυρή διάκριση. Η ερώτηση διαχωρίζει αποτελεσματικά τους εκπαιδευόμενους υψηλότερης και χαμηλότερης επίδοσης στο συγκεκριμένο ελεγχόμενο σύνολο δεδομένων."
    )


def review_action(row):
    status = row.get("Status", "N/A")
    facility = row.get("Facility index", np.nan)

    if status == "ΚΡΙΣΙΜΗ":
        return (
            "Urgent human review: verify the correct answer/key and scoring first; then inspect wording, ambiguity, "
            "content alignment, and response-option behavior. Re-run statistics after correction."
        )
    if status == "ΕΛΕΓΧΟΣ":
        if pd.notna(facility) and facility < 20:
            return (
                "Review difficulty and instructional alignment; simplify or clarify the item if needed, then collect "
                "a new cohort and re-check discrimination."
            )
        if pd.notna(facility) and facility > 80:
            return (
                "Consider increasing cognitive demand or improving distractors so the item provides more differentiation; "
                "then re-check with a new cohort."
            )
        return (
            "Inspect the stem, distractors/response options, scoring, and alignment with the learning objective. "
            "Revise only after human review, then re-run the psychometric analysis."
        )
    if status == "ΙΚΑΝΟΠΟΙΗΤΙΚΗ":
        return "Keep the item and monitor it across future cohorts; revise only if the pattern persists or worsens."
    if status == "ΙΣΧΥΡΗ":
        return "Retain the item. Use it as a reference example when reviewing weaker questions."
    return "No automated action is recommended because the required statistic is unavailable."


def review_priority(row):
    status = row.get("Status", "N/A")
    return {
        "ΚΡΙΣΙΜΗ": "1 — Επείγον",
        "ΕΛΕΓΧΟΣ": "2 — Έλεγχος",
        "ΙΚΑΝΟΠΟΙΗΤΙΚΗ": "3 — Παρακολούθηση",
        "ΙΣΧΥΡΗ": "4 — Διατήρηση",
    }.get(status, "N/A")



def greek_columns(frame):
    return frame.rename(columns={
        "Question": "Ερώτηση",
        "Attempts": "Προσπάθειες",
        "Facility index": "Δείκτης ευκολίας",
        "Difficulty": "Δυσκολία",
        "Discrimination index": "Δείκτης διάκρισης",
        "Discriminative efficiency": "Αποτελεσματικότητα διάκρισης",
        "Intended weight": "Προβλεπόμενο βάρος",
        "Effective weight": "Πραγματικό βάρος",
        "Status": "Κατάσταση",
        "Priority": "Προτεραιότητα",
        "Reason": "Αιτιολόγηση",
        "Recommended action": "Προτεινόμενη ενέργεια",
    })

def build_html_report(df, source_label, mean_facility, mean_disc, strong_count, ok_count, review_count, critical_count):
    report = df.copy()
    report["Reason"] = report.apply(review_reason, axis=1)
    report["Recommended action"] = report.apply(review_action, axis=1)
    report["Priority"] = report.apply(review_priority, axis=1)

    cols = [
        "Question", "Attempts", "Facility index", "Difficulty",
        "Discrimination index", "Discriminative efficiency", "Status",
        "Priority", "Reason", "Recommended action"
    ]
    available = [c for c in cols if c in report.columns]
    table_html = report[available].to_html(index=False, border=0, classes="report-table")

    return f"""<!doctype html>
<html lang="el">
<head>
<meta charset="utf-8">
<title>INELSO Service 21 — Αναφορά Ποιότητας Αξιολόγησης</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 32px; color: #1f2937; }}
h1 {{ margin-bottom: 4px; }}
.subtitle {{ color: #6b7280; margin-bottom: 24px; }}
.metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 20px 0 28px; }}
.metric {{ border: 1px solid #d1d5db; border-radius: 10px; padding: 14px; }}
.metric b {{ display: block; font-size: 24px; margin-top: 4px; }}
.notice {{ background:#eff6ff; border-left:4px solid #2563eb; padding:12px 14px; margin:18px 0; }}
.report-table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
.report-table th, .report-table td {{ border:1px solid #e5e7eb; padding:8px; vertical-align:top; text-align:left; }}
.report-table th {{ background:#f3f4f6; }}
.footer {{ margin-top:24px; color:#6b7280; font-size:12px; }}
</style>
</head>
<body>
<h1>INELSO Service 21 — Αναφορά Ποιότητας Αξιολόγησης</h1>
<div class="subtitle">Πηγή: {source_label}</div>
<div class="metrics">
  <div class="metric">Ερωτήσεις που αναλύθηκαν<b>{len(df)}</b></div>
  <div class="metric">Μέσος δείκτης ευκολίας<b>{mean_facility:.1f}%</b></div>
  <div class="metric">Μέσος δείκτης διάκρισης<b>{mean_disc:.1f}%</b></div>
  <div class="metric">Χρειάζονται έλεγχο<b>{review_count + critical_count}</b></div>
</div>
<div class="notice">
<strong>Ταξινόμηση:</strong> ΙΣΧΥΡΗ ≥ 40%; ΙΚΑΝΟΠΟΙΗΤΙΚΗ 20–39.99%; ΕΛΕΓΧΟΣ 0–19.99%; ΚΡΙΣΙΜΗ &lt; 0%.<br>
Η αναφορά είναι μόνο για ανάγνωση και δεν τροποποιεί βαθμούς ή δεδομένα κουίζ στο Moodle.
</div>
<p><strong>Πλήθος ανά κατηγορία:</strong> ΙΣΧΥΡΗ {strong_count} | ΙΚΑΝΟΠΟΙΗΤΙΚΗ {ok_count} | ΕΛΕΓΧΟΣ {review_count} | ΚΡΙΣΙΜΗ {critical_count}</p>
<h2>Έλεγχος ανά ερώτηση</h2>
{table_html}
<div class="footer">Δημιουργήθηκε από τον πίνακα ποιότητας αξιολόγησης INELSO Service 21.</div>
</body>
</html>"""

def demo_data():
    return pd.DataFrame({
        "Question name": [
            "S21 Marketing Q01", "S21 Marketing Q02", "S21 Marketing Q04",
            "S21 Marketing Q07", "S21 Marketing Q10", "S21 Marketing Q05",
            "S21 Marketing Q09", "S21 Marketing Q03", "S21 Marketing Q06",
            "S21 Marketing Q08",
        ],
        "Attempts": [50] * 10,
        "Facility index": [86, 58, 46, 42, 2, 20, 72, 44, 32, 52],
        "Discrimination index": [42.5, 51.2, 48.7, 45.0, 34.92, 44.11, 12.88, 73.22, 44.38, 60.89],
        "Discriminative efficiency": [66.0, 70.0, 68.0, 64.0, 100.0, 61.54, 21.49, 92.35, 52.03, 80.71],
        "Intended weight": [10.0] * 10,
        "Effective weight": [9.0, 10.5, 10.0, 9.8, 6.73, 13.82, 11.48, 18.06, 15.27, 17.29],
    })

def read_csv_robust(uploaded_file):
    uploaded_file.seek(0)
    try:
        return pd.read_csv(uploaded_file)
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        return pd.read_csv(uploaded_file, encoding="latin1")

def looks_like_shifted_moodle_questionstats(raw):
    """
    Moodle questionstats export seen in this INELSO installation:
    the dataframe headers are quiz-level labels, while item-level rows are
    positioned as:
      0 Q#
      1 Question type
      2 Question name
      3 Attempts
      4 Facility index
      5 Standard deviation
      6 Random guess score
      7 Intended weight
      8 Effective weight
      9 Discrimination index
     10 Discriminative efficiency
    """
    if raw.shape[1] < 11 or raw.shape[0] == 0:
        return False

    headers = [normalize_colname(c) for c in raw.columns]
    has_quiz_level_headers = (
        any("quiz name" in h for h in headers)
        and any("course name" in h for h in headers)
        and any("average grade" in h for h in headers)
    )

    # Column 2 should look like question names and column 3 like attempts.
    qnames = raw.iloc[:, 2].astype(str)
    attempts = pd.to_numeric(raw.iloc[:, 3], errors="coerce")

    question_like = qnames.str.contains(r"\bQ\d+\b", case=False, regex=True).mean() >= 0.5
    attempts_like = attempts.notna().mean() >= 0.5

    return has_quiz_level_headers and question_like and attempts_like

def map_shifted_moodle_questionstats(raw):
    df = pd.DataFrame({
        "Question": raw.iloc[:, 2].astype(str).str.strip(),
        "Attempts": pd.to_numeric(raw.iloc[:, 3], errors="coerce"),
        "Facility index": raw.iloc[:, 4].map(pct_to_float),
        "Discrimination index": raw.iloc[:, 9].map(pct_to_float),
        "Discriminative efficiency": raw.iloc[:, 10].map(pct_to_float),
        "Intended weight": raw.iloc[:, 7].map(pct_to_float),
        "Effective weight": raw.iloc[:, 8].map(pct_to_float),
    })

    # Keep only genuine item rows.
    df = df[
        df["Question"].str.contains(r"\bQ\d+\b", case=False, regex=True, na=False)
        & df["Attempts"].notna()
    ].copy()

    return df

def map_named_columns(raw):
    question_col = find_col(raw, ["Question name", "Question"])
    attempts_col = find_col(raw, ["Attempts"])
    facility_col = find_col(raw, ["Facility index"])
    disc_col = find_col(raw, ["Discrimination index"])
    eff_col = find_col(raw, ["Discriminative efficiency"])
    intended_col = find_col(raw, ["Intended weight"])
    effective_col = find_col(raw, ["Effective weight"])

    missing = []
    for label, col in [
        ("Question name", question_col),
        ("Attempts", attempts_col),
        ("Facility index", facility_col),
        ("Discrimination index", disc_col),
    ]:
        if col is None:
            missing.append(label)

    if missing:
        return None, missing

    df = pd.DataFrame({
        "Question": raw[question_col].astype(str),
        "Attempts": pd.to_numeric(raw[attempts_col], errors="coerce"),
        "Facility index": raw[facility_col].map(pct_to_float),
        "Discrimination index": raw[disc_col].map(pct_to_float),
    })

    df["Discriminative efficiency"] = (
        raw[eff_col].map(pct_to_float) if eff_col is not None else np.nan
    )
    df["Intended weight"] = (
        raw[intended_col].map(pct_to_float) if intended_col is not None else np.nan
    )
    df["Effective weight"] = (
        raw[effective_col].map(pct_to_float) if effective_col is not None else np.nan
    )
    return df, []

if uploaded is not None:
    raw = read_csv_robust(uploaded)
    source_label = uploaded.name
else:
    raw = demo_data()
    source_label = "Ενδεικτικά δεδομένα επίδειξης"

st.subheader("Φορτωμένο σύνολο δεδομένων")
st.write(f"**Πηγή:** {source_label}")

mapping_note = None

if looks_like_shifted_moodle_questionstats(raw):
    df = map_shifted_moodle_questionstats(raw)
    mapping_note = (
        "Η δομή Moodle questionstats εντοπίστηκε αυτόματα. "
        "Τα πεδία ανά ερώτηση αντιστοιχίστηκαν από τη διάταξη του εξαγόμενου αρχείου."
    )
else:
    df, missing = map_named_columns(raw)
    if df is None:
        st.error(
            "Το CSV δεν μπόρεσε να αντιστοιχιστεί πλήρως. Λείπουν τα αναμενόμενα πεδία: "
            + ", ".join(missing)
        )
        st.caption(
            "Συμβουλή: χρησιμοποιήστε την εξαγωγή CSV από Στατιστικά → Ανάλυση δομής κουίζ στο Moodle."
        )
        st.dataframe(raw, use_container_width=True)
        st.stop()

if mapping_note:
    st.success(mapping_note)

if df.empty:
    st.error("Δεν ήταν δυνατή η εξαγωγή γραμμών ανά ερώτηση από αυτό το CSV.")
    st.dataframe(raw, use_container_width=True)
    st.stop()

df["Status"] = df["Discrimination index"].apply(classify_discrimination)
df["Difficulty"] = df["Facility index"].apply(classify_facility)

tabs = st.tabs(["Συνοπτική εικόνα", "Τεχνική ανάλυση", "Έλεγχος ερωτήσεων", "Εξαγωγές"])

n_questions = len(df)
mean_facility = df["Facility index"].mean()
mean_disc = df["Discrimination index"].mean()
critical_count = (df["Status"] == "ΚΡΙΣΙΜΗ").sum()
review_count = (df["Status"] == "ΕΛΕΓΧΟΣ").sum()
strong_count = (df["Status"] == "ΙΣΧΥΡΗ").sum()
ok_count = (df["Status"] == "ΙΚΑΝΟΠΟΙΗΤΙΚΗ").sum()

with tabs[0]:
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Ερωτήσεις που αναλύθηκαν", f"{n_questions}")
    c2.metric("Μέσος δείκτης ευκολίας", f"{mean_facility:.1f}%")
    c3.metric("Μέσος δείκτης διάκρισης", f"{mean_disc:.1f}%")
    c4.metric("Χρειάζονται έλεγχο", f"{critical_count + review_count}")

    st.markdown("### Σύνοψη ποιότητας αξιολόγησης")

    if critical_count > 0:
        st.error(
            f"{critical_count} ερώτηση/εις έχουν αρνητικό δείκτη διάκρισης και απαιτούν άμεσο έλεγχο."
        )
    elif review_count > 0:
        st.warning(
            f"{review_count} ερώτηση/εις παρουσιάζουν ασθενή διάκριση και χρειάζονται έλεγχο."
        )
    else:
        st.success("Καμία ερώτηση δεν βρίσκεται αυτή τη στιγμή στις κατηγορίες ΕΛΕΓΧΟΣ ή ΚΡΙΣΙΜΗ.")

    summary_df = pd.DataFrame({
        "Κατηγορία": ["ΙΣΧΥΡΗ", "ΙΚΑΝΟΠΟΙΗΤΙΚΗ", "ΕΛΕΓΧΟΣ", "ΚΡΙΣΙΜΗ"],
        "Πλήθος": [strong_count, ok_count, review_count, critical_count],
    })
    st.dataframe(summary_df, hide_index=True, use_container_width=True)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    plotdf = df.sort_values("Discrimination index", ascending=False)
    ax.bar(plotdf["Question"], plotdf["Discrimination index"])
    ax.axhline(40, linestyle="--", linewidth=1)
    ax.axhline(20, linestyle="--", linewidth=1)
    ax.axhline(0, linestyle="-", linewidth=1)
    ax.set_ylabel("Δείκτης διάκρισης (%)")
    ax.set_xlabel("Ερώτηση")
    ax.tick_params(axis="x", rotation=55)
    ax.set_title("Επισκόπηση δείκτη διάκρισης ανά ερώτηση")
    fig.tight_layout()
    st.pyplot(fig)

with tabs[1]:
    st.markdown("### Ψυχομετρικά στατιστικά ερωτήσεων")

    technical_cols = [
        "Question",
        "Attempts",
        "Facility index",
        "Difficulty",
        "Discrimination index",
        "Discriminative efficiency",
        "Intended weight",
        "Effective weight",
        "Status",
    ]
    st.dataframe(
        greek_columns(df[technical_cols].sort_values("Discrimination index")),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### Δείκτης ευκολίας έναντι δείκτη διάκρισης")
    fig2, ax2 = plt.subplots(figsize=(8, 5))
    ax2.scatter(df["Facility index"], df["Discrimination index"], s=70)
    for _, r in df.iterrows():
        ax2.annotate(
            r["Question"],
            (r["Facility index"], r["Discrimination index"]),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=8,
        )
    ax2.axhline(20, linestyle="--", linewidth=1)
    ax2.axhline(40, linestyle="--", linewidth=1)
    ax2.set_xlabel("Δείκτης ευκολίας (%)")
    ax2.set_ylabel("Δείκτης διάκρισης (%)")
    ax2.set_title("Δείκτης ευκολίας και διάκρισης ανά ερώτηση")
    fig2.tight_layout()
    st.pyplot(fig2)

with tabs[2]:
    st.markdown("### Λίστα προτεραιότητας για έλεγχο")

    review_df = df.copy()
    review_df["Priority"] = review_df.apply(review_priority, axis=1)
    review_df["Reason"] = review_df.apply(review_reason, axis=1)
    review_df["Recommended action"] = review_df.apply(review_action, axis=1)

    priority = review_df[review_df["Status"].isin(["ΕΛΕΓΧΟΣ", "ΚΡΙΣΙΜΗ"])].copy()
    if priority.empty:
        st.success("Δεν υπάρχουν ερωτήσεις υψηλής προτεραιότητας για έλεγχο.")
    else:
        st.dataframe(
            greek_columns(priority[
                [
                    "Question",
                    "Facility index",
                    "Difficulty",
                    "Discrimination index",
                    "Status",
                    "Priority",
                    "Reason",
                    "Recommended action",
                ]
            ].sort_values(["Status", "Discrimination index"])),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("### Υποστήριξη απόφασης ανά ερώτηση")
    selected_question = st.selectbox(
        "Επιλέξτε ερώτηση",
        review_df.sort_values(["Status", "Discrimination index"])["Question"].tolist(),
    )
    selected = review_df.loc[review_df["Question"] == selected_question].iloc[0]

    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Δείκτης ευκολίας", f"{selected['Facility index']:.2f}%" if pd.notna(selected['Facility index']) else "N/A")
    q2.metric("Δείκτης διάκρισης", f"{selected['Discrimination index']:.2f}%" if pd.notna(selected['Discrimination index']) else "N/A")
    q3.metric("Κατάσταση", selected["Status"])
    q4.metric("Προτεραιότητα", selected["Priority"])

    if selected["Status"] == "ΚΡΙΣΙΜΗ":
        st.error(f"**Finding:** {selected['Reason']}")
    elif selected["Status"] == "ΕΛΕΓΧΟΣ":
        st.warning(f"**Finding:** {selected['Reason']}")
    elif selected["Status"] == "ΙΚΑΝΟΠΟΙΗΤΙΚΗ":
        st.info(f"**Finding:** {selected['Reason']}")
    else:
        st.success(f"**Finding:** {selected['Reason']}")

    st.markdown(f"**Προτεινόμενη ενέργεια:** {selected['Recommended action']}")
    st.caption(
        "Μόνο υποστήριξη απόφασης: ο πίνακας δεν αλλάζει αυτόματα ερωτήσεις, βαθμολόγηση ή βαθμούς. "
        "Κάθε αναθεώρηση παραμένει ανθρώπινη εκπαιδευτική απόφαση."
    )

    st.markdown("### Ισχυρότερες ερωτήσεις")
    strong = review_df.sort_values("Discrimination index", ascending=False).head(5)
    st.dataframe(
        greek_columns(strong[
            [
                "Question",
                "Facility index",
                "Discrimination index",
                "Discriminative efficiency",
                "Status",
            ]
        ]),
        use_container_width=True,
        hide_index=True,
    )

with tabs[3]:
    st.markdown("### Λήψη επεξεργασμένων αποτελεσμάτων")

    export_df = df.copy()
    export_df["Priority"] = export_df.apply(review_priority, axis=1)
    export_df["Reason"] = export_df.apply(review_reason, axis=1)
    export_df["Recommended action"] = export_df.apply(review_action, axis=1)

    csv_bytes = export_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Λήψη επεξεργασμένου CSV Service 21",
        data=csv_bytes,
        file_name="service21_assessment_quality_processed.csv",
        mime="text/csv",
    )

    action_plan = export_df[export_df["Status"].isin(["ΕΛΕΓΧΟΣ", "ΚΡΙΣΙΜΗ"])].copy()
    action_bytes = action_plan.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Λήψη σχεδίου ενεργειών για ερωτήσεις προτεραιότητας",
        data=action_bytes,
        file_name="service21_priority_review_action_plan.csv",
        mime="text/csv",
        disabled=action_plan.empty,
    )

    executive_text = f"""
INELSO Service 21 — Σύνοψη Ποιότητας Αξιολόγησης

Πηγή: {source_label}
Ερωτήσεις που αναλύθηκαν: {n_questions}
Μέσος δείκτης ευκολίας index: {mean_facility:.2f}%
Μέσος δείκτης διάκρισης index: {mean_disc:.2f}%
ΙΣΧΥΡΕΣ ερωτήσεις: {strong_count}
ΙΚΑΝΟΠΟΙΗΤΙΚΕΣ ερωτήσεις: {ok_count}
Ερωτήσεις για ΕΛΕΓΧΟ: {review_count}
ΚΡΙΣΙΜΕΣ ερωτήσεις: {critical_count}

Ερμηνεία:
- ΙΣΧΥΡΗ: δείκτης διάκρισης >= 40%
- ΙΚΑΝΟΠΟΙΗΤΙΚΗ: 20% έως 39.99%
- ΕΛΕΓΧΟΣ: 0% έως 19.99%
- ΚΡΙΣΙΜΗ: αρνητικός δείκτης διάκρισης

Ερωτήσεις προτεραιότητας για έλεγχο:
{action_plan[['Question','Discrimination index','Status']].to_string(index=False) if not action_plan.empty else 'Καμία'}

Η αναφορά είναι μόνο για ανάγνωση και δεν τροποποιεί βαθμούς ή δεδομένα κουίζ στο Moodle.
"""
    st.download_button(
        "Λήψη συνοπτικής αναφοράς",
        data=executive_text.encode("utf-8"),
        file_name="service21_executive_summary.txt",
        mime="text/plain",
    )

    html_report = build_html_report(
        export_df, source_label, mean_facility, mean_disc,
        strong_count, ok_count, review_count, critical_count
    )
    st.download_button(
        "Λήψη πλήρους αναφοράς HTML",
        data=html_report.encode("utf-8"),
        file_name="service21_assessment_quality_report.html",
        mime="text/html",
    )

    st.info(
        "Η αναφορά HTML είναι αυτόνομη: κατεβάστε την και ανοίξτε την απευθείας σε πρόγραμμα περιήγησης. "
        "Περιλαμβάνει σύνοψη, πλήθος ανά κατηγορία, ευρήματα ανά ερώτηση, προτεραιότητες και προτεινόμενες ενέργειες."
    )
