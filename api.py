import aiohttp
import re
from typing import Dict, Any, Optional

ANILIST_URL = "https://graphql.anilist.co"

async def fetch_anilist(title: str, media_type: str, country: Optional[str] = None) -> Dict[str, Any]:
    query = """
    query ($search: String, $type: MediaType, $country: CountryCode) {
        Media(search: $search, type: $type, countryOfOrigin: $country) {
            id
            title {
                romaji
                english
                native
            }
            coverImage {
                extraLarge
                large
                medium
            }
            bannerImage
            averageScore
            description
            genres
            startDate { year month day }
            format
            status
            episodes
            chapters
            volumes
            synonyms
            tags { name }
        }
    }
    """
    variables = {"search": title, "type": media_type}
    if country:
        variables["country"] = country

    async with aiohttp.ClientSession() as session:
        async with session.post(ANILIST_URL, json={"query": query, "variables": variables}) as resp:
            data = await resp.json()
            if "errors" in data:
                raise Exception(data["errors"][0]["message"])
            media = data.get("data", {}).get("Media")
            if not media:
                raise ValueError("No results found")
            return media

def clean_description(desc: str, max_len: int = 200) -> str:
    if not desc:
        return "No description available."
    clean = re.sub(r'<[^>]+>', '', desc)
    if len(clean) > max_len:
        clean = clean[:max_len].rsplit(' ', 1)[0] + "..."
    return clean.strip()

async def get_anime(title: str):
    media = await fetch_anilist(title, "ANIME")
    return {
        "title": media["title"]["english"] or media["title"]["romaji"],
        "cover": media["coverImage"]["extraLarge"] or media["coverImage"]["large"],
        "rating": media["averageScore"] / 10 if media["averageScore"] else 0.0,
        "genres": media["genres"][:3] if media["genres"] else [],
        "synopsis": clean_description(media["description"]),
        "format": media.get("format", ""),
        "episodes": media.get("episodes"),
        "status": media.get("status", ""),
        "year": media.get("startDate", {}).get("year"),
        "tags": [tag["name"] for tag in media.get("tags", [])[:3]]
    }

async def get_manga(title: str):
    media = await fetch_anilist(title, "MANGA")
    return {
        "title": media["title"]["english"] or media["title"]["romaji"],
        "cover": media["coverImage"]["extraLarge"] or media["coverImage"]["large"],
        "rating": media["averageScore"] / 10 if media["averageScore"] else 0.0,
        "genres": media["genres"][:3] if media["genres"] else [],
        "synopsis": clean_description(media["description"]),
        "format": media.get("format", ""),
        "chapters": media.get("chapters"),
        "volumes": media.get("volumes"),
        "status": media.get("status", ""),
        "year": media.get("startDate", {}).get("year"),
        "tags": [tag["name"] for tag in media.get("tags", [])[:3]]
    }

async def get_manhwa(title: str):
    try:
        media = await fetch_anilist(title, "MANGA", country="KR")
    except:
        media = await fetch_anilist(title, "MANGA")
    return {
        "title": media["title"]["english"] or media["title"]["romaji"],
        "cover": media["coverImage"]["extraLarge"] or media["coverImage"]["large"],
        "rating": media["averageScore"] / 10 if media["averageScore"] else 0.0,
        "genres": media["genres"][:3] if media["genres"] else [],
        "synopsis": clean_description(media["description"]),
        "format": media.get("format", ""),
        "chapters": media.get("chapters"),
        "volumes": media.get("volumes"),
        "status": media.get("status", ""),
        "year": media.get("startDate", {}).get("year"),
        "tags": [tag["name"] for tag in media.get("tags", [])[:3]]
                                }
