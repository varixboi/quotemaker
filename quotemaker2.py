import streamlit as st
import requests
from st_copy import copy_button

# ---------------- CONFIG ----------------
EMAIL = st.secrets["SHIPROCKET_EMAIL"]
PASSWORD = st.secrets["SHIPROCKET_PASSWORD"]
DELHIVERY_TOKEN = st.secrets["DELHIVERY_TOKEN"]

# ---------------- PRODUCT LIST ----------------
product_list = [
    {"pname":"240GSM French Terry OS","price":205,"weight":0.33},
    {"pname":"210GSM French Terry OS","price":195,"weight":0.28},
    {"pname":"180GSM Oversized Tshirt","price":185,"weight":0.27},

    {"pname":"180GSM Regular Fit Tshirt","price":150,"weight":0.22},
    {"pname":"180GSM Non-Biowash Tshirt","price":115,"weight":0.22},

    {"pname":"320GSM Hoodie","price":350,"weight":0.59},
    {"pname":"320GSM Sweatshirt","price":280,"weight":0.49},
    {"pname":"420GSM OS Hoodie","price":420,"weight":0.79},
    {"pname":"420GSM OS Hoodie - II","price":460,"weight":0.79},
    {"pname":"Varsity Jacket","price":400,"weight":0.59},

    {"pname":"240GSM Acid Wash OS","price":250,"weight":0.28},
    {"pname":"180GSM Acid Wash RF","price":190,"weight":0.22},

    {"pname":"Cotton Polo","price":210,"weight":0.28},
    {"pname":"Premium Cotton Polo","price":250,"weight":0.28},
]

# ---------------- UI ----------------
st.header("Quote Maker for Subtlewear")
st.caption("Generate customer-ready quotes instantly.")

# ---------------- SESSION STATE ----------------
for key in ["quote_ready", "courier_data", "form_data", "shipping_done"]:
    if key not in st.session_state:
        st.session_state[key] = False if key != "courier_data" else []

# =========================================================
# STEP 1 - CUSTOMER + PRODUCTS
# =========================================================
if not st.session_state.quote_ready:

    with st.form("quote_form"):

        st.subheader("Customer Details")

        cname = st.text_input("Customer Name")
        pincode = st.number_input("Customer Pincode", step=1)

        qty = [0] * len(product_list)

        for i in range(len(product_list)):

            if i == 0:
                st.subheader("Oversized Tshirts")

            elif i == 3:
                st.subheader("Regular Fit Tshirts")

            elif i == 5:
                st.subheader("Hoodies & More")

            elif i == 10:
                st.subheader("Acid Wash Tshirts")

            elif i == 12:
                st.subheader("Polo Tshirts")

            qty[i] = st.number_input(
                product_list[i]["pname"],
                min_value=0,
                step=1
            )

        submitted = st.form_submit_button("Next")

    if submitted:

        total_pieces = sum(qty)

        total_weight = 0

        for i, p in enumerate(product_list):
            total_weight += p["weight"] * qty[i]

        st.session_state.form_data = {
            "cname": cname,
            "pincode": pincode,
            "qty": qty,
            "total_pieces": total_pieces,
            "total_weight": total_weight
        }

        st.session_state.shipping_done = False
        st.session_state.quote_ready = True

        st.rerun()

# =========================================================
# STEP 2 - SHIPPING
# =========================================================
elif not st.session_state.shipping_done:

    st.subheader("Shipping Selection")

    fd = st.session_state.form_data

    # ---------------- SHIPROCKET FETCH ----------------
    if not st.session_state.courier_data:

        try:

            login = requests.post(
                "https://apiv2.shiprocket.in/v1/external/auth/login",
                json={
                    "email": EMAIL,
                    "password": PASSWORD
                }
            )

            token = login.json().get("token")

            if token:

                headers = {
                    "Authorization": f"Bearer {token}"
                }

                res = requests.get(
                    "https://apiv2.shiprocket.in/v1/external/courier/serviceability/",
                    headers=headers,
                    params={
                        "pickup_postcode": "110062",
                        "delivery_postcode": fd["pincode"],
                        "weight": fd["total_weight"],
                        "cod": 0
                    }
                )

                data = res.json()

                if "data" in data:
                    st.session_state.courier_data = (
                        data["data"]["available_courier_companies"]
                    )

        except Exception as e:
            st.error(f"Shiprocket Error: {e}")

    with st.form("ship_mode"):

        mode = st.radio(
            "Select Shipping Mode:",
            ["Shiprocket", "Delhivery", "Custom"]
        )

        submit = st.form_submit_button("Confirm")

    if submit:

        st.session_state.form_data["ship_mode"] = mode
        st.session_state.shipping_done = True

        st.rerun()

# =========================================================
# STEP 3 - FINAL QUOTE
# =========================================================
else:

    st.subheader("Final Adjustments")

    fd = st.session_state.form_data
    mode = fd["ship_mode"]

    # ---------------- DELHIVERY FETCH ----------------
    delhivery_rate = None
    delhivery_etd = "3-7 Days"

    if mode == "Delhivery":

        headers = {
            "Authorization": f"Token {DELHIVERY_TOKEN}"
        }

        params = {
            "md": "S",
            "ss": "Delivered",
            "d_pin": fd["pincode"],
            "o_pin": "110062",
            "cgm": int(fd["total_weight"] * 1000)
        }

        try:

            response = requests.get(
                "https://track.delhivery.com/api/kinko/v1/invoice/charges/.json",
                headers=headers,
                params=params
            )

            data = response.json()

            if "total_amount" in data:
                delhivery_rate = data["total_amount"]

        except Exception as e:
            st.error(f"Delhivery Error: {e}")

    # ---------------- FINAL FORM ----------------
    with st.form("final_form"):

        # ---------- SHIPROCKET ----------
        if mode == "Shiprocket":

            couriers = [
                f"{c['courier_name']} - ₹{c['rate']} ({c['etd']})"
                for c in st.session_state.courier_data
            ]

            selected = st.selectbox(
                "Select Courier:",
                couriers
            )

        # ---------- DELHIVERY ----------
        elif mode == "Delhivery":

            if delhivery_rate:
                st.success(f"Delhivery Shipping: ₹{delhivery_rate}")
                st.caption(f"Estimated Delivery: {delhivery_etd}")
            else:
                st.error("Unable to fetch Delhivery rate.")

        # ---------- CUSTOM ----------
        else:

            custom_shipping = st.number_input(
                "Custom Shipping Amount (₹)",
                min_value=0
            )

        # ---------- EXTRA ----------
        print_cost = st.number_input(
            "Print Cost (₹)",
            min_value=0
        )

        extra = st.number_input(
            "Extra Charges (₹)",
            min_value=0
        )

        notes = st.text_area("Notes")

        confirm = st.form_submit_button("Generate Final Quote")

    # =========================================================
    # GENERATE FINAL QUOTE
    # =========================================================
    if confirm:

        qty = fd["qty"]

        subtotal = 0
        total_weight = 0

        msg = f"""
Customer: {fd['cname']}
Pincode: {fd['pincode']}

Order Details:
"""

        for i, p in enumerate(product_list):

            if qty[i] > 0:

                price = p["price"]

                total_price = price * qty[i]
                item_weight = p["weight"] * qty[i]

                subtotal += total_price
                total_weight += item_weight

                msg += (
                    f"{p['pname']} | "
                    f"{qty[i]} x ₹{price} | "
                    f"₹{total_price}\n"
                )

        # ---------------- SHIPPING ----------------
        if mode == "Shiprocket":

            c = next(
                x for x in st.session_state.courier_data
                if (
                    f"{x['courier_name']} - ₹{x['rate']} ({x['etd']})"
                    == selected
                )
            )

            shipping = c["rate"]
            etd = c["etd"]

        elif mode == "Delhivery":

            shipping = delhivery_rate if delhivery_rate else 0
            etd = delhivery_etd

        else:

            shipping = custom_shipping
            etd = "As communicated"

        # ---------------- GST ----------------
        gst = (
            subtotal +
            shipping +
            print_cost +
            extra
        ) * 0.05

        final = (
            subtotal +
            shipping +
            print_cost +
            extra +
            gst
        )

        # ---------------- FINAL MESSAGE ----------------
        msg += f"""
-----------------------------------

Subtotal: ₹{subtotal}

Print Cost: ₹{print_cost}

Shipping: ₹{shipping}

Extra Charges: ₹{extra}

Total Weight: {total_weight:.2f} KG

GST (5%): ₹{gst:.2f}

Final Total: ₹{final:.2f}

Estimated Delivery: {etd}

Notes:
{notes}
"""

        st.text_area(
            "Generated Quote",
            msg,
            height=350
        )

        copy_button(
            msg,
            tooltip="Copy Quote",
            copied_label="Copied!",
            icon="📋"
        )

        # ---------------- RESET ----------------
        if st.button("Create New Quote"):

            for key in [
                "quote_ready",
                "courier_data",
                "form_data",
                "shipping_done"
            ]:
                st.session_state[key] = (
                    False if key != "courier_data" else []
                )

            st.rerun()
