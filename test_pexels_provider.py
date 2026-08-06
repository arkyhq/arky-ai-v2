from scripts.media_engine.providers.pexels_provider import PexelsProvider

provider = PexelsProvider()

result = provider.search({
    "search_query": "modern AI laboratory",
    "asset_type": "background",
    "per_page": 3
})

print(result)
