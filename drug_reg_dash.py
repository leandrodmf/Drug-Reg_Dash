# app.py
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import plotly
   
   
# Data loading function
@st.cache_data
def load_data():
    df = pd.read_csv('data/DADOS_ABERTOS_MEDICAMENTOS.csv', sep=';', encoding='latin-1')

    translation_dict = {
        "TIPO_PRODUTO": "PRODUCT_TYPE",
        "NOME_PRODUTO": "PRODUCT_NAME",
        "DATA_FINALIZACAO_PROCESSO": "PROCESS_FINALIZATION_DATE",
        "CATEGORIA_REGULATORIA": "REGULATORY_CATEGORY",
        "NUMERO_REGISTRO_PRODUTO": "PRODUCT_REGISTRATION_NUMBER",
        "DATA_VENCIMENTO_REGISTRO": "REGISTRATION_EXPIRATION_DATE",
        "NUMERO_PROCESSO": "PROCESS_NUMBER",
        "CLASSE_TERAPEUTICA": "THERAPEUTIC_CLASS",
        "EMPRESA_DETENTORA_REGISTRO": "REGISTRATION_HOLDER_COMPANY",
        "SITUACAO_REGISTRO": "REGISTRATION_STATUS",
        "PRINCIPIO_ATIVO": "ACTIVE_INGREDIENT"
    }

    # Renaming the columns names
    df = df.rename(columns=translation_dict)
    return df
   
# Data cleaning and preprocessing function
@st.cache_data
def preprocess_data(df):
    # Removing the unfinalized process and setting the datetime.
    df["PROCESS_FINALIZATION_DATE"] = pd.to_datetime(df["PROCESS_FINALIZATION_DATE"], format="%d/%m/%Y", errors="coerce")
      
    df_allregs = df.dropna(subset=["PROCESS_FINALIZATION_DATE"])
    df_allregs = df_allregs[["PROCESS_FINALIZATION_DATE", "REGULATORY_CATEGORY","PRODUCT_REGISTRATION_NUMBER"]]

    # Year column
    df_allregs['YEAR'] = df_allregs.PROCESS_FINALIZATION_DATE.dt.year

    # Creating 'new_reg_cat' column
    catgs = ['ESPECÍFICO', 'BIOLÓGICO', 'DINAMIZADO', 'RADIOFÁRMACO', 'PRODUTO DE T']

    def categorize_regulation(x):
        if x in ['NOVO', 'GENÉRICO', 'SIMILAR', 'FITOTERÁPICO']:
            return x
        elif x in catgs:
            return 'Others'
        else:
            return 'No category'

    df_allregs['new_reg_cat'] = df_allregs['REGULATORY_CATEGORY'].apply(categorize_regulation)
    df_allregs = df_allregs.rename(columns = {'NOVO': 'New', 'GENÉRICO': 'Generic', 'SIMILAR': 'Similar', 'FITOTERÁPICO': 'Phyto'})
    df_allregs['new_reg_cat'] = df_allregs['new_reg_cat'].replace({'NOVO': 'New', 'GENÉRICO': 'Generic', 'SIMILAR': 'Similar'})
    df_allregs.drop(labels = ['PROCESS_FINALIZATION_DATE', 'REGULATORY_CATEGORY'], axis = 1, inplace = True)

    df_allregs = pd.crosstab(index = df_allregs.YEAR, columns = df_allregs.new_reg_cat, values = df_allregs.PRODUCT_REGISTRATION_NUMBER, aggfunc="count")
    df_allregs = df_allregs.reindex(columns=['New', 'Generic', 'Similar', 'Others', 'No category'])
    df_allregs = df_allregs[df_allregs.index >= 1995]
      
    return df_allregs

# Function to create regulatory category plot
def create_reg_cat_plot(df_allregs):
    # Defining Pallete colors
    BLUE1, BLUE2, BLUE3, BLUE4, BLUE5 = '#03045e', '#0077b6', "#00b4d8", '#90e0ef', '#CDDBF3'
    GRAY1, GRAY2, GRAY3, GRAY4, GRAY5 = '#212529', '#495057', '#adb5bd', '#dee2e6', '#f8f9fa'
    RED1, ORAGNE1, YELLOW1, GREEN1, GREEN2 = '#e76f51', '#f4a261',	'#e9c46a', '#4c956c', '#2a9d8f'

    # Plotting line graph
    fig = px.line(df_allregs, x=df_allregs.index, y=df_allregs.columns, markers=True, labels={'new_reg_cat':'Regulatory Category'},
                    color_discrete_sequence=[BLUE2, RED1, YELLOW1 , GREEN1, GRAY2])

    # Adjusting the layout
    fig.update_layout(width=1000, height=500, font_family = 'DejaVu Sans', font_size=15,
                    font_color= GRAY2, title_font_color= GRAY1, title_font_size=24,
                    title_text='Brazil Drug Registrations' +
                                '<br><sup size=1 style="color:#555655">From 1995 to 2024</sup>',
                    xaxis_title='', yaxis_title='', plot_bgcolor= GRAY5)

    fig.update_traces(mode="markers+lines", hovertemplate = "<b>Year:</b> %{x} <br> <b>Registers:</b> %{y}")
    fig.update_layout(hovermode="x unified")
    return fig
   
# Function to create therapeutic class plot
@st.cache_data
def prepare_therapeutic_class_data(df):
    top_5_tc = df['THERAPEUTIC_CLASS'].value_counts().nlargest(5).index
    df_allregs_tc = df[['PROCESS_FINALIZATION_DATE', 'PRODUCT_REGISTRATION_NUMBER', 'THERAPEUTIC_CLASS']].copy()
    df_allregs_tc = pd.DataFrame(df_allregs_tc[df_allregs_tc['THERAPEUTIC_CLASS'].isin(top_5_tc)])
    df_allregs_tc['YEAR'] = pd.to_datetime(df_allregs_tc['PROCESS_FINALIZATION_DATE'], format="%Y-%m-%d", errors='coerce').dt.year
      
    # Crosstable with register count by year and Therapeutical Class
    df_allregs_tc = pd.crosstab(
        index=df_allregs_tc.YEAR,
        columns=df_allregs_tc.THERAPEUTIC_CLASS,
        values=df_allregs_tc.PRODUCT_REGISTRATION_NUMBER,
        aggfunc="count")
      
    # Renaming to ENG
    df_allregs_tc = df_allregs_tc.rename(columns={'ANALGESICOS NAO NARCOTICOS': 'Non-opioid analgesic',
                                        'ANTIBIOTICOS SISTEMICOS SIMPLES':	'Systemic antibiotics simple',
                                        'ANTIDEPRESSIVOS': 'Antidepressant',
                                        'ANTINEOPLASICO': 'Antineoplastic',
                                        'ANTINFLAMATORIOS': 'Non-steroidal anti-inflammatory'})
    # Data beyond 1995
    df_allregs_tc = df_allregs_tc[df_allregs_tc.index >= 1995]
    return df_allregs_tc
   
def create_ther_class_plot(df_allregs_tc):
    # Defining Pallete colors
    BLUE1, BLUE2, BLUE3, BLUE4, BLUE5 = '#03045e', '#0077b6', "#00b4d8", '#90e0ef', '#CDDBF3'
    GRAY1, GRAY2, GRAY3, GRAY4, GRAY5 = '#212529', '#495057', '#adb5bd', '#dee2e6', '#f8f9fa'
    RED1, ORAGNE1, YELLOW1, GREEN1, GREEN2 = '#e76f51', '#f4a261',	'#e9c46a', '#4c956c', '#2a9d8f'

    # Plotting line graph
    fig = px.line(df_allregs_tc, x=df_allregs_tc.index, y=df_allregs_tc.columns, markers=True,
                    color_discrete_sequence=[BLUE2, RED1, YELLOW1 , GREEN1, GRAY2])

    # Adjusting the Layout
    fig.update_layout(width=1000, height=500, font_family = 'DejaVu Sans', font_size=15,
                    font_color= GRAY2, title_font_color= GRAY1, title_font_size=24,
                    title_text='Brazil Drug Registrations: by Theapeutical Class' +
                                '<br><sup size=1 style="color:#555655">From 1995 to 2024</sup>',
                    xaxis_title='', yaxis_title='', plot_bgcolor= GRAY5)
    fig.update_traces(mode="markers+lines", hovertemplate = "<b>Year:</b> %{x} <br> <b>Registers:</b> %{y}")
    fig.update_layout(hovermode="x unified")

    return fig
   
def create_violin_plot(df_allregs_tc):
        # Defining Pallete colors
        BLUE1, BLUE2, BLUE3, BLUE4, BLUE5 = '#03045e', '#0077b6', "#00b4d8", '#90e0ef', '#CDDBF3'
        GRAY1, GRAY2, GRAY3, GRAY4, GRAY5 = '#212529', '#495057', '#adb5bd', '#dee2e6', '#f8f9fa'
        RED1, ORAGNE1, YELLOW1, GREEN1, GREEN2 = '#e76f51', '#f4a261',	'#e9c46a', '#4c956c', '#2a9d8f'
        # Reshape for violin plot using pandas.melt
        df_melted = pd.melt(df_allregs_tc.reset_index(), id_vars=['YEAR'],
                            value_vars=df_allregs_tc.columns,
                            var_name='THERAPEUTIC_CLASS', value_name='Registers')
        
        # Plotting area settings
        fig, axs = plt.subplots(figsize=(10,5))
        sns.set_theme(style="whitegrid")
        
        # Violin plot
        ax = sns.violinplot(data=df_melted, x='Registers', y='THERAPEUTIC_CLASS',
                            hue='THERAPEUTIC_CLASS',
                            palette=[BLUE2, RED1, YELLOW1 , GREEN1, GRAY2])
        
        # Adjusting the Layout
        plt.suptitle('Violin plot of Brazil Drug Registrations:', size=18, color=GRAY1, ha = 'right', x = 0.61, y = 1.06)
        
        plt.title(r'by $\bf{Therapeutical\ class}$'+ '\nFrom 2015 to 2024', fontsize=14, color=GRAY2, pad=15, loc="left")
        ax.set_xlabel('Number of Registers',  fontsize = 14)
        ax.set_ylabel('Therapeutical Class', fontsize = 14)
        ax.xaxis.set_tick_params(labelsize=12, labelcolor = GRAY2)
        ax.yaxis.set_tick_params(labelsize=12, labelcolor = GRAY2)
        sns.despine(bottom=True)
        
        # Median list
        median = df_allregs_tc.median()
        
        # Texto explicativo
        ax.text(151, 5.2,
                'The graph presents the distribution values of the\n'
                'Top 5 Therapeutical Class most registered:\n'
                '$\\bf{Systemic\ antibiotics\ simple}$, $\\bf{Non-steroidal\ anti-inflammatory}$,\n'
                '$\\bf{Non-opioid\ analgesic}$, $\\bf{Antineoplastic}$ and $\\bf{Antidepressant}$.\n\n'
                'Most of them presents a normal distribution shape,\n'
                f'with median flutuating from {median[3]} to {median[1]}.\n'
                'Which demonstrates a similar pattern for the number of registrations per year.\n\n'
                'But some distortions to max values are presented by  $\\bf{Systemic\ antibiotics\ simple}$,\n'
                f'because the peak of registration in 2001.\n\n',
                fontsize=12, linespacing=1.45, color=GRAY2)
        
        return fig
   

def main():
    # --- Main app ---
    st.set_page_config(
        page_title="Drug Registrations in Brazil",
        page_icon="⚕️",
        layout="wide",
    )

    st.title("Drug Registrations in Brazil")
    st.markdown(
    """
    ## 1 Project Overview
    This project aims to explore the Brazilian pharmaceutical market by analyzing data on drug registrations from the Brazilian Health Surveillance Agency (ANVISA).

    ANVISA DATABASE: Medicines Registered in Brazil

    > _"The open drug registration database is a data intelligence project that extracts information from the Datavisa system to list products that have been registered by Anvisa, including those whose registration is already valid or canceled/expired, as reported on the Agency's consultation portal."_

    The data used is public and can be found here: 
    [Medicamentos Registrados no Brasil](https://dados.gov.br/dados/conjuntos-dados/medicamentos-registrados-no-brasil)

    For more information visit the [full project's GitHub](https://github.com/leandrodmf/Drug_Reg_ANVISA/blob/main/README.md).
    """
    )

    # --- Load data ---
    df = load_data()
    
    # --- Data Processing and Plotting ---
    with st.spinner("Processing Data..."):
        df_allregs = preprocess_data(df)
        reg_cat_plot = create_reg_cat_plot(df_allregs)
        
        df_allregs_tc = prepare_therapeutic_class_data(df)
        ther_class_plot = create_ther_class_plot(df_allregs_tc)
        violin_plot = create_violin_plot(df_allregs_tc)

    # --- Layout ---
    st.header("Drug Registrations by Regulatory Category")
    st.plotly_chart(reg_cat_plot, use_container_width=True)
    st.markdown("""
        Was develped a temporal series analysis beyond 1995. In 1999, a legal milestone was reached for the production of medicines, with the creation of the National Health Surveillance Agency (Anvisa) and the Generic Medicines Law.

        Anvisa is a federal agency that acts in the sanitary control of products and services, responsible for registering and supervising the production of medicines, evaluating the technical and administrative documentation related to quality, safety and efficacy. The creation of this agency streamlined the process of registering new drugs.

        A generic medicine is a medicine with the same active substance, pharmaceutical form, dosage and therapeutic indication as the **"reference medicine"** (patent holder), but without having a commercial name, only the name of the active pharmaceutical ingredient on its packaging. The **first was registered in 1998**, but after the politics the registration number raised.

        While the generic medicine law, in addition to stimulating the production of generic medicines, allowed the production and marketing of medicines with expired patents. However, the greatest growth is related to "similar medicines", which are the generic with the trade name printed on its packaging, which favors its advertising, **which explains the growth above generic drugs in 2001**.

        The peak in 2011 appers related to the "No category", thats seem to be an missclassified data. In these data are included as therapeutic class  anti-inflammatory, antihypertensives, bronchodilators, expectorants, antivirals, among others. **Drug classes that should be included in some regulatory category for comercialization**.
        """)

    st.header("Drug Registrations by Therapeutic Class")
    st.plotly_chart(ther_class_plot, use_container_width=True)
    st.markdown("""
        The evaluation over the time (temporal series) demonstrates the same pattern presented by the Durg Registragion. 

        The number 1 are the antibiotics, due bacterial infections are prevalent across a range of age groups. 

        Non-steroidal anti-inflammatory drugs (NSAIDs) relieve inflammatory, are most of the are OTC (Over The Counter) that can be sold directly to people without a prescription. Non-opioid analgesics are complementary to NSAIDs.
        > If sum both will be the major class.
        > 
        > A competitive market with a high number of registrations of a therapeutic class indicates a great medical need and business opportunities, bringing benefits such as more options, lower prices and incentive to innovation for consumers and the market as a whole.

        Antineoplastic and antidepressant drugs appear in the TOP 5 of the list because they treat the most common diseases in Brazil.
        """)

    st.header("Distribution of Registrations by Therapeutic Class")
    st.pyplot(violin_plot)
    st.markdown("""
        The Violin graph presents the distribution values of the Top 5 Therapeutical Class most registered.

        Most of them presents a normal distribution shape, with median flutuating from 21.0 to 29.5. Which demonstrates a similar pattern for the number of registrations per year.

        But some distortions to max values are presented by  **Systemic antibiotics simple** because the peak of registration in 2001.
        """)
    
if __name__ == "__main__":
    main()