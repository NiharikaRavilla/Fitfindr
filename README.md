# FitFindr — Starter Kit

FitFindr is a multi-tool AI agent for thrift shopping. Given a natural-language request, it can search a mock secondhand listings dataset, choose a promising item, suggest how to wear it with the user’s wardrobe, and generate a short shareable fit-card caption.

The project is built around a planning loop: the agent does not blindly call every tool in the same order. Instead, it decides what to do next based on what the previous tool returned. That means it can stop early when no listings match, or continue through styling and caption generation when a good item is found.

## What's Included

```
The main files in this project are:

- `tools.py` — the three core tools used by the agent
- `agent.py` — the planning loop and session/state management
- `app.py` — the Gradio interface
- `tests/test_tools.py` — isolated tests for the tools
- `planning.md` — the design document for the agent

The mock data lives in:

- `data/listings.json`
- `data/wardrobe_schema.json`

Helper functions for loading data live in:

- `utils/data_loader.py`
```

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here

Run the app:

python app.py

Run the agent directly:

python agent.py

Run tests:

pytest tests/ -v
```
Tools
1) search_listings(description, size, max_price) -> list[dict]

Searches the mock listings dataset for secondhand items that match the user’s request.

Inputs

description (str): keywords describing the item the user wants
size (str | None): optional size filter
max_price (float | None): optional price ceiling

Output

A list of matching listing dictionaries sorted by relevance
Returns [] when nothing matches

Purpose

Finds candidate thrift items for the agent to style next
2) suggest_outfit(new_item, wardrobe) -> str

Uses the selected thrifted item and the user’s wardrobe to suggest one or more outfits.

Inputs

new_item (dict): the selected listing returned by search_listings
wardrobe (dict): the user’s wardrobe data, usually from get_example_wardrobe() or get_empty_wardrobe()

Output

A non-empty string containing outfit suggestions

Purpose

Helps the user see how the thrifted item fits into what they already own

Failure behavior

If the wardrobe is empty, the tool returns general styling advice instead of crashing
3) create_fit_card(outfit, new_item) -> str

Generates a short caption-style description of the outfit.

Inputs

outfit (str): the outfit suggestion returned by suggest_outfit
new_item (dict): the selected listing dictionary

Output

A short social-ready fit-card caption

Purpose

Creates a shareable post-style description of the final outfit

Failure behavior

If the outfit string is empty or missing, the tool returns a descriptive error message instead of raising an exception
Planning Loop

The agent runs as a conditional loop rather than a fixed sequence.

The user submits a natural-language query.
agent.py parses the query into search parameters such as description, size, and max price.
The agent calls search_listings(...).
If search_listings returns no results, the agent stops early and returns a helpful error message telling the user what to loosen or change.
If results are found, the agent chooses the top listing and stores it in the session as selected_item.
The agent then calls suggest_outfit(selected_item, wardrobe).
If outfit generation fails or returns something unusable, the agent stops and returns a useful message.
If outfit generation succeeds, the agent calls create_fit_card(outfit_suggestion, selected_item).
The completed session is returned to the UI.

This means the agent changes behavior based on the output of the previous step. It does not always call all three tools unconditionally.

State Management

FitFindr keeps one session dictionary for the whole interaction. That session stores:

the original query
parsed search parameters
search results
the selected listing
the wardrobe
the outfit suggestion
the final fit card
any error message

This state is what allows data to move from one step to the next without the user repeating anything.

For example:

search_listings(...) returns a list of matches
the agent stores results[0] as selected_item
selected_item is passed into suggest_outfit(...)
the returned outfit string is passed into create_fit_card(...)

That state flow is what makes the agent behave like a real multi-step system instead of three unrelated function calls.

Error Handling

FitFindr handles failure cases intentionally instead of crashing.

search_listings

If no listings match, the tool returns an empty list.

Example:

search_listings("designer ballgown", size="XXS", max_price=5)

Expected outcome:

returns []
agent stops early
UI tells the user to broaden the search
suggest_outfit

If the wardrobe is empty, the tool still returns useful styling guidance.

Example:

suggest_outfit(item, get_empty_wardrobe())

Expected outcome:

returns a helpful string with general styling ideas
does not raise an exception
does not return blank output
create_fit_card

If the outfit string is empty or incomplete, the tool returns a descriptive error message.

Example:

create_fit_card("", item)

Expected outcome:

returns a readable error message string
does not crash
Testing

The tools were tested in isolation with pytest before wiring them into the agent.

Run:

pytest tests/ -v

The tests cover:

successful listing search
no-results search
price filtering
empty-wardrobe outfit handling
empty-outfit fit-card handling
AI Usage

I used an AI tool in two main places during this project.

1) Tool implementation support

I gave the AI the tool specifications from planning.md and asked it to help implement search_listings, suggest_outfit, and create_fit_card. It produced an initial version of the logic, including prompt structure for the LLM-based tools and filtering logic for listings. I adjusted the final code to match my actual data schema and failure-handling requirements.

2) Planning loop support

I gave the AI the Planning Loop, State Management, and Architecture sections from planning.md and asked it to help draft the agent flow. It produced a branching structure for run_agent(), but I revised the query parser because the first version incorrectly treated the price in under $30 as a size. I also tightened the early-return behavior so the agent stops immediately when search_listings returns no matches.

Spec Reflection

Writing the planning document first made implementation much easier. The tool specs forced me to decide exactly what each function should accept, return, and do when something fails. That helped a lot when I started writing tests, because the tests could check the exact behavior I had already designed.

The biggest challenge was the planning loop. The agent had to branch based on tool output rather than always running all steps in sequence. Once I treated the session dictionary as the single source of truth, state flow became much easier to reason about and debug. The no-results path and empty-wardrobe path were especially useful because they proved the agent could recover gracefully instead of crashing.

Demo Notes

The demo shows:

a full successful interaction from search to outfit to fit card
state passing between tools through the session dictionary
at least one failure case with a graceful response
Example Queries

Successful path:

vintage graphic tee under $30

Failure path:

designer ballgown size XXS under $5