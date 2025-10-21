"""Validator for address completeness."""

import re
from typing import Dict, Any
import logging

from app.services.validators.base import BaseValidator

logger = logging.getLogger(__name__)


class AddressCompletenessValidator(BaseValidator):
    """Validates completeness of address information in scraped companies."""

    def get_criteria(self) -> Dict[str, float]:
        """
        Get validation criteria and their weights.

        Returns:
            Dictionary of criterion name to weight
        """
        return {
            "has_street_address": 0.30,
            "has_city": 0.25,
            "has_state": 0.25,
            "has_postal_code": 0.20,
        }

    def score_criterion(self, data: Any, criterion: str) -> float:
        """
        Score a single address criterion.

        Args:
            data: Response data containing companies
            criterion: Name of the criterion to score

        Returns:
            Score between 0.0 and 1.0
        """
        # Extract companies from response data
        companies = self._extract_companies(data)

        if not companies:
            return 0.0

        # Count how many companies meet the criterion
        passing_count = 0

        for company in companies:
            address = company.get("address", "")

            if criterion == "has_street_address":
                if self._has_street_address(address):
                    passing_count += 1

            elif criterion == "has_city":
                if self._has_city(address):
                    passing_count += 1

            elif criterion == "has_state":
                if self._has_state(address):
                    passing_count += 1

            elif criterion == "has_postal_code":
                if self._has_postal_code(address):
                    passing_count += 1

        # Return percentage of companies that pass this criterion
        return passing_count / len(companies)

    def _extract_companies(self, data: Any) -> list:
        """
        Extract companies list from response data.

        Args:
            data: Response data (can be dict or JSON string)

        Returns:
            List of companies
        """
        if isinstance(data, str):
            import json
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                logger.error("Failed to parse response data as JSON")
                return []

        # Handle different response formats
        if isinstance(data, dict):
            # Check for various possible keys
            if "companies" in data:
                return data["companies"]
            elif "data" in data and isinstance(data["data"], dict):
                return data["data"].get("companies", [])
            elif "data" in data and isinstance(data["data"], list):
                return data["data"]

        elif isinstance(data, list):
            return data

        return []

    def _has_street_address(self, address: str) -> bool:
        """
        Check if address contains a street address.

        Args:
            address: Address string

        Returns:
            True if street address is present
        """
        if not address:
            return False

        # Look for street number patterns
        # Examples: "123 Main St", "456 Oak Avenue"
        street_patterns = [
            r'\d+\s+\w+\s+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Court|Ct|Place|Pl)',
            r'\d+\s+[A-Z][a-z]+\s+\w+',  # "123 Main Something"
        ]

        for pattern in street_patterns:
            if re.search(pattern, address, re.IGNORECASE):
                return True

        return False

    def _has_city(self, address: str) -> bool:
        """
        Check if address contains a city name.

        Args:
            address: Address string

        Returns:
            True if city is present
        """
        if not address:
            return False

        # Cities are typically capitalized words that aren't state abbreviations
        # Look for comma-separated parts (common in addresses)
        parts = [p.strip() for p in address.split(',')]

        if len(parts) >= 2:
            # City is often before the state/zip
            # Check if second-to-last part looks like a city
            potential_city = parts[-2] if len(parts) >= 2 else ""

            # Check if it's not just a state abbreviation
            if potential_city and len(potential_city) > 2:
                # Remove any numbers (zip codes)
                city_part = re.sub(r'\d{5}(-\d{4})?', '', potential_city).strip()
                if city_part and len(city_part) > 2:
                    return True

        return False

    def _has_state(self, address: str) -> bool:
        """
        Check if address contains a state (abbreviation or full name).

        Args:
            address: Address string

        Returns:
            True if state is present
        """
        if not address:
            return False

        # US states - abbreviations and full names
        states = {
            'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
            'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
            'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
            'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
            'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
            'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
            'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
            'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
            'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
            'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
            'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
            'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
            'WI': 'Wisconsin', 'WY': 'Wyoming'
        }

        # Check for state abbreviations (as whole word)
        for abbrev in states.keys():
            if re.search(r'\b' + abbrev + r'\b', address):
                return True

        # Check for full state names (case-insensitive)
        for full_name in states.values():
            if re.search(r'\b' + re.escape(full_name) + r'\b', address, re.IGNORECASE):
                return True

        return False

    def _has_postal_code(self, address: str) -> bool:
        """
        Check if address contains a postal code.

        Args:
            address: Address string

        Returns:
            True if postal code is present
        """
        if not address:
            return False

        # US ZIP code patterns: 12345 or 12345-6789
        zip_pattern = r'\b\d{5}(-\d{4})?\b'

        return bool(re.search(zip_pattern, address))

    def generate_feedback(
        self,
        criteria_scores: Dict[str, float],
        overall_score: float
    ) -> str:
        """
        Generate feedback specific to address validation.

        Args:
            criteria_scores: Scores for each criterion
            overall_score: Overall validation score

        Returns:
            Feedback string
        """
        feedback_parts = []

        # Overall assessment
        if overall_score >= 0.9:
            feedback_parts.append("Excellent address completeness.")
        elif overall_score >= 0.7:
            feedback_parts.append("Good address data quality.")
        elif overall_score >= 0.5:
            feedback_parts.append("Addresses are partially complete.")
        else:
            feedback_parts.append("Address data is incomplete.")

        # Specific feedback for each criterion
        score_labels = {
            "has_street_address": "street addresses",
            "has_city": "city names",
            "has_state": "state information",
            "has_postal_code": "postal codes"
        }

        for criterion, label in score_labels.items():
            score = criteria_scores.get(criterion, 0)
            percentage = int(score * 100)

            if score < 0.5:
                feedback_parts.append(f"Only {percentage}% have {label}.")

        return " ".join(feedback_parts)
