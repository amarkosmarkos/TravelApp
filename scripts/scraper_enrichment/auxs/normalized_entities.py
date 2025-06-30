# Diccionario de normalización de ciudades de Tailandia
# Clave: nombre correcto, Valor: lista de variaciones

NORMALIZED_ENTITIES = {
    "Bangkok": [
        "Bangkok", 
        "Bangkok City", 
        "Krung Thep", 
        "Krung Thep Maha Nakhon",
        "BKK",
        "กรุงเทพมหานคร"
    ],
    "Chiang Mai": [
        "Chiang Mai", 
        "Chiangmai", 
        "Chiang-Mai", 
        "Chiang Mai City",
        "เชียงใหม่"
    ],
    "Phuket": [
        "Phuket", 
        "Phuket Town",
        "ภูเก็ต"
    ],
    "Koh Samui": [
        "Koh Samui", 
        "Ko Samui", 
        "Samui",
        "เกาะสมุย"
    ],
    "Koh Phi Phi": [
        "Koh Phi Phi", 
        "Ko Phi Phi", 
        "Phi Phi Islands", 
        "Phi Phi Island",
        "Phi Phi",
        "Islas Phi Phi",
        "Las islas Phi Phi",
        "เกาะพีพี"
    ],
    "Similan": [
        "Similan Islands",
        "Similan",
        "Islas Similan"
    ],
    "Mae Hong Son": [
        "Mae Hong Song", 
        "Mae Hong Son"
    ],
    "Songthaew": [
        "Songthaew", 
        "Songthaews"
    ],
    "Malasia": [
        "Malasya", 
        "Malasia"
    ],
    "Ayutthaya": [
        "Ayutthaya", 
        "Ayuthaya",
        "Ayyuthaya",
        "Ayutthaya City",
        "พระนครศรีอยุธยา"
    ],
    "Damnoen Saduak Floating Market": [
        "Klong Damnoen Saduak Floating Market", 
        "Damnoen Saduak Floating Market",
        "Mercado flotante de Damnoen Saduak",
        "El mercado flotante de Damnoen Saduak"
    ],
    "minivan": [
        "minivan", 
        "mini van",
        "miniván",
        "mini-van"
    ],
    "Night Bazaar": [
        "The Night Bazaar", 
        "Night Bazaar"
    ],
    "tuk-tuk": [
        "tuk-tuk", 
        "tuk tuk"
    ],
    "Wat Rong Khun": [
        "Wat Rong Khun", 
        "Wat Rong Khung"
    ],
    "Chatuchak Market": [
        "Chatuchak Market", 
        "Chatuchak Weekend Market"
    ],
    "Triángulo de Oro": [
        "Triángulo de Oro", 
        "Triángulo Dorado",
        "Triángulo del Oro",
        "Golden Triangle",
        "The Golden Triangle"
    ],
    "Grand Palace of Bangkok": [
        "Grand Palace of Bangkok", 
        "Grand Palace in Bangkok",
        "Grand Palace de Bangkok",
        "Bangkok Grand Palace",
        "Grand Palais de Bangkok",
        "El Gran Palacio de Bangkok",
        "Gran Palacio",
        "Gran Palacio Real"
    ],
    "Chiang Rai": [
        "Chiang Rai", 
        "Chiangrai", 
        "Chiang Rai City",
        "เชียงราย"
    ],
    "Krabi": [
        "Krabi", 
        "Krabi Province",
        "กระบี่"
    ],
    "Pattaya": [
        "Pattaya", 
        "Pattaya City", 
        "พัทยา"
    ],
    "Hua Hin": [
        "Hua Hin", 
        "Huahin", 
        "หัวหิน"
    ],
    "Koh Phangan": [
        "Koh Phangan", 
        "Koh Pha Ngan",
        "Ko Phangan",
        "Ko Pha Ngan",
        "Phangan Island",
        "เกาะพะงัน"
    ],
    "Koh Tao": [
        "Koh Tao", 
        "Ko Tao", 
        "Tao Island",
        "เกาะเต่า"
    ],
    "Phra Nang": [
        "Phra Nang", 
        "Phra Nang Beach", 
        "Ao Phra Nang",
        "Hat Phra Nang"
    ],
    "Kanchanaburi": [
        "Kanchanaburi", 
        "Kanchannaburi",
        "Kanchanaburi",
        "กาญจนบุรี"
    ],
    "Koh Chang": [
        "Koh Chang", 
        "Ko Chang"
    ],"Thailand": [
        "Thailand", 
        "Tailandia"
    ],
    "Sukhothai": [
        "Sukhothai", 
        "Sukhotai",
        "Sukhothai",
        "สุโขทัย"
    ],
    "Khao Sok National Park": [
        "Parque Nacional de Khao Sok",
        "Khao Sok National Park",
        "El Parque Nacional de Khao Sok",
        "Khao Sok"
    ],
    "Buri Ram": [
        "Buri Ram",
        "Buriram"
    ],
    "Koh Lanta": [
        "Koh Lanta", 
        "Ko Lanta", 
        "Lanta Island",
        "เกาะลันตา"
    ],
    "Khao Yai": [
        "Khao Yai", 
        "Khao Yai National Park",
        "Parque Nacional de Khao Yai",
        "El Parque Nacional de Khao Yai",
        "Parque Nacional Khao Yai"
    ],
    "Koh Yao Noi": [
        "Koh Yao Noi",
        "Ko Yao Noi"
    ]
}


def normalize_entity(entity_name):
    """
    Normaliza el nombre de una ciudad usando el diccionario.
    
    Args:
        entity_name (str): Nombre de la entidad a normalizar
        
    Returns:
        str: Nombre normalizado o el original si no se encuentra
    """
    if not entity_name:
        return entity_name
    
    entity_name = entity_name.strip()
    
    for normalized_name, variations in NORMALIZED_ENTITIES.items():
        if entity_name.lower() in [v.lower() for v in variations]:
            return normalized_name
    
    return entity_name

def get_all_variations():
    """
    Obtiene todas las variaciones de nombres de ciudades.
    
    Returns:
        list: Lista de todas las variaciones
    """
    all_variations = []
    for variations in NORMALIZED_ENTITIES.values():
        all_variations.extend(variations)
    return all_variations

def get_entity_info(entity_name):
    """
    Obtiene información de una entidad normalizada.
    
    Args:
        entity_name (str): Nombre de la entidad
        
    Returns:
        dict: Información de la ciudad o None si no se encuentra
    """
    normalized = normalize_entity(entity_name)
    if normalized in NORMALIZED_ENTITIES:
        return {
            "normalized_name": normalized,
            "variations": NORMALIZED_ENTITIES[normalized],
            "total_variations": len(NORMALIZED_ENTITIES[normalized])
        }
    return None
