import streamlit as st
import pandas as pd
import io
import random
from datetime import datetime

# 🔒 Set the password
PASSWORD = "specialized1974"

# Check if user is logged in
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Login form
if not st.session_state.logged_in:
    st.title("🔒 Secure Access")
    user_password = st.text_input("Enter Password:", type="password")
    if st.button("Login"):
        if user_password == PASSWORD:
            st.session_state.logged_in = True
            st.rerun()  # Refresh the app after login
        else:
            st.error("❌ Incorrect password. Please try again.")

# If logged in, show the main app
if st.session_state.logged_in:
    # Motivational messages
    motivational_phrases = [
        "🚀 Great things are coming! Hang tight...",
        "🔥 You're making big moves! Just a moment...",
        "💡 Smart choice! Processing your request...",
        "⏳ Almost there! Preparing your file...",
        "✨ Good things take time... but not too long!",
        "✅ Ensuring your catalog consistency!",
        "🌎 One step closer to a better catalog. Hold on!"
    ]

    # Approval/Inactivation switch
    action = st.toggle("Approve/Activate SKUs", value=True)
    action_text = "Activate" if action else "Deactivate"
    approval_status = "approved" if action else "unapproved"

    # Update switch title dynamically
    st.title("Approve/Activate SKUs" if action else "Unapprove/Deactivate SKUs")

    # Description text
    st.markdown(
        f"This tool will help you {action_text.lower()} the SKUs you input here on s.com. "
        "It will not only affect those specific SKUs but the full run of SKUs under the same Color ID to ensure consistency in the catalog. "
        f"(For example, if you want to {action_text.lower()} a bike size 52, the other sizes will be affected as well)."
    )

    # Dropdown for country selection
    st.subheader("Select Country")
    country_options = ["Brazil", "Chile", "Mexico", "Colombia", "Argentina"]
    selected_country = st.selectbox("Choose a country:", country_options)

    # File Upload
    st.subheader("Upload your country datafeed")
    uploaded_file = st.file_uploader("Choose a CSV or TXT file", type=["csv", "txt"])

    # Text area for PIDs
    st.subheader(f"Enter the SKUs you want to {action_text.lower()} (comma-separated OR line-separated)")
    pids_input = st.text_area("Paste SKUs here", placeholder="91825-3304\n98122-3105\n95223-7104")

    # Function to process both comma-separated and line-separated SKUs
    def process_pids(pids_text):
        if pids_text:
            return [pid.strip() for pid in pids_text.replace("\n", ",").split(",") if pid.strip()]
        return []

    # Function to read either CSV or TXT file
    def load_data(file):
        if file.name.endswith(".csv"):
            return pd.read_csv(file, delimiter=";", low_memory=False)
        elif file.name.endswith(".txt"):
            return pd.read_csv(file, delimiter="|", low_memory=False)
        else:
            return None

    # Use session state to store the generated file for multiple downloads
    if "approval_file_content" not in st.session_state:
        st.session_state.approval_file_content = None
    if "approval_file_name" not in st.session_state:
        st.session_state.approval_file_name = None

    if st.button("Process File"):
        if uploaded_file and pids_input:
            # Load the file based on format
            df = load_data(uploaded_file)

            if df is None:
                st.error("Invalid file format. Please upload a CSV or TXT file.")
            else:
                # Ensure required columns exist
                if not {'PID', 'MPL_PRODUCT_ID', 'COLOR_ID'}.issubset(df.columns):
                    st.error("File is missing required columns (PID, MPL_PRODUCT_ID, COLOR_ID).")
                else:
                    df_filtered = df[['PID', 'MPL_PRODUCT_ID', 'COLOR_ID']]

                    # Convert input SKUs into a list
                    user_pids = process_pids(pids_input)

                    # Display a random motivational message while processing
                    st.info(random.choice(motivational_phrases))

                    # Filter dataset for provided SKUs
                    df_selected = df_filtered[df_filtered['PID'].isin(user_pids)]

                    # Find COLOR_IDs linked to those SKUs
                    color_ids = df_selected['COLOR_ID'].dropna().unique()

                    # Get all SKUs that share the same COLOR_ID
                    df_final = df_filtered[df_filtered['COLOR_ID'].isin(color_ids)].copy()

                    # Add required columns
                    df_final['CATALOG_VERSION'] = f"SBC{selected_country}ProductCatalog"  # Dynamically replace COUNTRY
                    df_final['APPROVAL_STATUS'] = approval_status

                    # Rename columns for output
                    df_final.rename(columns={'PID': 'SKU', 'MPL_PRODUCT_ID': 'Base Product ID'}, inplace=True)
                    df_final = df_final[['SKU', 'Base Product ID', 'CATALOG_VERSION', 'APPROVAL_STATUS']]

                    # Generate output file content
                    output = io.StringIO()
                    df_final.to_csv(output, sep="|", index=False)
                    st.session_state.approval_file_content = output.getvalue()  # Store file for multiple downloads

                    # Set static filename
                    st.session_state.approval_file_name = "SBC_HYBRIS_SIZEVARIANT_APPROVAL.txt"

                    # Success message
                    st.success("✅ File successfully generated! Download it below.")

    # Show download button if a file is available
    if st.session_state.approval_file_content and st.session_state.approval_file_name:
        st.download_button(
            label="Download Processed File",
            data=st.session_state.approval_file_content,
            file_name=st.session_state.approval_file_name,
            mime="text/plain"
        )
