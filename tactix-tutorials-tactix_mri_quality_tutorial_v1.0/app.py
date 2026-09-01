"""!
Copyright (c) Fraunhofer MEVIS, Germany. All rights reserved.
The software is not qualified for use as a medical product or as part
thereof. No bugs or restrictions are known.
"""

import streamlit

streamlit.set_page_config(page_title="MR Image Quality Assessment")
streamlit.title("MR Image Quality Assessment")


streamlit.page_link("pages/1_Quality_Assessment.py", label="Quality Assessment", icon=":material/analytics:")
streamlit.page_link("pages/2_Quality_Parameter.py", label="Quality Parameter", icon=":material/straighten:")
streamlit.page_link("pages/3_Quality_Index.py", label="Quality Index", icon=":material/functions:")
streamlit.page_link("pages/4_Sharpness.py", label="Sharpness", icon=":material/blur_on:")
streamlit.page_link("pages/5_SNR.py", label="SNR", icon=":material/graphic_eq:")
streamlit.page_link("pages/6_Image_Processing.py", label="Image Processing", icon=":material/tune:")
