import streamlit as st
import pandas as pd
import math
from pathlib import Path
from typing import Optional

from config import PROJECT_NAME

# Optional: import fetch helper if available
try:
    from fetch_worldbank import fetch_indicator
except Exception:
    fetch_indicator = None

@st.cache_data
def get_gdp_data():
    """Grab GDP data from a CSV file."""
    DATA_FILENAME = Path(__file__).parent / 'data' / 'gdp_data.csv'
    raw_gdp_df = pd.read_csv(DATA_FILENAME)

    MIN_YEAR = 1960
    MAX_YEAR = 2022

    gdp_df = raw_gdp_df.melt(
        ['Country Code'],
        [str(x) for x in range(MIN_YEAR, MAX_YEAR + 1)],
        'Year',
        'GDP',
    )
    gdp_df['Year'] = pd.to_numeric(gdp_df['Year'])
    return gdp_df

@st.cache_data
def load_worldbank_indicator(iso3: str, code: str, date_range: str, out_dir: Path):
    """Load a World Bank indicator CSV from disk, fetching it if needed."""
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"{iso3}_{code}.csv"
    if not csv_path.exists():
        if fetch_indicator is None:
            raise RuntimeError("fetch_indicator helper is unavailable")
        fetch_indicator(iso3, code, out_dir, date_range)
    df = pd.read_csv(csv_path)
    df = df[['countryiso3code', 'date', 'value']].rename(
        columns={'countryiso3code': 'Country Code', 'date': 'Year', 'value': 'GDP per Capita'})
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    return df.sort_values('Year')


def render_gdp_dashboard() -> None:
    """Render the GDP dashboard inside the unified landing page."""
    st.header('GDP Dashboard')
    st.markdown(
        'Pregledaj GDP podatke uz mogućnost filtriranja po zemlji i periodu. '
        'Ovaj modul je integrisan u glavnu landing stranicu.'
    )

    gdp_df = get_gdp_data()
    min_value = int(gdp_df['Year'].min())
    max_value = int(gdp_df['Year'].max())

    from_year, to_year = st.slider(
        'Koji raspon godina želiš analizirati?',
        min_value=min_value,
        max_value=max_value,
        value=[min_value, max_value],
    )

    countries = sorted(gdp_df['Country Code'].unique())
    if not countries:
        st.warning('Nema dostupnih podataka za zemlje.')
        return

    selected_countries = st.multiselect(
        'Odaberi zemlje za analizu',
        countries,
        ['DEU', 'FRA', 'GBR', 'BRA', 'MEX', 'JPN'],
    )

    filtered_gdp_df = gdp_df[
        (gdp_df['Country Code'].isin(selected_countries))
        & (gdp_df['Year'] >= from_year)
        & (gdp_df['Year'] <= to_year)
    ]

    st.subheader('GDP over time')
    st.line_chart(
        filtered_gdp_df,
        x='Year',
        y='GDP',
        color='Country Code',
    )

    first_year = gdp_df[gdp_df['Year'] == from_year]
    last_year = gdp_df[gdp_df['Year'] == to_year]

    st.subheader(f'GDP u {to_year}')
    cols = st.columns(4)
    for i, country in enumerate(selected_countries):
        col = cols[i % len(cols)]
        with col:
            first_gdp_series = first_year[first_year['Country Code'] == country]['GDP']
            last_gdp_series = last_year[last_year['Country Code'] == country]['GDP']
            first_gdp = first_gdp_series.iat[0] / 1_000_000_000 if not first_gdp_series.empty else float('nan')
            last_gdp = last_gdp_series.iat[0] / 1_000_000_000 if not last_gdp_series.empty else float('nan')

            if math.isnan(first_gdp) or math.isnan(last_gdp):
                growth = 'n/a'
                delta_color = 'off'
            else:
                growth = f'{last_gdp / first_gdp:,.2f}x'
                delta_color = 'normal'

            st.metric(
                label=f'{country} GDP',
                value=f'{last_gdp:,.0f}B' if not math.isnan(last_gdp) else 'n/a',
                delta=growth,
                delta_color=delta_color,
            )


if __name__ == '__main__':
    st.set_page_config(page_title=PROJECT_NAME, page_icon=':earth_americas:')
    render_gdp_dashboard()
