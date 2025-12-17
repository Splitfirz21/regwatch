from scraper import extract_agency, classify_sector

text = "Regulatory changes in Singapore to simplify show-flat site sourcing for developers by URA and SLA."
print(f"Text: {text}")
agency = extract_agency(text)
print(f"Extracted Agency: {agency}")
sector = classify_sector(text, agency)
print(f"Classified Sector: {sector}")

if "URA" in agency and "SLA" in agency:
    print("SUCCESS: Found both.")
else:
    print("FAILURE: Missed one.")
