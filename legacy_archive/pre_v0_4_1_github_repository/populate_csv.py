import pandas as pd

# Define Canada, Venezuela, Indonesia data
comp_data = [
    # Canada
    ['Canada', 'CAN', 'oil sands', 'Athabasca, Cold Lake, Peace River', 'resource scale', 'proven reserves', '163-167', 'billion barrels', '2024', 'NRCan, CAPP', '', 'Mature commercial oil sands system', 'technical feasibility', 'high', 'World largest single deposit'],
    ['Canada', 'CAN', 'oil sands', 'Athabasca, Cold Lake, Peace River', 'production', 'annual production', '3.6', 'million bpd', '2024', 'CAPP', '', 'Commercial success proxy', 'technical feasibility', 'high', '53% in-situ, 47% mining'],
    ['Canada', 'CAN', 'oil sands', 'Athabasca, Cold Lake, Peace River', 'technology', 'mining depth', '<75', 'meters', '2024', 'NRCan', '', 'Mining technical threshold', 'technical feasibility', 'high', ''],
    ['Canada', 'CAN', 'oil sands', 'Athabasca, Cold Lake, Peace River', 'investment', 'capital expenditure', '13.3', 'billion CAD', '2024', 'AER', '', 'Private capital requirements', 'economic feasibility', 'high', 'Private led, no state NOC'],
    ['Canada', 'CAN', 'oil sands', 'Athabasca, Cold Lake, Peace River', 'regulation', 'pre-payout royalty', '1-9', '%', 'current', 'Alberta.ca', '', 'Profit-sensitive fiscal model', 'governance capability', 'high', 'Single regulator (AER)'],
    ['Canada', 'CAN', 'oil sands', 'Athabasca, Cold Lake, Peace River', 'environment', 'GHG intensity', '57', 'kg CO2e/bbl', '2024', 'S&P Global', '', 'Environmental mitigation baseline', 'environmental impact', 'high', 'Directive 085 for tailings'],

    # Venezuela
    ['Venezuela', 'VEN', 'extra-heavy oil', 'Orinoco Belt', 'resource scale', 'proven reserves', '303.2', 'billion barrels', '2023', 'EIA, OPEC', '', 'Huge resource base', 'technical feasibility', 'high', 'Largest global proven reserves'],
    ['Venezuela', 'VEN', 'extra-heavy oil', 'Orinoco Belt', 'production', 'annual production', '902,000', 'bpd', '2024', 'EIA', '', 'Decline of extraction', 'technical feasibility', 'high', 'Down from 3.7m peak'],
    ['Venezuela', 'VEN', 'extra-heavy oil', 'Orinoco Belt', 'technology', 'syncrude API', '15-26', '°API', 'Design', 'EIA, offshore-technology', '', 'Refining requirement', 'technical feasibility', 'medium', 'Requires major upgraders'],
    ['Venezuela', 'VEN', 'extra-heavy oil', 'Orinoco Belt', 'investment', 'state equity minimum', '60', '%', '2007', 'Decree 5200', '', 'Nationalization risk', 'governance capability', 'high', 'Led to IOC exodus'],
    ['Venezuela', 'VEN', 'extra-heavy oil', 'Orinoco Belt', 'regulation', 'CPI score', '10', 'score (out of 100)', '2024', 'Transparency International', '', 'Corruption impact on extraction', 'governance capability', 'high', 'Top 10 most corrupt'],
    ['Venezuela', 'VEN', 'extra-heavy oil', 'Orinoco Belt', 'environment', 'flaring intensity', '33.53', 'm3/bbl', '2022', 'World Bank GGFR', '', 'Environmental mismanagement', 'environmental impact', 'high', 'Highest flaring intensity'],

    # Indonesia
    ['Indonesia', 'IDN', 'natural asphalt', 'Buton Island', 'resource scale', 'geological resources', '576.87', 'million tonnes', '2023', 'ESDM', '', 'Similar scale solid deposit', 'technical feasibility', 'high', '218.87 Mt proven reserves'],
    ['Indonesia', 'IDN', 'natural asphalt', 'Buton Island', 'production', 'annual extraction', '5000', 'tonnes', '2025', 'CNBC Indonesia', '', 'Underutilization proxy', 'technical feasibility', 'high', 'Utilization <15% of capacity'],
    ['Indonesia', 'IDN', 'natural asphalt', 'Buton Island', 'technology', 'bitumen content', '10-40', '% by weight', 'current', 'pu.go.id', '', 'Direct road application', 'technical feasibility', 'high', 'CPHMA used directly for roads'],
    ['Indonesia', 'IDN', 'natural asphalt', 'Buton Island', 'investment', 'pre-feasibility value', '91', 'million USD', '2024', 'ESDM', '', 'Sovereign backing', 'economic feasibility', 'medium', 'BPI Danantara involvement'],
    ['Indonesia', 'IDN', 'natural asphalt', 'Buton Island', 'regulation', 'local use mandate', '30', '% target', '2030', 'antaranews.com', '', 'Import substitution policy', 'governance capability', 'high', 'Key lesson for Nigeria policy'],
    ['Indonesia', 'IDN', 'natural asphalt', 'Buton Island', 'value chain', 'import dependency', '80', '%', '2023', 'jakartaglobe.id', '', 'Market demand comparison', 'economic feasibility', 'high', 'Importing despite reserves']
]

comp_cols = ['country', 'iso3', 'resource_type', 'deposit_region', 'evidence_theme', 'indicator', 'value', 'unit', 'year', 'source', 'source_link_or_reference', 'relevance_to_nigeria', 'mcdm_criterion_supported', 'confidence', 'note']
df_comp = pd.DataFrame(comp_data, columns=comp_cols)
df_comp.to_csv('TAR_SAND_COMPARATOR_EVIDENCE.csv', index=False)

# Define Nigeria data
nig_data = [
    ['Lagos-Ogun-Ondo-Edo belt', 'geology', 'technical feasibility', 'Massive in-situ reserves spanning multiple states', 'in-situ reserves', '42.74', 'billion tonnes', 'NGSA', 'high', 'yes', 'Recoverable vs in-place clarity'],
    ['Agbabu, Ondo belt', 'geology', 'technical feasibility', 'Probable recoverable estimates', 'recoverable reserves', '156', 'million tonnes', 'Ondo State Ministry', 'medium', 'yes', 'Need bankable DFS'],
    ['Agbabu, Ondo belt', 'geology', 'technical feasibility', 'Shallow deposit depth', 'deposit depth', '0.5-50', 'meters', 'ResearchGate', 'high', 'yes', ''],
    ['Agbabu, Ondo belt', 'geology', 'technical feasibility', 'Heavy extra-heavy API gravity', 'API gravity', '7.87-10.54', '°API', 'pathofscience.org', 'high', 'yes', ''],
    ['Agbabu, Ondo belt', 'extraction', 'technical feasibility', 'Recommended extraction for shallow depth', 'extraction method', 'surface mining', 'method', 'boell.org', 'high', 'yes', ''],
    ['National', 'road bitumen', 'economic feasibility', 'Domestic annual demand', 'asphalt demand', '300,000', 'tonnes/year', 'Industry data (2023)', 'high', 'yes', ''],
    ['National', 'road bitumen', 'economic feasibility', 'Import expenditure cost', 'import cost', '172', 'million USD', 'WITS (2020)', 'high', 'yes', ''],
    ['Agbabu, Ondo belt', 'environment', 'environmental impact', 'Severe risk to traditional livelihoods (farming, fishing)', 'social risk', 'high', 'qualitative', 'boell.org (Heinrich Böll)', 'high', 'yes', 'EIA enforcement gaps'],
    ['National', 'regulation', 'governance capability', 'Mineral classification', 'legal status', 'Solid Mineral', 'classification', 'NMMA 2007', 'high', 'yes', 'Bitumen Bill 2025 pending'],
    ['National', 'investment', 'economic feasibility', 'Recent licensing round', 'new licenses', '34', 'licenses', 'FMSMD (2024)', 'high', 'yes', 'History of non-commercialization']
]

nig_cols = ['location/deposit', 'evidence_theme', 'criterion', 'evidence_summary', 'indicator/proxy', 'value', 'unit', 'source', 'confidence', 'usable_for_scoring', 'gap_remaining']
df_nig = pd.DataFrame(nig_data, columns=nig_cols)
df_nig.to_csv('NIGERIA_TAR_SAND_PROJECT_EVIDENCE.csv', index=False)

print("CSVs generated.")
