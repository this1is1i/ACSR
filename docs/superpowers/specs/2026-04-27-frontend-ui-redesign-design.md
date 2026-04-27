# Frontend UI Redesign Design

## Background

The current frontend already supports the core product capabilities:

- homepage recommendations
- personalized paper search
- standalone paper detail and TXT download
- knowledge graph / visualization
- research community
- realtime private messaging
- profile management
- administrator tools

However, the UI has grown page-by-page and now feels visually fragmented:

- multiple pages use different density and layout logic
- homepage, search, detail, and admin do not feel like one system
- the current style mixes product dashboard patterns with generic dark cards
- the personal user journey is still too search-led, while the actual product value is recommendation + learning path guidance

The redesign should not only “beautify” the UI. It should reposition the product as a cohesive AI-assisted academic research platform with:

1. a stronger futuristic / technological identity
2. better reading and content comprehension
3. clearer role separation between regular users and administrators
4. a more meaningful information architecture centered on recommendation and learning path progression

## Goals

1. Redesign the frontend into one coherent visual system with a dark, futuristic “future lab” identity.
2. Keep regular-user pages content-readable instead of turning every surface into a dense dashboard.
3. Make personalized recommendation and learning path display the main narrative of the product.
4. Reposition search as an important but secondary capability for goal-driven lookup.
5. Turn the admin experience into a true cockpit-style dashboard that highlights global control and system visibility.
6. Apply the redesign consistently across:
   - home
   - search
   - paper detail
   - knowledge graph / visualization
   - community
   - realtime messaging
   - profile
   - admin

## Non-Goals

- No backend API redesign as part of this UI effort.
- No redefinition of recommendation or learning-path business logic.
- No new major product module outside the existing page set.
- No light-theme-first redesign. Dark theme is the design baseline.
- No gratuitous cyberpunk effects, glitch effects, or decorative sci-fi noise that hurt readability.

## Product Positioning

The product should feel like an **AI-assisted academic operating environment**:

- futuristic, but not game-like
- advanced, but still professional
- immersive, but still readable
- data-aware, but not uniformly dashboard-heavy

The selected direction is:

**Future Lab shell + role-based density**

That means:

- the whole product shares one futuristic dark design system
- ordinary user pages emphasize exploration, recommendation, learning path, reading, and collaboration
- the administrator experience deliberately increases dashboard density and command visibility

## Core Experience Shift

## Old emphasis

- search feels like the main entry point
- recommendation appears as one feature among others
- learning path / knowledge graph feels more like a separate visualization area

## New emphasis

- personalized recommendation and learning path become the main personal guidance layer
- homepage becomes the user’s research hub
- knowledge graph / path views become part of the personal growth narrative
- search becomes a secondary workspace for explicit lookup and targeted filtering

This is the most important product-level change in the redesign.

## Design Principles

### 1. Futuristic shell, readable core

The UI should signal “advanced AI research system” through:

- dark layered backgrounds
- cold accent lighting
- subtle glass and panel depth
- structured information modules

But core content areas must remain easy to read:

- paper titles
- abstracts
- metadata
- conversations
- community posts
- profile information

### 2. One system, different densities

Not every page should have the same density or same emotional intensity.

- regular-user pages: medium density, clear hierarchy, readable spacing
- visualization pages: stronger immersion and motion
- admin pages: high-density operational cockpit

### 3. Recommendation-first personal journey

For ordinary users, the product should answer:

1. what should I read now?
2. where am I in my learning path?
3. what should I explore next?

before asking them to perform explicit search.

### 4. Search as a workspace, not the homepage identity

Search remains important, but it becomes the place users go when they already have an explicit query or need targeted filtering.

### 5. Admin as command center

The admin entry experience should feel fundamentally different from the normal user experience:

- broader visibility
- denser metrics
- faster actionability
- stronger “global state awareness”

## Global Visual System

## Theme strategy

- dark theme is the primary and polished baseline
- light theme is not part of the core redesign scope
- if the existing theme toggle remains, dark mode still receives the primary design treatment

## Color system

The design language should use a layered dark palette instead of flat charcoal cards.

### Base layers

- background base: deep midnight / near-black blue
- elevated surfaces: dark slate / blue-black panels
- muted surfaces: low-contrast dark containers for secondary modules

### Accent layers

- primary brand accent: violet-indigo
- secondary accent: cyan / teal
- success / system-positive: restrained green
- destructive / alerts: red, only for actual risk or error states

### Color behavior

- use glow only around primary focus, active states, key highlights, and graph / cockpit emphasis
- do not let every card glow equally
- preserve strong text contrast across all reading surfaces

## Typography

Typography should express “research technology” without making the UI feel like a terminal.

### Heading behavior

- headings use a more distinctive futuristic / technical display style
- headers and section labels should look more intentional and system-grade

### Body behavior

- body copy remains highly readable sans-serif
- abstracts, posts, and messages should avoid stylized display typography
- long-form reading should prioritize spacing and line-height over visual novelty

## Surface and component language

Cards and containers should follow a clear hierarchy:

### Level 1: primary panels

- used for page shells, major sections, hero modules
- stronger background separation
- subtle blur or surface depth
- consistent border radius

### Level 2: emphasis modules

- used for highlighted recommendation modules, progress summaries, important controls
- slightly stronger border / accent treatment
- optional restrained glow

### Level 3: utility modules

- used for filters, secondary data blocks, metadata, control clusters
- calmer appearance
- reduced visual weight

## Iconography

- replace structural emoji-based UI language with a consistent icon system
- navigation, metrics, actions, and controls should use vector icons with one visual family
- emoji are acceptable only inside user-generated content contexts and must not appear in system navigation, metrics, or structural UI

## Motion

Motion should support orientation and depth, not decoration.

### Allowed motion emphasis

- page entrance rhythm
- panel hover / press feedback
- state changes
- admin dashboard highlight transitions
- graph and path progression states

### Avoid

- glitch effects
- scanline overlays
- high-frequency decorative motion
- heavy glow pulses across the whole page

## Information Architecture Changes

## Top-level product emphasis

For ordinary users, the product hierarchy becomes:

1. personalized hub
2. recommendation and learning path
3. reading and paper detail
4. graph/path exploration
5. community and collaboration
6. search as a supporting workspace

## Navigation implications

The existing left sidebar remains a valid structural pattern, but it should be redesigned to reflect:

- stronger branding
- clearer active state hierarchy
- better role awareness
- better grouping of “explore”, “collaborate”, and “manage” functions

Recommended logical grouping:

### For ordinary users

- Home / Research Hub
- Recommendations / Learning Path
- Search
- Knowledge Graph / Insights
- Community
- Messages
- Profile

### For administrators

- Admin Cockpit
- Review Queue
- Data Import
- User / Permission Control
- System Health / Alerts

The administrator should land in the cockpit first rather than a generic tabbed tool page.

## Page-Level Redesign

## 1. Home page

### New role

The homepage becomes the **Personal Research Hub**.

### New purpose

It should immediately communicate:

- your current recommendation focus
- your current learning path stage
- your next suggested action
- relevant trend or collaboration signals

### Structure

1. top hero / mission strip
   - personalized greeting
   - recommendation summary
   - current learning path snapshot
   - quick path forward
2. main recommendation stream
   - high-quality personalized paper cards
   - clearer reasoning and ranking cues
3. learning path progress module
   - current stage
   - next milestone
   - recommended node / paper / topic
4. secondary insight modules
   - trend signal
   - collaborators
   - recent activity
   - community pulse
5. search entry
   - present, but visually secondary to recommendation/path

### Tone

- advanced
- motivating
- directional

not just “a dashboard with cards”.

## 2. Search page

### New role

The search page becomes an **Auxiliary Search Workspace**.

### New purpose

It serves explicit lookup and targeted filtering after the user leaves the recommendation/path flow.

### Structure

1. strong search command bar at the top
2. stable left filter rail
3. right result workspace
4. result comparison / save / action area
5. strong state visibility for:
   - query
   - result count
   - sort mode
   - active filters

### Design emphasis

- more professional search tooling feel
- less “marketing card wall”
- higher result readability

### Relative priority

Search remains powerful, but should no longer visually dominate the product identity.

## 3. Paper detail page

### New role

The paper detail page becomes a **Reading Canvas**.

### Structure

1. breadcrumb / return context
2. title and core metadata
3. readable abstract and key information
4. right-side or secondary support rail for:
   - TXT download
   - save / action controls
   - related recommendations
   - learning path relationship

### New emphasis

The page should show how the current paper fits into the learning path:

- prerequisite / follow-up relation
- why it matters to the user’s path
- what to read next

This is a key bridge between recommendation, graph, and reading.

## 4. Knowledge graph / visualization page

### New role

This page becomes a **Path and Insight Immersion Zone**.

### Purpose

It should be one of the most futuristic pages in the product, because it carries:

- path visualization
- knowledge relationship exploration
- learning progression
- behavioral insights

### Redesign direction

- preserve the strongest future-lab styling here
- improve focus hierarchy between charts, graph canvas, and path detail
- make the learning-path story more explicit and less buried inside generic analytics

### Personal emphasis

This page should help the user understand:

- where they are
- what concepts connect
- which node matters next

## 5. Community page

### New role

Community becomes a **research discussion layer around papers, topics, and learning progression**.

### Design direction

- less generic social-feed feeling
- stronger paper/topic context
- clearer discussion hierarchy
- better distinction between post status, linked paper context, and action area

### Product role

Community should support the recommendation and learning system, not feel detached from it.

## 6. Realtime messaging page

### New role

Messaging becomes a **collaboration workspace** instead of a plain chat split view.

### Direction

- cleaner contact hierarchy
- stronger conversation readability
- clearer online / activity states
- visual fit with the future-lab system, but calmer than graph or admin

## 7. Profile page

### New role

Profile becomes a **personal research identity and asset page**.

### New emphasis

Profile should foreground:

- recommendation relevance
- learning path progress
- interest distribution
- saved papers / reading assets

instead of feeling like a generic account center.

## 8. Admin experience

### New role

Admin becomes a **Command Cockpit**.

### Entry change

Administrator login should land first on a cockpit-style dashboard.

### Cockpit structure

1. KPI strip
   - pending review count
   - import health
   - active users
   - system events / alerts
2. main operations area
   - review queue overview
   - efficiency trends
   - import / task health
3. action rail
   - urgent approvals
   - alerts
   - risk summary
4. secondary workspaces
   - post review
   - paper import
   - permission management

### Important change

The current tab-first backend is not enough for the target system feel. Tabs can still exist deeper in the admin workflow, but not as the first impression.

## Shared Component Redesign

The following shared surfaces should be redesigned consistently:

- sidebar
- global page headers
- cards
- KPI stats
- paper cards
- search filters
- buttons and action groups
- panel titles and status chips
- tables in admin
- dialog surfaces
- chat contact rows and bubbles

These components should derive from one design-token system instead of page-local styling.

## Accessibility and Usability Requirements

The redesign must preserve or improve:

- strong text contrast on all dark surfaces
- visible active and focus states
- clear hover / press / disabled states
- readable typography for long abstracts and post content
- mobile-safe spacing and responsive layout behavior

The redesign should not trade usability away for effect.

## Implementation Strategy Guidance

The redesign should be implemented as a structured UI-system refactor, not as isolated page paint.

Recommended implementation order:

1. establish design tokens and shared visual primitives
2. redesign shared layout shell and sidebar
3. redesign regular-user primary pages:
   - home
   - search
   - paper detail
   - knowledge graph
4. redesign collaboration pages:
   - community
   - messaging
   - profile
5. redesign admin into cockpit + operational workspaces

## Expected Files To Be Involved

- `frontend/src/style.css`
- `frontend/src/components/Sidebar.vue`
- `frontend/src/components/PaperCard.vue`
- `frontend/src/components/RecommendList.vue`
- `frontend/src/views/Home.vue`
- `frontend/src/views/Search.vue`
- `frontend/src/views/PaperDetail.vue`
- `frontend/src/views/KnowledgeGraph.vue`
- `frontend/src/views/Community.vue`
- `frontend/src/views/RealtimeChat.vue`
- `frontend/src/views/Profile.vue`
- `frontend/src/views/AdminConsole.vue`

Introduce shared UI helper and token files wherever needed to centralize the design system and remove duplicated page-local styling.

## Verification Criteria

The redesign is successful when:

1. the product visibly reads as one coherent system instead of page-by-page styling
2. ordinary-user pages clearly center recommendation and learning path over search
3. search remains strong, but visually secondary to the personalized hub
4. paper detail feels like a reading surface, not just a card page
5. graph / visualization carries the strongest futuristic immersion
6. community, messaging, and profile feel integrated into the same product language
7. administrator entry feels like a command cockpit with clear global control
8. readability remains strong across abstracts, results, posts, and conversations

## Scope Check

This redesign is large but still coherent as a single design initiative because all work supports one outcome:

- one unified visual system
- one clearer user journey
- one stronger separation between personal exploration and administrative control

It should produce one implementation plan with staged execution, rather than multiple unrelated redesign projects.
