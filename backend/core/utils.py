"""Shared utility functions for Chimera."""

import re


def get_visual_context(topic: str) -> str:
    """Determine the visual theme based on topic keywords.

    Used by the VisualAgent to ensure stock footage matches the topic's vibe.
    """
    t = topic.lower()
    mappings = [
        (
            [
                "deep sea", "ocean", "underwater", "trench", "mariana",
                "abyss", "submarine", "whale", "shark", "marine", "sunken",
                "bloop", "coral", "sea monster", "shipwreck"
            ],
            "Underwater Abyss",
        ),
        (
            [
                "water", "lake", "river", "island", "beach", "ship",
                "boat", "waterfall", "coast", "tide"
            ],
            "Water Surface",
        ),
        (
            [
                "black hole", "cosmic", "galaxy", "supernova", "space",
                "universe", "star", "nebula", "astronaut", "cosmos",
                "orbit", "event horizon", "gamma-ray", "astronomy",
                "interstellar", "dyson sphere", "planet"
            ],
            "Deep Space",
        ),
        (
            [
                "cyberpunk", "neon", "matrix", "simulation", "glitch",
                "code", "virtual", "hacker", "synthetic", "dystopian"
            ],
            "Cyberpunk Neon",
        ),
        (
            [
                "quantum", "ai", "robot", "future", "technology",
                "nanotech", "algorithm", "supercomputer", "neural",
                "digital", "hologram", "tech"
            ],
            "Futuristic Technology",
        ),
        (
            [
                "ancient", "ruin", "civilization", "temple", "egypt",
                "pyramid", "rome", "greece", "megalith", "derinkuyu",
                "gobekli tepe", "archeology", "tomb", "pharaoh"
            ],
            "Ancient Megaliths",
        ),
        (
            [
                "medieval", "castle", "knight", "dynasty", "empire",
                "monarch", "fortress", "plague", "historical", "armor"
            ],
            "Medieval Fortress",
        ),
        (
            [
                "dna", "genetic", "biology", "fungi", "organism", "cell",
                "microscopic", "virus", "bacteria", "laboratory", "experiment"
            ],
            "Science Laboratory",
        ),
        (
            [
                "arctic", "ice", "antarctic", "glacier", "frozen",
                "blizzard", "snow", "polar", "tundra", "iceberg"
            ],
            "Frozen Arctic",
        ),
        (
            ["desert", "dune", "sandstorm", "sahara", "arid", "oasis"],
            "Desert Dunes",
        ),
        (
            [
                "forest", "jungle", "wilderness", "nature", "mountain",
                "woods", "trees", "wildlife", "biome", "rainforest"
            ],
            "Deep Forest",
        ),
        (
            [
                "volcano", "lava", "magma", "eruption", "volcanic",
                "pyroclastic", "firestorm", "molten"
            ],
            "Volcanic Storm",
        ),
        (
            [
                "city", "metropolis", "skyscraper", "urban", "street",
                "crowd", "traffic", "architecture"
            ],
            "Modern Metropolis",
        ),
        (
            [
                "serial killer", "crime", "heist", "murder", "police",
                "investigation", "cipher", "zodiac", "detective", "classified"
            ],
            "Dark Crime Scene",
        ),
        (
            [
                "psychology", "brain", "mind", "nightmare", "delusion",
                "sleep paralysis", "hallucination", "subconscious", "insanity"
            ],
            "Surreal Mindscape",
        ),
        (
            [
                "ghost", "haunted", "paranormal", "alien", "ufo",
                "creature", "cryptid", "skinwalker", "creepy", "horror"
            ],
            "Eerie Paranormal",
        ),
        (
            [
                "conspiracy", "secret", "government", "military", "bunker",
                "mkultra", "surveillance", "shadowy"
            ],
            "Classified Facility",
        ),
    ]
    for keywords, context in mappings:
        if any(x in t for x in keywords):
            return context
    return "Dark Cinematic Mystery"


def resize_to_vertical(clip, width=1080, height=1920):
    """Resize and crop a video clip to vertical (portrait) format.

    Maintains aspect ratio by center-cropping after scaling.
    Ensures safe integer bounds and prevents pixel overflow.
    """
    target_ratio = width / height
    clip_ratio = clip.w / clip.h

    def resize(**kwargs):
        method = getattr(clip, "resized", None) or clip.resize
        return method(**kwargs)

    def crop(**kwargs):
        method = getattr(clip, "cropped", None) or clip.crop
        return method(**kwargs)

    if clip_ratio >= target_ratio:
        clip = resize(height=height)
        if clip.w < width:
            clip = clip.resized(width=width) if hasattr(clip, "resized") else clip.resize(width=width)
        x_start = max(0, int((clip.w - width) / 2))
        clip = (clip.cropped(x1=x_start, width=width, height=height)
                if hasattr(clip, "cropped")
                else clip.crop(x1=x_start, width=width, height=height))
    else:
        clip = resize(width=width)
        if clip.h < height:
            clip = clip.resized(height=height) if hasattr(clip, "resized") else clip.resize(height=height)
        y_start = max(0, int((clip.h - height) / 2))
        clip = (clip.cropped(y1=y_start, width=width, height=height)
                if hasattr(clip, "cropped")
                else clip.crop(y1=y_start, width=width, height=height))
    return clip


def sanitize_filename(name: str) -> str:
    """Remove illegal filename characters and truncate."""
    cleaned = re.sub(r'[<>:"/\\|?*]', "", name).replace(" ", "_")
    cleaned = re.sub(r'_+', "_", cleaned)
    return cleaned.strip("._")[:80] or "chimera_video"


def sanitize_topic_input(topic: str) -> str:
    """Sanitize and validate user-supplied custom topics.

    Strips injection delimiters and restricts length.
    """
    if not topic:
        return ""
    cleaned = topic.strip().replace("\r\n", " ").replace("\n", " ")
    cleaned = re.sub(r'["\\]', "", cleaned)
    # Remove obvious prompt injection tags
    cleaned = re.sub(
        r'(?i)(system prompt|ignore previous|disregard all|as an ai)', '', cleaned
    )
    return cleaned.strip()[:200]


def validate_hf_token(token: str) -> bool:
    """Validate format of a HuggingFace API token."""
    if not token or not isinstance(token, str):
        return False
    token = token.strip()
    return bool(re.match(r"^hf_[A-Za-z0-9]{20,}$", token))
