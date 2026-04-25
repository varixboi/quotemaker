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
]

st.header("Quote Maker")

# --- Session ---
for key in ["quote_ready","courier_data","form_data","order_type_done","shipping_done"]:
    if key not in st.session_state:
        st.session_state[key] = False if key!="courier_data" else []

# --- STEP 1 ---
if not st.session_state.quote_ready:
    with st.form("form"):
        cname = st.text_input("Customer Name")
        pincode = st.number_input("Pincode", step=1)

        qty=[0]*len(product_list)
        for i,p in enumerate(product_list):
            qty[i]=st.number_input(p["pname"],step=1)

        submit=st.form_submit_button("Next")

    if submit:
        total_pieces = sum(qty)

        st.session_state.form_data={
            "cname":cname,
            "pincode":pincode,
            "qty":qty,
            "total_pieces": total_pieces
        }

        # 👇 Skip vendor/event if <10
        if total_pieces < 10:
            st.session_state.form_data["order_type"] = "Sample"
            st.session_state.order_type_done = True
        else:
            st.session_state.order_type_done = False

        st.session_state.quote_ready=True
        st.rerun()

# --- STEP 2: ORDER TYPE (ONLY IF ≥10) ---
elif not st.session_state.order_type_done:
    with st.form("type_form"):
        order_type = st.radio("Order Type:", ["Vendor", "Event"])
        submit = st.form_submit_button("Confirm")

    if submit:
        st.session_state.form_data["order_type"] = order_type
        st.session_state.order_type_done = True
        st.rerun()

# --- STEP 3: SHIPPING MODE ---
elif not st.session_state.shipping_done:

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
        mode = st.radio("Shipping Mode:", ["Courier", "Custom"])
        submit = st.form_submit_button("Confirm")

    if submit:
        st.session_state.form_data["ship_mode"] = mode
        st.session_state.shipping_done = True
        st.rerun()

# --- STEP 4: FINAL ---
else:
    fd = st.session_state.form_data
    mode = fd["ship_mode"]

    with st.form("final"):

        # Shipping
        if mode=="Courier":
            couriers = [
                f"{c['courier_name']} - ₹{c['rate']} ({c['etd']})"
                for c in st.session_state.courier_data
            ]
            selected = st.selectbox("Courier:", couriers)
        else:
            custom_shipping = st.number_input("Custom Shipping ₹", 0)

        # Extras
        extra = st.number_input("Extra Charges ₹", 0)
        notes = st.text_area("Notes")

        submit = st.form_submit_button("Generate Quote")

    if submit:
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
        else:
            shipping = custom_shipping
            etd = "As communicated"

        gst = (subtotal + shipping + extra)*0.05
        final = subtotal + shipping + extra + gst

        # Message
        msg=f"""
Customer: {fd['cname']}
Pincode: {fd['pincode']}

Order:
"""
        for i,p in enumerate(product_list):
            if qty[i]>0:
                if total_pieces<10:
                    price=p["sample_price"]
                else:
                    price = p["vendor_price"] if fd["order_type"]=="Vendor" else p["event_price"]

                msg+=f"{p['pname']} ₹{price} x {qty[i]}\n"

        msg+=f"""
Subtotal: ₹{subtotal}
Shipping: ₹{shipping}
Extra: ₹{extra}
GST: ₹{gst:.2f}
Total: ₹{final:.2f}
Delivery: {etd}

Notes:
{notes}
"""

        st.text_area("Quote",msg,height=300)
        copy_button(msg)
