import streamlit as st
import pandas as pd

st.set_page_config(
    page_title='Accounting & Prepayments Export',
    page_icon='🧾'
)

st.caption('VACAYZEN')
st.title('Accounting & Prepayments Export')
st.info('Hooking up the Accounting Bros with their monthly report.')

with st.expander('Uploaded Files'):
    
    file_descriptions = [
        ['Partners.csv','Google Drive > Shared with me > Tech'],
        ['Site_To_Partner.csv','Google Drive > Shared with me > Tech'],
        ['House_Agreements.csv','Google Drive > Shared with me > Tech'],
        ['CTLL_RentalAgreement.csv','Google Drive > Shared with me > Tech'],
        ['Prepayment Export.csv','Google Drive > Shared with me > Tech']
    ]

    files = {
        'Partners.csv': None,
        'Site_To_Partner.csv': None,
        'House_Agreements.csv': None,
        'CTLL_RentalAgreement.csv': None,
        'Prepayment Export.csv': None
    }


    uploaded_files = st.file_uploader(
        label='Files (' + str(len(files)) + ')',
        accept_multiple_files=True
    )

    st.info('File names are **case sensitive** and **must be identical** to the file name below.')
    st.dataframe(pd.DataFrame(file_descriptions, columns=['Required File','Source Location']), hide_index=True, use_container_width=True)










if len(uploaded_files) > 0:
    for index, file in enumerate(uploaded_files):
        files[file.name] = index

    hasAllRequiredFiles = True
    missing = []

    for file in files:
        if files[file] == None:
            hasAllRequiredFiles = False
            missing.append(file)

if len(uploaded_files) > 0 and not hasAllRequiredFiles:
    for item in missing:
        st.warning('**' + item + '** is missing and required.')


elif len(uploaded_files) > 0 and hasAllRequiredFiles:
    partners               = pd.read_csv(uploaded_files[files['Partners.csv']])
    sites                  = pd.read_csv(uploaded_files[files['Site_To_Partner.csv']])
    houseAgreements        = pd.read_csv(uploaded_files[files['House_Agreements.csv']])
    ra                     = pd.read_csv(uploaded_files[files['CTLL_RentalAgreement.csv']])
    pp                     = pd.read_csv(uploaded_files[files['Prepayment Export.csv']])


    src = pd.merge(partners,        sites, how='left')
    ha  = pd.merge(houseAgreements, ra,    how='left', left_on='RentalAgreementID', right_on='ID')

    df  = pd.merge(pp, ra,  how='left', left_on='RentalAgreementNo', right_on='ID', validate='m:1')
    src_temp = src.drop_duplicates(subset='CID')
    df  = pd.merge(df, src_temp, how='left', left_on='CustomerNumber',    right_on='CID')
    df  = df.drop(columns=['OriginSource_y'])
    df  = df.rename(columns={'OriginSource_x': 'OriginSource', 'Customer': 'PartnerOrder'})
    df  = pd.merge(df, src, how='left', on='OriginSource')
    df  = df.drop(columns=['CID_x','CID_y'], axis=1)
    df  = df.rename(columns={'Customer': 'PartnerSiteOrder'})
    ha_temp = ha.drop_duplicates(subset=['AgrmtJobAddrLat','AgrmtJobAddrLong'], keep='last')
    df  = pd.merge(df, ha_temp,  how='left', on=['AgrmtJobAddrLat','AgrmtJobAddrLong'], validate='m:1')
    df  = df.drop(columns=['ID_x','OriginSource_x','RentalAgreementID','ID_y','OriginSource_y','CustomerNumber_y','AgrmtJobAddrLong','CustomerNumber_x'])
    df  = df.rename(columns={'Partner': 'PartnerLatLong'})

    def Attribute_Prepayment_To_Partner(row):
        if pd.notna(row.PartnerOrder):
            return row.PartnerOrder
        
        if pd.notna(row.PartnerSiteOrder):
            return row.PartnerSiteOrder
        
        if row.AgrmtJobAddrLat != 0 and row.AgrmtJobAddrLat and pd.notna(row.PartnerLatLong):
            return row.PartnerLatLong


    df['Customer'] = df.apply(Attribute_Prepayment_To_Partner, axis=1)
    df = df.drop(columns=['AgrmtJobAddrLat','PartnerOrder','PartnerSiteOrder','PartnerLatLong'], axis=1)

    st.download_button(label='DOWNLOAD', data=df.to_csv(index=False), file_name='prepayments.csv', mime='csv', use_container_width=True, type='primary')