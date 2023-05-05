# %%
import pandas as pd
pd.set_option('display.max_columns', 50)
pd.set_option('display.max_colwidth', 150)
# %%
data = pd.read_csv("aptenisa_first_batch.csv")
# %%
# rename columns to english
col_dict = {
    'Marca temporal': 'timestamp',
    '¿Acepta la política de privacidad indicada arriba?': 'privacy_policy',
    'Nombre del proyecto:': 'project_name', 
    'Ecosistema al que pertenece:': 'ecosystem',
    '¿Tiene su empresa página web? Sí tiene web indique la URL y si no tiene, indique que no tiene web': 'website_url',
    '¿Ha constituido su empresa?': 'company_established',
    '¿En qué fecha fue constituida su empresa?': 'company_established_date',
    'Desde su constitución, ¿su empresa ha cerrado o cesado su actividad?': 'company_closed',
    'Si su respuesta es SÍ, ¿en qué fecha cesó su actividad?': 'company_closed_date',
    '¿Cuánto facturó en los últimos 3 meses de actividad? (cantidad en Euros)': 'last_3_months_revenue',
    '¿Cuál ha sido el número medio de clientes  en los últimos 3 meses de actividad? ': 'last_3_months_avg_clients',
    '¿Entre los clientes de los últimos 3 meses de actividad, cuántos han sido recurrentes? (Indicar nº) ': 'last_3_months_recurrent_clients',
    '¿Cuánto facturó en los últimos 12 meses? (Cantidad en Euros)': 'last_12_months_revenue',
    '¿Cuál ha sido el número medio de clientes  en los últimos 12 meses? ': 'last_12_months_avg_clients',
    '¿Entre los clientes de los últimos 3 meses, cuántos han sido recurrentes? (Indicar nº) ': 'last_12_months_recurrent_clients',
    'Indicar nº de empleados al iniciar el programa': 'employees_at_start',
    'Indicar nº de empleados al finalizar el programa?': 'employees_at_end',
    'Indicar nº de mujeres cofundadoras en el equipo': 'cofounders_female',
    '¿Cuántos empleados han sido contratados en los últimos tres meses de actividad?': 'employees_hired_last_3_months',
    '¿Cuántos empleados han dejado la empresa en los últimos tres meses de actividad?': 'employees_left_last_3_months',
    '¿Se ha presentado a rondas de financiación?': 'funding_rounds',
    'En caso de no haberse presentado a una ronda de financiación y si lo desea, proporcione una razón por la que no se ha presentado a ninguna ronda de financiación': 'no_funding_rounds_reason',
    '¿En cuántas rondas de financiación se ha presentado?': 'funding_rounds_count',
    '¿Cuándo se presentó a esas rondas de financiación? (Indicar fechas)': 'funding_rounds_dates',
    '¿Cuánto capital se ha levantado gracias  a las rondas de financiación a las que se ha presentado?': 'funding_rounds_capital_raised',
    '¿Ha recibido la empresa apoyo en algún programa de aceleración que no sea APTENISA?': 'other_accelerator',
    '¿En cuántos programas ha participado? Indique el número': 'other_accelerator_count',
    'Si lo desea proporcione el nombre de esos programas de aceleración': 'other_accelerator_names'
}

data = data.rename(columns=col_dict)

# %%
# adjust other_accelerator_names column to separate these by comma, "y", semi-colon, or "e". Optionally, remove space left and right, if applies.
data['other_accelerator_names'] = data['other_accelerator_names'].str.replace(' y | e | - |\n|;|\s*,\s*', ',', regex=True)
data['other_accelerator_names'] = data['other_accelerator_names'].str.strip()

# create nested lists
data['other_accelerator_names'] = data['other_accelerator_names'].str.split(',')

# drop rows with duplicated website, keep last
data = data.drop_duplicates(subset=['website_url'], keep='last')

# %%
# create interpolated column that computes the 3 months revenue as if the company was active for 3 months, unless the 3 months revenue is not NAN
data['last_3_months_revenue_interpolated'] = data['last_3_months_revenue']
data['last_3_months_revenue_interpolated'] = data['last_3_months_revenue_interpolated'].fillna(data['last_12_months_revenue']/4)

# do the same for clients
data['last_3_months_avg_clients_interpolated'] = data['last_3_months_avg_clients']
data['last_3_months_avg_clients_interpolated'] = data['last_3_months_avg_clients_interpolated'].fillna(data['last_12_months_avg_clients']/4).round(0)

# create datetimes
data['company_established_date'] = pd.to_datetime(data['company_established_date'], format='mixed')

# split coordinates in lon and lat columns
data[['lat', 'lon']] = data['coordinates'].str.split(',', expand=True)

# make sure these are floats
data['lon'] = data['lon'].astype(float)
data['lat'] = data['lat'].astype(float)

# fill na with zeros "other_accelerator count"
data['other_accelerator_count'] = data['other_accelerator_count'].fillna(0)
# %%
# save as csv
data.to_csv('aptenisa_first_batch_preprocessed.csv', index=False)

# %%