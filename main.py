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
        ['CTLL_RentalAgreementLines.csv','Google Drive > Shared with me > Tech'],
        ['CTLL_RentalAgreement.csv','Google Drive > Shared with me > Tech'],
        ['CTLL_PartnerSiteRentalAgreements.csv','Google Drive > Shared with me > Tech'],
        ['Prepayment Export.csv','Google Drive > Shared with me > Tech']
    ]

    files = {
        'Partners.csv': None,
        'Site_To_Partner.csv': None,
        'House_Agreements.csv': None,
        'CTLL_RentalAgreementLines.csv': None,
        'CTLL_RentalAgreement.csv': None,
        'CTLL_PartnerSiteRentalAgreements.csv': None,
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
    partnerSiteAgreements  = pd.read_csv(uploaded_files[files['CTLL_PartnerSiteRentalAgreements.csv']])
    ral                    = pd.read_csv(uploaded_files[files['CTLL_RentalAgreementLines.csv']])
    ra                     = pd.read_csv(uploaded_files[files['CTLL_RentalAgreement.csv']])
    pp                     = pd.read_csv(uploaded_files[files['Prepayment Export.csv']])


#################################################
#
# Revenue KPI
#
#################################################


    # Define House Agreement Versus Rental Agreement

    houseAgreements.sort_values(by=['RentalAgreementID'])

    house  = ral[ral['RentalAgreementID'].isin(houseAgreements.RentalAgreementID.array)]
    rental = ral[~ral['RentalAgreementID'].isin(houseAgreements.RentalAgreementID.array)]


    # House Agreement (Lat, Long) => Partner

    df           = house[['CustomerNumber','Latitude','Longitude']]
    df           = df[df['CustomerNumber'].isin(partners.CID.array)]
    df           = df.drop_duplicates()
    ra2c         = pd.merge(df, ra, left_on=['Latitude','Longitude'], right_on=['AgrmtJobAddrLat', 'AgrmtJobAddrLong'], how="left")
    ra2c         = ra2c.drop_duplicates(keep="last")
    ra2c         = ra2c[ra2c != 0]
    ra2c         = ra2c.dropna(subset=['AgrmtJobAddrLat','AgrmtJobAddrLong'])
    ra2c         = ra2c[['ID','CustomerNumber']]
    ra2c.columns = ['RentalAgreementNo','Partner']


    # Partner Site Submission Rental Agreement (Lat, Long) => Partner

    siteToPartner      = pd.merge(partners, sites, on="CID")
    partnerSiteLatLong = pd.merge(partnerSiteAgreements, ra, on="ID", how="left")
    partnerToLatLong   = pd.merge(partnerSiteLatLong, siteToPartner, on="OriginSource", how="left")
    partnerToLatLong   = partnerToLatLong[['CID','AgrmtJobAddrLat','AgrmtJobAddrLong']]
    partnerToLatLong   = partnerToLatLong.drop_duplicates(keep="last")
    ra2p               = pd.merge(partnerToLatLong, ra, left_on=['AgrmtJobAddrLat', 'AgrmtJobAddrLong'], right_on=['AgrmtJobAddrLat', 'AgrmtJobAddrLong'], how="left")
    ra2p               = ra2p.drop_duplicates(keep="last")
    ra2p               = ra2p[ra2p != 0]
    ra2p               = ra2p.dropna(subset=['AgrmtJobAddrLat','AgrmtJobAddrLong'])
    ra2p               = ra2p[['ID','CID']]
    ra2p.columns       = ['RentalAgreementNo','Partner']


    # Combine (House Agreement (Lat, Long) => Partner) & (Partner Site Submission Rental Agreement (Lat, Long) => Partner)

    ra2p = pd.concat([ra2c, ra2p])
    ra2p.drop_duplicates()

    # Generate Results

    result          = pd.merge(pp, ra2p, how='left')
    result          = result.drop_duplicates(subset=['RentalAgreementNo','RentalAgreementStartDate','RentalAgreementEndDate','RentalAgreementReservationStartDate','RentalAgreementReservationEndDate','TransactionAmount','PaymentDate','PaymentMethod'],keep='last')
    result          = pd.merge(result, partners, left_on="Partner", right_on="CID", how="left")

    result['RentalAgreementStartDate']            = pd.to_datetime(result['RentalAgreementStartDate']).dt.normalize()
    result['RentalAgreementEndDate']              = pd.to_datetime(result['RentalAgreementEndDate']).dt.normalize()
    result['RentalAgreementReservationStartDate'] = pd.to_datetime(result['RentalAgreementReservationStartDate']).dt.normalize()
    result['RentalAgreementReservationEndDate']   = pd.to_datetime(result['RentalAgreementReservationEndDate']).dt.normalize()
    result['PaymentDate']                         = pd.to_datetime(result['PaymentDate']).dt.normalize()

    result = result.drop(columns=['Partner','CID'])

    st.download_button(label='DOWNLOAD', data=result.to_csv(index=False), file_name='prepayments.csv', mime='csv', use_container_width=True, type='primary')