%%writefile ocr_app.py




import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
from PIL import Image
import pandas as pd
import numpy as np
import re
import io
import sqlite3


def image_to_text(path):

  input_img = Image.open(path)


  #CONVERTNG IMAGE TO ARRAY FORMAT
  image_array = np.array(input_img)

  reader = easyocr.Reader(['en'])
  text = reader.readtext(image_array,detail=0)

  return text,input_img

def extracted_text(texts):

  extracted_dict = {'NAME':[],'DESIGNATION':[],'COMPANY_NAME':[],'CONTACT':[],'EMAIL':[],'WEBSITE':[],'ADDRESS':[],'PINCODE':[]}

  extracted_dict['NAME'].append(texts[0])
  extracted_dict['DESIGNATION'].append(texts[1])

  for i in range(2,len(texts)):
    if texts[i].startswith("+") or (texts[i].replace("-","").isdigit() and '-' in texts[i]):
      extracted_dict['CONTACT'].append(texts[i])

    elif '@' in texts[i] and '.com' in texts[i]:
      extracted_dict['EMAIL'].append(texts[i])

    elif 'WWW' in texts[i] or 'www' in texts[i] or 'Www' in texts[i] or 'wWw' in texts[i] or 'wwW' in texts[i]:
      small = texts[i].lower()
      extracted_dict['WEBSITE'].append(small)

    elif "Tamil Nadu" in texts[i] or "TamilNadu" in texts[i] or texts[i].isdigit():
      extracted_dict['PINCODE'].append(texts[i])

    elif re.match(r'^[A-Za-z]',texts[i]):
      extracted_dict['COMPANY_NAME'].append(texts[i])

    else:
      remove_colon = re.sub(r'[,;]','',texts[i])
      extracted_dict['ADDRESS'].append(remove_colon)


  for key,value in extracted_dict.items():
    if len(value) > 0:
      concatenate = " ".join(value)
      extracted_dict[key] = [concatenate]

    else:
      value = "NA"
      extracted_dict[key] = [value]



  return extracted_dict





#streamlit code

st.set_page_config(layout = "wide")
st.title("Extracting Business Card Data with 'OCR'")

with st.sidebar:

  select = option_menu("Main menu", ["Home","Upload and Modify","Delete"])

if select == "Home":
  col1,col2 = st.columns(2)
  with col1:
        col1.image(Image.open("/content/drive/MyDrive/images.jpeg"),width = 500)

  with col2:
        st.markdown("#### :green[**Technologies Used :**] Python, easy OCR, Streamlit, SQL, Pandas.")
        st.markdown("#### :green[**Overview :**] In this streamlit web app you can upload an image of a business card and extract relevant information from it using easyOCR. You can view, modify or delete the extracted data in this app. This app would also allow users to save the extracted information into a database along with the Uploaded business card image. The database would be able to store multiple entries, each with its own business card image and extracted information.")

elif select == "Upload and Modify":
  img = st.file_uploader("Upload the File/Image",type=["png","jpg",'jpeg'])

  if img is not None:
    st.image(img, width = 300)

    text_img, input_img = image_to_text(img)

    text_dict = extracted_text(text_img)

    if text_dict:
        st.success("Text has extracted successfully")

        df = pd.DataFrame(text_dict)

        #converting image to bytes
        image_bytes = io.BytesIO()
        input_img.save(image_bytes, format = 'PNG')

        image_data = image_bytes.getvalue()

        #creating dictionary
        data = {"IMAGE":[image_data]}

        df_1 = pd.DataFrame(data)

        concat_df = pd.concat([df,df_1],axis= 1)

        st.dataframe(concat_df)

        button_1 = st.button("Save")

    if button_1:
        mydb = sqlite3.connect("bizcardx.db")
        cursor = mydb.cursor()

      # Table creation

        create_table_query = '''CREATE TABLE IF NOT EXISTS bizcard_details(name varchar(225),
                                                                      designation varchar(225),
                                                                      company_name varchar(225),
                                                                      contact varchar(225),
                                                                      email varchar(225),
                                                                      website text,
                                                                      address text,
                                                                      pincode varchar(225),
                                                                      image text)'''

        cursor.execute(create_table_query)
        mydb.commit()


        # INSERT QUERY

        insert_query = '''INSERT INTO bizcard_details(name, designation, company_name, contact, email, website, address,
                                                      pincode, image)

                                                      values(?,?,?,?,?,?,?,?,?)'''

        datas = concat_df.values.tolist()[0]
        cursor.execute(insert_query,datas)
        mydb.commit()

        st.success("Saved Successfully")

    method = st.radio("Select the Method",["None","Preview","Modify",])

    if method == "None":
      st.write("")

    if method == "Preview":
      mydb = sqlite3.connect("bizcardx.db")
      cursor = mydb.cursor()
      #select query
      select_query = "SELECT * FROM bizcard_details"

      cursor.execute(select_query)
      table = cursor.fetchall()
      mydb.commit()


      table_df = pd.DataFrame(table, columns = ("NAME", "DESIGNATION", "COMPANY_NAME", "CONTACT", "EMAIL",
                                                "WEBSITE", "ADDRESS", "PINCODE", "IMAGE"))

      st.dataframe(table_df)


    elif method == "Modify":

      mydb = sqlite3.connect("bizcardx.db")
      cursor = mydb.cursor()
      #select query
      select_query = "SELECT * FROM bizcard_details"

      cursor.execute(select_query)
      table = cursor.fetchall()
      mydb.commit()


      table_df = pd.DataFrame(table, columns = ("NAME", "DESIGNATION", "COMPANY_NAME", "CONTACT", "EMAIL",
                                                "WEBSITE", "ADDRESS", "PINCODE", "IMAGE"))

      col1, col2 = st.columns(2)
      with col1:

        selected_name = st.selectbox("Select the name",table_df['NAME'])

      df_3 = table_df[table_df["NAME"] == selected_name]

      df_4 = df_3.copy()

      col1,col2 = st.columns(2)

      with col1:
        modify_name = st.text_input("Name",df_3['NAME'].unique()[0])
        modify_des = st.text_input("Designation",df_3['DESIGNATION'].unique()[0])
        modify_Company = st.text_input("Company_name",df_3['COMPANY_NAME'].unique()[0])
        modify_contact = st.text_input("Contact",df_3['CONTACT'].unique()[0])
        modify_email = st.text_input("Email",df_3['EMAIL'].unique()[0])

        df_4['NAME'] = modify_name
        df_4['DESIGNATION'] = modify_des
        df_4['COMPANY_NAME'] = modify_Company
        df_4['CONTACT'] = modify_contact
        df_4['EMAIL'] = modify_email

      with col2:
        modify_web = st.text_input("Website",df_3['WEBSITE'].unique()[0])
        modify_address = st.text_input("Address",df_3['ADDRESS'].unique()[0])
        modify_pincode = st.text_input("Pincode",df_3['PINCODE'].unique()[0])
        modify_image = st.text_input("Image",df_3['IMAGE'].unique()[0])

        df_4['WEBSITE'] = modify_web
        df_4['ADDRESS'] = modify_address
        df_4['PINCODE'] = modify_pincode
        df_4['IMAGE'] = modify_image

      st.dataframe(df_4)

      col1,col2 = st.columns(2)

      with col1:
        button_3 = st.button("Modify", use_container_width = True)

      if button_3:
        mydb = sqlite3.connect("bizcardx.db")
        cursor = mydb.cursor()

        cursor.execute(f"DELETE FROM bizcard_details  WHERE NAME = '{selected_name}'")
        mydb.commit()

        # INSERT QUERY

        insert_query = '''INSERT INTO bizcard_details(name, designation, company_name, contact, email, website, address,
                                                      pincode, image)

                                                      values(?,?,?,?,?,?,?,?,?)'''

        datas = df_4.values.tolist()[0]
        cursor.execute(insert_query,datas)
        mydb.commit()

        st.success("Modified Successfully")


elif select == "Delete":
  mydb = sqlite3.connect("bizcardx.db")
  cursor = mydb.cursor()

  col1, col2 = st.columns(2)
  with col1:
    select_query = "SELECT NAME FROM bizcard_details"

    cursor.execute(select_query)
    table1 = cursor.fetchall()
    mydb.commit()


    names = []
    for i in table1:
      names.append(i[0])

    name_select = st.selectbox("Select the name", names)

  with col2:
    select_query = "SELECT DESIGNATION FROM bizcard_details WHERE NAME = '{designation_select}'"

    cursor.execute(select_query)
    table2 = cursor.fetchall()
    mydb.commit()


    designations = []
    for j in table2:
      designations.append(j[0])

    designation_select = st.selectbox("Select the designation", designations)

  if name_select and designation_select:
    col1,col2,col3 = st.columns(3)

    with col1:
      st.write(f"Selected Name: {name_select}")
      st.write("")
      st.write("")
      st.write("")
      st.write(f"Selected Designation: {designation_select}")

    with col2:
      st.write("")
      st.write("")
      st.write("")
      st.write("")

      remove = st.button("Delete", use_container_width = True)

      if remove:
        cursor.execute(f"DELETE FROM bizcard_details  WHERE NAME = ' {name_select}' AND DESIGNATION = '{designation_select}'")
        mydb.commit()
        st.success(f"DELETED")



