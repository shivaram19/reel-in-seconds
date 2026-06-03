"""
Vinayaka Hospital — Brand Soul Profile
======================================

A deep profile of Vinayaka Hospital, Suryapet, for narrative-driven
reel generation. This is the hospital's "soul" — its identity, values,
audience, and emotional core. Used by the narrative assembly engine to
generate patient-centric, values-driven content.

Location: Suryapet district, Telangana, India
Language: Telugu (primary), English (secondary)
Audience: Local Telugu-speaking families, 20km radius

Cultural Context:
- Suryapet is a tier-2 town in Telangana. Families are close-knit.
- Healthcare decisions are made by elders and women together.
- Trust is built through word-of-mouth, not advertising.
- Lord Ganesha is the hospital's patron deity — auspicious beginnings.
- The mother-child logo signals maternity as the core identity.

Values (in order of importance):
1. ప్రేమ (Prema) — Love/Care
2. శుశ్రూష (Shushrusha) — Service/Attendance
3. విశ్వాసం (Vishwasam) — Trust
4. సంతోషం (Santosham) — Happiness (of healthy mother and child)
5. భద్రత (Bhadrata) — Safety/Security
"""

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class HospitalSoul:
    name: str
    name_telugu: str
    location: str
    location_telugu: str
    established_year: int
    anniversary: int
    contact: str
    
    # Identity
    patron_deity: str
    logo_meaning: str
    tagline: str
    tagline_telugu: str
    
    # Doctors
    doctors: List[Dict]
    
    # Specialties
    specialties: List[Dict]
    
    # Values
    core_values: List[Dict]
    
    # Audience
    target_audience: str
    target_radius_km: int
    primary_language: str
    secondary_language: str
    
    # Emotional hooks
    patient_fears: List[str]
    patient_hopes: List[str]
    trust_signals: List[str]
    
    # Narrative roles for reels
    narrative_templates: List[Dict]


def load_vinayaka_soul() -> HospitalSoul:
    return HospitalSoul(
        name="Vinayaka Hospital",
        name_telugu="వినాయక హాస్పిటల్",
        location="Opposite New Bus Stand, Suryapet, Telangana",
        location_telugu="కొత్త బస్ స్టాండ్ ఎదురుగా, సూర్యాపేట",
        established_year=2015,
        anniversary=9,
        contact="9989890001",
        
        patron_deity="Lord Ganesha — remover of obstacles, god of beginnings",
        logo_meaning="Mother and child — safe maternity, nurturing care",
        tagline="Where care meets trust",
        tagline_telugu="ప్రేమ కలిసిన వైద్యం",
        
        doctors=[
            {
                "name": "Dr. S. Harsha Meena",
                "qualifications": "MBBS (Osmania), MS (OBG)",
                "registration": "07622",
                "specialty": "Gynecology, Obstetrics, Fertility",
                "specialty_telugu": "స్త్రీ రోగ నిపుణులు, ప్రసూతి వైద్యం, సంతాన సాఫల్యం",
                "image_role": "The compassionate guide — she holds the mother's hand through fear to joy",
            },
            {
                "name": "Dr. J. Ajay Kumar",
                "qualifications": "MBBS, MS (Ortho), KIMS",
                "registration": "75037",
                "specialty": "Orthopedics, Joint Replacement",
                "specialty_telugu": "ఎముకల శస్త్రచికిత్స, కీళ్ళ మార్పిడి",
                "image_role": "The restorer of movement — he gives back the ability to walk, to work, to live",
            },
        ],
        
        specialties=[
            {
                "name": "Normal Delivery",
                "name_telugu": "సహజ ప్రసవం",
                "claim": "Our specialty — safe, natural childbirth",
                "claim_telugu": "మా ప్రత్యేకత — సురక్షితమైన సహజ ప్రసవం",
                "emotion": "A mother's trust that her baby will arrive safely",
            },
            {
                "name": "Fertility Treatment",
                "name_telugu": "సంతాన సాఫల్య చికిత్స",
                "claim": "The only address for infertility in the region",
                "claim_telugu": "ఈ ప్రాంతంలో సంతాన లోపానికి ఏకైక చిరునామా",
                "emotion": "The hope of holding a child after years of waiting",
            },
            {
                "name": "Orthopedics",
                "name_telugu": "ఎముకల శస్త్రచికిత్స",
                "claim": "Advanced joint care, restoring movement",
                "claim_telugu": "ఆధునిక కీళ్ళ చికిత్స, కదలికను తిరిగి ఇవ్వడం",
                "emotion": "An elderly father walking again without pain",
            },
            {
                "name": "Women's Health",
                "name_telugu": "మహిళా ఆరోగ్యం",
                "claim": "Complete care for every stage of a woman's life",
                "claim_telugu": "మహిళ జీవితంలో ప్రతి దశకు పూర్తి సంరక్షణ",
                "emotion": "A daughter, mother, grandmother — all cared for",
            },
        ],
        
        core_values=[
            {
                "value": "Prema (ప్రేమ)",
                "meaning": "Love that heals — not just treatment, but tender care",
                "visual": "A nurse adjusting a blanket, a doctor's gentle touch",
            },
            {
                "value": "Shushrusha (శుశ్రూష)",
                "meaning": "Selfless service — attending to the patient as family",
                "visual": "Staff staying late, holding a patient's hand",
            },
            {
                "value": "Vishwasam (విశ్వాసం)",
                "meaning": "Trust earned through 8 years of consistent care",
                "visual": "Families returning for second and third deliveries",
            },
            {
                "value": "Santosham (సంతోషం)",
                "meaning": "The joy of a healthy mother and crying newborn",
                "visual": "A mother smiling while holding her baby for the first time",
            },
            {
                "value": "Bhadrata (భద్రత)",
                "meaning": "Safety — modern facilities, experienced hands",
                "visual": "Clean operation theater, advanced equipment",
            },
        ],
        
        target_audience="Telugu-speaking families in Suryapet and surrounding villages, 20km radius",
        target_radius_km=20,
        primary_language="Telugu",
        secondary_language="English",
        
        patient_fears=[
            "What if something goes wrong during delivery?",
            "Can we afford the treatment?",
            "Will the doctor understand our concerns?",
            "Is the hospital clean and safe?",
            "Will they force a C-section?",
        ],
        
        patient_hopes=[
            "A healthy baby and a safe mother",
            "Respectful treatment like family",
            "Clear communication in our language",
            "Affordable care without hidden costs",
            "A doctor who listens",
        ],
        
        trust_signals=[
            "8+ years of service in the same location",
            "Thousands of successful deliveries",
            "Same doctors, same care — consistency",
            "Free OPD camps for the community",
            "Transparent pricing",
            "Lord Ganesha's blessing — auspicious beginnings",
        ],
        
        narrative_templates=[
            {
                "name": "The Mother's Journey",
                "duration": "28 seconds",
                "structure": [
                    {"time": "0-3s", "act": "Hook", "content": "A pregnant woman's anxious face"},
                    {"time": "3-8s", "act": "Fear", "content": "Voice of worry — 'Will my baby be safe?'"},
                    {"time": "8-18s", "act": "Care", "content": "Dr. Harsha Meena's gentle reassurance, hospital facilities"},
                    {"time": "18-25s", "act": "Joy", "content": "Mother holding baby, smiling family"},
                    {"time": "25-28s", "act": "CTA", "content": "Vinayaka Hospital — ప్రేమ కలిసిన వైద్యం — 9989890001"},
                ],
            },
            {
                "name": "The Elder Father's Walk",
                "duration": "28 seconds",
                "structure": [
                    {"time": "0-3s", "act": "Hook", "content": "An elderly man struggling to walk"},
                    {"time": "3-8s", "act": "Pain", "content": "Family's concern — 'He can't walk to the temple anymore'"},
                    {"time": "8-18s", "act": "Healing", "content": "Dr. Ajay Kumar's treatment, joint care"},
                    {"time": "18-25s", "act": "Restoration", "content": "Father walking confidently, visiting temple"},
                    {"time": "25-28s", "act": "CTA", "content": "Vinayaka Hospital — కదలికను తిరిగి ఇవ్వడం — 9989890001"},
                ],
            },
        ],
    )


if __name__ == "__main__":
    soul = load_vinayaka_soul()
    print(f"Hospital: {soul.name_telugu} ({soul.name})")
    print(f"Location: {soul.location_telugu}")
    print(f"Contact: {soul.contact}")
    print(f"\nCore Values:")
    for v in soul.core_values:
        print(f"  • {v['value']}: {v['meaning']}")
