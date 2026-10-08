<div align="center">

# ⚽ SquadSync

### Tactical Intelligence & Football Analytics Platform

**Turning football event data into structured, interpretable match, player and tactical intelligence.**

<br>

![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-Visualisation-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Analytics-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active%20Development-orange?style=for-the-badge)

</div>

---

## 🎯 What is SquadSync?

**SquadSync** is a football analytics and tactical intelligence platform designed to move beyond isolated match statistics and transform football event data into structured, measurable and interpretable insights.

Instead of stopping at questions such as **“What happened?”**, SquadSync establishes the analytical foundation required to explore deeper questions around player behaviour, team structure and tactical patterns.

The current implementation is the **7th-semester midterm prototype**, built around a Barcelona-focused dataset derived from **StatsBomb Open Data**.

It provides two distinct experiences:

### 👥 Fan Mode
Built for accessible football exploration and match understanding.

### 🧠 Coach Mode
Built for deeper team, player and tactical analysis.

> **Current status:** The data pipeline, reusable analytics layer and interactive analytics interface are functional. Predictive modelling, recommendation systems and the football-specific AI assistant belong to later development phases.

---

# ✨ Current Capabilities

## 👥 Fan Mode

### 🏠 Home
- Team identity and recent form
- Latest fixture overview
- Recent match cards
- Quick access to football analytics

### 🗓️ Match Browser
Explore available matches using filters such as:

- season
- competition
- result

### 👤 Player Analysis
- Player search
- Appearance information
- Estimated minutes
- Goals and source-supplied xG
- Passing and carry statistics
- Pressure involvement
- Shot-location visualisation

### 🏟️ Match Centre

A match-focused analytical workspace containing:

- score and fixture context
- goal-event information where supported by the data
- match overview
- lineup visualisation
- match statistics
- shot map
- passing network
- tactical views
- event timeline
- optional advanced event data

---

## 🧠 Coach Mode

### 📊 Team Overview
- Win / draw / loss record
- Form trends
- Competition breakdown
- Formation usage
- Historical team overview

### ♟️ Tactical Analysis
- Formation-shape analysis
- Passing-zone distributions
- Pressure-zone distributions
- Progressive carry analysis
- Player involvement
- Formation-change sequences

### 🧬 Player Intelligence
- Sortable squad analytics
- Individual player profiles
- Multi-player comparison
- Performance and involvement indicators

### 🔬 Match Analysis
Coach Mode provides access to the complete Match Centre for deeper match-level inspection.

---

# 🗺️ Football-Native Visual Analytics

SquadSync converts event data into football-oriented visualisations rather than exposing raw tables directly.

### Shot Maps

Recorded shot coordinates are displayed on a football pitch, with source-provided expected-goals values available for shot analysis.

### Passing Networks

Players are represented as **nodes** and completed passing relationships as **weighted edges**.

Node positions are based on average completed-pass origins, while edge strength represents passing volume.

### Formation Views

Recorded lineup positions are mapped to schematic pitch positions to provide an intuitive view of team shape.

### Zone Analysis

Passing and pressure events are grouped spatially to expose where different actions occur across the pitch.

---

# 🏗️ Current Architecture

```text
                     StatsBomb Open Data
                              │
                              ▼
                   Data Processing / ETL
                              │
                              ▼
                      Parquet Cache
                              │
                              ▼
                         Data Loader
                              │
                              ▼
                    Analytics Layer
                 ┌────────────┼────────────┐
                 │            │            │
               Match        Player       Team
                 │            │            │
                 └────────────┼────────────┘
                              │
                           Tactical
                              │
                              ▼
                    Streamlit + Plotly
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
             Fan Mode                 Coach Mode
```

The project deliberately separates **data access**, **analytics** and **presentation**.

Analytics modules do not depend on Streamlit, allowing the underlying football logic to be reused independently of the current interface.

---

# 🔄 Data Pipeline

```text
StatsBomb JSON
      │
      ▼
Selection + Cleaning
      │
      ▼
Transformation
      │
      ▼
Barcelona Parquet Cache
      │
      ▼
Match-Level Data Loader
      │
      ▼
Reusable Analytics
      │
      ▼
Football Visualisations
```

Event-heavy data is partitioned and accessed at match level rather than repeatedly loading the complete event archive at runtime.

This keeps the interactive application lightweight while preserving a reusable analytical foundation.

---

# 📁 Project Structure

```text
SquadSync/
│
├── app.py
│
├── requirements.txt
│
├── README.md
│
├── .gitignore
│
├── analytics/
│   ├── match.py
│   ├── player.py
│   ├── team.py
│   └── tactical.py
│
├── data/
│   ├── build_cache.py
│   └── loader.py
│
├── ui/
│   ├── components.py
│   ├── dashboard.py
│   ├── match_analysis.py
│   ├── player_analysis.py
│   ├── tactical_analysis.py
│   ├── future_sections.py
│   ├── placeholders.py
│   └── theme.py
│
└── tests/
    ├── test_analytics.py
    └── test_match_goals.py
```

Large raw and processed football datasets are intentionally excluded from version control.

---

# 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python |
| **Data Processing** | Pandas, NumPy |
| **Source Data** | StatsBomb Open Data |
| **Raw Format** | JSON |
| **Processed Storage** | Parquet |
| **Parquet Engine** | PyArrow |
| **Application** | Streamlit |
| **Visualisation** | Plotly |
| **Version Control** | Git & GitHub |

---

# 🚀 Running the Project

## 1. Clone the repository

```bash
git clone https://github.com/SuvratJoshi2275/SquadSync.git
cd SquadSync
```

## 2. Create a virtual environment

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Prepare the dataset

The large football datasets are not included in this repository.

After placing the required Barcelona source data in the expected local data directory, build the processed cache:

```bash
python data/build_cache.py --team barcelona
```

## 5. Launch SquadSync

```bash
streamlit run app.py
```

---

# 🧪 Testing

The current prototype includes analytical and regression checks.

```bash
python tests/test_analytics.py
python tests/test_match_goals.py
```

The tests cover core analytics behaviour and regression checking for match-goal attribution logic.

---

# 📊 Data & Analytical Integrity

SquadSync deliberately distinguishes between:

**Observed Data**  
Directly available football events and match information.

**Derived Analytics**  
Metrics and visualisations computed from the available event data.

**Future Model Outputs**  
Predictions, recommendations and AI-generated explanations that require separate implementation and evaluation.

This distinction is important because football event data cannot support every tactical conclusion.

For example:

- source-provided xG is used rather than claiming a SquadSync-trained xG model;
- lineup positions are schematic rather than tracking coordinates;
- event locations are not treated as continuous player tracking;
- unavailable opponent-side event detail is not fabricated;
- tactical views currently report measurable patterns rather than unsupported qualitative narratives.

---

# ⚠️ Current Data Limitations

The current prototype is intentionally scoped around a **Barcelona-focused historical dataset**.

Current limitations include:

- opponent-side event detail is incomplete;
- minutes played are currently estimated and require further validation;
- xG is available only where supplied by source shot events;
- continuous tracking data is not part of the current pipeline;
- StatsBomb 360 data is not currently integrated into the runtime system;
- current analysis uses historical batch data rather than a live football feed.

These constraints define what the current system claims and what remains future work.

---

# 🧭 Development Roadmap

SquadSync is being developed incrementally, with the analytical foundation established before introducing model-driven intelligence.

### ✅ Phase 1 — Analytics Foundation

- [x] StatsBomb data ingestion
- [x] Processed Parquet storage
- [x] Match-level data loading
- [x] Team analytics
- [x] Player analytics
- [x] Match analytics
- [x] Tactical analytics
- [x] Fan Mode
- [x] Coach Mode
- [x] Match Centre
- [x] Shot maps
- [x] Passing networks
- [x] Formation visualisation
- [x] Passing and pressure zones
- [x] Carry progression
- [x] Player comparison

### 🔨 Phase 2 — Feature Engineering & Validation

- [ ] Improved minutes-played calculation
- [ ] Per-90 normalisation
- [ ] Rolling-form features
- [ ] Role-aware player features
- [ ] Opponent-relative features
- [ ] Graph-level passing-network metrics
- [ ] Expanded data-quality validation

### 🧠 Phase 3 — Football Intelligence

- [ ] Player-role classification
- [ ] Player similarity
- [ ] Team-style analysis
- [ ] Opponent analysis
- [ ] Squad intelligence
- [ ] Tactical pattern detection
- [ ] Selected predictive models

### 🤖 Phase 4 — Decision Support & AI

- [ ] Evidence-grounded recommendations
- [ ] Prediction with uncertainty handling
- [ ] Football-specific AI assistant
- [ ] Controlled analytics/model tool calling
- [ ] Evidence synthesis and explanation
- [ ] Retrieval-Augmented Generation for suitable football knowledge sources

### 🔬 Research Directions

These are **not current implementation commitments**:

- Expected Threat (xT)
- Graph Neural Networks
- Tracking-based spatial analysis
- Video understanding
- Near-real-time analytics
- Reinforcement learning
- Multimodal football intelligence

---

# 🧠 Long-Term Vision

SquadSync ultimately aims to progress through an intelligence hierarchy:

```text
Football Data
     ↓
Statistics
     ↓
Features
     ↓
Patterns
     ↓
Tactical Intelligence
     ↓
Context
     ↓
Prediction
     ↓
Decision Support
     ↓
Evidence-Grounded Explanation
```

The intended AI assistant sits **after the intelligence layer**, not in place of it.

Structured football questions should be answered by validated data and analytics. Future model-based questions should be handled by evaluated models. The assistant's role is to orchestrate these capabilities and explain their evidence naturally.

---

# 🎓 Academic Context

SquadSync is being developed as a **B.Tech CSE (Artificial Intelligence & Machine Learning) Major Project** at the **University of Petroleum & Energy Studies (UPES)**.

### Project Team

- **Suvrat Joshi**
- **Sushant Jaiswal**
- **Shivam Venkatesh**

**Project Mentor:** Prof. Lalit Sachan

The current repository represents the project's **7th-semester midterm implementation** and will evolve as subsequent analytics, machine-learning and decision-support modules are developed.

---

<div align="center">

### ⚽ From football events to football intelligence.

**Data → Patterns → Tactics → Decisions**

</div>
