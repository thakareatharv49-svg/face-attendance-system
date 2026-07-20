import streamlit as st
from database import init_db, get_all_attendance
import subprocess
import sys

st.set_page_config(page_title="AI Attendance System", layout="centered")

init_db()

st.title("🎯 AI Attendance System")
st.write("Face recognition based attendance tracking")

# Button to launch the live camera recognition
if st.button("📷 Start Live Attendance Camera"):
    st.info("Opening camera window... look at your webcam. Press 'q' in that window to close it when done.")
    subprocess.Popen([sys.executable, "live_recognize.py"])

st.divider()

st.subheader("📋 Attendance Records")

records = get_all_attendance()

if not records:
    st.write("No attendance records yet.")
else:
    # Format as a table
    import pandas as pd
    df = pd.DataFrame(records, columns=["ID", "Name", "Timestamp"])
    df = df.drop(columns=["ID"])
    st.dataframe(df, use_container_width=True)

    st.write(f"Total records: {len(records)}")

if st.button("🔄 Refresh"):
    st.rerun()