import streamlit as st

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

import requests

# ---- SHIPROCKET API HELPERS ----
def get_shiprocket_token(email, password):
    url = "https://apiv2.shiprocket.in/v1/external/auth/login"
    payload = {"email": email, "password": password}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()["token"]
    else:
        st.error("Failed to get Shiprocket token. Check your credentials.")
        return None

def get_shipping_rates(token, pickup_pincode, delivery_pincode, weight, cod=0):
    url = "https://apiv2.shiprocket.in/v1/external/courier/serviceability/"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "pickup_postcode": pickup_pincode,
        "delivery_postcode": delivery_pincode,
        "weight": weight,
        "cod": cod
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        if "data" in data and "available_courier_companies" in data["data"]:
            return data["data"]["available_courier_companies"]
        else:
            st.warning("No courier options available for given details.")
            return []
    else:
        st.error("Failed to fetch shipping rates from Shiprocket.")
        return []


st.header("Quote maker for Subtlewear")
st.caption("Enter your order here and copy the text and send to customer")



with st.form(key="quotemaker"):
    
    st.title("Enter Customer Details:")

    cname=st.text_input("Enter customer's name:")
    pincode=st.number_input("Enter customer pincode:",step=1)

    st.title("Enter Product Quantity:")

    qty=[0]*len(product_list)
    for i in range(len(product_list)):
        qty[i]=st.number_input(product_list[i]["pname"],step=1)

    

    submitted=st.form_submit_button()


    if submitted:
        taxable=0
        total_weight=0
        total_pieces=sum(qty)

        if(total_pieces<10):
            for i in range(total_pieces):
                taxable=qty[i]*product_list[i]["sample_price"]
                total_weight=qty[i]*product_list[i]["weight"]
        else:
            for i in range(total_pieces):
                taxable=qty[i]*product_list[i]["bulk_price"]
                total_weight=qty[i]*product_list[i]["weight"]

         # Display summary
    st.subheader("📦 Order Summary")
    st.write(f"**Customer:** {cname}")
    st.write(f"**Pincode:** {pincode}")
    st.write(f"**Total Pieces:** {total_pieces}")
    st.write(f"**Total Weight:** {round(total_weight, 2)} kg")
    st.write(f"**Subtotal (before GST): ₹{taxable:.2f}**")

    # ---- SHIPROCKET SHIPPING ESTIMATION ----
    st.subheader("🚚 Shipping Estimation (via Shiprocket)")
    email = st.text_input("Shiprocket Email")
    password = st.text_input("Shiprocket Password", type="password")
    pickup_pincode = st.text_input("Pickup Pincode", value="110062")

    if st.button("Get Shipping Options"):
        token = get_shiprocket_token(email, password)
        if token:
            couriers = get_shipping_rates(token, pickup_pincode, pincode, total_weight)
            if couriers:
                courier_names = [f"{c['courier_name']} - ₹{c['rate']}" for c in couriers]
                selected = st.selectbox("Select Courier Service", courier_names)

                if selected:
                    selected_rate = float(selected.split("₹")[-1])
                    gst = taxable * 0.05
                    total_amount = taxable + gst + selected_rate

                    result_text = (
                        f"Customer: {cname}\n"
                        f"Pincode: {pincode}\n"
                        f"Total pieces: {total_pieces}\n"
                        f"Weight: {round(total_weight,2)} kg\n"
                        f"Subtotal: ₹{taxable}\n"
                        f"GST (5%): ₹{gst:.2f}\n"
                        f"Shipping: ₹{selected_rate}\n"
                        f"**Total: ₹{total_amount:.2f}**"
                    )

                    st.code(result_text)
                    st.copy_to_clipboard(result_text)
                    st.success("Copied to clipboard ✅")