import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# Google Sheets setup
SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPE)
client = gspread.authorize(creds)
sheet = client.open("app-dataset-backup").sheet1

def load_data():
    records = sheet.get_all_records()
    return pd.DataFrame(records)

def save_data(df):
    sheet.clear()
    sheet.append_row(df.columns.tolist())
    for _, row in df.iterrows():
        sheet.append_row(row.tolist())

st.title("Car Sales Data Management\nMade By: Shoaib Khan")
data = load_data()

# Tabs for Lookup, Add, Delete, Edit, and Display All
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Lookup", "Add New Customer", "Delete Customer Data", "Edit Customer Data", "View All Customers"])

# --- Lookup Feature ---
with tab1:
    st.subheader("Lookup Customer Details")
    search_type = st.selectbox("Search by", ["Customer Name", "Chasis Number"], key="lookup_select")
    query = st.text_input(f"Enter {search_type}", key="lookup_query")
    if st.button("Search", key="lookup_button") and query.strip():
        query = query.strip()
        if search_type == "Customer Name":
            result = data[data['Customer Name'].str.lower().str.contains(query.lower(), na=False)]
        else:
            result = data[data['Chasis Number'].str.strip().str.upper() == query.upper()]

        if not result.empty:
            for _, row in result.iterrows():
                st.markdown("---")
                st.write(f"**Customer Name:** {row['Customer Name']}")
                st.write(f"**Car Model:** {row['Car Name/Model']}")
                st.write(f"**Chasis Number:** {row['Chasis Number']}")
                st.write(f"**Sold For (\u00a5):** {row['Sold For (\u00a5)']}")
                st.write(f"**Selling Date:** {row['Selling Date']}")
        else:
            st.warning("No matching records found.")

# --- Add New Customer Feature ---
with tab2:
    st.subheader("Add New Customer")
    with st.form("add_form"):
        customer_name = st.text_input("Customer Name")
        car_model = st.text_input("Car Name/Model")
        chasis_number = st.text_input("Chasis Number")
        sold_for = st.number_input("Sold For (\u00a5)", min_value=0, step=1000)
        selling_date = st.date_input("Selling Date")
        submitted = st.form_submit_button("Add Customer")

        if submitted:
            if not customer_name.strip() or not car_model.strip() or not chasis_number.strip():
                st.error("Please fill in all required fields (Customer Name, Car Model, Chasis Number).")
            else:
                if chasis_number.strip().upper() in data['Chasis Number'].str.strip().str.upper().values:
                    st.error("Chasis Number already exists. Please use a unique Chasis Number.")
                else:
                    new_row = pd.DataFrame([{
                        'Customer Name': customer_name.strip(),
                        'Car Name/Model': car_model.strip(),
                        'Chasis Number': chasis_number.strip(),
                        'Sold For (\u00a5)': str(sold_for),
                        'Selling Date': selling_date.strftime('%Y-%m-%d')
                    }])
                    updated_data = pd.concat([data, new_row], ignore_index=True)
                    save_data(updated_data)
                    st.success("Customer details added successfully!")
                    st.experimental_rerun()

# --- Delete Customer Data Feature ---
with tab3:
    st.subheader("Delete Customer Data by Chasis Number")
    delete_chasis = st.text_input("Enter Chasis Number to Delete")
    delete_btn = st.button("Delete Customer")

    if delete_btn and delete_chasis.strip():
        delete_chasis = delete_chasis.strip().upper()
        match = data[data['Chasis Number'].str.strip().str.upper() == delete_chasis]

        if not match.empty:
            st.write("### Matching Record:")
            st.dataframe(match)
            confirm_delete = st.checkbox("Confirm deletion")
            if confirm_delete:
                data = data[data['Chasis Number'].str.strip().str.upper() != delete_chasis]
                save_data(data)
                st.success(f"Record with Chasis Number '{delete_chasis}' deleted successfully!")
                st.experimental_rerun()
            else:
                st.info("Please confirm deletion by checking the box above.")
        else:
            st.warning("No customer found with the given Chasis Number.")

# --- Edit Customer Data Feature ---
with tab4:
    st.subheader("Edit Existing Customer Data")
    edit_search_type = st.selectbox("Search by", ["Customer Name", "Chasis Number"], key="edit_select")
    edit_query = st.text_input(f"Enter {edit_search_type}", key="edit_query")
    if st.button("Search", key="edit_search_button") and edit_query.strip():
        edit_query = edit_query.strip()
        if edit_search_type == "Customer Name":
            result = data[data['Customer Name'].str.lower().str.contains(edit_query.lower(), na=False)]
        else:
            result = data[data['Chasis Number'].str.strip().str.upper() == edit_query.upper()]

        if not result.empty:
            for index, row in result.iterrows():
                with st.form(f"edit_form_{index}"):
                    new_customer_name = st.text_input("Customer Name", row['Customer Name'], key=f"name_{index}")
                    new_car_model = st.text_input("Car Model", row['Car Name/Model'], key=f"model_{index}")
                    new_chasis_number = st.text_input("Chasis Number", row['Chasis Number'], key=f"chasis_{index}")
                    new_sold_for = st.text_input("Sold For (\u00a5)", row['Sold For (\u00a5)'], key=f"sold_{index}")
                    new_selling_date = st.text_input("Selling Date", row['Selling Date'], key=f"date_{index}")
                    submitted_edit = st.form_submit_button("Save Changes")

                    if submitted_edit:
                        if not new_customer_name.strip() or not new_car_model.strip() or not new_chasis_number.strip():
                            st.error("Customer Name, Car Model, and Chasis Number cannot be empty.")
                        else:
                            chasis_conflict = data[(data.index != index) &
                                                   (data['Chasis Number'].str.strip().str.upper() == new_chasis_number.strip().upper())]
                            if not chasis_conflict.empty:
                                st.error("Another record with this Chasis Number already exists. Please use a unique Chasis Number.")
                            else:
                                data.at[index, 'Customer Name'] = new_customer_name.strip()
                                data.at[index, 'Car Name/Model'] = new_car_model.strip()
                                data.at[index, 'Chasis Number'] = new_chasis_number.strip()
                                data.at[index, 'Sold For (\u00a5)'] = new_sold_for.strip()
                                data.at[index, 'Selling Date'] = new_selling_date.strip()
                                save_data(data)
                                st.success("\u2705 Changes saved to Google Sheet. Customer details updated successfully!")
                                st.experimental_rerun()
        else:
            st.warning("No matching records found.")

# --- View All Customers ---
with tab5:
    st.subheader("All Customers Data")
    latest_data = load_data()
    if latest_data.empty:
        st.info("No customer data available.")
    else:
        st.dataframe(latest_data)
