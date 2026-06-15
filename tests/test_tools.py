import tools
from tools import create_fit_card, search_listings, suggest_outfit


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    def __init__(self, content):
        self._content = content

    def create(self, *args, **kwargs):
        return _FakeResponse(self._content)


class _FakeChat:
    def __init__(self, content):
        self.completions = _FakeCompletions(content)


class _FakeClient:
    def __init__(self, content):
        self.chat = _FakeChat(content)


def test_search_returns_results(monkeypatch):
    fake_listings = [
        {
            "id": 1,
            "title": "Vintage Graphic Tee",
            "description": "Faded band tee with washed black print",
            "category": "tops",
            "style_tags": ["vintage", "grunge"],
            "size": "M",
            "condition": "good",
            "price": 22.0,
            "colors": ["black"],
            "brand": "Unknown",
            "platform": "Depop",
        },
        {
            "id": 2,
            "title": "Puffer Jacket",
            "description": "Warm winter jacket",
            "category": "outerwear",
            "style_tags": ["streetwear"],
            "size": "L",
            "condition": "great",
            "price": 40.0,
            "colors": ["blue"],
            "brand": "Nike",
            "platform": "Poshmark",
        },
    ]
    monkeypatch.setattr(tools, "load_listings", lambda: fake_listings)

    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["title"] == "Vintage Graphic Tee"


def test_search_empty_results(monkeypatch):
    fake_listings = [
        {
            "id": 1,
            "title": "Vintage Graphic Tee",
            "description": "Faded band tee with washed black print",
            "category": "tops",
            "style_tags": ["vintage", "grunge"],
            "size": "M",
            "condition": "good",
            "price": 22.0,
            "colors": ["black"],
            "brand": "Unknown",
            "platform": "Depop",
        }
    ]
    monkeypatch.setattr(tools, "load_listings", lambda: fake_listings)

    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []


def test_search_price_filter(monkeypatch):
    fake_listings = [
        {
            "id": 1,
            "title": "Budget Jacket",
            "description": "Simple thrifted jacket",
            "category": "outerwear",
            "style_tags": ["casual"],
            "size": "M",
            "condition": "fair",
            "price": 10.0,
            "colors": ["black"],
            "brand": "Unknown",
            "platform": "Depop",
        },
        {
            "id": 2,
            "title": "Pricier Jacket",
            "description": "Cleaner jacket",
            "category": "outerwear",
            "style_tags": ["streetwear"],
            "size": "M",
            "condition": "great",
            "price": 25.0,
            "colors": ["navy"],
            "brand": "Levi's",
            "platform": "Etsy",
        },
    ]
    monkeypatch.setattr(tools, "load_listings", lambda: fake_listings)

    results = search_listings("jacket", size=None, max_price=10)
    assert len(results) == 1
    assert all(item["price"] <= 10 for item in results)


def test_suggest_outfit_empty_wardrobe(monkeypatch):
    monkeypatch.setattr(tools, "_get_groq_client", lambda: _FakeClient("General styling advice here."))

    new_item = {
        "title": "Band Tee",
        "price": 22,
        "platform": "Depop",
        "description": "Vintage band tee",
    }
    wardrobe = {"items": []}

    result = suggest_outfit(new_item, wardrobe)
    assert isinstance(result, str)
    assert result.strip() != ""
    assert "General styling advice" in result


def test_suggest_outfit_with_wardrobe(monkeypatch):
    monkeypatch.setattr(tools, "_get_groq_client", lambda: _FakeClient("Pair it with baggy jeans and chunky sneakers."))

    new_item = {
        "title": "Band Tee",
        "price": 22,
        "platform": "Depop",
        "description": "Vintage band tee",
    }
    wardrobe = {
        "items": [
            {"name": "baggy jeans", "category": "bottoms", "colors": ["blue"]},
            {"name": "chunky sneakers", "category": "shoes", "colors": ["white"]},
        ]
    }

    result = suggest_outfit(new_item, wardrobe)
    assert isinstance(result, str)
    assert result.strip() != ""


def test_create_fit_card_empty_outfit():
    new_item = {
        "title": "Band Tee",
        "price": 22,
        "platform": "Depop",
        "description": "Vintage band tee",
    }

    result = create_fit_card("", new_item)
    assert isinstance(result, str)
    assert "missing or incomplete" in result.lower()


def test_create_fit_card_generates_caption(monkeypatch):
    monkeypatch.setattr(tools, "_get_groq_client", lambda: _FakeClient(
        "Thrifted this Band Tee for $22 on Depop and it instantly gave the fit a laid-back edge."
    ))

    new_item = {
        "title": "Band Tee",
        "price": 22,
        "platform": "Depop",
        "description": "Vintage band tee",
    }
    outfit = "Band tee with baggy jeans and chunky sneakers."

    result = create_fit_card(outfit, new_item)
    assert isinstance(result, str)
    assert result.strip() != ""
    assert "Band Tee" in result or "band tee" in result.lower()