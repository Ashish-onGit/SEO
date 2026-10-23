"""Mock AI provider for testing and offline execution without API credentials."""

import re
from typing import Dict, Any, Optional
from ai.provider import AIProvider
from config.brand_config import brand_config


class MockAIProvider(AIProvider):
    """High-fidelity mock provider producing compliant markdown and structured evaluation JSON."""

    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Generate a realistic markdown blog draft matching the requested outline and rules."""
        # Extract topic from prompt if possible
        topic_match = re.search(r'"topic":\s*"([^"]+)"', prompt)
        topic = topic_match.group(1) if topic_match else "Student Accommodation in Uttar Pradesh"

        # Determine primary city
        city = "Uttar Pradesh"
        for candidate_city in ["Greater Noida", "Noida", "Lucknow", "Kanpur", "Varanasi", "Prayagraj"]:
            if candidate_city.lower() in topic.lower():
                city = candidate_city
                break

        internal_links = brand_config.get_matching_internal_links(topic, max_links=2)
        link_md_1 = (
            f"[{internal_links[0].anchor_text}]({internal_links[0].url})"
            if internal_links
            else f"[verified student rooms]({brand_config.base_url})"
        )
        link_md_2 = (
            f"[{internal_links[1].anchor_text}]({internal_links[1].url})"
            if len(internal_links) > 1
            else f"[student budget calculator]({brand_config.base_url}/guides)"
        )

        return f"""# {topic}: The Ultimate Student Living & PG Guide

Finding safe, comfortable, and affordable student accommodation in {city} is one of the most critical decisions university students and outstation freshers face each academic year. Whether you are moving to attend campus lectures or preparing for competitive entrance examinations, having a reliable living environment directly impacts your academic focus, peace of mind, and overall wellbeing. In this comprehensive guide, we unpack local rental costs, campus proximity advantages, essential amenities, transit links, and legal safety safeguards to help you choose the right place to stay.

## Overview: Student Living in {city}

Higher education hubs across {city} attract tens of thousands of young scholars annually. As demand surges right before semester commencements, navigating local rental markets requires clear research and early planning.

### Why Location Matters for University Students
Living within walking distance or a short direct commute to your campus saves countless hours each week. In educational zones like {city}, daily traffic and transit bottlenecks make campus proximity one of the top factors determining student satisfaction. Outstation students frequently explore {link_md_1} to minimize morning transit stress and enjoy easy access to campus libraries and student cafeterias.

### Key Student Zones and Campus Proximity
Most student communities in {city} coalesce around major institutional corridors. These clusters offer vibrant student life, plenty of affordable dining options, stationery shops, and late-night study libraries. Staying in recognized student neighborhoods also ensures dependable availability of shared autos, e-rickshaws, and rapid public transit.

## Hostel vs PG vs Flat Sharing: Finding Your Fit

Students in Uttar Pradesh generally have three primary accommodation choices: university or private student hostels, paying guest (PG) accommodations, and independent rented flats.

### Budget and Rent Breakdown
While costs vary by exact locality and room sharing, student rents in {city} are typically structured as follows:
- **Triple or Quad Sharing Rooms**: ₹6,000 to ₹8,500 per month (often inclusive of regular mess meals and basic Wi-Fi).
- **Double Sharing Rooms**: ₹8,500 to ₹12,000 per month (standard choice balancing privacy and social life).
- **Single Occupancy Private Rooms**: ₹12,500 to ₹17,000+ per month (ideal for intensive study and final-year project work).

*Note: The prices above represent typical indicative ranges across the region. Actual tariffs depend on room type, air-conditioning, and specific property contracts.*

### Food, Mess, and Tiffin Services
Hygienic meals are vital for student health. Most organized student residences provide a set menu featuring North Indian vegetarian meals with optional weekend specials. Before finalizing an agreement, verify meal timings, kitchen hygiene standards, and whether filtered RO drinking water is included at no extra surcharge.

### Wi-Fi, Power Backup & Study Amenities
High-speed internet connectivity is non-negotiable for modern coursework and remote lectures. Furthermore, given peak summer temperatures across Uttar Pradesh, always ask whether the accommodation features full diesel generator (DG) power backup for air conditioning or an inverter system for basic fans and lights during power outages. For accurate expense planning, reference our {link_md_2} to budget your monthly costs effectively.

## Local Transit & Daily Commute Guide

Efficient daily travel keeps your monthly budget predictable and protects your study schedule.

### Metro & Shared Auto Route Connectivity
In cities like Noida and Greater Noida, the [NMRC Aqua Line](https://www.nmrcnoida.com) connects major institutional sectors directly with the Delhi Metro network. In Lucknow, the [UPMRC Lucknow Metro](https://www.lmrcl.com) links central hubs like Hazratganj and Charbagh. In cities like Kanpur, Varanasi, and Prayagraj, shared e-rickshaws and auto-rickshaws provide inexpensive last-mile transit between university gates and residential PG colonies.

### Estimated Monthly Commute Expenses
Most students commuting via shared public transport spend between ₹800 and ₹2,200 per month. Opting for student smart cards or metro passes can generate substantial monthly savings.

## Safety, Legal Agreements & Inspection Checklist

Safety and financial clarity must remain top priorities throughout your room selection process.

### Security Features to Check (CCTV, Biometric, Wardens)
Reputable student accommodations maintain 24/7 CCTV surveillance across common corridors and entrance gates, biometric entry systems, and on-site resident wardens. Female student residences typically follow standard entry time policies to maintain a secure environment.

### Rental Agreement & Security Deposit Rules
Always insist on a written rental agreement detailing:
- The exact security deposit amount (typically 1 to 2 months' rent).
- Written terms for deposit refund timelines and deduction policies upon checkout.
- Electricity meter billing rules (separate commercial vs residential unit tariffs).
- Advance notice period requirements (usually 30 days).

### Local Police Tenant Verification in Uttar Pradesh
Under state regulations, student housing operators and private landlords are required to submit tenant verification forms to the local police department. You will need to provide copies of your government ID (such as Aadhaar card), university admission letter or student ID, and emergency parent contact numbers.

## Frequently Asked Questions (FAQs)

### What is the average monthly rent for a student PG in {city}?
Typical student accommodation in {city} ranges from ₹6,000 to ₹14,000 per month depending on whether you choose shared or private occupancy, and whether mess meals are included.

### Are meals and Wi-Fi usually included in student hostels here?
Yes, most private student accommodations provide three daily meals, high-speed Wi-Fi, and housekeeping within the standard package. Always verify if AC power is billed separately via sub-meters.

### How early before the academic session starts should students book accommodation?
It is advisable to begin your search 4 to 6 weeks before semester classes start (typically June to July for autumn intake, and December for winter intake) to secure rooms closest to campus.

### What documents are required for student tenant verification in Uttar Pradesh?
Students must submit a valid government photo ID (Aadhaar/Passport), college admission slip or student ID card, passport-sized photographs, and contact information for a parent or legal guardian.

### Is public transport readily available near major university zones?
Yes, metro lines, frequent feeder buses, and inexpensive shared e-rickshaws connect primary university hubs with surrounding student residential sectors.

### What is the typical security deposit asked by PG owners in UP?
Most student accommodations require a refundable deposit equal to one or two months of room rent. Ensure the refund terms and notice period are clearly stated in writing.

### Can college freshers find single occupancy rooms, or is sharing mandatory?
Both options exist. Sharing rooms (double or triple) are popular for freshman socialization and lower expenses, while single rooms cater to students needing undisturbed quiet.

### How do student accommodations manage summer electricity and AC power cuts?
Reliable facilities maintain heavy-duty DG generator sets that support air conditioners during peak summer grid interruptions. Always clarify whether generator backup covers AC units or only lighting.

### Are female student hostels strictly secure with curfews?
Yes, female student residences generally implement 24/7 CCTV surveillance, biometric access, female resident wardens, and standard evening entry timings (often 8:30 PM to 9:30 PM).

### How can students avoid fraudulent broker listings in Uttar Pradesh?
Never pay non-refundable token money before scheduling a verified virtual or in-person walk-through. Seek feedback from current student occupants and verify that the property operates under verified management.

## Next Steps: Securing Your Student Room Without Hassle

Starting college or beginning an intensive coaching program is an exciting milestone. Taking the time to research transparent accommodations with verified amenities, supportive student peers, and safe transit routes sets you up for a successful academic tenure in {city}. Explore verified listings, schedule a visit, and reserve your space early to focus entirely on your educational ambitions.
"""

    def generate_structured_json(self, prompt: str, schema_description: str) -> Dict[str, Any]:
        """Generate a compliant QA inspection report in JSON format."""
        return {
            "readability_score": 92.0,
            "relevance_score": 95.0,
            "business_value_score": 90.0,
            "checks": [
                {
                    "check_name": "Readability",
                    "status": "PASS",
                    "severity": "MINOR",
                    "explanation": "Clear, student-friendly tone with natural phrasing and smooth transitions.",
                    "evidence": "Opening paragraph clearly addresses reader intent within first 120 words.",
                    "suggested_correction": "None required.",
                },
                {
                    "check_name": "Repetition",
                    "status": "PASS",
                    "severity": "MINOR",
                    "explanation": "No duplicate paragraphs or robotic sentence recycling found.",
                    "evidence": "Section outlines progress logically.",
                    "suggested_correction": "None required.",
                },
                {
                    "check_name": "Search Intent Alignment",
                    "status": "PASS",
                    "severity": "MAJOR",
                    "explanation": "Directly matches commercial investigation and student information search intent.",
                    "evidence": "Pricing ranges, transit guides, and comparison sections present.",
                    "suggested_correction": "None required.",
                },
                {
                    "check_name": "Business Relevance",
                    "status": "PASS",
                    "severity": "MAJOR",
                    "explanation": "High commercial alignment with student accommodation inquiries.",
                    "evidence": "Integrates verified internal URLs and non-misleading call to action.",
                    "suggested_correction": "None required.",
                },
                {
                    "check_name": "Keyword Stuffing",
                    "status": "PASS",
                    "severity": "CRITICAL",
                    "explanation": "Keywords appear organically without unnatural repetition.",
                    "evidence": "Primary keyword appears in H1, opening text, and naturally throughout headers.",
                    "suggested_correction": "None required.",
                },
                {
                    "check_name": "Factual Consistency",
                    "status": "PASS",
                    "severity": "CRITICAL",
                    "explanation": "No hallucinated absolute rates or fake reviews; uses clear indicative price ranges and official transit links.",
                    "evidence": "Disclaimers included for rental rates; official UP transit links cited.",
                    "suggested_correction": "None required.",
                },
                {
                    "check_name": "Missing Sections",
                    "status": "PASS",
                    "severity": "CRITICAL",
                    "explanation": "All 10 required FAQs and complete outline sections are fully present.",
                    "evidence": "Dedicated FAQs section with 10 questions and answers.",
                    "suggested_correction": "None required.",
                },
            ],
            "overall_recommendation": "APPROVED",
        }
