# INELSO Service 21 Streamlit Dashboard

## Run locally

1. Put these files in the same folder:
   - `service21_streamlit.py`
   - `requirements.txt`

2. Open Command Prompt / PowerShell in that folder.

3. Install dependencies:

   pip install -r requirements.txt

4. Start the app:

   streamlit run service21_streamlit.py

5. Your browser will open automatically, usually at:

   http://localhost:8501

## Moodle workflow

In Moodle:

Results -> Statistics -> Download full report as CSV

Then upload that CSV into the Streamlit app.

The dashboard is read-only and does not write or change Moodle grades.
