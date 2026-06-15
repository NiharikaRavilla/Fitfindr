# FitFindr 

FitFindr is a multi-tool AI agent for thrift shopping. Given a natural-language request, it can search a mock secondhand listings dataset, choose a promising item, suggest how to wear it with the user’s wardrobe, and generate a short shareable fit-card caption.

The project is built around a planning loop: the agent does not blindly call every tool in the same order. Instead, it decides what to do next based on what the previous tool returned. That means it can stop early when no listings match, or continue through styling and caption generation when a good item is found.

---

#  Project Structure

The main files in this project are:

* `tools.py` — contains the three core FitFindr tools
* `agent.py` — implements the planning loop and session management
* `app.py` — Gradio user interface
* `tests/test_tools.py` — unit tests for tool functionality
* `planning.md` — project design and architecture specification

### Mock Data

* `data/listings.json` — mock thrift listings dataset
* `data/wardrobe_schema.json` — wardrobe schema and example wardrobes

### Utility Functions

* `utils/data_loader.py` — helper functions for loading listings and wardrobes

---

#  Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_key_here
```

You can get a free API key from:

https://console.groq.com

---

#  Running the Project

### Run the Gradio Application

```bash
python app.py
```

Open the URL displayed in the terminal (usually `http://127.0.0.1:7860`).

### Run the Agent Directly

```bash
python agent.py
```

### Run Tests

```bash
pytest tests/ -v
```

---

#  Tool Inventory

## 1. search_listings(description, size, max_price)

### Purpose

Searches the mock listings dataset and returns relevant secondhand items.

### Inputs

| Parameter   | Type         | Description                  |
| ----------- | ------------ | ---------------------------- |
| description | str          | Item description or keywords |
| size        | str | None   | Optional size filter         |
| max_price   | float | None | Optional maximum price       |

### Output

```python
list[dict]
```

A list of matching listings sorted by relevance.

### Failure Handling

Returns:

```python
[]
```

when no matching listings are found.

---

## 2. suggest_outfit(new_item, wardrobe)

### Purpose

Generates outfit suggestions using a selected thrifted item and the user's wardrobe.

### Inputs

| Parameter | Type | Description      |
| --------- | ---- | ---------------- |
| new_item  | dict | Selected listing |
| wardrobe  | dict | User wardrobe    |

### Output

```python
str
```

One or more outfit suggestions.

### Failure Handling

If the wardrobe is empty, the tool returns general styling advice rather than failing.

---

## 3. create_fit_card(outfit, new_item)

### Purpose

Creates a social-media-ready outfit caption.

### Inputs

| Parameter | Type | Description            |
| --------- | ---- | ---------------------- |
| outfit    | str  | Outfit suggestion      |
| new_item  | dict | Selected thrifted item |

### Output

```python
str
```

A short fit-card caption.

### Failure Handling

If the outfit is empty or invalid, the tool returns a descriptive error message.

---

#  Planning Loop

The agent follows a conditional planning loop rather than executing every tool automatically.

### Workflow

1. Parse the user query.
2. Extract:

   * description
   * size
   * maximum price
3. Call `search_listings()`.
4. If no results are found:

   * store an error message
   * stop execution
5. If results exist:

   * select the top listing
   * save it as `selected_item`
6. Call `suggest_outfit(selected_item, wardrobe)`.
7. Save the outfit suggestion.
8. Call `create_fit_card(outfit_suggestion, selected_item)`.
9. Return the completed session.

The agent changes behavior depending on tool output. It does not call all tools unconditionally.

---

#  State Management

FitFindr uses a shared session dictionary throughout the interaction.

Example structure:

```python
session = {
    "query": "",
    "parsed": {},
    "search_results": [],
    "selected_item": None,
    "wardrobe": {},
    "outfit_suggestion": None,
    "fit_card": None,
    "error": None
}
```

### State Flow

```text
search_listings()
        ↓
selected_item
        ↓
suggest_outfit()
        ↓
outfit_suggestion
        ↓
create_fit_card()
        ↓
fit_card
```

This allows information to move between tools without requiring the user to re-enter data.

---

#  Error Handling

## search_listings()

### Failure Example

```python
search_listings(
    "designer ballgown",
    size="XXS",
    max_price=5
)
```

### Response

```python
[]
```

The agent responds:

> No listings matched that search. Try broadening the description, removing the size filter, or increasing the budget.

---

## suggest_outfit()

### Failure Example

```python
suggest_outfit(
    item,
    get_empty_wardrobe()
)
```

### Response

Returns general styling advice instead of crashing.

---

## create_fit_card()

### Failure Example

```python
create_fit_card("", item)
```

### Response

Returns a descriptive error message explaining that outfit information is missing.

---

#  Testing

The tools were tested individually before being connected to the planning loop.

Run:

```bash
pytest tests/ -v
```

The test suite verifies:

* successful listing search
* no-results search
* price filtering
* empty wardrobe handling
* empty outfit handling

---

#  AI Usage

## Example 1 — Tool Development

I used ChatGPT to help implement:

* `search_listings()`
* `suggest_outfit()`
* `create_fit_card()`

I provided:

* tool specifications from `planning.md`
* required inputs and outputs
* failure mode requirements

I reviewed and modified the generated code to ensure it matched the project requirements and dataset structure.

---

## Example 2 — Planning Loop Implementation

I used ChatGPT to help implement the planning loop in `agent.py`.

I provided:

* Planning Loop section from `planning.md`
* State Management section
* Architecture diagram

The generated implementation was revised to:

* correctly store state in the session dictionary
* stop execution when no listings were found
* fix query parsing so prices were not incorrectly interpreted as sizes

---

# Spec Reflection

Designing the planning loop before implementation made the project easier to build and debug. The planning document helped define clear tool responsibilities and failure behaviors before writing any code.

The most challenging part of the project was query parsing and ensuring the planning loop actually changed behavior based on tool output. Testing each tool independently with pytest made integration significantly easier because issues could be isolated before wiring everything together.

---

# 💡 Example Queries

### Successful Search

```text
vintage graphic tee under $30
```

### No-Results Search

```text
designer ballgown size XXS under $5
```
