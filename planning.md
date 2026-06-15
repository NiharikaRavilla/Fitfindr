# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->

Searches the mock listings dataset for secondhand items that match the user’s requested style, size, and budget. It ranks or filters results so the agent can choose the best item to style next.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): Free-text description of the item the user wants, such as “vintage graphic tee” or “black leather jacket.”
- `size` (str): The user’s preferred size, such as S, M, L, 28, or 10. Can be blank or None if the user does not specify.
- `max_price` (float): The highest price the user is willing to pay.

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->

A structured result containing either a list of matching listings or an empty result. Each listing should include the fields needed to identify and compare the item, such as id, title, description, category, style_tags, size, condition, price, colors, brand, and platform. The return value should also include a status flag and a message explaining the outcome.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->

If no listings match, the agent should stop the workflow and tell the user what part of the search was too narrow, such as size, budget, or description. It should not call suggest_outfit with an empty item list. It can suggest broadening one filter and trying again.

---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->

Takes one selected thrifted item and the user’s wardrobe, then generates one or more outfit combinations that work with that item. It should produce a realistic style suggestion, not just a random list of clothes.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): The selected listing from search_listings, represented as a structured item object.
- `wardrobe` (dict): The user’s wardrobe items from the provided wardrobe schema.

**What it returns:**
<!-- Describe the return value -->

A structured result containing one or more outfit suggestions. Each suggestion should include the pieces used, a short explanation of why the outfit works, and any styling notes. It should also include a status flag and a message.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? --> If the wardrobe is empty or too minimal to build a full outfit, the agent should explain that it needs more wardrobe items before styling can continue. It should not invent an outfit from nothing. If possible, it can return a partial suggestion or ask the user to provide a few staple wardrobe pieces.

---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->

Turns the selected outfit and new item into a short, shareable caption-like fit card. The output should sound like a social media caption or Instagram post, not a product description.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (dict): The chosen outfit suggestion.
- `new_item` (dict): The thrifted item that started the look.

**What it returns:**
<!-- Describe the return value -->

A short text caption or a small set of caption options that capture the vibe of the outfit. The return should include a status flag and the generated fit card text.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->

If the outfit data is incomplete, the agent should not invent missing pieces. It should either ask for the missing outfit details or fall back to a simpler caption based only on the item if enough information exists.
---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->

The agent should run as a conditional loop, not as a fixed script. It first reads the user request and extracts the item description, size, price limit, and wardrobe context if the user provided it. If the request is missing a buyable item, the agent asks for more detail before calling any tools.

If the request includes an item to find, the agent calls search_listings(description, size, max_price) first. After the call returns, it checks results:

If results is empty, the agent sets an error message in session state and returns immediately with a suggestion to loosen one constraint. It does not call any later tools.
If results is not empty, the agent selects the first result as selected_item and stores it in session state.

Next, the agent calls suggest_outfit(new_item=selected_item, wardrobe=session.wardrobe).

If the wardrobe is empty or the tool returns ok=False, the agent returns early with a helpful message asking for wardrobe items or stating that there is not enough context to style the item.
If the tool succeeds, the agent stores the best outfit as selected_outfit.

Finally, the agent calls create_fit_card(outfit=selected_outfit, new_item=selected_item).

If this succeeds, the agent returns the listing, outfit suggestion, and fit card to the user.
If it fails because outfit data is incomplete, the agent explains what is missing and does not claim the fit card is complete.

The loop ends when either:

a final fit card is produced, or
a failure occurs that requires user input before continuing.

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->

The agent should keep all session data in one shared state object. That state should include the user’s original request, the current search filters, search results, the selected listing, the wardrobe, the chosen outfit suggestion, and the final fit card. Each tool reads from and writes to that state so later steps can reuse earlier results without the user repeating them.

For example, the selected item from search_listings becomes the new_item input to suggest_outfit, and the outfit returned by suggest_outfit becomes the outfit input to create_fit_card. This state should live for the duration of one interaction session so the agent can carry context across multiple tool calls.

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query |Tell the user: “I couldn’t find any listings that match that combination of style, size, and budget. Try loosening one filter, like removing size or raising the max price.” Then stop. |
| suggest_outfit | Wardrobe is empty |Tell the user: “I found the item, but I need at least a few wardrobe pieces to build a full outfit. Add some tops, bottoms, or shoes and try again.” |
| create_fit_card | Tell the user: “I have the item, but the outfit is incomplete, so I can’t generate the final fit card yet. Please provide the missing outfit pieces or let me build a new look first.” |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

+------------------+
|   User Request   |
+------------------+
          |
          v
+------------------+
|  Planning Loop   |
+------------------+
          |
          v
+----------------------+
|   search_listings    |
+----------------------+
     |            |
     |            |
matches      no matches
     |            |
     v            v
+------------------+    +--------------------------+
|  Session State   |    | Explain search failure   |
+------------------+    | and stop                 |
     |
     v
+----------------------+
|   suggest_outfit     |
+----------------------+
     |            |
     |            |
success      empty wardrobe
     |            |
     v            v
+------------------+   +--------------------------+
|  Session State   |   | Ask for wardrobe info    |
+------------------+   +--------------------------+
     |
     v
+----------------------+
|   create_fit_card    |
+----------------------+
     |            |
     |            |
success     incomplete outfit
     |            |
     v            v
+------------------+   +--------------------------+
| Final Response   |   | Request missing details  |
+------------------+   +--------------------------+

Session State stores:
- User query
- Search results
- Selected listing
- Wardrobe
- Outfit suggestion
- Fit card
---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**

I will use ChatGPT or Claude to generate each tool separately. For search_listings, I will give it the Tool 1 section, the fields available in data/listings.json, and the helper functions from utils/data_loader.py, then ask it to implement the filter/ranking logic and structured return object. Before using the code, I will verify that it filters by description, size, and price and that it returns an empty-result response when nothing matches. I will test it with at least one normal query, one no-match query, and one edge case with a missing size.

For suggest_outfit, I will give the Tool 2 section plus the wardrobe schema from data/wardrobe_schema.json, then ask for outfit-generation logic that can handle both a realistic wardrobe and an empty wardrobe. I will verify that it returns full outfit suggestions when possible and a clear failure response when wardrobe data is too limited.

For create_fit_card, I will give the Tool 3 section and a sample outfit object, then ask for caption generation that changes based on the item and outfit details. I will verify that different outfits produce different captions and that the tool does not crash when fields are missing.

**Milestone 4 — Planning loop and state management:**

I will give the AI the Planning Loop section, the State Management section, and the Architecture diagram, then ask it to implement the session logic that chooses which tool to call next based on the latest result. I will verify the generated agent by running the full example flow from search to outfit to fit card, and then by running the error path where search_listings returns no matches to confirm the agent stops early.

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

FitFindr needs to turn a shopper's natural-language request into a listing search, choose a relevant item, style it with the user's wardrobe, and then write a short social-ready fit card. `search_listings` is triggered by the item description and constraints in the user request; if it returns no matches, the agent should explain what to adjust and stop before calling `suggest_outfit`. When a listing is found, `suggest_outfit` is triggered with the selected item and wardrobe, then `create_fit_card` is triggered from the outfit suggestion and new item; failures at either stage should produce a clear fallback instead of pretending the full flow completed.

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
The agent parses the request and extracts:
description = "vintage graphic tee"
size = "M" if the user gave one, otherwise blank
max_price = 30.0
It calls: search_listings(description="vintage graphic tee", size="M", max_price=30.0)

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
search_listings returns a list of matches, for example:
Faded Band Tee — $22, Depop, Good condition
Vintage Rock Tee — $26, Etsy, Fair condition
Graphic Tee — $28, Poshmark, Great condition
The agent stores the full results in session state, selects the top result as selected_item, and calls: suggest_outfit(new_item=selected_item, wardrobe=get_example_wardrobe())

**Step 3:**
<!-- Continue until the full interaction is complete -->
suggest_outfit returns an outfit suggestion such as:
pair the tee with baggy jeans and chunky sneakers
add a cropped jacket or overshirt for layering
roll the sleeves once and tuck one corner for shape
The agent stores the chosen outfit in session state and calls: create_fit_card(outfit=selected_outfit, new_item=selected_item)

**Final output to user:**
<!-- What does the user actually see at the end? -->
The user sees:
the best thrifted item found,
the outfit suggestion,
a short fit card caption such as
"thrifted this faded band tee for $22 and honestly it was made for my baggy jeans"
If the search returns no results, the final output is only a helpful search-failure message and a suggestion to adjust the filters.