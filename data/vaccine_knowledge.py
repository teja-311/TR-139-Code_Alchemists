# data/vaccine_knowledge.py

# Complete 12 Vaccine UIP Database with dynamically built 10% spoilage tiers 
# representing accurate clinical outcomes and public domain symptom images.

BASE_VACCINE_INFO = {
    "Bacillus Calmette–Guérin (Live Attenuated)": {
        "disease": "Tuberculosis (Severe Childhood TB)",
        "temp_range": (2, 8),
        "freeze_sensitive": False,
        "heat_sensitive": True,
        "q10_factor": 2.5,
        "base_images": [
            "https://upload.wikimedia.org/wikipedia/commons/9/9c/Tuberculosis-x-ray-1.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/0/0a/TB_Culture.jpg"
        ],
        "symptoms": "If administered spoiled: Reduced protection against severe forms of childhood TB like TB meningitis. Symptoms include chronic cough, weight loss, fever, night sweats, and potential fatal central nervous system involvement."
    },
    "Live Attenuated Poliovirus (Oral)": {
        "disease": "Polio (Poliomyelitis)",
        "temp_range": (2, 8), # Typical PHC storage, can also be -20
        "freeze_sensitive": False,
        "heat_sensitive": True,
        "q10_factor": 3.0,
        "base_images": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/Polio_lores134.jpg/960px-Polio_lores134.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/CDC_PHIL_3422_-_Medical_doctor.jpg/800px-CDC_PHIL_3422_-_Medical_doctor.jpg"
        ],
        "symptoms": "If administered spoiled: VDPV risk or complete failure to immunize. Symptoms of polio include fever, fatigue, vomiting, permanent paralysis (mostly legs), and breathing difficulty leading to death."
    },
    "Recombinant HBsAg": {
        "disease": "Hepatitis B Infection",
        "temp_range": (2, 8),
        "freeze_sensitive": True,
        "heat_sensitive": True,
        "q10_factor": 2.0,
        "base_images": [
            "https://upload.wikimedia.org/wikipedia/commons/1/12/Hepatitis-B_virions.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Jaundice08.jpg/960px-Jaundice08.jpg"
        ],
        "symptoms": "If administered spoiled: Chronic liver infection risk. Symptoms include yellowing of eyes/skin (jaundice), dark urine, extreme fatigue, leading eventually to cirrhosis or liver failure."
    },
    "DTP-HepB-Hib Antigens": {
        "disease": "Diphtheria, Tetanus, Pertussis, Hep B, Hib",
        "temp_range": (2, 8),
        "freeze_sensitive": True,
        "heat_sensitive": True,
        "q10_factor": 2.2,
        "base_images": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/Opisthotonus_in_a_patient_suffering_from_tetanus_-_Painting_by_Sir_Charles_Bell_-_1809.jpg/960px-Opisthotonus_in_a_patient_suffering_from_tetanus_-_Painting_by_Sir_Charles_Bell_-_1809.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/Dirty_white_pseudomembrane_classically_seen_in_diphtheria_2013-07-06_11-07.jpg/960px-Dirty_white_pseudomembrane_classically_seen_in_diphtheria_2013-07-06_11-07.jpg"
        ],
        "symptoms": "If administered spoiled: Loss of protection across 5 diseases. Key severe symptoms include thick gray coating in throat (Diphtheria), lockjaw/muscle spasms (Tetanus), and severe whooping cough (Pertussis)."
    },
    "Inactivated Poliovirus": {
        "disease": "Polio (Poliomyelitis)",
        "temp_range": (2, 8),
        "freeze_sensitive": True, # Unlike OPV, IPV is freeze-sensitive
        "heat_sensitive": True,
        "q10_factor": 2.1,
        "base_images": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/Polio_lores134.jpg/960px-Polio_lores134.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/1/14/Blausen_0822_SpinalCord.png"
        ],
        "symptoms": "If administered spoiled: Failure to boost systemic immunity. Symptoms of polio include fever, permanent paralysis, and breathing difficulty."
    },
    "Live Attenuated Rotavirus": {
        "disease": "Rotavirus Gastroenteritis",
        "temp_range": (2, 8),
        "freeze_sensitive": False,
        "heat_sensitive": True,
        "q10_factor": 2.6,
        "base_images": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/Rotavirus_Reconstruction.jpg/960px-Rotavirus_Reconstruction.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7c/Multiple_rotavirus_particles.jpg/960px-Multiple_rotavirus_particles.jpg"
        ],
        "symptoms": "If administered spoiled: High risk of severe watery diarrhea in children. Leads to extreme dehydration, vomiting, fever, and potential infant mortality if untreated."
    },
    "Pneumococcal Polysaccharide Conjugate": {
        "disease": "Pneumococcal Disease",
        "temp_range": (2, 8),
        "freeze_sensitive": True,
        "heat_sensitive": True,
        "q10_factor": 2.0,
        "base_images": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/8/81/Chest_radiograph_in_influensa_and_H_influenzae%2C_posteroanterior%2C_annotated.jpg/960px-Chest_radiograph_in_influensa_and_H_influenzae%2C_posteroanterior%2C_annotated.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/9/9f/Pneumococcus_CDC_PHIL_ID1003.jpg"
        ],
        "symptoms": "If administered spoiled: Risk of pneumonia, meningitis, and sepsis. Symptoms include high fever, cough, shortness of breath, and chest pain."
    },
    "Live Attenuated Measles & Rubella": {
        "disease": "Measles & Rubella",
        "temp_range": (2, 8),
        "freeze_sensitive": False,
        "heat_sensitive": True,
        "q10_factor": 2.8,
        "base_images": [
            "https://upload.wikimedia.org/wikipedia/commons/2/27/RougeoleDP.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/d/d8/Rash_of_rubella_on_back_%28crop%29.JPG"
        ],
        "symptoms": "If administered spoiled: Measles: high fever, full body rash, pneumonia risk. Rubella: rash, swollen lymph nodes, risk of Congenital Rubella Syndrome in pregnant women."
    },
    "Live Attenuated JE Virus": {
        "disease": "Japanese Encephalitis",
        "temp_range": (2, 8),
        "freeze_sensitive": False,
        "heat_sensitive": True,
        "q10_factor": 2.5,
        "base_images": [
            "https://upload.wikimedia.org/wikipedia/commons/c/c2/Japanese_encephalitis_distribution_2022.png",
            "https://upload.wikimedia.org/wikipedia/commons/d/d5/Hsv_encephalitis.jpg"
        ],
        "symptoms": "If administered spoiled: Risk of severe brain inflammation. Symptoms start with fever and headache, but can advance to stiff neck, disorientation, coma, seizures, and spastic paralysis."
    },
    "Tetanus Toxoid": {
        "disease": "Tetanus",
        "temp_range": (2, 8),
        "freeze_sensitive": True,
        "heat_sensitive": False, # Relatively heat stable but still 2-8 ideal
        "q10_factor": 1.5,
        "base_images": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/Opisthotonus_in_a_patient_suffering_from_tetanus_-_Painting_by_Sir_Charles_Bell_-_1809.jpg/960px-Opisthotonus_in_a_patient_suffering_from_tetanus_-_Painting_by_Sir_Charles_Bell_-_1809.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/c/c7/Clostridium_tetani_01.png"
        ],
        "symptoms": "If administered spoiled: Tetanus infection from wound contamination. Leads to painful muscle stiffness, 'lockjaw', trouble swallowing, and respiratory failure."
    },
    "Diphtheria & Tetanus Toxoids + Pertussis Antigen": {
        "disease": "Diphtheria, Pertussis, Tetanus",
        "temp_range": (2, 8),
        "freeze_sensitive": True,
        "heat_sensitive": True,
        "q10_factor": 2.1,
        "base_images": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/Dirty_white_pseudomembrane_classically_seen_in_diphtheria_2013-07-06_11-07.jpg/960px-Dirty_white_pseudomembrane_classically_seen_in_diphtheria_2013-07-06_11-07.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/CDC_PHIL_3422_-_Medical_doctor.jpg/800px-CDC_PHIL_3422_-_Medical_doctor.jpg"
        ],
        "symptoms": "If administered spoiled: Loss of protection. Diphtheria (breathing issues), Pertussis (severe whooping cough spasms), Tetanus (muscle stiffness/lockjaw)."
    },
    "Haemophilus influenzae type b Conjugate": {
        "disease": "Haemophilus influenzae type b",
        "temp_range": (2, 8),
        "freeze_sensitive": True,
        "heat_sensitive": True,
        "q10_factor": 2.3,
        "base_images": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/0/02/Haemophilus_influenzae.jpg/960px-Haemophilus_influenzae.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Meninges-en.svg/960px-Meninges-en.svg.png"
        ],
        "symptoms": "If administered spoiled: Bacterial meningitis risk in infants. Symptoms include fever, stiff neck, vomiting, leading to potential hearing loss, brain damage, or death."
    }
}

def generate_tiers(symptoms_desc):
    tiers = {}
    for i in range(10):
        start = i * 10
        end = min((i + 1) * 10, 100)
        tier_key = f"{start}-{end}%"
        
        # Calculate human body outcome severity
        if i < 2:
            outcome = f"Minimal risk - {100-end}-{100-start}% protection retained. Mild symptoms might occur if failure happens."
        elif i < 5:
            outcome = f"Moderate risk - {100-end}-{100-start}% protection retained. Vaccine efficacy significantly reduced. Increased chance of contracting disease with partial severity."
        elif i < 8:
            outcome = f"High risk - Only {100-end}-{100-start}% protection retained. Almost complete loss of immunogenicity. {symptoms_desc.split('.')[0]}."
        else:
            outcome = f"Critical failure - {100-end}-{100-start}% protection retained. Vaccine is completely dead/spoiled. {symptoms_desc}"
            
        tiers[tier_key] = {
            "efficacy_retained": f"{100-end}-{100-start}%",
            "human_body_outcome": outcome
        }
    return tiers

# Build the complete DB
VACCINE_DB = {}
for vac, info in BASE_VACCINE_INFO.items():
    VACCINE_DB[vac] = {
        "disease": info["disease"],
        "temp_range": info["temp_range"],
        "freeze_sensitive": info["freeze_sensitive"],
        "heat_sensitive": info["heat_sensitive"],
        "q10_factor": info["q10_factor"],
        "images": info["base_images"],
        "symptoms": info["symptoms"],
        "spoilage_tiers": generate_tiers(info["symptoms"])
    }

def get_vaccines():
    return list(VACCINE_DB.keys())

def get_vaccine_info(vaccine_name):
    return VACCINE_DB.get(vaccine_name, None)
