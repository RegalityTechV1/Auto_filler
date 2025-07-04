import random
from datetime import datetime, timedelta
import uuid

class DummyDataGenerator:
    def __init__(self):
        # Predefined realistic data for APR forms
        self.company_names = [
            "TechGlobal Solutions Pvt Ltd",
            "InnovateCorp International",
            "GlobalVentures Technologies",
            "NextGen Business Solutions",
            "Digital Dynamics Ltd",
            "Future Enterprises Inc",
            "Strategic Holdings Company",
            "Advanced Systems Corp"
        ]
        
        self.countries = ["India", "USA", "Singapore", "UK", "Canada", "Australia", "Germany", "Japan"]
        
        self.cities = {
            "India": ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Pune"],
            "USA": ["New York", "San Francisco", "Los Angeles", "Chicago", "Boston"],
            "Singapore": ["Singapore"],
            "UK": ["London", "Manchester", "Birmingham"],
            "Canada": ["Toronto", "Vancouver", "Montreal"],
            "Australia": ["Sydney", "Melbourne", "Brisbane"],
            "Germany": ["Berlin", "Munich", "Frankfurt"],
            "Japan": ["Tokyo", "Osaka", "Yokohama"]
        }
        
        self.activity_codes_1987 = ["892", "893", "851", "852", "853", "859"]
        self.activity_codes_2008 = ["62099", "62091", "62092", "72100", "72200", "63099"]
        
        self.contact_names = [
            "Rajesh Kumar", "Priya Sharma", "Amit Patel", "Sneha Gupta", 
            "Vikram Singh", "Kavya Reddy", "Arjun Mehta", "Pooja Agarwal"
        ]
        
        self.designations = [
            "Managing Director", "Chief Executive Officer", "Chief Financial Officer",
            "Director", "Partner", "General Manager", "Vice President"
        ]
    
    def generate_apr_data(self, form_structure):
        """Generate complete APR form data"""
        filled_data = {}
        
        # Copy existing data
        for key, value in form_structure.items():
            filled_data[key] = value if value and str(value).strip() else self._generate_field_value(key)
        
        # Ensure consistency across related fields
        self._ensure_data_consistency(filled_data)
        
        return filled_data
    
    def enhance_form_data(self, existing_data):
        """Enhance existing form data with missing fields"""
        enhanced_data = existing_data.copy()
        
        # Fill any remaining empty fields
        for key, value in enhanced_data.items():
            if not value or str(value).strip() == "":
                enhanced_data[key] = self._generate_field_value(key)
        
        # Ensure consistency
        self._ensure_data_consistency(enhanced_data)
        
        return enhanced_data
    
    def _generate_field_value(self, field_name):
        """Generate appropriate value based on field name"""
        field_lower = field_name.lower()
        
        # Date fields
        if any(date_term in field_lower for date_term in ["date", "from_date", "to_date"]):
            return self._generate_date(field_name)
        
        # UIN fields
        if "uin" in field_lower:
            return 'B Y W A Z 2 0 2 3 0 0 6 3'
            # return self._generate_uin()
        
        # Amount fields (financial figures)
        if any(amount_term in field_lower for amount_term in ["amount", "usd", "inr", "capital", "worth", "profit", "dividend", "repatriation", "repayment", "exports", "royalties", "fees", "fdi", "refund"]):
            return self._generate_amount()
        
        # Percentage fields
        if any(perc_term in field_lower for perc_term in ["percentage", "%", "stake", "share"]):
            return self._generate_percentage()
        
        # Company/Entity names and partner names
        if any(name_term in field_lower for name_term in ["company", "entity", "firm", "sds", "partner"]) and "name" in field_lower:
            return random.choice(self.company_names)
        
        # Country fields
        if "country" in field_lower:
            return random.choice(self.countries)
        
        # Address and place fields
        if any(address_term in field_lower for address_term in ["address", "place"]):
            return self._generate_address()
        
        # Contact fields (telephone, phone)
        if any(contact_term in field_lower for contact_term in ["telephone", "phone", "mobile"]):
            return self._generate_phone()
        
        # Email fields
        if "email" in field_lower:
            return self._generate_email()
        
        # Activity codes
        if "activity" in field_lower and "1987" in field_name:
            return random.choice(self.activity_codes_1987)
        elif "activity" in field_lower and "2008" in field_name:
            return random.choice(self.activity_codes_2008)
        
        # Contact person names and official names
        if any(person_term in field_lower for person_term in ["contact", "person", "authorized", "official", "auditor"]) and "name" in field_lower:
            return random.choice(self.contact_names)
        
        # Designations
        if "designation" in field_lower:
            return random.choice(self.designations)
        
        # Registration numbers and codes
        if any(reg_term in field_lower for reg_term in ["registration", "transaction", "udin"]):
            return self._generate_registration_number()
        
        # Currency fields
        if "currency" in field_lower:
            return random.choice(["USD", "INR", "SGD", "GBP"])
        
        # Level fields (for SDS)
        if "level" in field_lower:
            return f"Level-{random.randint(1, 3)}"
        
        # Signature fields
        if "signature" in field_lower:
            return f"[Signature of {random.choice(self.contact_names)}]"
        
        # Audit firm names
        if "firm" in field_lower and any(audit_term in field_lower for audit_term in ["audit", "chartered"]):
            return f"{random.choice(['Associates & Co', 'Partners LLP', 'Chartered Accountants', 'Audit Services'])} - {random.choice(['Mumbai', 'Delhi', 'Bangalore'])}"
        
        # Yes/No fields
        if any(yn_term in field_lower for yn_term in ["control", "financial_services", "yes", "no"]) or field_name.endswith("_yes") or field_name.endswith("_no"):
            if field_name.endswith("_yes"):
                return "✓" if random.choice([True, False]) else ""
            elif field_name.endswith("_no"):
                return "✓" if random.choice([True, False]) else ""
            else:
                return random.choice(["Yes", "No"])
        
        # Day/Month/Year fields for dates
        if any(time_term in field_lower for time_term in ["day", "month", "year"]):
            if "day" in field_lower:
                return str(random.randint(1, 28))
            elif "month" in field_lower:
                months = ["January", "February", "March", "April", "May", "June", 
                         "July", "August", "September", "October", "November", "December"]
                return random.choice(months)
            elif "year" in field_lower:
                return "2023"
        
        # Special handling for "others specify"
        if "specify" in field_lower:
            return "Professional Services"
        
        # Handle empty/nil financial fields specifically
        if any(financial_term in field_lower for financial_term in ["repatriation", "repayment", "exports", "royalties", "fees", "profit", "earnings"]) and "current" not in field_lower and "total" not in field_lower:
            if random.random() < 0.7:  # 70% chance for Nil in repatriation fields
                return "Nil"
            else:
                return self._generate_amount()
        
        # Default handling for remaining fields
        if field_lower in ["nil", "n/a", "na", "not applicable"]:
            return "Nil"
        
        # Default for unknown fields - use "Nil" for financial, "N/A" for others
        if any(financial_term in field_lower for financial_term in ["amount", "usd", "profit", "dividend", "worth"]):
            return "Nil"
        
        return "N/A"
    
    def _generate_date(self, field_name):
        """Generate appropriate date"""
        if "from" in field_name.lower():
            return "01-01-2023"
        elif "to" in field_name.lower():
            return "31-12-2023"
        else:
            # Random date in 2023
            start_date = datetime(2023, 1, 1)
            end_date = datetime(2023, 12, 31)
            random_date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
            return random_date.strftime("%d-%m-%Y")
    
    def _generate_uin(self):
        """Generate UIN in proper format matching APR structure"""
        # UIN format: 5 letters + 8 numbers, total 13 characters
        # Example from reference: B Y W A Z 2 0 2 3 0 0 6 3
        letters = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=5))
        
        # Generate 8 digits with year reference (2023) and sequence
        year_part = "2023"  # Current year
        sequence = f"{random.randint(0, 9999):04d}"  # 4-digit sequence
        numbers = year_part + sequence
        
        # Combine and format with spaces as shown in reference
        uin_chars = list(letters + numbers)
        # uin_chars=['B','Y','W','A','Z',2,0,2,3,0,0,6,3]
        return ' '.join(uin_chars)
    
    def _generate_amount(self):
        """Generate financial amount in proper APR format"""
        # APR forms typically use USD for foreign transactions
        currency = "USD"
        
        # Generate realistic amounts based on APR patterns
        amount_ranges = [
            (50, 10000),        # Small investments/amounts like USD 90, USD 124.37
            (10000, 100000),    # Medium amounts
            (100000, 1000000),  # Larger amounts like USD 221473
        ]
        
        min_amt, max_amt = random.choice(amount_ranges)
        
        # Generate with decimals for realism (like USD 124.37)
        if random.random() < 0.3:  # 30% chance for decimal amounts
            amount = round(random.uniform(min_amt, max_amt), 2)
        else:
            amount = random.randint(min_amt, max_amt)
        
        # Sometimes negative for losses (like USD -66617)
        if random.random() < 0.15:  # 15% chance of negative
            amount = -amount
            return f"{currency} {amount:,}" if amount < -1000 else f"{currency} {amount}"
        
        # Format with commas for large amounts
        if abs(amount) >= 1000:
            return f"{currency} {amount:,}"
        else:
            return f"{currency} {amount}"
    
    def _generate_percentage(self):
        """Generate percentage in APR format"""
        # Common APR percentages with realistic precision
        common_percentages = [100.00, 92.85, 51.00, 49.00, 75.00, 25.00, 60.00, 40.00]
        
        if random.random() < 0.6:  # 60% chance for common values
            percentage = random.choice(common_percentages)
        else:
            # Generate random percentage with 2 decimal precision
            percentage = round(random.uniform(1, 100), 2)
        
        # Format like APR examples: "100%" or "92.85%"
        if percentage == int(percentage):
            return f"{int(percentage)}%"
        else:
            return f"{percentage:.2f}%"
    
    def _generate_address(self):
        """Generate realistic address"""
        street_numbers = random.randint(1, 999)
        street_names = ["Business Park", "Tech Plaza", "Corporate Avenue", "Industrial Estate", "Commerce Street"]
        areas = ["Sector 15", "Block A", "Phase II", "Zone 3", "District Center"]
        
        country = random.choice(self.countries)
        city = random.choice(self.cities.get(country, ["Metropolitan City"]))
        
        return f"{street_numbers} {random.choice(street_names)}, {random.choice(areas)}, {city}, {country}"
    
    def _generate_phone(self):
        """Generate phone number"""
        # Indian format
        return f"+91 {random.randint(70000, 99999)} {random.randint(10000, 99999)}"
    
    def _generate_email(self):
        """Generate email address"""
        domains = ["company.com", "business.in", "corp.com", "enterprises.net", "solutions.org"]
        usernames = ["contact", "info", "admin", "finance", "corporate", "director"]
        
        return f"{random.choice(usernames)}@{random.choice(self.company_names).lower().replace(' ', '').replace('ltd', '').replace('pvt', '').replace('inc', '')}.{random.choice(domains).split('.')[1]}"
    
    def _generate_registration_number(self):
        """Generate registration numbers and codes"""
        # Different formats for different types
        formats = [
            f"{random.randint(100000, 999999)}S",  # Firm registration
            f"{random.randint(10000000000000, 99999999999999)}",  # Transaction number (15 digits)
            f"{random.randint(1000000000000000, 9999999999999999)}",  # Transaction number (17 digits)
            f"UDIN{random.randint(10000000, 99999999)}"  # UDIN format
        ]
        return random.choice(formats)
    
    def _ensure_data_consistency(self, data):
        """Ensure data consistency across related fields"""
        
        # Ensure date consistency
        if "from_date" in data and "to_date" in data:
            data["from_date"] = "01-01-2023"
            data["to_date"] = "31-12-2023"
        
        # Ensure percentage consistency (should add up to 100% for shareholding)
        percentage_fields = [k for k in data.keys() if "percentage" in k.lower() or "%" in str(data.get(k, ""))]
        if len(percentage_fields) >= 2:
            # Distribute percentages
            total = 100
            for i, field in enumerate(percentage_fields[:-1]):
                if i == 0:
                    data[field] = "100%"  # Indian entity typically has majority
                else:
                    remaining = max(0, total - 100)
                    data[field] = f"{remaining}%"
        
        # Ensure currency consistency
        currency_fields = [k for k in data.keys() if any(curr in str(data.get(k, "")) for curr in ["USD", "INR"])]
        if currency_fields:
            # Use USD for foreign transactions
            for field in currency_fields:
                if data[field] and not any(curr in str(data[field]) for curr in ["USD", "INR"]):
                    data[field] = f"USD {data[field]}"
        
        # Ensure contact consistency
        if "email" in data and "company" in data:
            company_name = str(data["company"]).lower().replace(" ", "").replace("ltd", "").replace("pvt", "")
            if company_name:
                data["email"] = f"contact@{company_name}.com"
