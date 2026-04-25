import streamlit as st
import requests
from st_copy import copy_button

EMAIL = st.secrets["SHIPROCKET_EMAIL"]
PASSWORD = st.secrets["SHIPROCKET_PASSWORD"]

# --- Product list ---
product_list=[
    {"pname":"240GSM French Terry OS","vendor_price":205,"event_price":220,"sample_price":250,"weight":0.33},
    {"pname":"210GSM French Terry OS","vendor_price":195,"event_price":210,"sample_price":240,"weight":0.28},
    {"pname":"180GSM Oversized Tshirt","vendor_price":185,"event_price":200,"sample_price":230,"weight":0.27},

    {"pname":"180GSM Regular Fit Tshirt","vendor_price":150,"event_price":170,"sample_price":200,"weight":0.22},
    {"pname":"180GSM Non-Biowash Tshirt","vendor_price":115,"event_price":130,"sample_price":150,"weight":0.22},

    {"pname":"320GSM Hoodie","vendor_price":350,"event_price":370,"sample_price":400,"weight":0.59},
    {"pname":"320GSM Sweatshirt","vendor_price":280,"event_price":300,"sample_price":330,"weight":0.49},
    {"pname":"420GSM OS Hoodie","vendor_price":420,"event_price":450,"sample_price":500,"weight":0.79},
    {"pname":"420GSM OS Hoodie - II","vendor_price":460,"event_price":480,"sample_price":550,"weight":0.79},
    {"pname":"Varsity Jacket","vendor_price":400,"event_price":420,"sample_price":450,"weight":0.59},

    {"pname":"240GSM Acid Wash OS","vendor_price":250,"event_price":270,"sample_price":300,"weight":0.28},
    {"pname":"180GSM Acid Wash RF","vendor_price":190,"event_price":210,"sample_price":250,"weight":0.22},

    {"pname":"Cotton Polo","vendor_price":210,"event_price":230,"sample_price":250,"weight":0.28},
    {"pname":"Premium Cotton Polo","vendor_price":250,"event_price":270,"sample_price":300,"weight":0.28},
]

st.header("Quote Maker for Subtlewear")
st.caption("Enter your order details and generate a customer-ready quote.")

# --- Session state ---
for key in ["quote_ready","courier_data","form_data","order_type_done","shipping_done"]:
    if key not in st.session_state:
        st.session_state[key] = False if key!="courier_data" else []

# ---------------- STEP 1 ----------------
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

        submitted = st.form_submit_button("Next")

    if submitted:
        total_pieces = sum(qty)

        st.session_state.form_data={
            "cname":cname,
            "pincode":pincode,
            "qty":qty,
            "total_pieces":total_pieces
        }

        if total_pieces < 10:
            st.session_state.form_data["order_type"] = "Sample"
            st.session_state.order_type_done = True
        else:
            st.session_state.order_type_done = False

        st.session_state.quote_ready=True
        st.rerun()

# ---------------- STEP 2 ----------------
elif not st.session_state.order_type_done:
    st.subheader("Order Type")

    with st.form("type_form"):
        order_type = st.radio("Select Order Type:", ["Vendor", "Event"])
        submit = st.form_submit_button("Confirm")

    if submit:
        st.session_state.form_data["order_type"] = order_type
        st.session_state.order_type_done = True
        st.rerun()

# ---------------- STEP 3 ----------------
elif not st.session_state.shipping_done:
    st.subheader("Shipping Selection")

    fd = st.session_state.form_data

    # Fetch couriers once
    if not st.session_state.courier_data:
        login = requests.post(
            "https://apiv2.shiprocket.in/v1/external/auth/login",
            json={"email": EMAIL, "password": PASSWORD}
        )
        token = login.json().get("token")

        if token:
            headers = {"Authorization": f"Bearer {token}"}
            res = requests.get(
                "https://apiv2.shiprocket.in/v1/external/courier/serviceability/",
                headers=headers,
                params={
                    "pickup_postcode":"110062",
                    "delivery_postcode":fd["pincode"],
                    "weight":1,
                    "cod":0
                }
            )
            data = res.json()
            if "data" in data:
                st.session_state.courier_data = data["data"]["available_courier_companies"]

    with st.form("ship_mode"):
        mode = st.radio("Select Shipping Mode:", ["Courier", "Custom"])
        submit = st.form_submit_button("Confirm")

    if submit:
        st.session_state.form_data["ship_mode"] = mode
        st.session_state.shipping_done = True
        st.rerun()

# ---------------- STEP 4 ----------------
else:
    st.subheader("Final Adjustments")

    fd = st.session_state.form_data
    mode = fd["ship_mode"]

    with st.form("final_form"):

        # Shipping
        if mode=="Courier":
            couriers = [
                f"{c['courier_name']} - ₹{c['rate']} ({c['etd']})"
                for c in st.session_state.courier_data
            ]
            selected = st.selectbox("Select Courier:", couriers)
        else:
            custom_shipping = st.number_input("Custom Shipping Amount (₹)", 0)

        # Extras
        extra = st.number_input("Extra Charges (₹)", 0)
        notes = st.text_area("Notes")

        confirm = st.form_submit_button("Generate Final Quote")

    if confirm:
        qty = fd["qty"]
        total_pieces = fd["total_pieces"]

        subtotal=0
        for i,p in enumerate(product_list):
            if qty[i]>0:
                if total_pieces<10:
                    price = p["sample_price"]
                else:
                    price = p["vendor_price"] if fd["order_type"]=="Vendor" else p["event_price"]

                subtotal += price*qty[i]

        # Shipping
        if mode=="Courier":
            c = next(x for x in st.session_state.courier_data if f"{x['courier_name']} - ₹{x['rate']} ({x['etd']})"==selected)
            shipping = c["rate"]
            etd = c["etd"]
            cname = c["courier_name"]
        else:
            shipping = custom_shipping
            etd = "As communicated"
            cname = "Custom"

        gst = (subtotal + shipping + extra)*0.05
        final = subtotal + shipping + extra + gst

        # Message
# --- MESSAGE ---
msg = f"""
Customer: {fd['cname']}
Pincode: {fd['pincode']}

Order Details:
"""

for i, p in enumerate(product_list):
    if qty[i] > 0:
        if total_pieces < 10:
            price = p["sample_price"]
        else:
            price = p["vendor_price"] if fd["order_type"] == "Vendor" else p["event_price"]

        total_price = price * qty[i]

        msg += f"{p['pname']} | {qty[i]} x ₹{price} | ₹{total_price}\n"

# --- Totals ---
msg += f"""
-----------------------------------
Subtotal: ₹{subtotal}
Shipping: ₹{shipping}
Extra Charges: ₹{extra}
"""

# ✅ GST on EVERYTHING
gst = (subtotal + shipping + extra) * 0.05
final = subtotal + shipping + extra + gst

msg += f"""GST (5%): ₹{gst:.2f}
Final Total: ₹{final:.2f}
Estimated Delivery: {etd}

Notes:
{notes}
"""
"""

        st.text_area("Generated Quote",msg,height=300)
        copy_button(msg, tooltip="Copy Quote", copied_label="Copied!", icon="📋")

        if st.button("Create New Quote"):
            for key in ["quote_ready","courier_data","form_data","order_type_done","shipping_done"]:
                st.session_state[key] = False if key!="courier_data" else []
            st.rerun()
