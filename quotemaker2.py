import streamlit as st
import requests

from dotenv import load_dotenv
import os

import streamlit.components.v1 as components

# --- Load credentials ---

EMAIL = st.secrets["SHIPROCKET_EMAIL"]
PASSWORD = st.secrets["SHIPROCKET_PASSWORD"]

# --- Product list ---
product_list=[
        {"pname":"240GSM French Terry OS",
         "bulk_price":205,
         "sample_price":250,
         "weight":0.33},

        {"pname":"210GSM French Terry OS",         
         "bulk_price":195,
         "sample_price":240,
         "weight":0.28},

        {"pname":"180GSM Oversized Tshirt",
         "bulk_price":185,
         "sample_price":230,
         "weight":0.27},

        {"pname":"180GSM Regular Fit Tshirt",
         "bulk_price":150,
         "sample_price":200,
         "weight":0.22},

        {"pname":"180GSM Non-Biowash Tshirt",
         "bulk_price":115,
         "sample_price":150,
         "weight":0.22},

        {"pname":"320GSM Hoodie",
         "bulk_price":350,
         "sample_price":400,
         "weight":0.59},

        {"pname":"320GSM Sweatshirt",
         "bulk_price":280,
         "sample_price":330,
         "weight":0.49},

        {"pname":"420GSM OS Hoodie",
         "bulk_price":420,
         "sample_price":500,
         "weight":0.79},

         {"pname":"420GSM OS Hoodie - II",
         "bulk_price":460,
         "sample_price":550,
         "weight":0.79},

        {"pname":"Varsity Jacket",
         "bulk_price":400,
         "sample_price":450,
         "weight":0.59},

        {"pname":"240GSM Acid Wash OS",
         "bulk_price":250,
         "sample_price":300,
         "weight":0.28},

        {"pname":"180GSM Acid Wash RF",
         "bulk_price":190,
         "sample_price":250,
         "weight":0.22},

        {"pname":"Cotton Polo",
         "bulk_price":210,
         "sample_price":250,
         "weight":0.28},

        {"pname":"Premium Cotton Polo",
         "bulk_price":250,
         "sample_price":300,
         "weight":0.28},
    ]

st.header("Quote Maker for Subtlewear")
st.caption("Enter your order details and generate a customer-ready quote.")

# --- Initialize session state ---
if "quote_ready" not in st.session_state:
    st.session_state.quote_ready = False
if "courier_data" not in st.session_state:
    st.session_state.courier_data = []
if "form_data" not in st.session_state:
    st.session_state.form_data = {}

# --- Step 1: Customer & Product Form ---
if not st.session_state.quote_ready:
    with st.form("quote_form"):
        st.subheader("Customer Details:")
        cname = st.text_input("Customer Name")
        pincode = st.number_input("Customer Pincode", step=1)
        qty=[0]*len(product_list)

        for i in range(len(product_list)):
            if i==0:
                st.subheader("Oversized Tshirts")
            elif i==3:
                st.subheader("Regular Fit Tshirts")
            elif i==5:
                st.subheader("Hoodies & More")
            elif i==10:
                st.subheader("Acid wash Tshirts")
            elif i==12:
                st.subheader("Polo Tshirts")

            qty[i]=st.number_input(product_list[i]["pname"],step=1)
        

        submitted = st.form_submit_button("Get Courier Options")

    if submitted:
        total_pieces = sum(qty)
        subtotal = 0
        total_weight = 0
        for i, p in enumerate(product_list):
            if qty[i] > 0:
                price = p["sample_price"] if total_pieces < 10 else p["bulk_price"]
                subtotal += qty[i] * price
                total_weight += qty[i] * p["weight"]

        # Store the basic form data
        st.session_state.form_data = {
            "cname": cname,
            "pincode": pincode,
            "qty": qty,
            "subtotal": subtotal,
            "total_weight": total_weight,
            "total_pieces": total_pieces,
        }

        # --- Shiprocket login ---
        login_url = "https://apiv2.shiprocket.in/v1/external/auth/login"
        response = requests.post(login_url, json={"email": EMAIL, "password": PASSWORD})
        token = response.json().get("token")

        if token:
            headers = {"Authorization": f"Bearer {token}"}
            estimate_url = "https://apiv2.shiprocket.in/v1/external/courier/serviceability/"
            params = {
                "pickup_postcode": "110062",
                "delivery_postcode": pincode,
                "weight": round(total_weight, 2),
                "cod": 0,
            }
            est_response = requests.get(estimate_url, headers=headers, params=params)
            est_data = est_response.json()

            if "data" in est_data and "available_courier_companies" in est_data["data"]:
                st.session_state.courier_data = est_data["data"]["available_courier_companies"]
                st.session_state.quote_ready = True
                st.rerun()
            else:
                st.warning("No courier options available.")

        else:
            st.error("Shiprocket login failed. Please check credentials.")
else:
    # --- Step 2: Courier Selection Form ---
    couriers = [
        f"{c['courier_name']} - ₹{c['rate']} ({c['etd']})"
        for c in st.session_state.courier_data
    ]
    with st.form("courier_form"):
        selected = st.selectbox("Select Courier Option:", couriers)
        confirm = st.form_submit_button("Generate Final Quote")

    if confirm:
        selected_courier = next(
            c for c in st.session_state.courier_data if f"{c['courier_name']} - ₹{c['rate']} ({c['etd']})" == selected
        )
        fd = st.session_state.form_data

        # --- Calculate totals ---
        shipping = selected_courier["rate"]*1.1
        gst = (fd["subtotal"] + shipping) * 0.05
        final_total = fd["subtotal"] + shipping + gst

        # --- Build message ---
        message = f"""
Customer: {fd['cname']}
Pincode: {fd['pincode']}

Order Details:
"""
        for i, p in enumerate(product_list):
            if fd["qty"][i] > 0:
                price = p["sample_price"] if fd["total_pieces"] < 10 else p["bulk_price"]
                total_price = price * fd["qty"][i]
                message += f"{p['pname']}\n₹{price} × {fd['qty'][i]} = ₹{total_price}\n\n"

        message += f"""
Total Pieces: {fd['total_pieces']}
Total Weight: {fd['total_weight']:.2f} kg
Subtotal: ₹{fd['subtotal']:.2f}
Shipping via {selected_courier['courier_name']}: ₹{shipping:.2f}
GST (5%): ₹{gst:.2f}
Estimated Delivery: {selected_courier['etd']}
Final Total: ₹{final_total:.2f}
"""

        st.text_area("Generated Quote", message, height=300)
        copy_button = f"""
    <button onclick="navigator.clipboard.writeText(`{message}`)"
    style="
        background-color:#f0f2f6;
        color:#000;
        padding:10px 16px;
        border:none;
        border-radius:8px;
        font-size:16px;
        cursor:pointer;
        box-shadow:0 2px 5px rgba(0,0,0,0.1);
    ">
    📋 Copy Quote
    </button>
"""
components.html(copy_button, height=60)

        # Reset for new quote if needed
        if st.button("Create New Quote"):
            st.session_state.quote_ready = False
            st.session_state.courier_data = []
            st.session_state.form_data = {}
            st.rerun()

